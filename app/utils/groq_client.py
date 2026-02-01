"""
Groq API Client Module with Rate Limiting and Retry Logic.

Implements Task 6.1 requirements:
- Rate limiting for Groq API (25 calls/minute with buffer)
- Retry logic with exponential backoff
- Response time measurement
- Support for Hindi and English prompts

Acceptance Criteria:
- Rate limiting prevents API errors
- Retry logic handles transient failures
- Response time <2s per call
"""

import time
import threading
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from datetime import datetime

from app.config import settings
from app.utils.logger import get_logger
from app.utils.metrics import track_response_time, track_error

logger = get_logger(__name__)

# Type variable for generic function return
T = TypeVar("T")

# Default rate limiting configuration
DEFAULT_MAX_CALLS_PER_MINUTE = 25  # Buffer below Groq's 30 limit
DEFAULT_MAX_RETRIES = 3
DEFAULT_BASE_DELAY = 1.0  # seconds
DEFAULT_MAX_DELAY = 30.0  # seconds
DEFAULT_TIMEOUT = 30.0  # seconds

# Response time target
TARGET_RESPONSE_TIME = 2.0  # seconds


class RateLimitError(Exception):
    """Exception raised when rate limit is exceeded and waiting is not desired."""
    
    def __init__(self, message: str, retry_after: float = 0.0):
        super().__init__(message)
        self.retry_after = retry_after


class GroqAPIError(Exception):
    """Exception raised for Groq API errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, retryable: bool = False):
        super().__init__(message)
        self.status_code = status_code
        self.retryable = retryable


class RateLimiter:
    """
    Thread-safe rate limiter using sliding window algorithm.
    
    Limits API calls to a maximum number per minute window.
    When limit is reached, blocks until a slot becomes available.
    
    Attributes:
        max_calls: Maximum calls allowed per minute
        calls: List of call timestamps
        lock: Thread lock for synchronization
    """
    
    def __init__(self, max_calls_per_minute: int = DEFAULT_MAX_CALLS_PER_MINUTE):
        """
        Initialize the rate limiter.
        
        Args:
            max_calls_per_minute: Maximum API calls allowed per minute
        """
        self.max_calls = max_calls_per_minute
        self.calls: List[float] = []
        self.lock = threading.Lock()
        
        logger.info(f"RateLimiter initialized: {max_calls_per_minute} calls/minute")
    
    def acquire(self, block: bool = True) -> bool:
        """
        Acquire a rate limit slot.
        
        Args:
            block: Whether to block until slot is available
            
        Returns:
            True if slot acquired, False if non-blocking and limit exceeded
            
        Raises:
            RateLimitError: If block=False and limit exceeded
        """
        with self.lock:
            now = time.time()
            
            # Remove calls older than 60 seconds
            self.calls = [c for c in self.calls if c > now - 60]
            
            if len(self.calls) >= self.max_calls:
                if not block:
                    wait_time = 60 - (now - self.calls[0])
                    raise RateLimitError(
                        f"Rate limit exceeded: {len(self.calls)}/{self.max_calls}",
                        retry_after=wait_time,
                    )
                
                # Calculate sleep time
                sleep_time = 60 - (now - self.calls[0]) + 0.1  # Small buffer
                
                logger.warning(
                    f"Rate limit reached ({len(self.calls)}/{self.max_calls}), "
                    f"sleeping for {sleep_time:.2f}s"
                )
                
                # Release lock while sleeping
                self.lock.release()
                try:
                    time.sleep(sleep_time)
                finally:
                    self.lock.acquire()
                
                # Update now and clean up again
                now = time.time()
                self.calls = [c for c in self.calls if c > now - 60]
            
            # Record this call
            self.calls.append(now)
            
            return True
    
    def get_current_usage(self) -> Dict[str, Any]:
        """
        Get current rate limit usage.
        
        Returns:
            Dict with current usage statistics
        """
        with self.lock:
            now = time.time()
            active_calls = [c for c in self.calls if c > now - 60]
            
            return {
                "current_calls": len(active_calls),
                "max_calls": self.max_calls,
                "remaining": self.max_calls - len(active_calls),
                "reset_in_seconds": 60 - (now - active_calls[0]) if active_calls else 0,
            }
    
    def reset(self) -> None:
        """Reset the rate limiter (for testing)."""
        with self.lock:
            self.calls = []
    
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Use as decorator to rate limit function calls.
        
        Args:
            func: Function to decorate
            
        Returns:
            Decorated function
        """
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            self.acquire(block=True)
            return func(*args, **kwargs)
        
        return wrapper


def exponential_backoff(
    attempt: int,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
) -> float:
    """
    Calculate exponential backoff delay.
    
    Uses exponential backoff with jitter for optimal retry timing.
    
    Args:
        attempt: Current attempt number (0-indexed)
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        
    Returns:
        Delay in seconds
    """
    import random
    
    # Calculate exponential delay with jitter
    delay = min(base_delay * (2 ** attempt), max_delay)
    
    # Add jitter (up to 25% of delay)
    jitter = delay * 0.25 * random.random()
    
    return delay + jitter


def is_retryable_error(error: Exception) -> bool:
    """
    Check if an error is retryable.
    
    Args:
        error: Exception to check
        
    Returns:
        True if error should be retried
    """
    error_str = str(error).lower()
    
    # Rate limit errors are retryable
    if "rate_limit" in error_str or "rate limit" in error_str:
        return True
    
    # Timeout errors are retryable
    if "timeout" in error_str:
        return True
    
    # Connection errors are retryable
    if "connection" in error_str or "network" in error_str:
        return True
    
    # Server errors (5xx) are generally retryable
    if "500" in error_str or "502" in error_str or "503" in error_str or "504" in error_str:
        return True
    
    # Check for GroqAPIError
    if isinstance(error, GroqAPIError):
        return error.retryable
    
    return False


def retry_with_backoff(
    max_retries: int = DEFAULT_MAX_RETRIES,
    base_delay: float = DEFAULT_BASE_DELAY,
    max_delay: float = DEFAULT_MAX_DELAY,
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator factory for retry with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries
        max_delay: Maximum delay between retries
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_error: Optional[Exception] = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    
                    if not is_retryable_error(e):
                        logger.error(f"Non-retryable error on attempt {attempt + 1}: {e}")
                        raise
                    
                    if attempt < max_retries - 1:
                        delay = exponential_backoff(attempt, base_delay, max_delay)
                        logger.warning(
                            f"Retryable error on attempt {attempt + 1}/{max_retries}: {e}. "
                            f"Retrying in {delay:.2f}s"
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"Max retries ({max_retries}) exceeded: {e}")
            
            # Raise the last error
            if last_error:
                raise last_error
            
            raise RuntimeError("Unexpected state in retry logic")
        
        return wrapper
    
    return decorator


class GroqClient:
    """
    High-level Groq API client with rate limiting and retry logic.
    
    Provides a robust interface to the Groq LLM API with:
    - Automatic rate limiting
    - Exponential backoff retry
    - Response time tracking
    - Multi-language support
    
    Attributes:
        llm: Underlying LangChain Groq LLM
        rate_limiter: Rate limiter instance
        max_retries: Maximum retry attempts
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_calls_per_minute: int = DEFAULT_MAX_CALLS_PER_MINUTE,
        max_retries: int = DEFAULT_MAX_RETRIES,
    ):
        """
        Initialize the Groq client.
        
        Args:
            api_key: Groq API key (defaults to settings)
            model: Model name (defaults to settings)
            temperature: Generation temperature (defaults to settings)
            max_tokens: Maximum tokens (defaults to settings)
            max_calls_per_minute: Rate limit
            max_retries: Maximum retry attempts
        """
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        self.temperature = temperature if temperature is not None else settings.GROQ_TEMPERATURE
        self.max_tokens = max_tokens or settings.GROQ_MAX_TOKENS
        
        self.rate_limiter = RateLimiter(max_calls_per_minute)
        self.max_retries = max_retries
        
        self.llm = None
        self._initialized = False
        
        if self.api_key:
            self._initialize_llm()
    
    def _initialize_llm(self) -> None:
        """Initialize the LangChain Groq LLM."""
        try:
            from langchain_groq import ChatGroq
            
            self.llm = ChatGroq(
                model=self.model,
                api_key=self.api_key,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            self._initialized = True
            
            logger.info(f"GroqClient initialized: model={self.model}")
            
        except ImportError as e:
            logger.error(f"Failed to import langchain_groq: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize GroqClient: {e}")
            raise
    
    @property
    def is_available(self) -> bool:
        """Check if the client is available for calls."""
        return self._initialized and self.llm is not None
    
    def invoke(
        self,
        messages: List[Dict[str, str]],
        language: str = "en",
    ) -> str:
        """
        Invoke the LLM with rate limiting and retry.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            language: Expected response language ('en' or 'hi')
            
        Returns:
            Generated response text
            
        Raises:
            GroqAPIError: If API call fails after retries
            RateLimitError: If rate limit exceeded and non-blocking
        """
        if not self.is_available:
            raise GroqAPIError("GroqClient not initialized", retryable=False)
        
        return self._invoke_with_rate_limit_and_retry(messages, language)
    
    def _invoke_with_rate_limit_and_retry(
        self,
        messages: List[Dict[str, str]],
        language: str,
    ) -> str:
        """
        Internal invoke with rate limiting and retry.
        
        Args:
            messages: LLM messages
            language: Response language
            
        Returns:
            Generated text
        """
        last_error: Optional[Exception] = None
        
        for attempt in range(self.max_retries):
            try:
                # Acquire rate limit slot
                self.rate_limiter.acquire(block=True)
                
                # Measure response time
                start_time = time.time()
                
                try:
                    # Convert messages to LangChain format
                    from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
                    
                    lc_messages = []
                    for msg in messages:
                        role = msg.get("role", "user")
                        content = msg.get("content", "")
                        
                        if role == "system":
                            lc_messages.append(SystemMessage(content=content))
                        elif role == "assistant":
                            lc_messages.append(AIMessage(content=content))
                        else:
                            lc_messages.append(HumanMessage(content=content))
                    
                    # Make API call
                    response = self.llm.invoke(lc_messages)
                    
                    # Track response time
                    elapsed = time.time() - start_time
                    track_response_time(elapsed)
                    
                    # Log if response time exceeds target
                    if elapsed > TARGET_RESPONSE_TIME:
                        logger.warning(
                            f"Response time {elapsed:.2f}s exceeds target {TARGET_RESPONSE_TIME}s"
                        )
                    else:
                        logger.debug(f"Groq API response in {elapsed:.2f}s")
                    
                    # Extract content
                    if hasattr(response, "content"):
                        return response.content
                    return str(response)
                    
                except Exception as e:
                    elapsed = time.time() - start_time
                    track_response_time(elapsed)
                    raise
                
            except Exception as e:
                last_error = e
                track_error("groq_api_error")
                
                if not is_retryable_error(e):
                    logger.error(f"Non-retryable Groq error: {e}")
                    raise GroqAPIError(str(e), retryable=False)
                
                if attempt < self.max_retries - 1:
                    delay = exponential_backoff(attempt)
                    logger.warning(
                        f"Groq API error (attempt {attempt + 1}/{self.max_retries}): {e}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    time.sleep(delay)
                else:
                    logger.error(f"Groq API failed after {self.max_retries} attempts: {e}")
        
        if last_error:
            raise GroqAPIError(str(last_error), retryable=True)
        
        raise GroqAPIError("Unknown error in Groq API call", retryable=False)
    
    def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        language: str = "en",
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """
        Generate a response with proper message formatting.
        
        Args:
            system_prompt: System prompt text
            user_message: User message text
            language: Response language
            conversation_history: Optional previous messages
            
        Returns:
            Generated response text
        """
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if provided
        if conversation_history:
            for msg in conversation_history:
                role = msg.get("sender", "user")
                if role == "scammer":
                    role = "user"
                elif role == "agent":
                    role = "assistant"
                
                messages.append({
                    "role": role,
                    "content": msg.get("message", msg.get("content", "")),
                })
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        return self.invoke(messages, language=language)
    
    def get_rate_limit_status(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        return self.rate_limiter.get_current_usage()
    
    def reset_rate_limiter(self) -> None:
        """Reset the rate limiter (for testing)."""
        self.rate_limiter.reset()


# Rate limiter decorator for use with existing LLM instances
_default_rate_limiter = RateLimiter(DEFAULT_MAX_CALLS_PER_MINUTE)


@_default_rate_limiter
@retry_with_backoff(max_retries=DEFAULT_MAX_RETRIES)
def call_groq_with_retry(
    llm: Any,
    messages: List[Any],
    timeout: float = DEFAULT_TIMEOUT,
) -> Any:
    """
    Call Groq API with rate limiting and retry logic.
    
    This is a convenience function for calling existing LLM instances
    with proper rate limiting and retry.
    
    Args:
        llm: LangChain Groq LLM instance
        messages: List of LangChain messages
        timeout: Request timeout in seconds
        
    Returns:
        LLM response object
        
    Raises:
        GroqAPIError: If call fails after retries
    """
    start_time = time.time()
    
    try:
        response = llm.invoke(messages)
        
        elapsed = time.time() - start_time
        track_response_time(elapsed)
        
        if elapsed > TARGET_RESPONSE_TIME:
            logger.warning(f"Response time {elapsed:.2f}s exceeds {TARGET_RESPONSE_TIME}s target")
        
        return response
        
    except Exception as e:
        elapsed = time.time() - start_time
        track_response_time(elapsed)
        track_error("groq_api_error")
        raise


def reset_rate_limiter() -> None:
    """Reset the default rate limiter (for testing)."""
    _default_rate_limiter.reset()


def get_rate_limit_status() -> Dict[str, Any]:
    """Get default rate limiter status."""
    return _default_rate_limiter.get_current_usage()


# Singleton client instance
_groq_client: Optional[GroqClient] = None


def get_groq_client() -> GroqClient:
    """
    Get singleton Groq client instance.
    
    Returns:
        GroqClient instance
    """
    global _groq_client
    
    if _groq_client is None:
        _groq_client = GroqClient()
    
    return _groq_client


def reset_groq_client() -> None:
    """Reset the singleton client (for testing)."""
    global _groq_client
    _groq_client = None

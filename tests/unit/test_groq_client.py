"""
Unit Tests for Groq API Client Module.

Tests Task 6.1 implementation:
- Rate limiting for Groq API
- Retry logic with exponential backoff
- Hindi and English prompt support
- Response time measurement

Acceptance Criteria:
- Rate limiting prevents API errors
- Retry logic handles transient failures
- Response time <2s per call
"""

import os
import time
import threading
import pytest
from unittest.mock import patch, MagicMock, PropertyMock

from app.utils.groq_client import (
    RateLimiter,
    RateLimitError,
    GroqAPIError,
    GroqClient,
    call_groq_with_retry,
    get_groq_client,
    reset_groq_client,
    reset_rate_limiter,
    get_rate_limit_status,
    exponential_backoff,
    is_retryable_error,
    retry_with_backoff,
    DEFAULT_MAX_CALLS_PER_MINUTE,
    DEFAULT_MAX_RETRIES,
    TARGET_RESPONSE_TIME,
)


# ============================================================================
# RateLimiter Tests
# ============================================================================

class TestRateLimiter:
    """Tests for RateLimiter class."""
    
    def test_rate_limiter_initialization(self):
        """Test RateLimiter initialization with default values."""
        limiter = RateLimiter()
        
        assert limiter.max_calls == DEFAULT_MAX_CALLS_PER_MINUTE
        assert limiter.calls == []
    
    def test_rate_limiter_custom_max_calls(self):
        """Test RateLimiter initialization with custom max calls."""
        limiter = RateLimiter(max_calls_per_minute=10)
        
        assert limiter.max_calls == 10
    
    def test_rate_limiter_acquire_single_call(self):
        """Test acquiring a single rate limit slot."""
        limiter = RateLimiter(max_calls_per_minute=5)
        
        result = limiter.acquire(block=True)
        
        assert result is True
        assert len(limiter.calls) == 1
    
    def test_rate_limiter_acquire_multiple_calls(self):
        """Test acquiring multiple rate limit slots."""
        limiter = RateLimiter(max_calls_per_minute=5)
        
        for i in range(3):
            result = limiter.acquire(block=True)
            assert result is True
        
        assert len(limiter.calls) == 3
    
    def test_rate_limiter_raises_when_limit_exceeded_non_blocking(self):
        """Test RateLimitError is raised when limit exceeded with block=False."""
        limiter = RateLimiter(max_calls_per_minute=3)
        
        # Fill up the limit
        for _ in range(3):
            limiter.acquire(block=True)
        
        # Next call should raise
        with pytest.raises(RateLimitError) as exc_info:
            limiter.acquire(block=False)
        
        assert "Rate limit exceeded" in str(exc_info.value)
        assert exc_info.value.retry_after > 0
    
    def test_rate_limiter_get_current_usage(self):
        """Test getting current usage statistics."""
        limiter = RateLimiter(max_calls_per_minute=10)
        
        for _ in range(5):
            limiter.acquire(block=True)
        
        usage = limiter.get_current_usage()
        
        assert usage["current_calls"] == 5
        assert usage["max_calls"] == 10
        assert usage["remaining"] == 5
    
    def test_rate_limiter_reset(self):
        """Test resetting the rate limiter."""
        limiter = RateLimiter(max_calls_per_minute=5)
        
        for _ in range(3):
            limiter.acquire(block=True)
        
        assert len(limiter.calls) == 3
        
        limiter.reset()
        
        assert len(limiter.calls) == 0
    
    def test_rate_limiter_as_decorator(self):
        """Test RateLimiter as a function decorator."""
        limiter = RateLimiter(max_calls_per_minute=5)
        call_count = 0
        
        @limiter
        def test_func():
            nonlocal call_count
            call_count += 1
            return "result"
        
        for _ in range(3):
            result = test_func()
            assert result == "result"
        
        assert call_count == 3
        assert len(limiter.calls) == 3
    
    def test_rate_limiter_cleans_old_calls(self):
        """Test that old calls are cleaned from the window."""
        limiter = RateLimiter(max_calls_per_minute=5)
        
        # Add an old call (61 seconds ago)
        old_time = time.time() - 61
        limiter.calls.append(old_time)
        
        # Acquire should clean up the old call
        limiter.acquire(block=True)
        
        # Only the new call should remain
        assert len(limiter.calls) == 1
        assert limiter.calls[0] > old_time
    
    def test_rate_limiter_thread_safety(self):
        """Test that rate limiter is thread-safe."""
        limiter = RateLimiter(max_calls_per_minute=100)
        results = []
        
        def worker():
            result = limiter.acquire(block=True)
            results.append(result)
        
        threads = [threading.Thread(target=worker) for _ in range(10)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        assert len(results) == 10
        assert all(r is True for r in results)


# ============================================================================
# Exponential Backoff Tests
# ============================================================================

class TestExponentialBackoff:
    """Tests for exponential backoff calculation."""
    
    def test_exponential_backoff_first_attempt(self):
        """Test backoff delay for first attempt."""
        delay = exponential_backoff(0, base_delay=1.0, max_delay=30.0)
        
        # First attempt: 1.0 + jitter (up to 0.25)
        assert 1.0 <= delay <= 1.25
    
    def test_exponential_backoff_second_attempt(self):
        """Test backoff delay for second attempt."""
        delay = exponential_backoff(1, base_delay=1.0, max_delay=30.0)
        
        # Second attempt: 2.0 + jitter (up to 0.5)
        assert 2.0 <= delay <= 2.5
    
    def test_exponential_backoff_third_attempt(self):
        """Test backoff delay for third attempt."""
        delay = exponential_backoff(2, base_delay=1.0, max_delay=30.0)
        
        # Third attempt: 4.0 + jitter (up to 1.0)
        assert 4.0 <= delay <= 5.0
    
    def test_exponential_backoff_respects_max_delay(self):
        """Test that backoff respects maximum delay."""
        delay = exponential_backoff(10, base_delay=1.0, max_delay=5.0)
        
        # Should be capped at 5.0 + jitter (up to 1.25)
        assert delay <= 6.25
    
    def test_exponential_backoff_custom_base_delay(self):
        """Test backoff with custom base delay."""
        delay = exponential_backoff(0, base_delay=2.0, max_delay=60.0)
        
        # First attempt: 2.0 + jitter (up to 0.5)
        assert 2.0 <= delay <= 2.5


# ============================================================================
# Error Classification Tests
# ============================================================================

class TestIsRetryableError:
    """Tests for error classification."""
    
    def test_rate_limit_error_is_retryable(self):
        """Test that rate limit errors are retryable."""
        error = Exception("Rate limit exceeded")
        assert is_retryable_error(error) is True
        
        error = Exception("rate_limit_error: too many requests")
        assert is_retryable_error(error) is True
    
    def test_timeout_error_is_retryable(self):
        """Test that timeout errors are retryable."""
        error = Exception("Request timeout")
        assert is_retryable_error(error) is True
    
    def test_connection_error_is_retryable(self):
        """Test that connection errors are retryable."""
        error = Exception("Connection refused")
        assert is_retryable_error(error) is True
        
        error = Exception("Network error")
        assert is_retryable_error(error) is True
    
    def test_server_5xx_errors_are_retryable(self):
        """Test that server 5xx errors are retryable."""
        for code in ["500", "502", "503", "504"]:
            error = Exception(f"HTTP {code} Internal Server Error")
            assert is_retryable_error(error) is True
    
    def test_client_error_not_retryable(self):
        """Test that generic client errors are not retryable."""
        error = Exception("Invalid API key")
        assert is_retryable_error(error) is False
        
        error = Exception("Bad request")
        assert is_retryable_error(error) is False
    
    def test_groq_api_error_retryable_flag(self):
        """Test GroqAPIError with retryable flag."""
        error = GroqAPIError("Error", retryable=True)
        assert is_retryable_error(error) is True
        
        error = GroqAPIError("Error", retryable=False)
        assert is_retryable_error(error) is False


# ============================================================================
# Retry Decorator Tests
# ============================================================================

class TestRetryWithBackoff:
    """Tests for retry_with_backoff decorator."""
    
    def test_retry_succeeds_on_first_attempt(self):
        """Test that successful call returns immediately."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def successful_func():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = successful_func()
        
        assert result == "success"
        assert call_count == 1
    
    def test_retry_succeeds_on_second_attempt(self):
        """Test retry succeeds after transient failure."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def transient_failure():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("rate_limit error")
            return "success"
        
        result = transient_failure()
        
        assert result == "success"
        assert call_count == 2
    
    def test_retry_exhausts_retries(self):
        """Test that all retries are exhausted before failing."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def always_fails():
            nonlocal call_count
            call_count += 1
            raise Exception("rate_limit persistent failure")
        
        with pytest.raises(Exception) as exc_info:
            always_fails()
        
        assert "persistent failure" in str(exc_info.value)
        assert call_count == 3
    
    def test_retry_does_not_retry_non_retryable_error(self):
        """Test that non-retryable errors fail immediately."""
        call_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def non_retryable_error():
            nonlocal call_count
            call_count += 1
            raise Exception("Invalid API key")
        
        with pytest.raises(Exception):
            non_retryable_error()
        
        assert call_count == 1


# ============================================================================
# GroqAPIError Tests
# ============================================================================

class TestGroqAPIError:
    """Tests for GroqAPIError exception."""
    
    def test_groq_api_error_basic(self):
        """Test basic GroqAPIError creation."""
        error = GroqAPIError("Test error")
        
        assert str(error) == "Test error"
        assert error.status_code is None
        assert error.retryable is False
    
    def test_groq_api_error_with_status_code(self):
        """Test GroqAPIError with status code."""
        error = GroqAPIError("Rate limited", status_code=429, retryable=True)
        
        assert error.status_code == 429
        assert error.retryable is True


# ============================================================================
# RateLimitError Tests
# ============================================================================

class TestRateLimitError:
    """Tests for RateLimitError exception."""
    
    def test_rate_limit_error_basic(self):
        """Test basic RateLimitError creation."""
        error = RateLimitError("Limit exceeded")
        
        assert str(error) == "Limit exceeded"
        assert error.retry_after == 0.0
    
    def test_rate_limit_error_with_retry_after(self):
        """Test RateLimitError with retry_after."""
        error = RateLimitError("Limit exceeded", retry_after=30.5)
        
        assert error.retry_after == 30.5


# ============================================================================
# GroqClient Tests
# ============================================================================

class TestGroqClient:
    """Tests for GroqClient class."""
    
    def test_client_initialization_without_api_key(self):
        """Test client initialization without API key."""
        with patch.dict(os.environ, {}, clear=False):
            with patch("app.utils.groq_client.settings") as mock_settings:
                mock_settings.GROQ_API_KEY = None
                mock_settings.GROQ_MODEL = "test-model"
                mock_settings.GROQ_TEMPERATURE = 0.7
                mock_settings.GROQ_MAX_TOKENS = 500
                
                client = GroqClient(api_key=None)
                
                assert client.is_available is False
    
    def test_client_initialization_with_api_key(self):
        """Test client initialization with API key."""
        with patch("langchain_groq.ChatGroq") as MockChatGroq:
            mock_llm = MagicMock()
            MockChatGroq.return_value = mock_llm
            
            client = GroqClient(api_key="test_key")
            
            assert client.is_available is True
            MockChatGroq.assert_called_once()
    
    def test_client_rate_limiter_instance(self):
        """Test client has rate limiter instance."""
        with patch("langchain_groq.ChatGroq"):
            client = GroqClient(api_key="test_key", max_calls_per_minute=10)
            
            assert isinstance(client.rate_limiter, RateLimiter)
            assert client.rate_limiter.max_calls == 10
    
    def test_client_get_rate_limit_status(self):
        """Test getting rate limit status from client."""
        with patch("langchain_groq.ChatGroq"):
            client = GroqClient(api_key="test_key", max_calls_per_minute=20)
            
            status = client.get_rate_limit_status()
            
            assert status["max_calls"] == 20
            assert status["remaining"] == 20
    
    def test_client_reset_rate_limiter(self):
        """Test resetting client's rate limiter."""
        with patch("langchain_groq.ChatGroq"):
            client = GroqClient(api_key="test_key")
            
            # Make some calls to fill the limiter
            client.rate_limiter.acquire()
            client.rate_limiter.acquire()
            
            assert len(client.rate_limiter.calls) == 2
            
            client.reset_rate_limiter()
            
            assert len(client.rate_limiter.calls) == 0
    
    def test_client_invoke_without_initialization(self):
        """Test invoke raises error when client not initialized."""
        client = GroqClient(api_key=None)
        client._initialized = False
        
        with pytest.raises(GroqAPIError) as exc_info:
            client.invoke([{"role": "user", "content": "test"}])
        
        assert "not initialized" in str(exc_info.value)
    
    def test_client_invoke_success(self):
        """Test successful invoke call."""
        with patch("langchain_groq.ChatGroq") as MockChatGroq:
            mock_response = MagicMock()
            mock_response.content = "Test response"
            
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = mock_response
            MockChatGroq.return_value = mock_llm
            
            client = GroqClient(api_key="test_key")
            
            result = client.invoke([
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "Hello"},
            ])
            
            assert result == "Test response"
    
    def test_client_invoke_with_hindi_prompt(self):
        """Test invoke with Hindi language prompt."""
        with patch("langchain_groq.ChatGroq") as MockChatGroq:
            mock_response = MagicMock()
            mock_response.content = "नमस्ते, मैं आपकी मदद कर सकता हूं"
            
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = mock_response
            MockChatGroq.return_value = mock_llm
            
            client = GroqClient(api_key="test_key")
            
            result = client.invoke([
                {"role": "user", "content": "नमस्ते"},
            ], language="hi")
            
            assert "नमस्ते" in result
    
    def test_client_generate_response(self):
        """Test generate_response helper method."""
        with patch("langchain_groq.ChatGroq") as MockChatGroq:
            mock_response = MagicMock()
            mock_response.content = "Generated response"
            
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = mock_response
            MockChatGroq.return_value = mock_llm
            
            client = GroqClient(api_key="test_key")
            
            result = client.generate_response(
                system_prompt="You are a helpful assistant",
                user_message="How are you?",
                language="en",
            )
            
            assert result == "Generated response"
    
    def test_client_generate_response_with_history(self):
        """Test generate_response with conversation history."""
        with patch("langchain_groq.ChatGroq") as MockChatGroq:
            mock_response = MagicMock()
            mock_response.content = "Response with context"
            
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = mock_response
            MockChatGroq.return_value = mock_llm
            
            client = GroqClient(api_key="test_key")
            
            history = [
                {"sender": "scammer", "message": "Hello"},
                {"sender": "agent", "message": "Hi there"},
            ]
            
            result = client.generate_response(
                system_prompt="You are helpful",
                user_message="What's up?",
                conversation_history=history,
            )
            
            assert result == "Response with context"
            
            # Verify the LLM was called with proper message structure
            call_args = mock_llm.invoke.call_args[0][0]
            assert len(call_args) == 4  # system + 2 history + user


# ============================================================================
# Module-level Function Tests
# ============================================================================

class TestModuleFunctions:
    """Tests for module-level convenience functions."""
    
    def setup_method(self):
        """Reset state before each test."""
        reset_rate_limiter()
        reset_groq_client()
    
    def test_get_rate_limit_status(self):
        """Test getting module-level rate limit status."""
        status = get_rate_limit_status()
        
        assert "current_calls" in status
        assert "max_calls" in status
        assert "remaining" in status
    
    def test_reset_rate_limiter(self):
        """Test resetting module-level rate limiter."""
        # This should not raise
        reset_rate_limiter()
        
        status = get_rate_limit_status()
        assert status["current_calls"] == 0
    
    def test_get_groq_client_singleton(self):
        """Test singleton pattern for GroqClient."""
        with patch("langchain_groq.ChatGroq"):
            with patch("app.utils.groq_client.settings") as mock_settings:
                mock_settings.GROQ_API_KEY = "test_key"
                mock_settings.GROQ_MODEL = "test-model"
                mock_settings.GROQ_TEMPERATURE = 0.7
                mock_settings.GROQ_MAX_TOKENS = 500
                
                client1 = get_groq_client()
                client2 = get_groq_client()
                
                assert client1 is client2
    
    def test_reset_groq_client(self):
        """Test resetting singleton client."""
        with patch("langchain_groq.ChatGroq"):
            with patch("app.utils.groq_client.settings") as mock_settings:
                mock_settings.GROQ_API_KEY = "test_key"
                mock_settings.GROQ_MODEL = "test-model"
                mock_settings.GROQ_TEMPERATURE = 0.7
                mock_settings.GROQ_MAX_TOKENS = 500
                
                client1 = get_groq_client()
                reset_groq_client()
                client2 = get_groq_client()
                
                assert client1 is not client2


# ============================================================================
# call_groq_with_retry Function Tests
# ============================================================================

class TestCallGroqWithRetry:
    """Tests for call_groq_with_retry convenience function."""
    
    def setup_method(self):
        """Reset state before each test."""
        reset_rate_limiter()
    
    def test_call_groq_with_retry_success(self):
        """Test successful Groq API call."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test response"
        mock_llm.invoke.return_value = mock_response
        
        result = call_groq_with_retry(mock_llm, [])
        
        assert result.content == "Test response"
    
    def test_call_groq_with_retry_tracks_response_time(self):
        """Test that response time is tracked."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_llm.invoke.return_value = mock_response
        
        with patch("app.utils.groq_client.track_response_time") as mock_track:
            call_groq_with_retry(mock_llm, [])
            
            mock_track.assert_called_once()
            # Verify duration is a float
            duration = mock_track.call_args[0][0]
            assert isinstance(duration, float)


# ============================================================================
# Acceptance Criteria Tests
# ============================================================================

class TestAcceptanceCriteria:
    """Tests for Task 6.1 acceptance criteria."""
    
    def setup_method(self):
        """Reset state before each test."""
        reset_rate_limiter()
        reset_groq_client()
    
    def test_ac_rate_limiting_prevents_api_errors(self):
        """AC: Rate limiting prevents API errors."""
        limiter = RateLimiter(max_calls_per_minute=3)
        
        # Should allow up to max calls
        for _ in range(3):
            assert limiter.acquire(block=False) is True
        
        # Next call should be blocked
        with pytest.raises(RateLimitError):
            limiter.acquire(block=False)
    
    def test_ac_retry_logic_handles_transient_failures(self):
        """AC: Retry logic handles transient failures."""
        attempt_count = 0
        
        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def flaky_call():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise Exception("rate_limit exceeded")
            return "success"
        
        result = flaky_call()
        
        assert result == "success"
        assert attempt_count == 3
    
    def test_ac_response_time_target(self):
        """AC: Response time target is defined."""
        assert TARGET_RESPONSE_TIME == 2.0
    
    def test_ac_default_rate_limit_within_groq_limits(self):
        """AC: Default rate limit (25) is below Groq's limit (30)."""
        assert DEFAULT_MAX_CALLS_PER_MINUTE == 25
        assert DEFAULT_MAX_CALLS_PER_MINUTE < 30


# ============================================================================
# Hindi and English Prompt Tests
# ============================================================================

class TestMultiLanguageSupport:
    """Tests for Hindi and English prompt support."""
    
    def test_english_prompt_handling(self):
        """Test English prompt is handled correctly."""
        with patch("langchain_groq.ChatGroq") as MockChatGroq:
            mock_response = MagicMock()
            mock_response.content = "Hello, how can I help you?"
            
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = mock_response
            MockChatGroq.return_value = mock_llm
            
            client = GroqClient(api_key="test_key")
            
            result = client.invoke([
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello, please help me."},
            ], language="en")
            
            assert result == "Hello, how can I help you?"
    
    def test_hindi_prompt_handling(self):
        """Test Hindi prompt is handled correctly."""
        with patch("langchain_groq.ChatGroq") as MockChatGroq:
            mock_response = MagicMock()
            mock_response.content = "नमस्ते, मैं आपकी मदद कर सकता हूं।"
            
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = mock_response
            MockChatGroq.return_value = mock_llm
            
            client = GroqClient(api_key="test_key")
            
            result = client.invoke([
                {"role": "system", "content": "आप एक सहायक हैं।"},
                {"role": "user", "content": "नमस्ते, कृपया मेरी मदद करें।"},
            ], language="hi")
            
            assert "नमस्ते" in result
    
    def test_hinglish_prompt_handling(self):
        """Test Hinglish (mixed) prompt is handled correctly."""
        with patch("langchain_groq.ChatGroq") as MockChatGroq:
            mock_response = MagicMock()
            mock_response.content = "Sure, main aapki help karunga"
            
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = mock_response
            MockChatGroq.return_value = mock_llm
            
            client = GroqClient(api_key="test_key")
            
            result = client.invoke([
                {"role": "user", "content": "Please meri help karo"},
            ], language="hinglish")
            
            assert result == "Sure, main aapki help karunga"


# ============================================================================
# Edge Cases Tests
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_message_list(self):
        """Test handling of empty message list."""
        with patch("langchain_groq.ChatGroq") as MockChatGroq:
            mock_response = MagicMock()
            mock_response.content = "Empty response"
            
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = mock_response
            MockChatGroq.return_value = mock_llm
            
            client = GroqClient(api_key="test_key")
            
            result = client.invoke([])
            
            assert result == "Empty response"
    
    def test_very_long_message(self):
        """Test handling of very long messages."""
        with patch("langchain_groq.ChatGroq") as MockChatGroq:
            mock_response = MagicMock()
            mock_response.content = "Response to long message"
            
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = mock_response
            MockChatGroq.return_value = mock_llm
            
            client = GroqClient(api_key="test_key")
            
            long_message = "A" * 10000  # 10K characters
            
            result = client.invoke([
                {"role": "user", "content": long_message},
            ])
            
            assert result == "Response to long message"
    
    def test_special_characters_in_message(self):
        """Test handling of special characters."""
        with patch("langchain_groq.ChatGroq") as MockChatGroq:
            mock_response = MagicMock()
            mock_response.content = "Processed special chars"
            
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = mock_response
            MockChatGroq.return_value = mock_llm
            
            client = GroqClient(api_key="test_key")
            
            special_message = "Hello! @#$%^&*() 你好 مرحبا"
            
            result = client.invoke([
                {"role": "user", "content": special_message},
            ])
            
            assert result == "Processed special chars"
    
    def test_response_without_content_attribute(self):
        """Test handling of response without content attribute."""
        with patch("langchain_groq.ChatGroq") as MockChatGroq:
            mock_response = "Plain string response"
            
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = mock_response
            MockChatGroq.return_value = mock_llm
            
            client = GroqClient(api_key="test_key")
            
            result = client.invoke([
                {"role": "user", "content": "test"},
            ])
            
            assert result == "Plain string response"
    
    def test_concurrent_rate_limiting(self):
        """Test rate limiting under concurrent access."""
        limiter = RateLimiter(max_calls_per_minute=10)
        results = []
        errors = []
        
        def worker():
            try:
                result = limiter.acquire(block=False)
                results.append(result)
            except RateLimitError:
                errors.append(True)
        
        # Create more workers than the limit
        threads = [threading.Thread(target=worker) for _ in range(15)]
        
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        
        # Should have exactly max_calls successes
        assert len(results) == 10
        assert len(errors) == 5


# ============================================================================
# Integration Tests (with mocks)
# ============================================================================

class TestIntegration:
    """Integration tests with mocked external services."""
    
    def setup_method(self):
        """Reset state before each test."""
        reset_rate_limiter()
        reset_groq_client()
    
    def test_full_workflow_with_rate_limiting_and_retry(self):
        """Test complete workflow with rate limiting and retry."""
        with patch("langchain_groq.ChatGroq") as MockChatGroq:
            attempt_count = 0
            
            def mock_invoke(messages):
                nonlocal attempt_count
                attempt_count += 1
                if attempt_count == 1:
                    raise Exception("rate_limit exceeded")
                response = MagicMock()
                response.content = f"Success on attempt {attempt_count}"
                return response
            
            mock_llm = MagicMock()
            mock_llm.invoke.side_effect = mock_invoke
            MockChatGroq.return_value = mock_llm
            
            client = GroqClient(api_key="test_key", max_retries=3)
            
            result = client.invoke([
                {"role": "user", "content": "Test"},
            ])
            
            assert "Success on attempt 2" in result
            assert attempt_count == 2
    
    def test_client_respects_rate_limit(self):
        """Test that client respects rate limit."""
        with patch("langchain_groq.ChatGroq") as MockChatGroq:
            mock_response = MagicMock()
            mock_response.content = "Response"
            
            mock_llm = MagicMock()
            mock_llm.invoke.return_value = mock_response
            MockChatGroq.return_value = mock_llm
            
            client = GroqClient(api_key="test_key", max_calls_per_minute=3)
            
            # Make calls up to limit
            for _ in range(3):
                client.invoke([{"role": "user", "content": "test"}])
            
            # Check rate limiter status
            status = client.get_rate_limit_status()
            assert status["current_calls"] == 3
            assert status["remaining"] == 0

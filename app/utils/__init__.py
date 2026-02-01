"""
Utils Layer - Helper functions and utilities.

This module provides:
- Text preprocessing utilities
- Input validation helpers
- Metrics and monitoring
- Logging configuration
- Groq API client with rate limiting
"""

from app.utils.preprocessing import (
    clean_text,
    normalize_text,
    convert_devanagari_digits,
)
from app.utils.validation import (
    validate_message,
    validate_session_id,
    validate_language,
)
from app.utils.metrics import (
    track_detection,
    track_extraction,
    track_response_time,
)
from app.utils.logger import get_logger, setup_logging
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
)

__all__ = [
    # Preprocessing
    "clean_text",
    "normalize_text",
    "convert_devanagari_digits",
    # Validation
    "validate_message",
    "validate_session_id",
    "validate_language",
    # Metrics
    "track_detection",
    "track_extraction",
    "track_response_time",
    # Logging
    "get_logger",
    "setup_logging",
    # Groq Client
    "RateLimiter",
    "RateLimitError",
    "GroqAPIError",
    "GroqClient",
    "call_groq_with_retry",
    "get_groq_client",
    "reset_groq_client",
    "reset_rate_limiter",
    "get_rate_limit_status",
    "exponential_backoff",
    "is_retryable_error",
    "retry_with_backoff",
]

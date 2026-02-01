"""
Metrics and Monitoring Module.

Provides Prometheus metrics for:
- Scam detection statistics
- Intelligence extraction counts
- Response time tracking
- Error rate monitoring
"""

from typing import Optional, Dict, Any
import time
from functools import wraps


# Placeholder for Prometheus metrics
# In actual implementation, these would be Prometheus Counter, Histogram, etc.

# Detection metrics
_detection_total = 0
_detection_by_language: Dict[str, int] = {}
_detection_by_result: Dict[str, int] = {}

# Extraction metrics
_extraction_total = 0
_extraction_by_type: Dict[str, int] = {}

# Response time metrics
_response_times: list = []

# Error metrics
_error_total = 0
_error_by_type: Dict[str, int] = {}

# Active sessions
_active_sessions = 0


def track_detection(language: str, scam_detected: bool) -> None:
    """
    Track scam detection event.
    
    Args:
        language: Detected language
        scam_detected: Whether scam was detected
    """
    global _detection_total
    
    # TODO: Implement with Prometheus
    # scam_detection_total.labels(language=language, result=str(scam_detected)).inc()
    
    _detection_total += 1
    _detection_by_language[language] = _detection_by_language.get(language, 0) + 1
    result_key = "scam" if scam_detected else "legitimate"
    _detection_by_result[result_key] = _detection_by_result.get(result_key, 0) + 1


def track_extraction(entity_type: str, count: int = 1) -> None:
    """
    Track intelligence extraction event.
    
    Args:
        entity_type: Type of entity extracted (upi_ids, bank_accounts, etc.)
        count: Number of entities extracted
    """
    global _extraction_total
    
    # TODO: Implement with Prometheus
    # intelligence_extracted_total.labels(type=entity_type).inc(count)
    
    _extraction_total += count
    _extraction_by_type[entity_type] = _extraction_by_type.get(entity_type, 0) + count


def track_response_time(duration_seconds: float) -> None:
    """
    Track API response time.
    
    Args:
        duration_seconds: Response time in seconds
    """
    # TODO: Implement with Prometheus
    # response_time_seconds.observe(duration_seconds)
    
    _response_times.append(duration_seconds)


def track_error(error_type: str) -> None:
    """
    Track error event.
    
    Args:
        error_type: Type of error
    """
    global _error_total
    
    # TODO: Implement with Prometheus
    # error_rate.labels(type=error_type).inc()
    
    _error_total += 1
    _error_by_type[error_type] = _error_by_type.get(error_type, 0) + 1


def update_active_sessions(delta: int) -> None:
    """
    Update active session count.
    
    Args:
        delta: Change in session count (+1 for new, -1 for ended)
    """
    global _active_sessions
    
    # TODO: Implement with Prometheus
    # active_honeypot_sessions.inc(delta)
    
    _active_sessions += delta


def timed(func):
    """
    Decorator to track function execution time.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start
            track_response_time(duration)
    
    return wrapper


async def timed_async(func):
    """
    Async decorator to track function execution time.
    
    Args:
        func: Async function to decorate
        
    Returns:
        Decorated async function
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start = time.time()
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            duration = time.time() - start
            track_response_time(duration)
    
    return wrapper


def get_metrics_summary() -> Dict[str, Any]:
    """
    Get summary of all metrics.
    
    Returns:
        Dictionary with all metric values
    """
    return {
        "detection": {
            "total": _detection_total,
            "by_language": _detection_by_language.copy(),
            "by_result": _detection_by_result.copy(),
        },
        "extraction": {
            "total": _extraction_total,
            "by_type": _extraction_by_type.copy(),
        },
        "response_times": {
            "count": len(_response_times),
            "avg_seconds": sum(_response_times) / len(_response_times) if _response_times else 0,
            "max_seconds": max(_response_times) if _response_times else 0,
        },
        "errors": {
            "total": _error_total,
            "by_type": _error_by_type.copy(),
        },
        "active_sessions": _active_sessions,
    }


def reset_metrics() -> None:
    """Reset all metrics (for testing purposes)."""
    global _detection_total, _extraction_total, _error_total, _active_sessions
    global _detection_by_language, _detection_by_result
    global _extraction_by_type, _error_by_type, _response_times
    
    _detection_total = 0
    _extraction_total = 0
    _error_total = 0
    _active_sessions = 0
    _detection_by_language = {}
    _detection_by_result = {}
    _extraction_by_type = {}
    _error_by_type = {}
    _response_times = []

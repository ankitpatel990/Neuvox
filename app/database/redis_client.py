"""
Redis Client Module.

Provides session state management with TTL for:
- Active honeypot sessions
- Conversation context caching
- Rate limiting counters

Implements Task 6.2 requirements:
- AC-2.3.1: State persists across API calls
- AC-2.3.2: Session expires after 1 hour
- AC-2.3.4: Redis failure degrades gracefully
"""

from typing import Dict, Optional, Any, Callable, TypeVar
import json
import os
import time
from functools import wraps
import redis
from redis.exceptions import ConnectionError as RedisConnectionError, RedisError

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Type variable for generic returns
T = TypeVar("T")

# Global Redis client
redis_client: Optional[redis.Redis] = None

# Track if Redis is known to be unavailable (to skip connection attempts)
_redis_unavailable: bool = False
_redis_last_check: float = 0
_REDIS_RECHECK_INTERVAL = 60  # Only try reconnecting every 60 seconds

# In-memory fallback cache when Redis is unavailable
_fallback_cache: Dict[str, Dict[str, Any]] = {}
_fallback_cache_ttl: Dict[str, float] = {}

# Default TTL in seconds (1 hour)
DEFAULT_SESSION_TTL = 3600


def init_redis_client() -> None:
    """
    Initialize Redis client from configuration.
    
    Raises:
        ValueError: If REDIS_URL is not configured
    """
    global redis_client
    
    if redis_client is not None:
        return
    
    redis_url = settings.REDIS_URL
    
    if not redis_url:
        logger.warning("REDIS_URL not configured. Redis operations will fail.")
        return
    
    try:
        redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=1,  # Reduced from 5s for faster fallback
            socket_timeout=1,          # Reduced from 5s for faster fallback
            retry_on_timeout=False,    # Don't retry, use fallback cache instead
            health_check_interval=60,
        )
        # Test connection
        redis_client.ping()
        logger.info("Redis client initialized successfully")
    except (RedisConnectionError, RedisError) as e:
        logger.error(f"Failed to initialize Redis client: {e}")
        redis_client = None
        raise


def get_redis_client() -> redis.Redis:
    """
    Get Redis client connection.
    
    Returns:
        Redis client object
        
    Raises:
        ConnectionError: If Redis connection fails
        ValueError: If REDIS_URL is not configured
    """
    global _redis_unavailable, _redis_last_check
    
    # Skip connection attempts if Redis was recently unavailable
    if _redis_unavailable:
        if time.time() - _redis_last_check < _REDIS_RECHECK_INTERVAL:
            raise ConnectionError("Redis unavailable (cached)")
        # Time to recheck
        _redis_unavailable = False
    
    if redis_client is None:
        try:
            init_redis_client()
        except Exception:
            _redis_unavailable = True
            _redis_last_check = time.time()
            raise
    
    if redis_client is None:
        _redis_unavailable = True
        _redis_last_check = time.time()
        raise ConnectionError("Redis client not initialized. Check REDIS_URL configuration.")
    
    return redis_client


def save_session_state(session_id: str, state: Dict[str, Any], ttl: int = 3600) -> bool:
    """
    Save session state to Redis with TTL.
    
    Args:
        session_id: Unique session identifier
        state: Session state dictionary
        ttl: Time-to-live in seconds (default 1 hour)
        
    Returns:
        True if successful, False otherwise
    """
    try:
        client = get_redis_client()
        key = f"session:{session_id}"
        client.setex(key, ttl, json.dumps(state))
        return True
    except (ConnectionError, RedisError) as e:
        logger.error(f"Failed to save session state: {e}")
        return False


def get_session_state(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve session state from Redis.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session state dictionary or None if not found/expired
    """
    try:
        client = get_redis_client()
        key = f"session:{session_id}"
        data = client.get(key)
        if data:
            return json.loads(data)
        return None
    except (ConnectionError, RedisError) as e:
        logger.error(f"Failed to get session state: {e}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode session state JSON: {e}")
        return None


def delete_session_state(session_id: str) -> bool:
    """
    Delete session state from Redis.
    
    Args:
        session_id: Session identifier
        
    Returns:
        True if deleted, False if not found
    """
    try:
        client = get_redis_client()
        key = f"session:{session_id}"
        deleted = client.delete(key)
        return deleted > 0
    except (ConnectionError, RedisError) as e:
        logger.error(f"Failed to delete session state: {e}")
        return False


def update_session_state(session_id: str, updates: Dict[str, Any]) -> bool:
    """
    Update existing session state.
    
    Args:
        session_id: Session identifier
        updates: Fields to update
        
    Returns:
        True if successful, False if session not found
    """
    # TODO: Implement session update
    state = get_session_state(session_id)
    if state is None:
        return False
    
    state.update(updates)
    return save_session_state(session_id, state)


def increment_rate_counter(key: str, window_seconds: int = 60) -> int:
    """
    Increment rate limiting counter.
    
    Args:
        key: Counter key (e.g., IP address)
        window_seconds: Time window for counter
        
    Returns:
        Current count within window
    """
    try:
        client = get_redis_client()
        counter_key = f"rate_limit:{key}"
        count = client.incr(counter_key)
        if count == 1:
            # Set expiration on first increment
            client.expire(counter_key, window_seconds)
        return count
    except (ConnectionError, RedisError) as e:
        logger.error(f"Failed to increment rate counter: {e}")
        return 0


def check_rate_limit(key: str, limit: int, window_seconds: int = 60) -> bool:
    """
    Check if rate limit is exceeded.
    
    Args:
        key: Counter key
        limit: Maximum allowed requests
        window_seconds: Time window
        
    Returns:
        True if within limit, False if exceeded
    """
    try:
        count = increment_rate_counter(key, window_seconds)
        return count <= limit
    except Exception as e:
        logger.error(f"Failed to check rate limit: {e}")
        # Fail open - allow request if Redis is down
        return True


def health_check() -> bool:
    """
    Check Redis connection health.
    
    Returns:
        True if Redis is responsive, False otherwise
    """
    try:
        client = get_redis_client()
        client.ping()
        return True
    except (ConnectionError, RedisError) as e:
        logger.warning(f"Redis health check failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in Redis health check: {e}")
        return False


# ============================================================================
# Graceful Degradation with In-Memory Fallback
# ============================================================================

def _cleanup_fallback_cache() -> None:
    """Remove expired entries from fallback cache."""
    now = time.time()
    expired_keys = [
        key for key, expiry in _fallback_cache_ttl.items()
        if expiry < now
    ]
    for key in expired_keys:
        _fallback_cache.pop(key, None)
        _fallback_cache_ttl.pop(key, None)


def save_session_state_with_fallback(
    session_id: str,
    state: Dict[str, Any],
    ttl: int = DEFAULT_SESSION_TTL,
) -> bool:
    """
    Save session state with in-memory fallback.
    
    Implements AC-2.3.4: Redis failure degrades gracefully.
    
    Args:
        session_id: Unique session identifier
        state: Session state dictionary
        ttl: Time-to-live in seconds (default 1 hour per AC-2.3.2)
        
    Returns:
        True if saved (Redis or fallback), False on complete failure
    """
    # Try Redis first
    if save_session_state(session_id, state, ttl):
        return True
    
    # Fall back to in-memory cache
    logger.warning(f"Redis unavailable, using fallback cache for session {session_id}")
    try:
        _cleanup_fallback_cache()
        key = f"session:{session_id}"
        _fallback_cache[key] = state.copy()
        _fallback_cache_ttl[key] = time.time() + ttl
        return True
    except Exception as e:
        logger.error(f"Fallback cache failed: {e}")
        return False


def get_session_state_with_fallback(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get session state with in-memory fallback.
    
    Implements AC-2.3.4: Redis failure degrades gracefully.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Session state or None if not found/expired
    """
    # Try Redis first
    state = get_session_state(session_id)
    if state is not None:
        logger.debug(f"Session {session_id} found in Redis")
        return state
    
    # Try fallback cache
    _cleanup_fallback_cache()
    key = f"session:{session_id}"
    
    if key in _fallback_cache:
        expiry = _fallback_cache_ttl.get(key, 0)
        if expiry > time.time():
            logger.debug(f"Session {session_id} retrieved from fallback cache")
            return _fallback_cache[key].copy()
        else:
            # Expired
            _fallback_cache.pop(key, None)
            _fallback_cache_ttl.pop(key, None)
    
    return None


def delete_session_state_with_fallback(session_id: str) -> bool:
    """
    Delete session state from Redis and fallback cache.
    
    Args:
        session_id: Session identifier
        
    Returns:
        True if deleted from either location
    """
    redis_deleted = delete_session_state(session_id)
    
    # Also remove from fallback
    key = f"session:{session_id}"
    fallback_deleted = key in _fallback_cache
    _fallback_cache.pop(key, None)
    _fallback_cache_ttl.pop(key, None)
    
    return redis_deleted or fallback_deleted


def extend_session_ttl(session_id: str, additional_seconds: int = DEFAULT_SESSION_TTL) -> bool:
    """
    Extend session TTL.
    
    Useful for keeping active sessions alive beyond initial TTL.
    
    Args:
        session_id: Session identifier
        additional_seconds: Additional time in seconds
        
    Returns:
        True if extended, False otherwise
    """
    try:
        client = get_redis_client()
        key = f"session:{session_id}"
        
        # Get current TTL
        current_ttl = client.ttl(key)
        
        if current_ttl > 0:
            # Extend by adding to current TTL
            new_ttl = current_ttl + additional_seconds
            client.expire(key, new_ttl)
            logger.debug(f"Session {session_id} TTL extended by {additional_seconds}s")
            return True
        
        return False
    except (ConnectionError, RedisError) as e:
        logger.error(f"Failed to extend session TTL: {e}")
        return False


def get_session_ttl(session_id: str) -> int:
    """
    Get remaining TTL for a session.
    
    Args:
        session_id: Session identifier
        
    Returns:
        Remaining TTL in seconds, -2 if key doesn't exist, -1 if no expiry
    """
    try:
        client = get_redis_client()
        key = f"session:{session_id}"
        return client.ttl(key)
    except (ConnectionError, RedisError) as e:
        logger.error(f"Failed to get session TTL: {e}")
        return -2


def get_active_session_count() -> int:
    """
    Get count of active sessions.
    
    Returns:
        Number of active sessions
    """
    try:
        client = get_redis_client()
        keys = client.keys("session:*")
        return len(keys)
    except (ConnectionError, RedisError) as e:
        logger.error(f"Failed to get active session count: {e}")
        # Return fallback count
        _cleanup_fallback_cache()
        return len([k for k in _fallback_cache if k.startswith("session:")])


def clear_all_sessions() -> int:
    """
    Clear all session data (for testing/admin purposes).
    
    Returns:
        Number of sessions cleared
    """
    try:
        client = get_redis_client()
        keys = client.keys("session:*")
        if keys:
            deleted = client.delete(*keys)
            logger.info(f"Cleared {deleted} sessions from Redis")
            return deleted
        return 0
    except (ConnectionError, RedisError) as e:
        logger.error(f"Failed to clear sessions: {e}")
        return 0


def reset_fallback_cache() -> None:
    """Reset the in-memory fallback cache (for testing)."""
    global _fallback_cache, _fallback_cache_ttl
    _fallback_cache = {}
    _fallback_cache_ttl = {}


def get_fallback_cache_stats() -> Dict[str, Any]:
    """
    Get fallback cache statistics.
    
    Returns:
        Dictionary with cache stats
    """
    _cleanup_fallback_cache()
    return {
        "entries": len(_fallback_cache),
        "total_size_bytes": sum(
            len(json.dumps(v)) for v in _fallback_cache.values()
        ),
    }


def is_redis_available() -> bool:
    """
    Check if Redis is available without raising exceptions.
    
    Returns:
        True if Redis is available, False otherwise
    """
    return health_check()

"""
Unit tests for Redis client module.

Tests Redis connection, session state management, and rate limiting.

Task 6.2 Acceptance Criteria:
- AC-2.3.1: State persists across API calls
- AC-2.3.2: Session expires after 1 hour
- AC-2.3.4: Redis failure degrades gracefully
"""

import pytest
import json
import time
from unittest.mock import patch, MagicMock
from redis.exceptions import ConnectionError as RedisConnectionError, RedisError

from app.database.redis_client import (
    get_redis_client,
    save_session_state,
    get_session_state,
    delete_session_state,
    update_session_state,
    increment_rate_counter,
    check_rate_limit,
    health_check,
    init_redis_client,
    # Graceful degradation functions
    save_session_state_with_fallback,
    get_session_state_with_fallback,
    delete_session_state_with_fallback,
    reset_fallback_cache,
    get_fallback_cache_stats,
    # Session utilities
    extend_session_ttl,
    get_session_ttl,
    get_active_session_count,
    clear_all_sessions,
    is_redis_available,
    # Constants
    DEFAULT_SESSION_TTL,
)


class TestRedisConnection:
    """Test Redis connection functionality."""
    
    def test_get_redis_client_no_config(self):
        """Test connection fails gracefully when REDIS_URL not set."""
        with patch('app.database.redis_client.settings') as mock_settings:
            mock_settings.REDIS_URL = None
            with patch('app.database.redis_client.redis_client', None):
                with pytest.raises(ConnectionError, match="not initialized"):
                    get_redis_client()
    
    def test_init_redis_client_success(self):
        """Test Redis client initialization with valid URL."""
        test_url = "redis://localhost:6379/0"
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True
        
        with patch('app.database.redis_client.settings') as mock_settings:
            mock_settings.REDIS_URL = test_url
            with patch('app.database.redis_client.redis') as mock_redis_module:
                mock_redis_module.from_url.return_value = mock_redis
                
                init_redis_client()
                
                mock_redis_module.from_url.assert_called_once()
                mock_redis.ping.assert_called_once()
    
    def test_init_redis_client_no_url(self):
        """Test Redis client initialization fails gracefully without URL."""
        # Reset global redis_client
        import app.database.redis_client as redis_module
        redis_module.redis_client = None
        
        with patch('app.database.redis_client.settings') as mock_settings:
            mock_settings.REDIS_URL = None
            with patch('app.database.redis_client.logger') as mock_logger:
                init_redis_client()
                mock_logger.warning.assert_called()
    
    def test_init_redis_client_connection_error(self):
        """Test Redis client initialization handles connection errors."""
        # Reset global redis_client
        import app.database.redis_client as redis_module
        redis_module.redis_client = None
        
        test_url = "redis://localhost:6379/0"
        mock_redis = MagicMock()
        mock_redis.ping.side_effect = RedisConnectionError("Connection failed")
        
        with patch('app.database.redis_client.settings') as mock_settings:
            mock_settings.REDIS_URL = test_url
            with patch('app.database.redis_client.redis') as mock_redis_module:
                mock_redis_module.from_url.return_value = mock_redis
                
                with pytest.raises(RedisConnectionError):
                    init_redis_client()


class TestSessionStateManagement:
    """Test session state management functions."""
    
    def test_save_session_state_success(self):
        """Test saving session state successfully."""
        mock_client = MagicMock()
        session_id = "test-session-123"
        state = {"turn_count": 1, "language": "en"}
        
        with patch('app.database.redis_client.get_redis_client', return_value=mock_client):
            result = save_session_state(session_id, state, ttl=3600)
            
            assert result is True
            mock_client.setex.assert_called_once()
            call_args = mock_client.setex.call_args
            assert call_args[0][0] == f"session:{session_id}"
            assert call_args[0][1] == 3600
            assert json.loads(call_args[0][2]) == state
    
    def test_save_session_state_connection_error(self):
        """Test saving session state handles connection errors."""
        with patch('app.database.redis_client.get_redis_client') as mock_get:
            mock_get.side_effect = ConnectionError("Redis down")
            with patch('app.database.redis_client.logger') as mock_logger:
                result = save_session_state("test", {})
                assert result is False
                mock_logger.error.assert_called()
    
    def test_get_session_state_success(self):
        """Test retrieving session state successfully."""
        mock_client = MagicMock()
        session_id = "test-session-123"
        state = {"turn_count": 1, "language": "en"}
        mock_client.get.return_value = json.dumps(state)
        
        with patch('app.database.redis_client.get_redis_client', return_value=mock_client):
            result = get_session_state(session_id)
            
            assert result == state
            mock_client.get.assert_called_once_with(f"session:{session_id}")
    
    def test_get_session_state_not_found(self):
        """Test retrieving non-existent session state."""
        mock_client = MagicMock()
        mock_client.get.return_value = None
        
        with patch('app.database.redis_client.get_redis_client', return_value=mock_client):
            result = get_session_state("non-existent")
            assert result is None
    
    def test_get_session_state_invalid_json(self):
        """Test retrieving session state with invalid JSON."""
        mock_client = MagicMock()
        mock_client.get.return_value = "invalid json{"
        
        with patch('app.database.redis_client.get_redis_client', return_value=mock_client):
            with patch('app.database.redis_client.logger') as mock_logger:
                result = get_session_state("test")
                assert result is None
                mock_logger.error.assert_called()
    
    def test_delete_session_state_success(self):
        """Test deleting session state successfully."""
        mock_client = MagicMock()
        mock_client.delete.return_value = 1  # Key was deleted
        
        with patch('app.database.redis_client.get_redis_client', return_value=mock_client):
            result = delete_session_state("test-session")
            
            assert result is True
            mock_client.delete.assert_called_once_with("session:test-session")
    
    def test_delete_session_state_not_found(self):
        """Test deleting non-existent session state."""
        mock_client = MagicMock()
        mock_client.delete.return_value = 0  # Key not found
        
        with patch('app.database.redis_client.get_redis_client', return_value=mock_client):
            result = delete_session_state("non-existent")
            assert result is False
    
    def test_update_session_state_success(self):
        """Test updating existing session state."""
        existing_state = {"turn_count": 1, "language": "en"}
        updates = {"turn_count": 2}
        
        with patch('app.database.redis_client.get_session_state', return_value=existing_state):
            with patch('app.database.redis_client.save_session_state', return_value=True):
                result = update_session_state("test", updates)
                assert result is True
    
    def test_update_session_state_not_found(self):
        """Test updating non-existent session state."""
        with patch('app.database.redis_client.get_session_state', return_value=None):
            result = update_session_state("non-existent", {})
            assert result is False


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def test_increment_rate_counter_success(self):
        """Test incrementing rate counter successfully."""
        mock_client = MagicMock()
        mock_client.incr.return_value = 1
        mock_client.expire.return_value = True
        
        with patch('app.database.redis_client.get_redis_client', return_value=mock_client):
            result = increment_rate_counter("192.168.1.1", window_seconds=60)
            
            assert result == 1
            mock_client.incr.assert_called_once()
            mock_client.expire.assert_called_once()
    
    def test_increment_rate_counter_connection_error(self):
        """Test incrementing rate counter handles connection errors."""
        with patch('app.database.redis_client.get_redis_client') as mock_get:
            mock_get.side_effect = ConnectionError("Redis down")
            with patch('app.database.redis_client.logger') as mock_logger:
                result = increment_rate_counter("test")
                assert result == 0
                mock_logger.error.assert_called()
    
    def test_check_rate_limit_within_limit(self):
        """Test rate limit check when within limit."""
        with patch('app.database.redis_client.increment_rate_counter', return_value=5):
            result = check_rate_limit("test", limit=10, window_seconds=60)
            assert result is True
    
    def test_check_rate_limit_exceeded(self):
        """Test rate limit check when limit exceeded."""
        with patch('app.database.redis_client.increment_rate_counter', return_value=15):
            result = check_rate_limit("test", limit=10, window_seconds=60)
            assert result is False
    
    def test_check_rate_limit_fail_open(self):
        """Test rate limit check fails open on error."""
        with patch('app.database.redis_client.increment_rate_counter') as mock_incr:
            mock_incr.side_effect = Exception("Error")
            with patch('app.database.redis_client.logger') as mock_logger:
                result = check_rate_limit("test", limit=10)
                assert result is True  # Fail open
                mock_logger.error.assert_called()


class TestHealthCheck:
    """Test Redis health check functionality."""
    
    def test_health_check_success(self):
        """Test health check when Redis is healthy."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        
        with patch('app.database.redis_client.get_redis_client', return_value=mock_client):
            result = health_check()
            assert result is True
            mock_client.ping.assert_called_once()
    
    def test_health_check_connection_error(self):
        """Test health check when Redis connection fails."""
        with patch('app.database.redis_client.get_redis_client') as mock_get:
            mock_get.side_effect = ConnectionError("Redis down")
            with patch('app.database.redis_client.logger') as mock_logger:
                result = health_check()
                assert result is False
                mock_logger.warning.assert_called()
    
    def test_health_check_redis_error(self):
        """Test health check when Redis returns error."""
        mock_client = MagicMock()
        mock_client.ping.side_effect = RedisError("Redis error")
        
        with patch('app.database.redis_client.get_redis_client', return_value=mock_client):
            with patch('app.database.redis_client.logger') as mock_logger:
                result = health_check()
                assert result is False
                mock_logger.warning.assert_called()


# ============================================================================
# Task 6.2 Tests: Graceful Degradation (AC-2.3.4)
# ============================================================================

class TestGracefulDegradation:
    """Tests for graceful degradation with in-memory fallback."""
    
    def setup_method(self):
        """Reset fallback cache before each test."""
        reset_fallback_cache()
    
    def test_save_session_state_with_fallback_redis_available(self):
        """Test saves to Redis when available."""
        mock_client = MagicMock()
        
        with patch('app.database.redis_client.get_redis_client', return_value=mock_client):
            result = save_session_state_with_fallback(
                "session-123",
                {"turn_count": 1},
                ttl=3600,
            )
            
            assert result is True
            mock_client.setex.assert_called_once()
    
    def test_save_session_state_with_fallback_redis_unavailable(self):
        """Test falls back to in-memory cache when Redis unavailable."""
        with patch('app.database.redis_client.get_redis_client') as mock_get:
            mock_get.side_effect = ConnectionError("Redis down")
            with patch('app.database.redis_client.logger'):
                result = save_session_state_with_fallback(
                    "session-456",
                    {"turn_count": 5, "language": "hi"},
                    ttl=3600,
                )
                
                assert result is True
                
                # Verify it's in the fallback cache
                state = get_session_state_with_fallback("session-456")
                assert state is not None
                assert state["turn_count"] == 5
    
    def test_get_session_state_with_fallback_redis_available(self):
        """Test retrieves from Redis when available."""
        mock_client = MagicMock()
        mock_client.get.return_value = json.dumps({"turn_count": 3})
        
        with patch('app.database.redis_client.get_redis_client', return_value=mock_client):
            result = get_session_state_with_fallback("session-123")
            
            assert result is not None
            assert result["turn_count"] == 3
    
    def test_get_session_state_with_fallback_uses_cache(self):
        """Test retrieves from fallback cache when Redis unavailable."""
        # First, save to fallback
        with patch('app.database.redis_client.get_redis_client') as mock_get:
            mock_get.side_effect = ConnectionError("Redis down")
            with patch('app.database.redis_client.logger'):
                save_session_state_with_fallback(
                    "session-789",
                    {"persona": "elderly"},
                    ttl=3600,
                )
        
        # Then retrieve from fallback
        with patch('app.database.redis_client.get_redis_client') as mock_get:
            mock_get.side_effect = ConnectionError("Redis down")
            with patch('app.database.redis_client.logger'):
                result = get_session_state_with_fallback("session-789")
                
                assert result is not None
                assert result["persona"] == "elderly"
    
    def test_delete_session_state_with_fallback(self):
        """Test deletes from both Redis and fallback cache."""
        # Save to fallback
        with patch('app.database.redis_client.get_redis_client') as mock_get:
            mock_get.side_effect = ConnectionError("Redis down")
            with patch('app.database.redis_client.logger'):
                save_session_state_with_fallback("session-delete", {"test": True})
        
        # Verify it exists
        with patch('app.database.redis_client.get_redis_client') as mock_get:
            mock_get.side_effect = ConnectionError("Redis down")
            with patch('app.database.redis_client.logger'):
                assert get_session_state_with_fallback("session-delete") is not None
        
        # Delete
        with patch('app.database.redis_client.get_redis_client') as mock_get:
            mock_get.side_effect = ConnectionError("Redis down")
            with patch('app.database.redis_client.logger'):
                result = delete_session_state_with_fallback("session-delete")
                assert result is True
        
        # Verify it's gone
        with patch('app.database.redis_client.get_redis_client') as mock_get:
            mock_get.side_effect = ConnectionError("Redis down")
            with patch('app.database.redis_client.logger'):
                assert get_session_state_with_fallback("session-delete") is None
    
    def test_fallback_cache_stats(self):
        """Test getting fallback cache statistics."""
        reset_fallback_cache()
        
        # Save some data to fallback
        with patch('app.database.redis_client.get_redis_client') as mock_get:
            mock_get.side_effect = ConnectionError("Redis down")
            with patch('app.database.redis_client.logger'):
                save_session_state_with_fallback("session-1", {"a": 1})
                save_session_state_with_fallback("session-2", {"b": 2})
        
        stats = get_fallback_cache_stats()
        
        assert stats["entries"] == 2
        assert stats["total_size_bytes"] > 0
    
    def test_reset_fallback_cache(self):
        """Test resetting the fallback cache."""
        # Save something
        with patch('app.database.redis_client.get_redis_client') as mock_get:
            mock_get.side_effect = ConnectionError("Redis down")
            with patch('app.database.redis_client.logger'):
                save_session_state_with_fallback("session-temp", {"temp": True})
        
        # Reset
        reset_fallback_cache()
        
        # Verify empty
        stats = get_fallback_cache_stats()
        assert stats["entries"] == 0


class TestSessionTTL:
    """Tests for session TTL functionality."""
    
    def test_default_session_ttl_is_one_hour(self):
        """AC-2.3.2: Session expires after 1 hour."""
        assert DEFAULT_SESSION_TTL == 3600
    
    def test_extend_session_ttl(self):
        """Test extending session TTL."""
        mock_client = MagicMock()
        mock_client.ttl.return_value = 1800  # 30 minutes remaining
        mock_client.expire.return_value = True
        
        with patch('app.database.redis_client.get_redis_client', return_value=mock_client):
            result = extend_session_ttl("session-123", additional_seconds=1800)
            
            assert result is True
            mock_client.expire.assert_called_once()
    
    def test_extend_session_ttl_not_found(self):
        """Test extending TTL for non-existent session."""
        mock_client = MagicMock()
        mock_client.ttl.return_value = -2  # Key doesn't exist
        
        with patch('app.database.redis_client.get_redis_client', return_value=mock_client):
            result = extend_session_ttl("non-existent")
            assert result is False
    
    def test_get_session_ttl(self):
        """Test getting remaining session TTL."""
        mock_client = MagicMock()
        mock_client.ttl.return_value = 2400
        
        with patch('app.database.redis_client.get_redis_client', return_value=mock_client):
            result = get_session_ttl("session-123")
            assert result == 2400


class TestSessionUtilities:
    """Tests for session utility functions."""
    
    def test_get_active_session_count(self):
        """Test counting active sessions."""
        mock_client = MagicMock()
        mock_client.keys.return_value = [
            "session:1", "session:2", "session:3"
        ]
        
        with patch('app.database.redis_client.get_redis_client', return_value=mock_client):
            result = get_active_session_count()
            assert result == 3
    
    def test_get_active_session_count_redis_error(self):
        """Test active session count falls back to cache count on error."""
        reset_fallback_cache()
        
        # Add to fallback cache first
        with patch('app.database.redis_client.get_redis_client') as mock_get:
            mock_get.side_effect = ConnectionError("Redis down")
            with patch('app.database.redis_client.logger'):
                save_session_state_with_fallback("s1", {"a": 1})
                save_session_state_with_fallback("s2", {"b": 2})
        
        # Now get count (Redis still down)
        with patch('app.database.redis_client.get_redis_client') as mock_get:
            mock_get.side_effect = ConnectionError("Redis down")
            with patch('app.database.redis_client.logger'):
                result = get_active_session_count()
                assert result == 2
    
    def test_clear_all_sessions(self):
        """Test clearing all sessions."""
        mock_client = MagicMock()
        mock_client.keys.return_value = ["session:1", "session:2"]
        mock_client.delete.return_value = 2
        
        with patch('app.database.redis_client.get_redis_client', return_value=mock_client):
            result = clear_all_sessions()
            assert result == 2
            mock_client.delete.assert_called_once()
    
    def test_is_redis_available(self):
        """Test is_redis_available function."""
        mock_client = MagicMock()
        mock_client.ping.return_value = True
        
        with patch('app.database.redis_client.get_redis_client', return_value=mock_client):
            result = is_redis_available()
            assert result is True
    
    def test_is_redis_available_when_down(self):
        """Test is_redis_available returns False when Redis is down."""
        with patch('app.database.redis_client.get_redis_client') as mock_get:
            mock_get.side_effect = ConnectionError("Redis down")
            with patch('app.database.redis_client.logger'):
                result = is_redis_available()
                assert result is False


class TestAcceptanceCriteria:
    """Tests for Task 6.2 Redis Acceptance Criteria."""
    
    def setup_method(self):
        """Reset state before each test."""
        reset_fallback_cache()
    
    def test_ac_2_3_1_state_persists_across_api_calls(self):
        """AC-2.3.1: State persists across API calls."""
        mock_client = MagicMock()
        stored_data = {}
        
        def mock_setex(key, ttl, value):
            stored_data[key] = {"value": value, "ttl": ttl}
        
        def mock_get(key):
            return stored_data.get(key, {}).get("value")
        
        mock_client.setex = mock_setex
        mock_client.get = mock_get
        
        with patch('app.database.redis_client.get_redis_client', return_value=mock_client):
            # First API call - save state
            session_id = "persist-test"
            state1 = {"turn_count": 1, "language": "en"}
            save_session_state(session_id, state1)
            
            # Second API call - retrieve and update state
            retrieved = get_session_state(session_id)
            assert retrieved is not None
            assert retrieved["turn_count"] == 1
            
            # Update state
            state2 = {"turn_count": 2, "language": "en"}
            save_session_state(session_id, state2)
            
            # Third API call - verify updated state
            final = get_session_state(session_id)
            assert final["turn_count"] == 2
    
    def test_ac_2_3_2_session_expires_after_one_hour(self):
        """AC-2.3.2: Session expires after 1 hour."""
        mock_client = MagicMock()
        
        with patch('app.database.redis_client.get_redis_client', return_value=mock_client):
            save_session_state("expire-test", {"data": "value"})
            
            # Verify setex was called with 3600 seconds (1 hour)
            call_args = mock_client.setex.call_args[0]
            assert call_args[1] == 3600  # TTL
    
    def test_ac_2_3_4_redis_failure_degrades_gracefully(self):
        """AC-2.3.4: Redis failure degrades gracefully."""
        # Simulate Redis being down
        with patch('app.database.redis_client.get_redis_client') as mock_get:
            mock_get.side_effect = ConnectionError("Redis down")
            with patch('app.database.redis_client.logger'):
                # Should not raise, should use fallback
                result = save_session_state_with_fallback(
                    "graceful-test",
                    {"important": "data"},
                )
                assert result is True
        
        # Should still be retrievable from fallback
        with patch('app.database.redis_client.get_redis_client') as mock_get:
            mock_get.side_effect = ConnectionError("Redis down")
            with patch('app.database.redis_client.logger'):
                state = get_session_state_with_fallback("graceful-test")
                assert state is not None
                assert state["important"] == "data"
    
    def test_fallback_cache_respects_ttl(self):
        """Test that fallback cache respects TTL."""
        reset_fallback_cache()
        
        # Manually add an expired entry to test cleanup
        import app.database.redis_client as redis_module
        
        key = "session:expired-test"
        redis_module._fallback_cache[key] = {"expired": True}
        redis_module._fallback_cache_ttl[key] = time.time() - 10  # Expired 10 seconds ago
        
        # Getting should return None because entry is expired
        with patch('app.database.redis_client.get_redis_client') as mock_get:
            mock_get.side_effect = ConnectionError("Redis down")
            with patch('app.database.redis_client.logger'):
                result = get_session_state_with_fallback("expired-test")
                assert result is None

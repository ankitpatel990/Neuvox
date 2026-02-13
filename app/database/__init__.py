"""
Database Layer - Storage backends for conversations, sessions, and embeddings.

This module provides:
- PostgreSQL: Conversation logs and extracted intelligence
- Redis: Session state management with TTL
- ChromaDB: Vector embeddings for semantic search

Task 6.2 Implementation:
- AC-2.3.1: State persists across API calls
- AC-2.3.2: Session expires after 1 hour
- AC-2.3.3: PostgreSQL stores complete logs
- AC-2.3.4: Redis failure degrades gracefully

Note: PostgreSQL is not imported here to avoid loading SQLAlchemy when POSTGRES_URL
is unset (Python 3.14 typing compatibility). Import from app.database.postgres directly
when POSTGRES_URL is configured.
"""

from app.database.redis_client import (
    # Connection management
    get_redis_client,
    init_redis_client,
    health_check,
    is_redis_available,
    # Session state management
    save_session_state,
    get_session_state,
    delete_session_state,
    update_session_state,
    # Graceful degradation with fallback
    save_session_state_with_fallback,
    get_session_state_with_fallback,
    delete_session_state_with_fallback,
    # Session utilities
    extend_session_ttl,
    get_session_ttl,
    get_active_session_count,
    clear_all_sessions,
    reset_fallback_cache,
    get_fallback_cache_stats,
    # Rate limiting
    increment_rate_counter,
    check_rate_limit,
    # Constants
    DEFAULT_SESSION_TTL,
)
from app.database.chromadb_client import (
    get_chromadb_client,
    store_embedding,
    search_similar,
)

__all__ = [
    # Redis - Connection
    "get_redis_client",
    "init_redis_client",
    "health_check",
    "is_redis_available",
    # Redis - Session state
    "save_session_state",
    "get_session_state",
    "delete_session_state",
    "update_session_state",
    # Redis - Graceful degradation
    "save_session_state_with_fallback",
    "get_session_state_with_fallback",
    "delete_session_state_with_fallback",
    # Redis - Utilities
    "extend_session_ttl",
    "get_session_ttl",
    "get_active_session_count",
    "clear_all_sessions",
    "reset_fallback_cache",
    "get_fallback_cache_stats",
    # Redis - Rate limiting
    "increment_rate_counter",
    "check_rate_limit",
    # Redis - Constants
    "DEFAULT_SESSION_TTL",
    # ChromaDB
    "get_chromadb_client",
    "store_embedding",
    "search_similar",
]

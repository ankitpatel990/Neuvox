"""
API Layer - FastAPI endpoints and request/response schemas.

This module contains the REST API implementation for the ScamShield AI system.
"""

from app.api.endpoints import router
from app.api.schemas import (
    EngageRequest,
    EngageResponse,
    HealthResponse,
    BatchRequest,
    BatchResponse,
    SessionResponse,
    ErrorResponse,
    GUVIEngageRequest,
    GUVIMessageInput,
    GUVIMetadata,
    UnifiedEngageRequest,
)
from app.api.auth import verify_api_key, optional_api_key

__all__ = [
    "router",
    "EngageRequest",
    "EngageResponse",
    "HealthResponse",
    "BatchRequest",
    "BatchResponse",
    "SessionResponse",
    "ErrorResponse",
    "GUVIEngageRequest",
    "GUVIMessageInput",
    "GUVIMetadata",
    "UnifiedEngageRequest",
    "verify_api_key",
    "optional_api_key",
]

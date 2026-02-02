"""
API Key Authentication Module.

Provides middleware for validating x-api-key header as required by
the GUVI Hackathon submission requirements.

Requirement: "Participants must deploy a public API endpoint secured
with a user-provided API key."
"""

from typing import Optional

from fastapi import Request, HTTPException, Security
from fastapi.security import APIKeyHeader

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Define the API key header
api_key_header = APIKeyHeader(name="x-api-key", auto_error=False)


async def verify_api_key(api_key: Optional[str] = Security(api_key_header)) -> str:
    """
    Verify the x-api-key header for API authentication.
    
    This is required for GUVI Hackathon submission compliance.
    The API key is provided by the participant and must be included
    in all requests to protected endpoints.
    
    Args:
        api_key: The API key from x-api-key header
        
    Returns:
        The validated API key
        
    Raises:
        HTTPException: 401 if API key is missing or invalid
    """
    # Skip authentication in development mode
    if settings.is_development:
        logger.debug("Development mode, skipping API key validation")
        return api_key or "dev-mode"
    
    # If API key is not configured, skip authentication
    if not settings.API_KEY:
        logger.warning("API_KEY not configured, skipping authentication")
        return "no-auth"
    
    if not api_key:
        logger.warning("Request missing x-api-key header")
        raise HTTPException(
            status_code=401,
            detail={
                "code": "MISSING_API_KEY",
                "message": "Missing x-api-key header. API key is required for authentication.",
            },
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    if api_key != settings.API_KEY:
        logger.warning(f"Invalid API key provided: {api_key[:8]}...")
        raise HTTPException(
            status_code=401,
            detail={
                "code": "INVALID_API_KEY",
                "message": "Invalid API key. Please provide a valid x-api-key header.",
            },
            headers={"WWW-Authenticate": "ApiKey"},
        )
    
    logger.debug("API key validated successfully")
    return api_key


async def optional_api_key(api_key: Optional[str] = Security(api_key_header)) -> Optional[str]:
    """
    Optional API key validation for endpoints that support both authenticated
    and unauthenticated access.
    
    Args:
        api_key: The API key from x-api-key header (optional)
        
    Returns:
        The API key if provided and valid, None otherwise
    """
    if not api_key:
        return None
    
    if settings.API_KEY and api_key == settings.API_KEY:
        return api_key
    
    return None

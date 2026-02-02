"""
Pydantic schemas for API request/response validation.

Defines all data models used by the ScamShield AI API endpoints.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import uuid


class EngageRequest(BaseModel):
    """Request schema for POST /api/v1/honeypot/engage."""
    
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="The message to analyze for scam detection",
    )
    session_id: Optional[str] = Field(
        None,
        description="Session ID for multi-turn conversations. Auto-generated if not provided.",
    )
    language: Optional[str] = Field(
        "auto",
        description="Message language. 'auto' for automatic detection.",
    )
    mock_scammer_callback: Optional[str] = Field(
        None,
        description="Competition testing: URL to call with agent responses",
    )

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate session_id is a valid UUID if provided."""
        if v is None:
            return v
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError("session_id must be a valid UUID v4 format")

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> str:
        """Validate language is one of the supported values."""
        allowed = {"auto", "en", "hi"}
        if v not in allowed:
            raise ValueError(f"language must be one of: {', '.join(allowed)}")
        return v


class MessageEntry(BaseModel):
    """Schema for a single message in conversation history."""
    
    turn: int = Field(..., ge=1, description="Turn number in conversation")
    sender: str = Field(..., description="Message sender: 'scammer' or 'agent'")
    message: str = Field(..., description="Message content")
    timestamp: str = Field(..., description="Message timestamp in ISO-8601 format")


class EngagementInfo(BaseModel):
    """Schema for engagement details in response."""
    
    agent_response: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="AI agent's response to the scammer",
    )
    turn_count: int = Field(
        ...,
        ge=1,
        le=20,
        description="Current conversation turn number",
    )
    max_turns_reached: bool = Field(
        ...,
        description="Whether maximum conversation turns reached",
    )
    strategy: str = Field(
        ...,
        description="Current engagement strategy",
    )
    persona: Optional[str] = Field(
        None,
        description="Active persona type",
    )


class ExtractedIntelligence(BaseModel):
    """Schema for extracted intelligence data."""
    
    upi_ids: List[str] = Field(
        default_factory=list,
        description="Extracted UPI IDs (e.g., user@paytm)",
    )
    bank_accounts: List[str] = Field(
        default_factory=list,
        description="Extracted bank account numbers (9-18 digits)",
    )
    ifsc_codes: List[str] = Field(
        default_factory=list,
        description="Extracted IFSC codes (11 chars, format XXXX0XXXXXX)",
    )
    phone_numbers: List[str] = Field(
        default_factory=list,
        description="Extracted phone numbers (Indian mobile format)",
    )
    phishing_links: List[str] = Field(
        default_factory=list,
        description="Extracted phishing/suspicious URLs",
    )
    suspicious_keywords: List[str] = Field(
        default_factory=list,
        description="Suspicious keywords detected in scam messages",
    )
    extraction_confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Overall confidence in extracted intelligence",
    )


class ResponseMetadata(BaseModel):
    """Schema for response metadata."""
    
    model_config = {"protected_namespaces": ()}
    
    processing_time_ms: int = Field(
        ...,
        ge=0,
        description="Total processing time in milliseconds",
    )
    model_version: str = Field(..., description="System version")
    detection_model: Optional[str] = Field(None, description="Model used for scam detection")
    engagement_model: Optional[str] = Field(None, description="Model used for engagement")


class EngageResponse(BaseModel):
    """Response schema for POST /api/v1/honeypot/engage when scam is detected."""
    
    status: str = Field(..., description="Request processing status")
    scam_detected: bool = Field(..., description="Whether the message was classified as a scam")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Scam detection confidence score",
    )
    language_detected: str = Field(..., description="Detected language of the message")
    session_id: str = Field(..., description="Session identifier for this conversation")
    reply: Optional[str] = Field(
        None,
        description="Agent's reply to the scammer (GUVI format requirement)",
    )
    agent_notes: Optional[str] = Field(
        None,
        description="Summary of scammer behavior and tactics",
    )
    engagement: Optional[EngagementInfo] = Field(None, description="Engagement details")
    extracted_intelligence: Optional[ExtractedIntelligence] = Field(
        None,
        description="Extracted financial intelligence",
    )
    conversation_history: Optional[List[MessageEntry]] = Field(
        None,
        description="Complete conversation history",
    )
    message: Optional[str] = Field(None, description="Human-readable response message")
    metadata: Optional[ResponseMetadata] = Field(None, description="Response metadata")


class HealthDependencies(BaseModel):
    """Schema for health check dependencies status."""
    
    groq_api: str = Field(..., description="Groq API status")
    postgres: str = Field(..., description="PostgreSQL status")
    redis: str = Field(..., description="Redis status")
    models_loaded: bool = Field(..., description="Whether ML models are loaded")


class HealthResponse(BaseModel):
    """Response schema for GET /api/v1/health."""
    
    status: str = Field(..., description="Service health status")
    version: str = Field(..., description="Service version")
    timestamp: str = Field(..., description="Current timestamp in ISO-8601 format")
    dependencies: Optional[HealthDependencies] = Field(None, description="Dependency statuses")
    uptime_seconds: Optional[int] = Field(None, ge=0, description="Service uptime in seconds")


class BatchMessageItem(BaseModel):
    """Schema for a single message in batch request."""
    
    id: str = Field(..., description="Client-provided message ID")
    message: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Message to analyze",
    )
    language: Optional[str] = Field("auto", description="Message language")


class BatchRequest(BaseModel):
    """Request schema for POST /api/v1/honeypot/batch."""
    
    messages: List[BatchMessageItem] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Array of messages to process",
    )


class BatchResultItem(BaseModel):
    """Schema for a single result in batch response."""
    
    id: str = Field(..., description="Client-provided message ID")
    status: str = Field(..., description="Processing status")
    scam_detected: Optional[bool] = Field(None, description="Whether scam was detected")
    confidence: Optional[float] = Field(None, description="Detection confidence")
    language_detected: Optional[str] = Field(None, description="Detected language")
    error: Optional[Dict[str, str]] = Field(None, description="Error details if failed")


class BatchResponse(BaseModel):
    """Response schema for POST /api/v1/honeypot/batch."""
    
    status: str = Field(..., description="Overall request status")
    processed: int = Field(..., ge=0, description="Number of messages successfully processed")
    failed: int = Field(..., ge=0, description="Number of messages that failed processing")
    results: List[BatchResultItem] = Field(..., description="Processing results")
    processing_time_ms: int = Field(..., ge=0, description="Total processing time")


class SessionResponse(BaseModel):
    """Response schema for GET /api/v1/honeypot/session/{session_id}."""
    
    session_id: str = Field(..., description="Session identifier")
    language: str = Field(..., description="Conversation language")
    persona: Optional[str] = Field(None, description="Active persona")
    scam_confidence: float = Field(..., ge=0.0, le=1.0, description="Scam confidence score")
    turn_count: int = Field(..., ge=0, description="Number of turns")
    conversation_history: List[MessageEntry] = Field(
        ...,
        description="Conversation history",
    )
    extracted_intelligence: ExtractedIntelligence = Field(
        ...,
        description="Extracted intelligence",
    )
    created_at: str = Field(..., description="Session creation timestamp")
    updated_at: str = Field(..., description="Session last update timestamp")


class ErrorDetail(BaseModel):
    """Schema for error details."""
    
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error context")


class ErrorResponse(BaseModel):
    """Response schema for error responses."""
    
    status: str = Field(default="error", description="Error status")
    error: ErrorDetail = Field(..., description="Error details")


# =====================================================
# GUVI Format Schemas
# These schemas support the exact input format specified by GUVI
# =====================================================

class GUVIMessageInput(BaseModel):
    """
    GUVI format: Nested message object with sender, text, timestamp.
    
    Example:
        {
            "sender": "scammer",
            "text": "Your bank account will be blocked today.",
            "timestamp": "2026-01-21T10:15:30Z"
        }
    """
    
    sender: str = Field(
        ...,
        description="Message sender: 'scammer' or 'user'",
    )
    text: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="Message content",
    )
    timestamp: Optional[str] = Field(
        None,
        description="Message timestamp in ISO-8601 format",
    )


class GUVIMetadata(BaseModel):
    """
    GUVI format: Metadata about the message.
    
    Example:
        {
            "channel": "SMS",
            "language": "English",
            "locale": "IN"
        }
    """
    
    channel: Optional[str] = Field(
        None,
        description="Communication channel: SMS, WhatsApp, Email, Chat",
    )
    language: Optional[str] = Field(
        None,
        description="Language: English, Hindi, etc.",
    )
    locale: Optional[str] = Field(
        None,
        description="Country or region code: IN, US, etc.",
    )


class GUVIConversationHistoryItem(BaseModel):
    """
    GUVI format: Single item in conversation history.
    
    Example:
        {
            "sender": "scammer",
            "text": "Previous message",
            "timestamp": "2026-01-21T10:15:30Z"
        }
    """
    
    sender: str = Field(..., description="Message sender: 'scammer' or 'user'")
    text: str = Field(..., description="Message content")
    timestamp: Optional[str] = Field(None, description="Message timestamp")


class GUVIEngageRequest(BaseModel):
    """
    GUVI format request schema for POST /api/v1/honeypot/engage.
    
    This schema matches the exact format specified in the GUVI problem statement.
    
    Example:
        {
            "sessionId": "wertyu-dfghj-ertyui",
            "message": {
                "sender": "scammer",
                "text": "Your bank account will be blocked today.",
                "timestamp": "2026-01-21T10:15:30Z"
            },
            "conversationHistory": [],
            "metadata": {
                "channel": "SMS",
                "language": "English",
                "locale": "IN"
            }
        }
    """
    
    sessionId: Optional[str] = Field(
        None,
        alias="sessionId",
        description="Session ID for multi-turn conversations (GUVI format: camelCase)",
    )
    message: GUVIMessageInput = Field(
        ...,
        description="The incoming message object",
    )
    conversationHistory: Optional[List[GUVIConversationHistoryItem]] = Field(
        default_factory=list,
        alias="conversationHistory",
        description="Previous messages in the conversation",
    )
    metadata: Optional[GUVIMetadata] = Field(
        None,
        description="Message metadata",
    )
    
    model_config = {"populate_by_name": True}
    
    def to_internal_format(self) -> Dict[str, Any]:
        """
        Convert GUVI format to our internal format.
        
        Returns:
            Dictionary with our internal field names
        """
        # Map GUVI language names to our codes
        language_map = {
            "english": "en",
            "hindi": "hi",
            "hinglish": "hinglish",
        }
        
        language = "auto"
        if self.metadata and self.metadata.language:
            lang_lower = self.metadata.language.lower()
            language = language_map.get(lang_lower, "auto")
        
        return {
            "message": self.message.text,
            "session_id": self.sessionId,
            "language": language,
            "conversation_history": [
                {
                    "sender": item.sender,
                    "message": item.text,
                    "timestamp": item.timestamp,
                }
                for item in (self.conversationHistory or [])
            ],
            "metadata": {
                "channel": self.metadata.channel if self.metadata else None,
                "locale": self.metadata.locale if self.metadata else None,
            },
        }


class UnifiedEngageRequest(BaseModel):
    """
    Unified request schema that accepts both our format and GUVI format.
    
    This schema auto-detects the format based on the presence of nested
    'message' object vs. simple string 'message' field.
    """
    
    # Our format fields
    message: Optional[Any] = Field(
        None,
        description="Message (string for our format, object for GUVI format)",
    )
    session_id: Optional[str] = Field(
        None,
        description="Session ID (our format: snake_case)",
    )
    sessionId: Optional[str] = Field(
        None,
        description="Session ID (GUVI format: camelCase)",
    )
    language: Optional[str] = Field(
        "auto",
        description="Language code for our format",
    )
    conversationHistory: Optional[List[GUVIConversationHistoryItem]] = Field(
        None,
        description="Conversation history (GUVI format)",
    )
    metadata: Optional[GUVIMetadata] = Field(
        None,
        description="Metadata (GUVI format)",
    )
    mock_scammer_callback: Optional[str] = Field(
        None,
        description="Competition testing callback URL",
    )
    
    model_config = {"populate_by_name": True}
    
    def get_message_text(self) -> str:
        """Extract message text from either format."""
        if isinstance(self.message, dict):
            # GUVI format: nested object
            return self.message.get("text", "")
        elif isinstance(self.message, str):
            # Our format: simple string
            return self.message
        else:
            return ""
    
    def get_session_id(self) -> Optional[str]:
        """Get session ID from either format."""
        return self.session_id or self.sessionId
    
    def get_language(self) -> str:
        """Get language from either format."""
        if self.metadata and self.metadata.language:
            lang_lower = self.metadata.language.lower()
            language_map = {"english": "en", "hindi": "hi", "hinglish": "hinglish"}
            return language_map.get(lang_lower, "auto")
        return self.language or "auto"
    
    def is_guvi_format(self) -> bool:
        """Check if request is in GUVI format."""
        return isinstance(self.message, dict) or self.sessionId is not None

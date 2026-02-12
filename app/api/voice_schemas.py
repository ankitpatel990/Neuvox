"""
Pydantic schemas for Phase 2 voice API endpoints.

Defines request/response models for voice-based interaction with the
ScamShield AI honeypot, including transcription metadata, voice fraud
detection results, and the voice engagement response.
"""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from app.api.schemas import ExtractedIntelligence


class TranscriptionMetadata(BaseModel):
    """Speech-to-text transcription result metadata."""

    text: str = Field(
        ...,
        description="Transcribed text from the audio input",
    )
    language: str = Field(
        ...,
        description="Detected or specified language (ISO 639-1 code)",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Transcription confidence score",
    )


class VoiceFraudMetadata(BaseModel):
    """Voice fraud detection result metadata (optional feature).

    Present in the response only when voice fraud detection is enabled
    via the ``VOICE_FRAUD_DETECTION`` configuration flag.
    """

    is_synthetic: bool = Field(
        ...,
        description="Whether the voice is classified as synthetic or deepfake",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Voice fraud detection confidence score",
    )
    risk_level: str = Field(
        ...,
        description="Assessed risk level: 'low', 'medium', or 'high'",
    )


class VoiceEngageResponse(BaseModel):
    """Response schema for POST /api/v1/voice/engage."""

    session_id: str = Field(
        ...,
        description="Session identifier for multi-turn voice conversations",
    )
    scam_detected: bool = Field(
        ...,
        description="Whether a scam was detected in the transcribed message",
    )
    scam_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Scam detection confidence score",
    )
    scam_type: Optional[str] = Field(
        None,
        description="Classified scam type derived from detection indicators",
    )
    turn_count: int = Field(
        ...,
        ge=0,
        description="Current conversation turn number",
    )
    ai_reply_text: str = Field(
        ...,
        description="AI honeypot agent's text reply to the scammer",
    )
    ai_reply_audio_url: Optional[str] = Field(
        None,
        description="URL to the synthesized audio response file",
    )
    transcription: TranscriptionMetadata = Field(
        ...,
        description="Speech-to-text transcription results",
    )
    voice_fraud: Optional[VoiceFraudMetadata] = Field(
        None,
        description="Voice fraud detection results (present when enabled)",
    )
    extracted_intelligence: Optional[ExtractedIntelligence] = Field(
        None,
        description="Extracted financial intelligence from the conversation",
    )
    processing_time_ms: int = Field(
        ...,
        ge=0,
        description="Total end-to-end processing time in milliseconds",
    )


class VoiceHealthResponse(BaseModel):
    """Response schema for GET /api/v1/voice/health."""

    status: str = Field(
        ...,
        description="Overall voice subsystem health status",
    )
    asr: Optional[Dict[str, Any]] = Field(
        None,
        description="ASR engine health details (model, device, loaded)",
    )
    tts: Optional[Dict[str, Any]] = Field(
        None,
        description="TTS engine health details (engine, loaded)",
    )

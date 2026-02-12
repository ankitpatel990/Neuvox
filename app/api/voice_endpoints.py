"""
Voice API endpoints for Phase 2 of ScamShield AI.

Provides voice-based scam interaction endpoints that wrap the existing
Phase 1 text pipeline with ASR (speech-to-text) on input and TTS
(text-to-speech) on output.  Phase 1 code is imported and reused
without modification.

Endpoints:
    POST /api/v1/voice/engage         - Voice-based honeypot engagement
    GET  /api/v1/voice/audio/{filename} - Serve generated audio files
    GET  /api/v1/voice/health         - Voice subsystem health check
"""

import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.api.auth import verify_api_key
from app.api.schemas import ExtractedIntelligence
from app.api.voice_schemas import (
    TranscriptionMetadata,
    VoiceEngageResponse,
    VoiceHealthResponse,
)
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AUDIO_OUTPUT_DIR: Path = Path(tempfile.gettempdir()) / "scamshield_audio"
AUDIO_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_AUDIO_CONTENT_TYPES = frozenset({
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/x-wav",
    "audio/wave",
    "audio/ogg",
    "audio/flac",
    "audio/webm",
    "audio/mp4",
    "audio/x-m4a",
})

# TTS-supported language codes (subset of ISO 639-1 supported by gTTS)
_TTS_SUPPORTED_CODES = frozenset({"en", "hi", "gu", "ta", "te", "bn", "mr"})

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

voice_router = APIRouter(prefix="/api/v1/voice", tags=["voice"])


# ---------------------------------------------------------------------------
# POST /engage
# ---------------------------------------------------------------------------

@voice_router.post(
    "/engage",
    response_model=VoiceEngageResponse,
    dependencies=[Depends(verify_api_key)],
    summary="Voice-based honeypot engagement",
)
async def voice_engage(
    audio_file: UploadFile = File(
        ..., description="Audio file (mp3, wav, ogg, flac, webm)"
    ),
    session_id: Optional[str] = Form(
        None, description="Session ID for multi-turn conversations"
    ),
    language: Optional[str] = Form(
        None,
        description="Language hint (ISO 639-1 code, e.g. 'en', 'hi')",
    ),
) -> VoiceEngageResponse:
    """Process voice input through the scam detection and honeypot pipeline.

    Complete flow:
        1. Save uploaded audio to a temporary file.
        2. Transcribe audio to text via ASR (Whisper).
        3. Run Phase 1 scam detection on the transcribed text.
        4. If scam detected (or ongoing session), engage honeypot agent.
        5. Extract financial intelligence from the conversation.
        6. Convert the agent's text reply to speech via TTS (gTTS).
        7. Return structured response with transcription, detection
           results, agent reply text, audio URL, and intelligence.

    Args:
        audio_file: Uploaded audio in a supported format.
        session_id: Optional session identifier for continuing a
            multi-turn conversation.
        language: Optional ISO 639-1 language hint for ASR and TTS.

    Returns:
        VoiceEngageResponse containing the full processing result.

    Raises:
        HTTPException: 400 for invalid input, 500 for internal errors.
    """
    start_time: float = time.time()
    temp_audio_path: Optional[str] = None

    try:
        # Lazy imports -- avoids loading heavy models at module import time
        # and mirrors the Phase 1 import pattern inside endpoint handlers.
        from app.models.detector import get_detector
        from app.models.extractor import extract_intelligence
        from app.agent.honeypot import HoneypotAgent
        from app.database.redis_client import (
            get_session_state_with_fallback,
            save_session_state_with_fallback,
        )
        from app.voice.asr import get_asr_engine
        from app.voice.tts import get_tts_engine

        # ---- 1. Validate and persist upload --------------------------------
        _validate_audio_upload(audio_file)
        temp_audio_path = await _save_upload_to_temp(audio_file)

        # ---- 2. ASR: speech-to-text ----------------------------------------
        asr_engine = get_asr_engine()
        transcription = asr_engine.transcribe(
            temp_audio_path,
            language=language if language and language != "auto" else None,
        )

        transcribed_text: str = transcription.get("text", "")
        asr_language: str = transcription.get("language", "unknown")
        asr_confidence: float = transcription.get("confidence", 0.0)

        if not transcribed_text.strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "code": "EMPTY_TRANSCRIPTION",
                    "message": (
                        "No speech detected in the uploaded audio file."
                    ),
                },
            )

        logger.info(
            "ASR complete: language=%s, confidence=%.3f, text_length=%d",
            asr_language,
            asr_confidence,
            len(transcribed_text),
        )

        # ---- 3. Determine processing language ------------------------------
        process_language: str = (
            language
            if language and language != "auto"
            else asr_language
        )

        # ---- 4. Session management -----------------------------------------
        if not session_id:
            session_id = str(uuid.uuid4())

        session_state = None
        is_ongoing_session: bool = False

        existing_state = get_session_state_with_fallback(session_id)
        if existing_state and existing_state.get("turn_count", 0) > 0:
            session_state = existing_state
            is_ongoing_session = True
            logger.info(
                "Continuing voice session %s, turn=%d",
                session_id,
                session_state.get("turn_count", 0),
            )

        # ---- 5. Scam detection (Phase 1 detector) --------------------------
        detector = get_detector()
        detection = detector.detect(transcribed_text, process_language)

        scam_detected: bool = detection.get("scam_detected", False)
        confidence: float = detection.get("confidence", 0.0)
        indicators: list = detection.get("indicators", [])
        scam_type: Optional[str] = indicators[0] if indicators else None

        # ---- 6. Non-scam, non-ongoing -> early return ----------------------
        if not scam_detected and not is_ongoing_session:
            processing_time_ms = int((time.time() - start_time) * 1000)
            logger.info(
                "No scam detected in voice session %s (confidence=%.2f)",
                session_id,
                confidence,
            )
            return VoiceEngageResponse(
                session_id=session_id,
                scam_detected=False,
                scam_confidence=confidence,
                scam_type=None,
                turn_count=0,
                ai_reply_text="No scam detected. Message appears legitimate.",
                ai_reply_audio_url=None,
                transcription=TranscriptionMetadata(
                    text=transcribed_text,
                    language=asr_language,
                    confidence=asr_confidence,
                ),
                voice_fraud=None,
                extracted_intelligence=None,
                processing_time_ms=processing_time_ms,
            )

        # ---- 7. Scam or ongoing -> honeypot engagement ---------------------
        if is_ongoing_session:
            existing_confidence = session_state.get("scam_confidence", 0.0)
            confidence = max(confidence, existing_confidence)
            scam_detected = True

        agent = HoneypotAgent()
        result = agent.engage(transcribed_text, session_state)

        # ---- 8. Intelligence extraction (Phase 1 extractor) ----------------
        full_text: str = " ".join(
            msg.get("message", "") for msg in result.get("messages", [])
        )
        intel, extraction_confidence = extract_intelligence(full_text)

        result["extracted_intel"] = intel
        result["extraction_confidence"] = extraction_confidence
        result["scam_confidence"] = confidence

        # ---- 9. Persist session to Redis -----------------------------------
        save_session_state_with_fallback(session_id, result)

        # ---- 10. Extract agent reply text ----------------------------------
        agent_messages = [
            m for m in result.get("messages", [])
            if m.get("sender") == "agent"
        ]
        agent_reply: str = (
            agent_messages[-1]["message"]
            if agent_messages
            else "Engaged with scammer."
        )

        # ---- 11. TTS: text-to-speech ---------------------------------------
        tts_language: str = _resolve_tts_language(asr_language, language)
        audio_url: Optional[str] = None

        try:
            tts_engine = get_tts_engine()
            audio_filename: str = f"reply_{uuid.uuid4().hex}.mp3"
            audio_output_path: str = str(AUDIO_OUTPUT_DIR / audio_filename)

            tts_engine.synthesize(
                text=agent_reply,
                language=tts_language,
                output_path=audio_output_path,
            )
            audio_url = f"/api/v1/voice/audio/{audio_filename}"
            logger.info("TTS complete: %s", audio_url)
        except Exception as tts_exc:
            # TTS is non-critical; the text reply is still usable.
            logger.warning(
                "TTS synthesis failed, returning text-only response: %s",
                tts_exc,
            )

        # ---- 12. Build response --------------------------------------------
        turn_count: int = result.get("turn_count", 1)
        processing_time_ms = int((time.time() - start_time) * 1000)

        extracted_intelligence = ExtractedIntelligence(
            upi_ids=intel.get("upi_ids", []),
            bank_accounts=intel.get("bank_accounts", []),
            ifsc_codes=intel.get("ifsc_codes", []),
            phone_numbers=intel.get("phone_numbers", []),
            phishing_links=intel.get("phishing_links", []),
            extraction_confidence=extraction_confidence,
        )

        logger.info(
            "Voice engagement complete: session=%s, turn=%d, "
            "confidence=%.2f, processing_time=%dms",
            session_id,
            turn_count,
            confidence,
            processing_time_ms,
        )

        return VoiceEngageResponse(
            session_id=session_id,
            scam_detected=True,
            scam_confidence=confidence,
            scam_type=scam_type,
            turn_count=turn_count,
            ai_reply_text=agent_reply,
            ai_reply_audio_url=audio_url,
            transcription=TranscriptionMetadata(
                text=transcribed_text,
                language=asr_language,
                confidence=asr_confidence,
            ),
            voice_fraud=None,
            extracted_intelligence=extracted_intelligence,
            processing_time_ms=processing_time_ms,
        )

    except HTTPException:
        raise
    except ValueError as exc:
        logger.warning("Validation error in voice engage: %s", exc)
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_REQUEST",
                "message": str(exc),
            },
        )
    except Exception as exc:
        logger.error("Voice engage failed: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "VOICE_PROCESSING_ERROR",
                "message": "An error occurred during voice processing.",
                "details": str(exc) if settings.DEBUG else None,
            },
        )
    finally:
        if temp_audio_path:
            _cleanup_file(temp_audio_path)


# ---------------------------------------------------------------------------
# GET /audio/{filename}
# ---------------------------------------------------------------------------

@voice_router.get(
    "/audio/{filename}",
    summary="Serve generated audio response",
)
async def serve_audio(filename: str) -> FileResponse:
    """Serve a previously generated TTS audio file.

    Args:
        filename: Name of the audio file (e.g. ``reply_<uuid>.mp3``).

    Returns:
        FileResponse streaming the MP3 audio content.

    Raises:
        HTTPException: 400 if the filename contains path-traversal
            characters, 404 if the file does not exist.
    """
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_FILENAME",
                "message": "Invalid audio filename.",
            },
        )

    file_path: Path = AUDIO_OUTPUT_DIR / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail={
                "code": "AUDIO_NOT_FOUND",
                "message": f"Audio file '{filename}' not found.",
            },
        )

    return FileResponse(
        path=str(file_path),
        media_type="audio/mpeg",
        filename=filename,
    )


# ---------------------------------------------------------------------------
# GET /health
# ---------------------------------------------------------------------------

@voice_router.get(
    "/health",
    response_model=VoiceHealthResponse,
    summary="Voice subsystem health check",
)
async def voice_health() -> VoiceHealthResponse:
    """Check the operational status of ASR and TTS engines.

    Returns:
        VoiceHealthResponse reporting the status of each voice engine.
    """
    asr_info = None
    tts_info = None
    overall_status = "healthy"

    # ASR health
    try:
        from app.voice.asr import get_asr_engine

        asr = get_asr_engine()
        asr_info = {
            "model": asr.model_size,
            "device": asr.device,
            "loaded": asr.model is not None,
        }
    except Exception as exc:
        logger.warning("ASR health check failed: %s", exc)
        asr_info = {"loaded": False, "error": str(exc)}
        overall_status = "degraded"

    # TTS health
    try:
        from app.voice.tts import get_tts_engine

        tts = get_tts_engine()
        tts_info = {
            "engine": tts.engine,
            "loaded": True,
        }
    except Exception as exc:
        logger.warning("TTS health check failed: %s", exc)
        tts_info = {"loaded": False, "error": str(exc)}
        overall_status = "degraded"

    # Both engines down => unhealthy
    if (
        asr_info
        and not asr_info.get("loaded")
        and tts_info
        and not tts_info.get("loaded")
    ):
        overall_status = "unhealthy"

    return VoiceHealthResponse(
        status=overall_status,
        asr=asr_info,
        tts=tts_info,
    )


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _validate_audio_upload(audio_file: UploadFile) -> None:
    """Validate that the uploaded file is a usable audio file.

    Args:
        audio_file: FastAPI UploadFile instance.

    Raises:
        HTTPException: 400 if the file is missing or has an
            unsupported content type.
    """
    if not audio_file or not audio_file.filename:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "MISSING_AUDIO_FILE",
                "message": "An audio file is required.",
            },
        )

    content_type: str = (audio_file.content_type or "").lower()

    # Only reject when the content type is explicitly non-audio.
    # Allow unknown/octet-stream through so that clients without proper
    # MIME detection still work.
    if (
        content_type
        and content_type not in ALLOWED_AUDIO_CONTENT_TYPES
        and not content_type.startswith("audio/")
        and content_type != "application/octet-stream"
    ):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_AUDIO_FORMAT",
                "message": (
                    f"Unsupported content type '{content_type}'. "
                    f"Accepted: {', '.join(sorted(ALLOWED_AUDIO_CONTENT_TYPES))}"
                ),
            },
        )


async def _save_upload_to_temp(audio_file: UploadFile) -> str:
    """Persist an uploaded audio file to a temporary path on disk.

    Args:
        audio_file: FastAPI UploadFile instance.

    Returns:
        Absolute path to the saved temporary file.

    Raises:
        HTTPException: 400 if the file body is empty, 500 if the
            file cannot be written.
    """
    suffix: str = Path(audio_file.filename or "audio.wav").suffix or ".wav"

    try:
        fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix="voice_in_")
        with os.fdopen(fd, "wb") as tmp:
            content: bytes = await audio_file.read()
            if not content:
                os.unlink(temp_path)
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": "EMPTY_AUDIO_FILE",
                        "message": "The uploaded audio file is empty.",
                    },
                )
            tmp.write(content)

        logger.debug(
            "Saved upload to temp file: %s (%d bytes)",
            temp_path,
            len(content),
        )
        return temp_path

    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to save uploaded audio: %s", exc)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "FILE_SAVE_ERROR",
                "message": "Failed to process the uploaded audio file.",
            },
        ) from exc


def _resolve_tts_language(
    asr_language: str,
    language_hint: Optional[str],
) -> str:
    """Determine the best language code for TTS synthesis.

    Priority order:
        1. Explicit client hint (if TTS-supported).
        2. ASR-detected language (if TTS-supported).
        3. English (``'en'``) as fallback.

    Args:
        asr_language: Language code detected by the ASR engine.
        language_hint: Optional language hint from the client form data.

    Returns:
        ISO 639-1 code supported by the TTS engine.
    """
    if language_hint:
        normalized: str = language_hint.strip().lower()
        if normalized in _TTS_SUPPORTED_CODES:
            return normalized

    if asr_language:
        normalized = asr_language.strip().lower()
        if normalized in _TTS_SUPPORTED_CODES:
            return normalized

    return "en"


def _cleanup_file(path: str) -> None:
    """Remove a temporary file, suppressing errors.

    Args:
        path: Absolute path to the file to remove.
    """
    try:
        if os.path.exists(path):
            os.remove(path)
    except OSError as exc:
        logger.debug("Failed to clean up temp file %s: %s", path, exc)

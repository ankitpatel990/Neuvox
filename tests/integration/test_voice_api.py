"""
Integration Tests for Phase 2 Voice API Endpoints.

Tests the full voice pipeline (engage, audio serving, health) with all
heavy dependencies (Whisper, gTTS, scam detector, honeypot agent) mocked
to allow fast, deterministic execution in CI.

Also verifies that Phase 1 text endpoints remain unaffected when
PHASE_2_ENABLED is toggled.
"""

import io
import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def voice_client():
    """Create a test client with Phase 2 voice routes registered.

    Patches PHASE_2_ENABLED=True in settings so that the voice router
    is included, then patches heavy voice dependencies so no real model
    loading occurs.
    """
    with patch.dict(os.environ, {"PHASE_2_ENABLED": "true", "ENVIRONMENT": "development"}):
        # Reload settings so PHASE_2_ENABLED takes effect
        from app.config import Settings
        patched_settings = Settings()

        with patch("app.config.settings", patched_settings), \
             patch("app.config.get_settings", return_value=patched_settings):
            # Import app *after* patching so the conditional router inclusion
            # picks up PHASE_2_ENABLED=True. We must also ensure that
            # voice_endpoints can be imported without Whisper/gTTS being real.
            # The endpoint itself lazy-imports them, so we just need the
            # router to register.
            from fastapi.testclient import TestClient
            from app.main import app
            client = TestClient(app)
            yield client


@pytest.fixture
def sample_audio_bytes():
    """Minimal WAV-like bytes for upload testing.

    Not a valid WAV file but sufficient to test form parsing and
    early validation in the endpoint (actual ASR is mocked).
    """
    # RIFF header + minimal data so the file is not empty
    return b"RIFF" + b"\x00" * 40 + b"WAVEfmt " + b"\x00" * 200


@pytest.fixture
def mock_voice_pipeline():
    """Mock the entire voice processing pipeline used inside voice_engage.

    Yields a dict of all mocked objects so tests can customise return
    values or assert calls.
    """
    mock_asr = MagicMock()
    mock_asr.transcribe.return_value = {
        "text": "You have won ten lakh rupees. Send OTP now.",
        "language": "en",
        "confidence": 0.92,
    }

    mock_tts = MagicMock()
    mock_tts.synthesize.return_value = "/tmp/reply_test.mp3"

    mock_detector = MagicMock()
    mock_detector.detect.return_value = {
        "scam_detected": True,
        "confidence": 0.95,
        "indicators": ["lottery_scam"],
    }

    mock_agent = MagicMock()
    mock_agent.engage.return_value = {
        "messages": [
            {"sender": "scammer", "message": "You won 10 lakh!"},
            {"sender": "agent", "message": "Oh wonderful! How do I claim it?"},
        ],
        "turn_count": 1,
        "strategy": "build_trust",
        "persona": "elderly",
    }

    mock_extract = MagicMock(return_value=(
        {
            "upi_ids": ["scammer@paytm"],
            "bank_accounts": [],
            "ifsc_codes": [],
            "phone_numbers": ["+919876543210"],
            "phishing_links": [],
        },
        0.75,
    ))

    mock_redis_get = MagicMock(return_value=None)
    mock_redis_save = MagicMock()

    # Lazy imports inside voice_engage resolve names from the source modules,
    # so patches must target those modules directly.
    patches = {
        "asr": patch(
            "app.voice.asr.get_asr_engine", return_value=mock_asr
        ),
        "tts": patch(
            "app.voice.tts.get_tts_engine", return_value=mock_tts
        ),
        "detector": patch(
            "app.models.detector.get_detector", return_value=mock_detector
        ),
        "agent_cls": patch(
            "app.agent.honeypot.HoneypotAgent", return_value=mock_agent
        ),
        "extract": patch(
            "app.models.extractor.extract_intelligence", mock_extract
        ),
        "redis_get": patch(
            "app.database.redis_client.get_session_state_with_fallback",
            mock_redis_get,
        ),
        "redis_save": patch(
            "app.database.redis_client.save_session_state_with_fallback",
            mock_redis_save,
        ),
    }

    started = {}
    for key, p in patches.items():
        started[key] = p.start()

    yield {
        "asr": mock_asr,
        "tts": mock_tts,
        "detector": mock_detector,
        "agent": mock_agent,
        "extract": mock_extract,
        "redis_get": mock_redis_get,
        "redis_save": mock_redis_save,
    }

    for p in patches.values():
        p.stop()


# ---------------------------------------------------------------------------
# Voice Engage Endpoint
# ---------------------------------------------------------------------------

class TestVoiceEngageEndpoint:
    """Tests for POST /api/v1/voice/engage."""

    def test_engage_returns_200_with_valid_audio(
        self, voice_client, sample_audio_bytes, mock_voice_pipeline
    ):
        """Verify a valid audio upload returns 200 with expected response fields."""
        response = voice_client.post(
            "/api/v1/voice/engage",
            files={"audio_file": ("test.wav", io.BytesIO(sample_audio_bytes), "audio/wav")},
            data={"language": "en"},
            headers={"x-api-key": "dev-key-12345"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "session_id" in data
        assert data["scam_detected"] is True
        assert 0.0 <= data["scam_confidence"] <= 1.0
        assert data["ai_reply_text"] == "Oh wonderful! How do I claim it?"
        assert data["turn_count"] == 1
        assert data["processing_time_ms"] >= 0

        # Transcription metadata
        assert data["transcription"]["text"] == "You have won ten lakh rupees. Send OTP now."
        assert data["transcription"]["language"] == "en"
        assert data["transcription"]["confidence"] == 0.92

    def test_engage_returns_extracted_intelligence(
        self, voice_client, sample_audio_bytes, mock_voice_pipeline
    ):
        """Verify extracted intelligence fields are populated."""
        response = voice_client.post(
            "/api/v1/voice/engage",
            files={"audio_file": ("test.wav", io.BytesIO(sample_audio_bytes), "audio/wav")},
            headers={"x-api-key": "dev-key-12345"},
        )
        data = response.json()
        intel = data.get("extracted_intelligence")

        assert intel is not None
        assert "scammer@paytm" in intel["upi_ids"]
        assert "+919876543210" in intel["phone_numbers"]

    def test_engage_returns_audio_url_when_tts_succeeds(
        self, voice_client, sample_audio_bytes, mock_voice_pipeline
    ):
        """Verify ai_reply_audio_url is present when TTS synthesis succeeds."""
        response = voice_client.post(
            "/api/v1/voice/engage",
            files={"audio_file": ("test.wav", io.BytesIO(sample_audio_bytes), "audio/wav")},
            headers={"x-api-key": "dev-key-12345"},
        )
        data = response.json()

        # The endpoint builds the URL from the filename portion of the TTS output
        assert data["ai_reply_audio_url"] is not None
        assert "/api/v1/voice/audio/" in data["ai_reply_audio_url"]

    def test_engage_with_session_id_continues_conversation(
        self, voice_client, sample_audio_bytes, mock_voice_pipeline
    ):
        """Verify providing a session_id is accepted and echoed back."""
        session_id = str(uuid.uuid4())

        response = voice_client.post(
            "/api/v1/voice/engage",
            files={"audio_file": ("test.wav", io.BytesIO(sample_audio_bytes), "audio/wav")},
            data={"session_id": session_id},
            headers={"x-api-key": "dev-key-12345"},
        )
        data = response.json()
        assert data["session_id"] == session_id

    def test_engage_auto_generates_session_id(
        self, voice_client, sample_audio_bytes, mock_voice_pipeline
    ):
        """Verify a session_id is generated when none is provided."""
        response = voice_client.post(
            "/api/v1/voice/engage",
            files={"audio_file": ("test.wav", io.BytesIO(sample_audio_bytes), "audio/wav")},
            headers={"x-api-key": "dev-key-12345"},
        )
        data = response.json()
        # Validate UUID format
        uuid.UUID(data["session_id"])

    def test_engage_non_scam_returns_safe_response(
        self, voice_client, sample_audio_bytes, mock_voice_pipeline
    ):
        """Verify a non-scam transcription returns scam_detected=false."""
        mock_voice_pipeline["asr"].transcribe.return_value = {
            "text": "Hello, how are you?",
            "language": "en",
            "confidence": 0.88,
        }
        mock_voice_pipeline["detector"].detect.return_value = {
            "scam_detected": False,
            "confidence": 0.10,
            "indicators": [],
        }
        # Clear any prior session state
        mock_voice_pipeline["redis_get"].return_value = None

        response = voice_client.post(
            "/api/v1/voice/engage",
            files={"audio_file": ("test.wav", io.BytesIO(sample_audio_bytes), "audio/wav")},
            headers={"x-api-key": "dev-key-12345"},
        )
        data = response.json()

        assert data["scam_detected"] is False
        assert data["ai_reply_text"] == "No scam detected. Message appears legitimate."


class TestVoiceInvalidAudio:
    """Tests for invalid audio uploads to POST /api/v1/voice/engage."""

    def test_engage_missing_audio_file_returns_422(self, voice_client):
        """Verify 422 when no audio_file part is included in the request."""
        response = voice_client.post(
            "/api/v1/voice/engage",
            headers={"x-api-key": "dev-key-12345"},
        )
        assert response.status_code == 422

    def test_engage_empty_audio_file_returns_400(
        self, voice_client, mock_voice_pipeline
    ):
        """Verify 400 when the uploaded audio file is empty (zero bytes)."""
        response = voice_client.post(
            "/api/v1/voice/engage",
            files={"audio_file": ("empty.wav", io.BytesIO(b""), "audio/wav")},
            headers={"x-api-key": "dev-key-12345"},
        )
        assert response.status_code == 400

    def test_engage_non_audio_content_type_returns_400(
        self, voice_client, mock_voice_pipeline
    ):
        """Verify 400 when the uploaded file has a non-audio content type."""
        response = voice_client.post(
            "/api/v1/voice/engage",
            files={"audio_file": ("doc.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
            headers={"x-api-key": "dev-key-12345"},
        )
        assert response.status_code == 400

    def test_engage_empty_transcription_returns_400(
        self, voice_client, sample_audio_bytes, mock_voice_pipeline
    ):
        """Verify 400 when ASR produces an empty transcription."""
        mock_voice_pipeline["asr"].transcribe.return_value = {
            "text": "",
            "language": "unknown",
            "confidence": 0.0,
        }
        response = voice_client.post(
            "/api/v1/voice/engage",
            files={"audio_file": ("test.wav", io.BytesIO(sample_audio_bytes), "audio/wav")},
            headers={"x-api-key": "dev-key-12345"},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["code"] == "EMPTY_TRANSCRIPTION"


# ---------------------------------------------------------------------------
# Audio Download Endpoint
# ---------------------------------------------------------------------------

class TestVoiceAudioDownload:
    """Tests for GET /api/v1/voice/audio/{filename}."""

    def test_serve_existing_audio_file(self, voice_client):
        """Verify a valid audio file is served with correct media type."""
        # Create a temp file in the audio output directory
        from app.api.voice_endpoints import AUDIO_OUTPUT_DIR
        test_filename = f"reply_{uuid.uuid4().hex}.mp3"
        test_path = AUDIO_OUTPUT_DIR / test_filename
        test_path.write_bytes(b"\xff\xfb\x90\x00" + b"\x00" * 100)

        try:
            response = voice_client.get(f"/api/v1/voice/audio/{test_filename}")
            assert response.status_code == 200
            assert "audio" in response.headers.get("content-type", "")
        finally:
            if test_path.exists():
                test_path.unlink()

    def test_serve_nonexistent_file_returns_404(self, voice_client):
        """Verify 404 for a file that does not exist."""
        response = voice_client.get("/api/v1/voice/audio/nonexistent_abc123.mp3")
        assert response.status_code == 404

    def test_serve_path_traversal_returns_400(self, voice_client):
        """Verify 400 for path traversal attempts."""
        response = voice_client.get("/api/v1/voice/audio/../../../etc/passwd")
        assert response.status_code == 400

    def test_serve_path_with_backslash_returns_400(self, voice_client):
        """Verify 400 for filenames containing backslashes."""
        response = voice_client.get("/api/v1/voice/audio/..\\..\\etc\\passwd")
        assert response.status_code == 400


# ---------------------------------------------------------------------------
# Voice Health Endpoint
# ---------------------------------------------------------------------------

class TestVoiceHealthEndpoint:
    """Tests for GET /api/v1/voice/health."""

    def test_health_returns_200(self, voice_client):
        """Verify voice health endpoint returns 200."""
        with patch("app.voice.asr.get_asr_engine") as mock_asr, \
             patch("app.voice.tts.get_tts_engine") as mock_tts:
            asr_instance = MagicMock()
            asr_instance.model_size = "base"
            asr_instance.device = "cpu"
            asr_instance.model = MagicMock()
            mock_asr.return_value = asr_instance

            tts_instance = MagicMock()
            tts_instance.engine = "gtts"
            mock_tts.return_value = tts_instance

            response = voice_client.get("/api/v1/voice/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("healthy", "degraded", "unhealthy")
        assert "asr" in data
        assert "tts" in data

    def test_health_reports_degraded_when_asr_fails(self, voice_client):
        """Verify health reports degraded when ASR engine cannot be loaded."""
        with patch("app.voice.asr.get_asr_engine") as mock_asr, \
             patch("app.voice.tts.get_tts_engine") as mock_tts:
            mock_asr.side_effect = RuntimeError("Whisper model not found")

            tts_instance = MagicMock()
            tts_instance.engine = "gtts"
            mock_tts.return_value = tts_instance

            response = voice_client.get("/api/v1/voice/health")

        data = response.json()
        assert data["status"] in ("degraded", "unhealthy")

    def test_health_reports_unhealthy_when_both_fail(self, voice_client):
        """Verify health reports unhealthy when both ASR and TTS fail."""
        with patch("app.voice.asr.get_asr_engine") as mock_asr, \
             patch("app.voice.tts.get_tts_engine") as mock_tts:
            mock_asr.side_effect = RuntimeError("ASR unavailable")
            mock_tts.side_effect = RuntimeError("TTS unavailable")

            response = voice_client.get("/api/v1/voice/health")

        data = response.json()
        assert data["status"] == "unhealthy"


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

class TestVoiceAuthRequired:
    """Tests for authentication on voice endpoints.

    In production mode (ENVIRONMENT != development), requests without a
    valid x-api-key header should be rejected.
    """

    def test_engage_without_api_key_in_production(self, sample_audio_bytes):
        """Verify 401 when x-api-key is missing in production mode."""
        with patch.dict(os.environ, {
            "PHASE_2_ENABLED": "true",
            "ENVIRONMENT": "production",
            "API_KEY": "secret-prod-key",
        }):
            from app.config import Settings
            prod_settings = Settings()

            with patch("app.config.settings", prod_settings), \
                 patch("app.config.get_settings", return_value=prod_settings), \
                 patch("app.api.auth.settings", prod_settings):
                from app.main import app
                client = TestClient(app)
                response = client.post(
                    "/api/v1/voice/engage",
                    files={"audio_file": ("test.wav", io.BytesIO(sample_audio_bytes), "audio/wav")},
                )
                assert response.status_code == 401

    def test_engage_with_invalid_api_key_in_production(self, sample_audio_bytes):
        """Verify 401 when x-api-key is wrong in production mode."""
        with patch.dict(os.environ, {
            "PHASE_2_ENABLED": "true",
            "ENVIRONMENT": "production",
            "API_KEY": "secret-prod-key",
        }):
            from app.config import Settings
            prod_settings = Settings()

            with patch("app.config.settings", prod_settings), \
                 patch("app.config.get_settings", return_value=prod_settings), \
                 patch("app.api.auth.settings", prod_settings):
                from app.main import app
                client = TestClient(app)
                response = client.post(
                    "/api/v1/voice/engage",
                    files={"audio_file": ("test.wav", io.BytesIO(sample_audio_bytes), "audio/wav")},
                    headers={"x-api-key": "wrong-key"},
                )
                assert response.status_code == 401


# ---------------------------------------------------------------------------
# Phase 1 Unaffected
# ---------------------------------------------------------------------------

class TestPhase1Unaffected:
    """Verify Phase 1 text endpoints work regardless of Phase 2 state."""

    def test_health_endpoint_with_phase_2_disabled(self):
        """Verify /api/v1/health works when PHASE_2_ENABLED=false."""
        with patch.dict(os.environ, {"PHASE_2_ENABLED": "false", "ENVIRONMENT": "development"}):
            from app.config import Settings
            s = Settings()
            with patch("app.config.settings", s), \
                 patch("app.config.get_settings", return_value=s):
                from app.main import app
                client = TestClient(app)
                response = client.get("/api/v1/health")
                assert response.status_code == 200
                data = response.json()
                assert "status" in data
                assert "version" in data

    def test_engage_endpoint_with_phase_2_disabled(self):
        """Verify /api/v1/honeypot/engage works when PHASE_2_ENABLED=false."""
        with patch.dict(os.environ, {"PHASE_2_ENABLED": "false", "ENVIRONMENT": "development"}):
            from app.config import Settings
            s = Settings()
            with patch("app.config.settings", s), \
                 patch("app.config.get_settings", return_value=s):
                from app.main import app
                client = TestClient(app)
                response = client.post(
                    "/api/v1/honeypot/engage",
                    json={"message": "You won 10 lakh! Send OTP now!"},
                )
                assert response.status_code == 200
                data = response.json()
                assert "scam_detected" in data
                assert "session_id" in data

    def test_voice_endpoints_not_registered_when_disabled(self):
        """Verify voice routes return 404 when PHASE_2_ENABLED=false."""
        with patch.dict(os.environ, {"PHASE_2_ENABLED": "false", "ENVIRONMENT": "development"}):
            from app.config import Settings
            s = Settings()
            with patch("app.config.settings", s), \
                 patch("app.config.get_settings", return_value=s):
                from app.main import app
                client = TestClient(app)
                response = client.get("/api/v1/voice/health")
                assert response.status_code == 404

    def test_batch_endpoint_with_phase_2_disabled(self):
        """Verify /api/v1/honeypot/batch works when PHASE_2_ENABLED=false."""
        with patch.dict(os.environ, {"PHASE_2_ENABLED": "false", "ENVIRONMENT": "development"}):
            from app.config import Settings
            s = Settings()
            with patch("app.config.settings", s), \
                 patch("app.config.get_settings", return_value=s):
                from app.main import app
                client = TestClient(app)
                response = client.post(
                    "/api/v1/honeypot/batch",
                    json={"messages": [{"id": "1", "message": "Test message"}]},
                )
                assert response.status_code == 200

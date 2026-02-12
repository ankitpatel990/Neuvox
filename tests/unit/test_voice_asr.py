"""
Unit Tests for Phase 2 ASR (Automatic Speech Recognition) Engine.

Tests the Whisper-based ASREngine covering initialization, transcription,
confidence calculation, error handling, and singleton management.

All Whisper and torch dependencies are mocked to allow running tests
without GPU hardware or downloaded model weights.
"""

import math
import os
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_asr_singleton():
    """Reset the module-level ASR singleton before each test."""
    import app.voice.asr as asr_mod
    asr_mod._asr_engine = None
    yield
    asr_mod._asr_engine = None


@pytest.fixture
def mock_whisper_model():
    """Return a MagicMock that behaves like a loaded Whisper model."""
    model = MagicMock()
    model.transcribe.return_value = {
        "text": " Hello, you have won ten lakh rupees. ",
        "language": "en",
        "segments": [
            {
                "avg_logprob": -0.25,
                "no_speech_prob": 0.05,
                "start": 0.0,
                "end": 3.0,
            },
            {
                "avg_logprob": -0.30,
                "no_speech_prob": 0.08,
                "start": 3.0,
                "end": 5.5,
            },
        ],
    }
    return model


@pytest.fixture
def mock_whisper_hindi_result():
    """Whisper result simulating a Hindi transcription."""
    return {
        "text": " आप जीत गए हैं दस लाख रुपये ",
        "language": "hi",
        "segments": [
            {
                "avg_logprob": -0.35,
                "no_speech_prob": 0.10,
                "start": 0.0,
                "end": 4.0,
            },
        ],
    }


# ---------------------------------------------------------------------------
# Test Classes
# ---------------------------------------------------------------------------

class TestASREngineInitialization:
    """Tests for ASREngine.__init__ and model loading."""

    @patch("app.voice.asr.whisper")
    @patch("app.voice.asr.torch")
    def test_init_with_valid_model_size(self, mock_torch, mock_whisper):
        """Verify engine initializes with each valid model size."""
        mock_torch.cuda.is_available.return_value = False
        mock_whisper.load_model.return_value = MagicMock()

        from app.voice.asr import ASREngine, VALID_MODEL_SIZES

        for size in VALID_MODEL_SIZES:
            engine = ASREngine(model_size=size)
            assert engine.model_size == size
            assert engine.device == "cpu"
            assert engine.model is not None

    def test_init_with_invalid_model_size(self):
        """Verify ValueError is raised for unrecognized model sizes."""
        from app.voice.asr import ASREngine

        with pytest.raises(ValueError, match="Invalid model size"):
            ASREngine(model_size="nonexistent")

    @patch("app.voice.asr.whisper")
    @patch("app.voice.asr.torch")
    def test_init_selects_cuda_when_available(self, mock_torch, mock_whisper):
        """Verify engine selects CUDA when GPU is available and WHISPER_DEVICE=auto."""
        mock_torch.cuda.is_available.return_value = True
        mock_whisper.load_model.return_value = MagicMock()

        with patch("app.voice.asr.settings") as mock_settings:
            mock_settings.WHISPER_DEVICE = "auto"
            from app.voice.asr import ASREngine
            engine = ASREngine(model_size="base")
            assert engine.device == "cuda"

    @patch("app.voice.asr.whisper")
    @patch("app.voice.asr.torch")
    def test_init_falls_back_to_cpu_when_cuda_unavailable(
        self, mock_torch, mock_whisper
    ):
        """Verify engine falls back to CPU when CUDA is requested but unavailable."""
        mock_torch.cuda.is_available.return_value = False
        mock_whisper.load_model.return_value = MagicMock()

        with patch("app.voice.asr.settings") as mock_settings:
            mock_settings.WHISPER_DEVICE = "cuda"
            from app.voice.asr import ASREngine
            engine = ASREngine(model_size="tiny")
            assert engine.device == "cpu"

    @patch("app.voice.asr.whisper")
    @patch("app.voice.asr.torch")
    def test_init_respects_explicit_cpu_setting(self, mock_torch, mock_whisper):
        """Verify engine uses CPU when WHISPER_DEVICE=cpu regardless of GPU."""
        mock_torch.cuda.is_available.return_value = True
        mock_whisper.load_model.return_value = MagicMock()

        with patch("app.voice.asr.settings") as mock_settings:
            mock_settings.WHISPER_DEVICE = "cpu"
            from app.voice.asr import ASREngine
            engine = ASREngine(model_size="base")
            assert engine.device == "cpu"

    @patch("app.voice.asr.whisper")
    @patch("app.voice.asr.torch")
    def test_init_raises_on_model_load_failure(self, mock_torch, mock_whisper):
        """Verify RuntimeError is raised when Whisper model fails to load."""
        mock_torch.cuda.is_available.return_value = False
        mock_whisper.load_model.side_effect = OSError("Download failed")

        from app.voice.asr import ASREngine

        with pytest.raises(RuntimeError, match="Failed to load Whisper model"):
            ASREngine(model_size="base")


class TestASRTranscribeEnglish:
    """Tests for ASREngine.transcribe with English audio."""

    @patch("app.voice.asr.whisper")
    @patch("app.voice.asr.torch")
    def test_transcribe_returns_expected_keys(
        self, mock_torch, mock_whisper, mock_whisper_model, tmp_path
    ):
        """Verify transcription result contains text, language, and confidence."""
        mock_torch.cuda.is_available.return_value = False
        mock_whisper.load_model.return_value = mock_whisper_model

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"\x00" * 1024)

        from app.voice.asr import ASREngine
        engine = ASREngine(model_size="base")
        result = engine.transcribe(str(audio_file))

        assert "text" in result
        assert "language" in result
        assert "confidence" in result

    @patch("app.voice.asr.whisper")
    @patch("app.voice.asr.torch")
    def test_transcribe_returns_stripped_text(
        self, mock_torch, mock_whisper, mock_whisper_model, tmp_path
    ):
        """Verify transcribed text has leading/trailing whitespace removed."""
        mock_torch.cuda.is_available.return_value = False
        mock_whisper.load_model.return_value = mock_whisper_model

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"\x00" * 1024)

        from app.voice.asr import ASREngine
        engine = ASREngine(model_size="base")
        result = engine.transcribe(str(audio_file))

        assert result["text"] == "Hello, you have won ten lakh rupees."
        assert result["language"] == "en"

    @patch("app.voice.asr.whisper")
    @patch("app.voice.asr.torch")
    def test_transcribe_with_language_hint(
        self, mock_torch, mock_whisper, mock_whisper_model, tmp_path
    ):
        """Verify language hint is passed to the Whisper model."""
        mock_torch.cuda.is_available.return_value = False
        mock_whisper.load_model.return_value = mock_whisper_model

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"\x00" * 1024)

        from app.voice.asr import ASREngine
        engine = ASREngine(model_size="base")
        engine.transcribe(str(audio_file), language="en")

        call_kwargs = mock_whisper_model.transcribe.call_args
        assert call_kwargs[1].get("language") == "en"

    @patch("app.voice.asr.whisper")
    @patch("app.voice.asr.torch")
    def test_transcribe_confidence_in_valid_range(
        self, mock_torch, mock_whisper, mock_whisper_model, tmp_path
    ):
        """Verify transcription confidence is in [0.0, 1.0]."""
        mock_torch.cuda.is_available.return_value = False
        mock_whisper.load_model.return_value = mock_whisper_model

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"\x00" * 1024)

        from app.voice.asr import ASREngine
        engine = ASREngine(model_size="base")
        result = engine.transcribe(str(audio_file))

        assert 0.0 <= result["confidence"] <= 1.0


class TestASRConfidenceCalculation:
    """Tests for ASREngine._calculate_confidence."""

    @patch("app.voice.asr.whisper")
    @patch("app.voice.asr.torch")
    def _make_engine(self, mock_torch, mock_whisper):
        mock_torch.cuda.is_available.return_value = False
        mock_whisper.load_model.return_value = MagicMock()
        from app.voice.asr import ASREngine
        return ASREngine(model_size="tiny")

    def test_confidence_zero_for_empty_segments(self):
        """Verify confidence is 0.0 when no segments are present."""
        engine = self._make_engine()
        assert engine._calculate_confidence({"segments": []}) == 0.0

    def test_confidence_high_for_strong_logprob(self):
        """Verify confidence is high when avg_logprob is near zero and no_speech is low."""
        engine = self._make_engine()
        result = {
            "segments": [
                {
                    "avg_logprob": -0.05,
                    "no_speech_prob": 0.02,
                    "start": 0.0,
                    "end": 5.0,
                }
            ]
        }
        confidence = engine._calculate_confidence(result)
        assert confidence > 0.8

    def test_confidence_low_for_poor_logprob(self):
        """Verify confidence is low when avg_logprob is very negative."""
        engine = self._make_engine()
        result = {
            "segments": [
                {
                    "avg_logprob": -3.0,
                    "no_speech_prob": 0.9,
                    "start": 0.0,
                    "end": 2.0,
                }
            ]
        }
        confidence = engine._calculate_confidence(result)
        assert confidence < 0.1

    def test_confidence_weighted_by_duration(self):
        """Verify longer segments have more influence on confidence."""
        engine = self._make_engine()

        # Short poor segment + long good segment should yield high confidence
        result = {
            "segments": [
                {
                    "avg_logprob": -2.0,
                    "no_speech_prob": 0.5,
                    "start": 0.0,
                    "end": 0.5,
                },
                {
                    "avg_logprob": -0.1,
                    "no_speech_prob": 0.03,
                    "start": 0.5,
                    "end": 10.0,
                },
            ]
        }
        confidence = engine._calculate_confidence(result)
        assert confidence > 0.6

    def test_confidence_clamped_to_unit_range(self):
        """Verify confidence is always clamped to [0.0, 1.0]."""
        engine = self._make_engine()

        # Extreme values that could push outside range
        result = {
            "segments": [
                {
                    "avg_logprob": 0.0,
                    "no_speech_prob": 0.0,
                    "start": 0.0,
                    "end": 1.0,
                }
            ]
        }
        confidence = engine._calculate_confidence(result)
        assert 0.0 <= confidence <= 1.0

    def test_confidence_handles_zero_duration_segments(self):
        """Verify confidence does not crash on zero-duration segments."""
        engine = self._make_engine()
        result = {
            "segments": [
                {
                    "avg_logprob": -0.5,
                    "no_speech_prob": 0.1,
                    "start": 0.0,
                    "end": 0.0,
                }
            ]
        }
        confidence = engine._calculate_confidence(result)
        assert 0.0 <= confidence <= 1.0


class TestASRErrorHandling:
    """Tests for ASREngine.transcribe error paths."""

    @patch("app.voice.asr.whisper")
    @patch("app.voice.asr.torch")
    def test_transcribe_nonexistent_file(self, mock_torch, mock_whisper):
        """Verify transcribe returns empty result for a missing file."""
        mock_torch.cuda.is_available.return_value = False
        mock_whisper.load_model.return_value = MagicMock()

        from app.voice.asr import ASREngine
        engine = ASREngine(model_size="base")
        result = engine.transcribe("/nonexistent/path/audio.wav")

        assert result["text"] == ""
        assert result["confidence"] == 0.0

    @patch("app.voice.asr.whisper")
    @patch("app.voice.asr.torch")
    def test_transcribe_directory_path(self, mock_torch, mock_whisper, tmp_path):
        """Verify transcribe returns empty result when path is a directory."""
        mock_torch.cuda.is_available.return_value = False
        mock_whisper.load_model.return_value = MagicMock()

        from app.voice.asr import ASREngine
        engine = ASREngine(model_size="base")
        result = engine.transcribe(str(tmp_path))

        assert result["text"] == ""
        assert result["confidence"] == 0.0

    @patch("app.voice.asr.whisper")
    @patch("app.voice.asr.torch")
    def test_transcribe_with_unloaded_model(self, mock_torch, mock_whisper, tmp_path):
        """Verify transcribe returns empty result when model is None."""
        mock_torch.cuda.is_available.return_value = False
        mock_whisper.load_model.return_value = MagicMock()

        from app.voice.asr import ASREngine
        engine = ASREngine(model_size="base")
        engine.model = None

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"\x00" * 512)
        result = engine.transcribe(str(audio_file))

        assert result["text"] == ""
        assert result["confidence"] == 0.0

    @patch("app.voice.asr.whisper")
    @patch("app.voice.asr.torch")
    def test_transcribe_handles_whisper_exception(
        self, mock_torch, mock_whisper, tmp_path
    ):
        """Verify transcribe catches internal Whisper exceptions gracefully."""
        mock_torch.cuda.is_available.return_value = False
        model = MagicMock()
        model.transcribe.side_effect = RuntimeError("CUDA OOM")
        mock_whisper.load_model.return_value = model

        from app.voice.asr import ASREngine
        engine = ASREngine(model_size="base")

        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"\x00" * 512)
        result = engine.transcribe(str(audio_file))

        assert result["text"] == ""
        assert result["confidence"] == 0.0


class TestASRSingleton:
    """Tests for the module-level get_asr_engine singleton."""

    @patch("app.voice.asr.whisper")
    @patch("app.voice.asr.torch")
    def test_get_asr_engine_returns_same_instance(
        self, mock_torch, mock_whisper
    ):
        """Verify get_asr_engine returns the same object on successive calls."""
        mock_torch.cuda.is_available.return_value = False
        mock_whisper.load_model.return_value = MagicMock()

        from app.voice.asr import get_asr_engine

        engine_a = get_asr_engine()
        engine_b = get_asr_engine()
        assert engine_a is engine_b

    @patch("app.voice.asr.whisper")
    @patch("app.voice.asr.torch")
    def test_get_asr_engine_reads_settings(self, mock_torch, mock_whisper):
        """Verify get_asr_engine reads WHISPER_MODEL from settings."""
        mock_torch.cuda.is_available.return_value = False
        mock_whisper.load_model.return_value = MagicMock()

        with patch("app.voice.asr.settings") as mock_settings:
            mock_settings.WHISPER_MODEL = "small"
            mock_settings.WHISPER_DEVICE = "cpu"

            from app.voice.asr import get_asr_engine
            engine = get_asr_engine()
            assert engine.model_size == "small"

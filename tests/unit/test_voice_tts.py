"""
Unit Tests for Phase 2 TTS (Text-to-Speech) Engine.

Tests the gTTS-based TTSEngine covering initialization, synthesis,
language resolution, output path handling, error handling, and
singleton management.

The gTTS network dependency is mocked in all tests.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch, call

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_tts_singleton():
    """Reset the module-level TTS singleton before each test."""
    import app.voice.tts as tts_mod
    tts_mod._tts_engine = None
    yield
    tts_mod._tts_engine = None


@pytest.fixture
def mock_gtts():
    """Patch gTTS so no network calls are made during tests."""
    with patch("app.voice.tts.gTTS") as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance
        yield mock_cls, instance


# ---------------------------------------------------------------------------
# Test Classes
# ---------------------------------------------------------------------------

class TestTTSEngineInitialization:
    """Tests for TTSEngine.__init__."""

    def test_init_with_default_engine(self):
        """Verify engine initializes with the default gtts backend."""
        with patch("app.voice.tts.settings") as mock_settings:
            mock_settings.TTS_ENGINE = "gtts"
            from app.voice.tts import TTSEngine
            engine = TTSEngine()
            assert engine.engine == "gtts"

    def test_init_rejects_unsupported_engine(self):
        """Verify ValueError is raised for an unsupported TTS engine."""
        with patch("app.voice.tts.settings") as mock_settings:
            mock_settings.TTS_ENGINE = "unsupported_engine"
            from app.voice.tts import TTSEngine
            with pytest.raises(ValueError, match="Unsupported TTS engine"):
                TTSEngine()

    def test_init_reads_engine_from_settings(self):
        """Verify engine name is read from application settings."""
        with patch("app.voice.tts.settings") as mock_settings:
            mock_settings.TTS_ENGINE = "gtts"
            from app.voice.tts import TTSEngine
            engine = TTSEngine()
            assert engine.engine == "gtts"


class TestTTSSynthesizeEnglish:
    """Tests for TTSEngine.synthesize with English text."""

    def test_synthesize_creates_file(self, mock_gtts, tmp_path):
        """Verify synthesize produces an output file at the given path."""
        mock_cls, mock_instance = mock_gtts
        output_file = str(tmp_path / "output.mp3")

        # Simulate gTTS writing a file
        def fake_save(path):
            Path(path).write_bytes(b"\xff" * 100)

        mock_instance.save.side_effect = fake_save

        with patch("app.voice.tts.settings") as mock_settings:
            mock_settings.TTS_ENGINE = "gtts"
            from app.voice.tts import TTSEngine
            engine = TTSEngine()
            result_path = engine.synthesize("Hello world", language="en", output_path=output_file)

        assert result_path == output_file
        mock_cls.assert_called_once_with(text="Hello world", lang="en")
        mock_instance.save.assert_called_once_with(output_file)

    def test_synthesize_auto_generates_temp_file(self, mock_gtts):
        """Verify synthesize generates a temporary file when output_path is None."""
        mock_cls, mock_instance = mock_gtts
        mock_instance.save.side_effect = lambda p: Path(p).write_bytes(b"\xff" * 50)

        with patch("app.voice.tts.settings") as mock_settings:
            mock_settings.TTS_ENGINE = "gtts"
            from app.voice.tts import TTSEngine
            engine = TTSEngine()
            result_path = engine.synthesize("Test speech")

        assert result_path.endswith(".mp3")
        assert os.path.isabs(result_path)

        # Clean up temp file
        if os.path.exists(result_path):
            os.remove(result_path)

    def test_synthesize_returns_absolute_path(self, mock_gtts, tmp_path):
        """Verify synthesize always returns an absolute path."""
        _, mock_instance = mock_gtts
        mock_instance.save.side_effect = lambda p: Path(p).write_bytes(b"\xff" * 10)

        output_file = str(tmp_path / "result.mp3")
        with patch("app.voice.tts.settings") as mock_settings:
            mock_settings.TTS_ENGINE = "gtts"
            from app.voice.tts import TTSEngine
            engine = TTSEngine()
            result_path = engine.synthesize("Hello", output_path=output_file)

        assert os.path.isabs(result_path)


class TestTTSSynthesizeHindi:
    """Tests for TTSEngine.synthesize with Hindi text."""

    def test_synthesize_hindi_with_iso_code(self, mock_gtts, tmp_path):
        """Verify synthesis with ISO 639-1 code 'hi'."""
        mock_cls, mock_instance = mock_gtts
        mock_instance.save.side_effect = lambda p: Path(p).write_bytes(b"\xff" * 50)
        output_file = str(tmp_path / "hindi.mp3")

        with patch("app.voice.tts.settings") as mock_settings:
            mock_settings.TTS_ENGINE = "gtts"
            from app.voice.tts import TTSEngine
            engine = TTSEngine()
            engine.synthesize("नमस्ते", language="hi", output_path=output_file)

        mock_cls.assert_called_once_with(text="नमस्ते", lang="hi")

    def test_synthesize_hindi_with_full_name(self, mock_gtts, tmp_path):
        """Verify synthesis resolves 'hindi' to 'hi'."""
        mock_cls, mock_instance = mock_gtts
        mock_instance.save.side_effect = lambda p: Path(p).write_bytes(b"\xff" * 50)
        output_file = str(tmp_path / "hindi.mp3")

        with patch("app.voice.tts.settings") as mock_settings:
            mock_settings.TTS_ENGINE = "gtts"
            from app.voice.tts import TTSEngine
            engine = TTSEngine()
            engine.synthesize("नमस्ते दोस्तों", language="hindi", output_path=output_file)

        mock_cls.assert_called_once_with(text="नमस्ते दोस्तों", lang="hi")


class TestTTSLanguageMapping:
    """Tests for TTSEngine._resolve_language and LANGUAGE_MAP."""

    def test_resolve_all_iso_codes(self):
        """Verify all ISO 639-1 codes in SUPPORTED_LANGUAGE_CODES resolve correctly."""
        from app.voice.tts import TTSEngine, SUPPORTED_LANGUAGE_CODES
        for code in SUPPORTED_LANGUAGE_CODES:
            resolved = TTSEngine._resolve_language(code)
            assert resolved == code

    def test_resolve_all_language_names(self):
        """Verify all full language names in LANGUAGE_MAP resolve to their codes."""
        from app.voice.tts import TTSEngine, LANGUAGE_MAP
        for name, expected_code in LANGUAGE_MAP.items():
            resolved = TTSEngine._resolve_language(name)
            assert resolved == expected_code

    def test_resolve_case_insensitive(self):
        """Verify language resolution is case-insensitive."""
        from app.voice.tts import TTSEngine
        assert TTSEngine._resolve_language("ENGLISH") == "en"
        assert TTSEngine._resolve_language("Hindi") == "hi"
        assert TTSEngine._resolve_language("EN") == "en"
        assert TTSEngine._resolve_language("HI") == "hi"

    def test_resolve_strips_whitespace(self):
        """Verify language resolution strips leading/trailing whitespace."""
        from app.voice.tts import TTSEngine
        assert TTSEngine._resolve_language("  en  ") == "en"
        assert TTSEngine._resolve_language(" hindi ") == "hi"

    def test_resolve_rejects_unsupported_language(self):
        """Verify ValueError for languages not in the supported set."""
        from app.voice.tts import TTSEngine
        with pytest.raises(ValueError, match="Unsupported language"):
            TTSEngine._resolve_language("klingon")

    def test_resolve_rejects_empty_string(self):
        """Verify ValueError for empty language string."""
        from app.voice.tts import TTSEngine
        with pytest.raises(ValueError):
            TTSEngine._resolve_language("")

    def test_get_supported_languages_returns_full_map(self):
        """Verify get_supported_languages returns all entries from LANGUAGE_MAP."""
        with patch("app.voice.tts.settings") as mock_settings:
            mock_settings.TTS_ENGINE = "gtts"
            from app.voice.tts import TTSEngine, LANGUAGE_MAP
            engine = TTSEngine()
            supported = engine.get_supported_languages()
            assert supported == LANGUAGE_MAP
            # Confirm it returns a copy, not the original dict
            assert supported is not LANGUAGE_MAP


class TestTTSTempFileGeneration:
    """Tests for TTSEngine._resolve_output_path."""

    def test_auto_generates_temp_file_with_mp3_suffix(self):
        """Verify auto-generated path has .mp3 suffix."""
        from app.voice.tts import TTSEngine
        path = TTSEngine._resolve_output_path(None)
        assert path.endswith(".mp3")
        assert os.path.isabs(path)
        # Clean up the empty temp file that mkstemp created
        if os.path.exists(path):
            os.remove(path)

    def test_explicit_path_creates_parent_dirs(self, tmp_path):
        """Verify explicit output_path creates parent directories as needed."""
        from app.voice.tts import TTSEngine
        target = str(tmp_path / "nested" / "dir" / "output.mp3")
        resolved = TTSEngine._resolve_output_path(target)
        assert os.path.isdir(str(tmp_path / "nested" / "dir"))
        assert resolved == str(Path(target).resolve())

    def test_explicit_path_returns_absolute(self, tmp_path):
        """Verify explicit output_path is always resolved to absolute."""
        from app.voice.tts import TTSEngine
        target = str(tmp_path / "relative.mp3")
        resolved = TTSEngine._resolve_output_path(target)
        assert os.path.isabs(resolved)


class TestTTSErrorHandling:
    """Tests for TTSEngine error paths."""

    def test_synthesize_rejects_empty_text(self):
        """Verify ValueError is raised for empty text."""
        with patch("app.voice.tts.settings") as mock_settings:
            mock_settings.TTS_ENGINE = "gtts"
            from app.voice.tts import TTSEngine
            engine = TTSEngine()
            with pytest.raises(ValueError, match="Cannot synthesize empty text"):
                engine.synthesize("")

    def test_synthesize_rejects_whitespace_only_text(self):
        """Verify ValueError is raised for whitespace-only text."""
        with patch("app.voice.tts.settings") as mock_settings:
            mock_settings.TTS_ENGINE = "gtts"
            from app.voice.tts import TTSEngine
            engine = TTSEngine()
            with pytest.raises(ValueError, match="Cannot synthesize empty text"):
                engine.synthesize("   \n\t  ")

    def test_synthesize_rejects_unsupported_language(self):
        """Verify ValueError is raised for unsupported language in synthesize."""
        with patch("app.voice.tts.settings") as mock_settings:
            mock_settings.TTS_ENGINE = "gtts"
            from app.voice.tts import TTSEngine
            engine = TTSEngine()
            with pytest.raises(ValueError, match="Unsupported language"):
                engine.synthesize("hello", language="zz")

    def test_synthesize_wraps_gtts_failure_as_runtime_error(self, mock_gtts, tmp_path):
        """Verify RuntimeError wraps gTTS internal failures."""
        _, mock_instance = mock_gtts
        mock_instance.save.side_effect = Exception("Network timeout")

        output_file = str(tmp_path / "fail.mp3")
        with patch("app.voice.tts.settings") as mock_settings:
            mock_settings.TTS_ENGINE = "gtts"
            from app.voice.tts import TTSEngine
            engine = TTSEngine()
            with pytest.raises(RuntimeError, match="TTS synthesis failed"):
                engine.synthesize("Hello", output_path=output_file)

    def test_cleanup_file_removes_existing_file(self, tmp_path):
        """Verify _cleanup_file removes an existing file without error."""
        from app.voice.tts import TTSEngine
        target = tmp_path / "temp.mp3"
        target.write_bytes(b"\xff" * 10)
        TTSEngine._cleanup_file(str(target))
        assert not target.exists()

    def test_cleanup_file_ignores_missing_file(self):
        """Verify _cleanup_file does not raise for a non-existent file."""
        from app.voice.tts import TTSEngine
        TTSEngine._cleanup_file("/nonexistent/path.mp3")


class TestTTSSingleton:
    """Tests for the module-level get_tts_engine singleton."""

    def test_get_tts_engine_returns_same_instance(self):
        """Verify get_tts_engine returns the same object on successive calls."""
        with patch("app.voice.tts.settings") as mock_settings:
            mock_settings.TTS_ENGINE = "gtts"
            from app.voice.tts import get_tts_engine
            engine_a = get_tts_engine()
            engine_b = get_tts_engine()
            assert engine_a is engine_b

    def test_get_tts_engine_creates_tts_engine_type(self):
        """Verify get_tts_engine returns a TTSEngine instance."""
        with patch("app.voice.tts.settings") as mock_settings:
            mock_settings.TTS_ENGINE = "gtts"
            from app.voice.tts import get_tts_engine, TTSEngine
            engine = get_tts_engine()
            assert isinstance(engine, TTSEngine)

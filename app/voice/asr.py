"""
Automatic Speech Recognition (ASR) Module.

Provides speech-to-text transcription using OpenAI's Whisper model.
Supports multiple model sizes, automatic language detection, and
GPU acceleration when available.

This module is part of Phase 2 voice features and acts as the entry
point for converting spoken audio into text, which is then fed into
the Phase 1 text-based honeypot pipeline.
"""

import math
from pathlib import Path
from typing import Dict, Optional

import torch
import whisper

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

VALID_MODEL_SIZES = ("tiny", "base", "small", "medium", "large")

# Domain-specific vocabulary prompt.
# Whisper uses this as conditioning context to bias recognition toward
# expected terms in Indian financial scam conversations.  It is never
# emitted in the transcription output -- it only primes the decoder.
_DOMAIN_PROMPT = (
    "This is a phone call about financial transactions in India. "
    "Common terms: HDFC, SBI, ICICI, Axis Bank, UPI, Google Pay, PhonePe, "
    "Paytm, NEFT, RTGS, IFSC, bank account, lottery, reward, OTP, "
    "Aadhaar, PAN card, transfer, payment, rupees, lakhs, crores."
)


class ASREngine:
    """Automatic Speech Recognition engine powered by OpenAI Whisper.

    Handles audio transcription with configurable model sizes,
    automatic language detection, and confidence scoring.

    Attributes:
        model_size: Whisper model variant in use.
        device: Torch device for inference ('cuda' or 'cpu').
        model: Loaded Whisper model instance, or None if loading failed.
    """

    def __init__(self, model_size: str = "base") -> None:
        """Initialize the ASR engine.

        Args:
            model_size: Whisper model size. One of: tiny, base, small,
                medium, large. Larger models yield better accuracy at
                the cost of higher latency and memory usage.

        Raises:
            ValueError: If model_size is not a recognized Whisper variant.
        """
        if model_size not in VALID_MODEL_SIZES:
            raise ValueError(
                f"Invalid model size '{model_size}'. "
                f"Must be one of: {', '.join(VALID_MODEL_SIZES)}"
            )

        self.model_size: str = model_size
        self.device: str = self._resolve_device()
        self.model: Optional[whisper.Whisper] = None

        logger.info(
            "ASREngine initializing with model_size=%s, device=%s",
            self.model_size,
            self.device,
        )
        self._load_model()

    def _resolve_device(self) -> str:
        """Determine the compute device for Whisper inference.

        Reads the WHISPER_DEVICE setting ('auto', 'cpu', or 'cuda') and
        validates hardware availability before returning the device string.

        Returns:
            Device identifier: 'cuda' if GPU is available and requested,
            otherwise 'cpu'.
        """
        device_setting: str = getattr(settings, "WHISPER_DEVICE", "auto")

        if device_setting == "cuda":
            if torch.cuda.is_available():
                return "cuda"
            logger.warning(
                "CUDA requested but not available; falling back to CPU"
            )
            return "cpu"

        if device_setting == "cpu":
            return "cpu"

        # Auto-detection (default)
        if torch.cuda.is_available():
            logger.info("CUDA device detected; using GPU acceleration")
            return "cuda"

        logger.info("No CUDA device detected; using CPU")
        return "cpu"

    def _load_model(self) -> None:
        """Load the Whisper model into memory.

        Downloads model weights on first use and caches them in the
        default Whisper cache directory (~/.cache/whisper).

        Raises:
            RuntimeError: If model loading fails for any reason.
        """
        try:
            logger.info(
                "Loading Whisper model '%s' on device '%s'...",
                self.model_size,
                self.device,
            )
            self.model = whisper.load_model(
                self.model_size, device=self.device
            )
            logger.info(
                "Whisper model '%s' loaded successfully", self.model_size
            )
        except Exception as exc:
            logger.error(
                "Failed to load Whisper model '%s': %s",
                self.model_size,
                exc,
            )
            raise RuntimeError(
                f"Failed to load Whisper model '{self.model_size}': {exc}"
            ) from exc

    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = None,
    ) -> Dict[str, object]:
        """Transcribe an audio file to text.

        Args:
            audio_path: Path to the audio file. Whisper accepts mp3, wav,
                flac, ogg, and other ffmpeg-compatible formats.
            language: Optional ISO 639-1 language code (e.g. 'en', 'hi').
                When provided, skips automatic language detection and may
                improve accuracy for known languages.

        Returns:
            Dictionary with keys:
                - text (str): Transcribed text, or empty string on failure.
                - language (str): Detected or specified language code.
                - confidence (float): Score in [0.0, 1.0] reflecting
                  transcription reliability.
        """
        empty_result: Dict[str, object] = {
            "text": "",
            "language": language or "unknown",
            "confidence": 0.0,
        }

        audio_file = Path(audio_path)
        if not audio_file.exists():
            logger.error("Audio file not found: %s", audio_path)
            return empty_result

        if not audio_file.is_file():
            logger.error("Audio path is not a file: %s", audio_path)
            return empty_result

        if self.model is None:
            logger.error("Whisper model is not loaded; cannot transcribe")
            return empty_result

        try:
            logger.info("Transcribing audio file: %s", audio_path)

            decode_options: Dict[str, object] = {
                # Beam search for higher accuracy (default is greedy)
                "beam_size": 5,
                # Domain vocabulary prompt -- biases decoder toward
                # financial and Indian banking terminology
                "initial_prompt": _DOMAIN_PROMPT,
                # Disable FP16 on CPU to avoid precision issues
                "fp16": self.device == "cuda",
                # Prevent hallucinated repetitions at end of audio
                "condition_on_previous_text": False,
            }
            if language:
                decode_options["language"] = language

            result = self.model.transcribe(str(audio_file), **decode_options)

            transcribed_text: str = result.get("text", "").strip()
            detected_language: str = result.get(
                "language", language or "unknown"
            )
            confidence: float = self._calculate_confidence(result)

            logger.info(
                "Transcription complete: language=%s, confidence=%.3f, "
                "text_length=%d",
                detected_language,
                confidence,
                len(transcribed_text),
            )

            return {
                "text": transcribed_text,
                "language": detected_language,
                "confidence": confidence,
            }

        except Exception as exc:
            logger.error(
                "Transcription failed for '%s': %s", audio_path, exc
            )
            return empty_result

    def _calculate_confidence(self, result: Dict) -> float:
        """Calculate a confidence score from Whisper transcription output.

        Derives confidence from two signals in Whisper's segment data:
        1. Average log-probability of recognized tokens (higher is better).
        2. No-speech probability (lower is better).

        Segment contributions are weighted by their duration so that longer
        segments have proportionally more influence on the final score.

        Args:
            result: Raw Whisper transcription result containing a
                'segments' list. Each segment has 'avg_logprob',
                'no_speech_prob', 'start', and 'end' fields.

        Returns:
            Confidence score clamped to [0.0, 1.0], rounded to four
            decimal places.
        """
        segments = result.get("segments", [])

        if not segments:
            return 0.0

        weighted_logprob: float = 0.0
        total_duration: float = 0.0
        total_no_speech: float = 0.0

        for segment in segments:
            avg_logprob: float = segment.get("avg_logprob", -1.0)
            no_speech_prob: float = segment.get("no_speech_prob", 0.5)
            start: float = segment.get("start", 0.0)
            end: float = segment.get("end", 0.0)
            duration: float = max(end - start, 0.0)

            weighted_logprob += avg_logprob * duration
            total_duration += duration
            total_no_speech += no_speech_prob

        # Duration-weighted average log-probability
        if total_duration > 0:
            avg_logprob_score = weighted_logprob / total_duration
        else:
            avg_logprob_score = sum(
                s.get("avg_logprob", -1.0) for s in segments
            ) / len(segments)

        # Convert log-probability to linear [0, 1] range.
        # avg_logprob typically ranges from ~-1.0 (poor) to ~0.0 (perfect).
        prob_confidence: float = math.exp(max(avg_logprob_score, -10.0))

        # Average no-speech probability across segments (lower is better)
        avg_no_speech: float = total_no_speech / len(segments)
        speech_confidence: float = 1.0 - avg_no_speech

        # Combined score: product penalizes low confidence in either signal
        combined: float = prob_confidence * speech_confidence

        return round(max(0.0, min(1.0, combined)), 4)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_asr_engine: Optional[ASREngine] = None


def get_asr_engine() -> ASREngine:
    """Get or create the global ASR engine instance.

    Uses the singleton pattern to ensure only one copy of the Whisper
    model is loaded into memory. Configuration is read from application
    settings on first invocation.

    Returns:
        The shared ASREngine instance.
    """
    global _asr_engine

    if _asr_engine is None:
        model_size: str = getattr(settings, "WHISPER_MODEL", "base")
        logger.info(
            "Creating ASR engine singleton with model_size=%s", model_size
        )
        _asr_engine = ASREngine(model_size=model_size)

    return _asr_engine

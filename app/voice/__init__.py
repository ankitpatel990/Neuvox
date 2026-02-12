"""
Voice Module for Phase 2.

Provides voice-based interaction capabilities:
- ASR (Automatic Speech Recognition)
- TTS (Text-to-Speech)
- Voice fraud detection (optional)
"""

from typing import Optional

__all__ = [
    "ASREngine",
    "TTSEngine",
    "VoiceFraudDetector",
    "get_asr_engine",
    "get_tts_engine",
    "get_fraud_detector",
]

# Lazy imports to avoid loading heavy models unless Phase 2 is enabled
def get_asr_engine():
    """Get ASR engine instance."""
    from app.voice.asr import get_asr_engine as _get_asr
    return _get_asr()

def get_tts_engine():
    """Get TTS engine instance."""
    from app.voice.tts import get_tts_engine as _get_tts
    return _get_tts()

def get_fraud_detector():
    """Get voice fraud detector instance."""
    from app.voice.fraud_detector import get_fraud_detector as _get_fraud
    return _get_fraud()

"""
Language Detection Module.

Provides multi-language detection for:
- English (en)
- Hindi (hi)
- Hinglish (code-mixed Hindi and English)

Uses langdetect library with custom Hinglish detection logic.
Performance target: <100ms per detection.
"""

import time
from typing import Tuple, Optional

import langdetect
from langdetect import detect_langs, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException

from app.utils.logger import get_logger

logger = get_logger(__name__)

# Set seed for reproducible results in langdetect
DetectorFactory.seed = 0

# Supported language codes
SUPPORTED_LANGUAGES = {"en", "hi", "hinglish"}

# Default fallback values
DEFAULT_LANGUAGE = "en"
DEFAULT_CONFIDENCE = 0.3
ERROR_CONFIDENCE = 0.3

# Hinglish detection threshold - minimum ratio of each script type
HINGLISH_MIN_RATIO = 0.1


class LanguageDetector:
    """
    Language detection for English, Hindi, and Hinglish.
    
    Uses langdetect library with custom Hinglish detection logic.
    Thread-safe with deterministic results.
    
    Attributes:
        _initialized: Flag indicating successful initialization
    """
    
    def __init__(self) -> None:
        """
        Initialize the LanguageDetector.
        
        Sets the seed for reproducible results.
        """
        self._initialized = False
        try:
            # Ensure deterministic results
            DetectorFactory.seed = 0
            self._initialized = True
            logger.debug("LanguageDetector initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LanguageDetector: {e}")
            self._initialized = False
    
    def detect(self, text: str) -> Tuple[str, float]:
        """
        Detect the language of input text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Tuple of (language_code, confidence)
            language_code: 'en', 'hi', or 'hinglish'
            confidence: 0.0-1.0
            
        Raises:
            No exceptions - returns fallback on error
        """
        return detect_language(text)
    
    def is_hinglish(self, text: str) -> bool:
        """
        Check if text is Hinglish (code-mixed).
        
        Hinglish is detected when text contains both:
        - Devanagari characters (Hindi script)
        - Latin characters (English script)
        
        Args:
            text: Input text
            
        Returns:
            True if text contains both Devanagari and Latin characters
        """
        return has_devanagari(text) and has_latin(text)
    
    def get_script_ratios(self, text: str) -> dict:
        """
        Calculate the ratio of different scripts in text.
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with ratios for each script type
        """
        if not text:
            return {"devanagari": 0.0, "latin": 0.0, "other": 0.0}
        
        total_chars = len(text)
        devanagari_count = sum(1 for char in text if is_devanagari_char(char))
        latin_count = sum(1 for char in text if is_latin_char(char))
        other_count = total_chars - devanagari_count - latin_count
        
        return {
            "devanagari": devanagari_count / total_chars,
            "latin": latin_count / total_chars,
            "other": other_count / total_chars,
        }


def detect_language(text: str) -> Tuple[str, float]:
    """
    Detect language of text.
    
    Detection priority:
    1. Check for Hinglish (mixed scripts) first
    2. Use langdetect for primary detection
    3. Fallback to character-based detection if langdetect fails
    4. Default to English with low confidence on error
    
    Args:
        text: Input message
        
    Returns:
        Tuple of (language_code, confidence)
        language_code: 'en', 'hi', or 'hinglish'
        confidence: 0.0-1.0
    """
    start_time = time.time()
    
    # Validate input
    if not text or not text.strip():
        logger.debug("Empty text provided, returning default")
        return (DEFAULT_LANGUAGE, ERROR_CONFIDENCE)
    
    text = text.strip()
    
    try:
        # Step 1: Check for Hinglish (code-mixed) first
        # Hinglish contains both Devanagari and Latin characters
        has_dev = has_devanagari(text)
        has_lat = has_latin(text)
        
        if has_dev and has_lat:
            # Calculate script ratios for confidence
            ratios = _get_script_ratios(text)
            
            # Both scripts must have significant presence for Hinglish
            if ratios["devanagari"] >= HINGLISH_MIN_RATIO and ratios["latin"] >= HINGLISH_MIN_RATIO:
                confidence = min(0.95, 0.7 + (min(ratios["devanagari"], ratios["latin"]) * 2))
                _log_detection("hinglish", confidence, start_time)
                return ("hinglish", confidence)
        
        # Step 2: Use langdetect for primary detection
        detected_langs = detect_langs(text)
        
        if detected_langs:
            top_detection = detected_langs[0]
            lang_code = top_detection.lang
            confidence = top_detection.prob
            
            # Map to our supported categories
            if lang_code == "en":
                _log_detection("en", confidence, start_time)
                return ("en", confidence)
            elif lang_code == "hi":
                _log_detection("hi", confidence, start_time)
                return ("hi", confidence)
            else:
                # Unsupported language detected
                # Use character-based fallback
                return _character_based_detection(text, has_dev, has_lat, start_time)
        
        # No detection result
        return _character_based_detection(text, has_dev, has_lat, start_time)
        
    except LangDetectException as e:
        logger.debug(f"LangDetect exception: {e}")
        # Fallback to character-based detection
        return _character_based_detection(text, has_devanagari(text), has_latin(text), start_time)
        
    except Exception as e:
        logger.warning(f"Language detection error: {e}")
        _log_detection(DEFAULT_LANGUAGE, ERROR_CONFIDENCE, start_time)
        return (DEFAULT_LANGUAGE, ERROR_CONFIDENCE)


def _character_based_detection(
    text: str, 
    has_dev: bool, 
    has_lat: bool, 
    start_time: float
) -> Tuple[str, float]:
    """
    Fallback detection using character analysis.
    
    Args:
        text: Input text
        has_dev: Whether text contains Devanagari
        has_lat: Whether text contains Latin
        start_time: Detection start time for logging
        
    Returns:
        Tuple of (language_code, confidence)
    """
    if has_dev and has_lat:
        _log_detection("hinglish", 0.7, start_time)
        return ("hinglish", 0.7)
    elif has_dev:
        _log_detection("hi", 0.85, start_time)
        return ("hi", 0.85)
    elif has_lat:
        _log_detection("en", 0.75, start_time)
        return ("en", 0.75)
    else:
        # No recognizable characters
        _log_detection(DEFAULT_LANGUAGE, 0.5, start_time)
        return (DEFAULT_LANGUAGE, 0.5)


def _get_script_ratios(text: str) -> dict:
    """
    Calculate the ratio of different scripts in text.
    
    Args:
        text: Input text
        
    Returns:
        Dictionary with ratios for each script type
    """
    if not text:
        return {"devanagari": 0.0, "latin": 0.0, "other": 0.0}
    
    # Only count alphabetic characters (ignore spaces, numbers, punctuation)
    alpha_chars = [char for char in text if char.isalpha()]
    
    if not alpha_chars:
        return {"devanagari": 0.0, "latin": 0.0, "other": 0.0}
    
    total_alpha = len(alpha_chars)
    devanagari_count = sum(1 for char in alpha_chars if is_devanagari_char(char))
    latin_count = sum(1 for char in alpha_chars if is_latin_char(char))
    other_count = total_alpha - devanagari_count - latin_count
    
    return {
        "devanagari": devanagari_count / total_alpha,
        "latin": latin_count / total_alpha,
        "other": other_count / total_alpha,
    }


def _log_detection(lang: str, confidence: float, start_time: float) -> None:
    """Log detection result with timing."""
    elapsed_ms = (time.time() - start_time) * 1000
    logger.debug(f"Detected language: {lang}, confidence: {confidence:.2f}, time: {elapsed_ms:.2f}ms")


def has_devanagari(text: str) -> bool:
    """
    Check if text contains Devanagari characters.
    
    Devanagari Unicode range: U+0900 to U+097F
    
    Args:
        text: Input text
        
    Returns:
        True if text contains Devanagari Unicode characters
    """
    if not text:
        return False
    return any(is_devanagari_char(char) for char in text)


def has_latin(text: str) -> bool:
    """
    Check if text contains Latin characters.
    
    Args:
        text: Input text
        
    Returns:
        True if text contains ASCII letters (a-z, A-Z)
    """
    if not text:
        return False
    return any(is_latin_char(char) for char in text)


def is_devanagari_char(char: str) -> bool:
    """
    Check if a single character is Devanagari.
    
    Args:
        char: Single character
        
    Returns:
        True if character is in Devanagari Unicode range
    """
    return "\u0900" <= char <= "\u097F"


def is_latin_char(char: str) -> bool:
    """
    Check if a single character is Latin.
    
    Args:
        char: Single character
        
    Returns:
        True if character is ASCII letter
    """
    return "a" <= char.lower() <= "z"


def get_language_name(code: str) -> str:
    """
    Get human-readable language name from code.
    
    Args:
        code: Language code ('en', 'hi', 'hinglish')
        
    Returns:
        Human-readable language name
    """
    names = {
        "en": "English",
        "hi": "Hindi",
        "hinglish": "Hinglish (Code-Mixed)",
    }
    return names.get(code, "Unknown")

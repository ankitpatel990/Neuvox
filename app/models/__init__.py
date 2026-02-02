"""
Models Layer - ML models for scam detection, language detection, and intelligence extraction.

This module contains the core ML components:
- ScamDetector: IndicBERT-based scam classification
- LanguageDetector: Multi-language detection (English, Hindi, Hinglish)
- IntelligenceExtractor: NER and regex-based entity extraction
"""

from app.models.detector import ScamDetector, get_detector, detect_scam, reset_detector_cache
from app.models.language import detect_language, LanguageDetector
from app.models.extractor import IntelligenceExtractor, extract_intelligence

__all__ = [
    "ScamDetector",
    "get_detector",
    "detect_scam",
    "reset_detector_cache",
    "LanguageDetector",
    "detect_language",
    "IntelligenceExtractor",
    "extract_intelligence",
]

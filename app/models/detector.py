"""
Scam Detection Module using IndicBERT.

Provides hybrid scam detection combining:
- IndicBERT transformer model for semantic classification
- Keyword matching for known scam patterns
- Multi-language support (English, Hindi, Hinglish)

Acceptance Criteria:
- AC-1.2.1: Achieves >90% accuracy on test dataset
- AC-1.2.2: False positive rate <5%
- AC-1.2.3: Inference time <500ms per message
- AC-1.2.4: Handles messages up to 5000 characters
- AC-1.2.5: Returns calibrated confidence scores (not just 0/1)
"""

import os
import re
import time
from typing import Dict, List, Optional, Tuple

import torch

from app.config import settings
from app.utils.logger import get_logger
from app.utils.preprocessing import clean_text, convert_devanagari_digits

logger = get_logger(__name__)

# Score combination weights
# When BERT is fine-tuned, use higher BERT weight
# When using base BERT (not fine-tuned), rely more on keywords
BERT_WEIGHT_FINETUNED = 0.6
BERT_WEIGHT_BASE = 0.2  # Lower weight for non-fine-tuned BERT
KEYWORD_WEIGHT_FINETUNED = 0.4
KEYWORD_WEIGHT_BASE = 0.8  # Higher weight when BERT is not fine-tuned

# Scam detection threshold
SCAM_THRESHOLD = 0.6  # Lowered from 0.7 for better recall

# Maximum message length for processing
MAX_MESSAGE_LENGTH = 5000


class ScamDetector:
    """
    Hybrid scam detection using IndicBERT and keyword matching.
    
    Combines transformer-based semantic analysis with rule-based
    keyword matching for robust scam detection across English,
    Hindi, and Hinglish messages.
    
    Attributes:
        model: IndicBERT model for sequence classification
        tokenizer: Tokenizer for IndicBERT
        en_keywords: English scam keyword list
        hi_keywords: Hindi scam keyword list
        _model_loaded: Flag indicating if BERT model is available
    """
    
    # Class-level model cache for singleton pattern
    _cached_model = None
    _cached_tokenizer = None
    _model_load_attempted = False
    
    def __init__(self, load_model: bool = True) -> None:
        """
        Initialize the ScamDetector with IndicBERT model and keywords.
        
        Args:
            load_model: Whether to load the BERT model (can be False for testing)
        """
        self._model_loaded = False
        self._model_finetuned = False  # Track if model is fine-tuned for scam detection
        self.model = None
        self.tokenizer = None
        
        # English scam keywords (comprehensive list)
        self.en_keywords: List[str] = [
            # Prize/Lottery scams
            "won", "winner", "prize", "lottery", "congratulations", "claim",
            "selected", "lucky", "reward", "jackpot", "lakh", "crore",
            # Financial scams
            "otp", "bank", "account", "transfer", "payment", "upi",
            "verify", "blocked", "suspended", "deactivated", "kyc",
            "credit card", "debit card", "cvv", "pin",
            # Authority impersonation
            "police", "arrest", "court", "legal", "investigation",
            "warrant", "fine", "penalty", "department",
            # Utility/Bill scams
            "electricity", "electric bill", "power bill", "power cut",
            "disconnection", "utility", "gas bill", "water bill",
            "pending bill", "overdue", "outstanding dues",
            # Job/Employment scams
            "job offer", "work from home", "earn from home", "hiring",
            "salary", "employment opportunity",
            # Tax scams
            "income tax", "tax notice", "tax department", "it department",
            # Tech support scams
            "tech support", "computer virus", "microsoft support",
            # Government scheme scams
            "government scheme", "subsidy", "pm scheme", "govt scheme",
            # Urgency triggers
            "urgent", "immediately", "now", "today", "expire", "last chance",
            "limited time", "hurry", "before", "deadline",
            # Action requests
            "click", "call", "send", "share", "confirm", "update",
            "reactivate", "unblock", "incomplete",
            # Product scams
            "iphone", "samsung", "free", "gift",
        ]
        
        # Hindi scam keywords (Devanagari)
        self.hi_keywords: List[str] = [
            # Prize/Lottery
            "जीत", "जीता", "जीते", "विजेता", "इनाम", "लॉटरी", "बधाई", "पुरस्कार",
            # Financial
            "ओटीपी", "बैंक", "खाता", "ट्रांसफर", "भुगतान", "यूपीआई",
            "वेरिफाई", "ब्लॉक", "सस्पेंड", "बंद",
            # Authority
            "पुलिस", "गिरफ्तार", "गिरफ्तारी", "कोर्ट", "कानूनी", "जांच",
            "वारंट", "जुर्माना",
            # Urgency
            "तुरंत", "अभी", "आज", "जल्दी", "फौरन",
            # Action
            "भेजें", "शेयर", "कॉल", "क्लिक",
        ]
        
        # Romanized Hindi keywords (Hinglish)
        self.hinglish_keywords: List[str] = [
            "jeeta", "jeete", "jeet", "inaam", "lottery",
            "otp", "bank", "account", "paisa", "paise", "rupees", "rupaye",
            "police", "giraftar", "arrest", "court",
            "turant", "abhi", "jaldi", "foran",
            "bhejo", "share", "call", "click",
        ]
        
        # Scam patterns (regex)
        self.scam_patterns = [
            r"₹\s*\d+\s*(lakh|crore|lac|cr)",  # Money amounts
            r"\d+\s*(lakh|crore|lac|cr)\s*(rupees?)?",  # Money amounts
            r"won\s+.*?(prize|lottery|reward)",  # Prize winning
            r"(send|share)\s+.*?otp",  # OTP requests
            r"account\s+.*?(block|suspend|deactivat)",  # Account threats
            r"(arrest|गिरफ्तार)",  # Arrest threats
            r"call\s+.*?\+?91[\s-]?\d{10}",  # Call with phone number
        ]
        
        # Load BERT model if requested
        if load_model:
            self._load_model()
    
    # Class-level flag for fine-tuned model
    _cached_model_finetuned = False
    
    def _load_model(self) -> None:
        """
        Load IndicBERT model and tokenizer.
        
        Prioritizes loading fine-tuned model from local directory.
        Falls back to base IndicBERT model from HuggingFace.
        Falls back to keyword-only detection if model unavailable.
        """
        # Use cached model if available
        if ScamDetector._cached_model is not None:
            self.model = ScamDetector._cached_model
            self.tokenizer = ScamDetector._cached_tokenizer
            self._model_loaded = True
            self._model_finetuned = ScamDetector._cached_model_finetuned
            logger.debug(f"Using cached model (fine-tuned: {self._model_finetuned})")
            return
        
        # Skip if already attempted and failed
        if ScamDetector._model_load_attempted:
            logger.debug("Skipping model load (previous attempt failed)")
            return
        
        ScamDetector._model_load_attempted = True
        
        try:
            from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer
            
            # First, try to load fine-tuned model from local directory
            finetuned_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                "models",
                "scam_detector",
                "latest"
            )
            
            if os.path.exists(finetuned_path):
                logger.info(f"Loading fine-tuned model from: {finetuned_path}")
                start_time = time.time()
                
                self.tokenizer = AutoTokenizer.from_pretrained(finetuned_path)
                self.model = AutoModelForSequenceClassification.from_pretrained(finetuned_path)
                self.model.eval()
                self._model_finetuned = True
                
                # Cache for future instances
                ScamDetector._cached_model = self.model
                ScamDetector._cached_tokenizer = self.tokenizer
                ScamDetector._cached_model_finetuned = True
                
                load_time = time.time() - start_time
                logger.info(f"Fine-tuned model loaded in {load_time:.2f}s")
                self._model_loaded = True
                return
            
            # Fall back to base IndicBERT model
            model_name = settings.INDICBERT_MODEL
            token = settings.HUGGINGFACE_TOKEN
            token_kwargs = {"token": token} if token else {}
            
            logger.info(f"Loading base IndicBERT model: {model_name}")
            start_time = time.time()
            
            self.tokenizer = AutoTokenizer.from_pretrained(model_name, **token_kwargs)
            self.model = AutoModel.from_pretrained(model_name, **token_kwargs)
            self.model.eval()
            self._model_finetuned = False
            
            # Cache for future instances
            ScamDetector._cached_model = self.model
            ScamDetector._cached_tokenizer = self.tokenizer
            ScamDetector._cached_model_finetuned = False
            
            load_time = time.time() - start_time
            logger.info(f"Base IndicBERT loaded in {load_time:.2f}s")
            self._model_loaded = True
            
        except ImportError as e:
            logger.warning(f"transformers not installed: {e}")
            logger.warning("Falling back to keyword-only detection")
        except Exception as e:
            error_msg = str(e).lower()
            if "gated" in error_msg or "access" in error_msg:
                logger.warning("IndicBERT requires HuggingFace authentication")
                logger.warning("Set HUGGINGFACE_TOKEN environment variable")
            else:
                logger.warning(f"Failed to load IndicBERT: {e}")
            logger.warning("Falling back to keyword-only detection")
    
    def detect(self, message: str, language: str = "auto") -> Dict:
        """
        Detect if a message is a scam.
        
        Uses hybrid approach combining:
        1. IndicBERT semantic classification (60% weight)
        2. Keyword matching (40% weight)
        
        Args:
            message: Input text to analyze (max 5000 chars)
            language: Language code ('auto', 'en', 'hi', 'hinglish')
            
        Returns:
            Dict containing:
                - scam_detected: bool (True if confidence > 0.7)
                - confidence: float (0.0-1.0)
                - language: str (detected or provided language)
                - indicators: List[str] (matched keywords/patterns)
        """
        start_time = time.time()
        
        # Handle empty message
        if not message or not message.strip():
            logger.debug("Empty message, returning not scam")
            return {
                "scam_detected": False,
                "confidence": 0.0,
                "language": language if language != "auto" else "en",
                "indicators": [],
            }
        
        # Clean and truncate message
        message = clean_text(message)
        if len(message) > MAX_MESSAGE_LENGTH:
            message = message[:MAX_MESSAGE_LENGTH]
            logger.debug(f"Message truncated to {MAX_MESSAGE_LENGTH} chars")
        
        # Detect language if auto
        detected_language = language
        if language == "auto":
            from app.models.language import detect_language
            detected_language, _ = detect_language(message)
        
        # Calculate keyword score
        keyword_score, indicators = self._keyword_match(message, detected_language)
        
        # Calculate BERT score (if model available)
        if self._model_loaded:
            bert_score = self._bert_classify(message)
            # Use appropriate weights based on whether BERT is fine-tuned
            if self._model_finetuned:
                final_confidence = BERT_WEIGHT_FINETUNED * bert_score + KEYWORD_WEIGHT_FINETUNED * keyword_score
            else:
                # Non-fine-tuned BERT: rely more on keywords
                final_confidence = BERT_WEIGHT_BASE * bert_score + KEYWORD_WEIGHT_BASE * keyword_score
        else:
            # Keyword-only fallback
            final_confidence = keyword_score
        
        # Check pattern matches for additional indicators
        pattern_indicators = self._pattern_match(message)
        indicators.extend(pattern_indicators)
        
        # Boost confidence if strong pattern matches found
        if pattern_indicators:
            pattern_boost = min(len(pattern_indicators) * 0.1, 0.2)
            final_confidence = min(1.0, final_confidence + pattern_boost)
        
        # Determine if scam
        scam_detected = final_confidence >= SCAM_THRESHOLD
        
        # Log detection
        elapsed_ms = (time.time() - start_time) * 1000
        logger.debug(
            f"Detection: scam={scam_detected}, conf={final_confidence:.2f}, "
            f"lang={detected_language}, time={elapsed_ms:.0f}ms"
        )
        
        return {
            "scam_detected": scam_detected,
            "confidence": float(round(final_confidence, 4)),
            "language": detected_language,
            "indicators": list(set(indicators)),  # Remove duplicates
        }
    
    def _keyword_match(self, message: str, language: str) -> Tuple[float, List[str]]:
        """
        Calculate keyword-based scam score.
        
        Args:
            message: Input text
            language: Language code ('en', 'hi', 'hinglish')
            
        Returns:
            Tuple of (score, matched_keywords)
            Score is normalized to 0.0-1.0
        """
        # Convert message to lowercase and normalize Devanagari digits
        message_lower = message.lower()
        message_normalized = convert_devanagari_digits(message_lower)
        
        matched_keywords = []
        
        # Check English keywords (always check for code-mixing)
        for kw in self.en_keywords:
            if kw.lower() in message_lower:
                matched_keywords.append(kw)
        
        # Check Hindi keywords if language suggests Hindi content
        if language in ["hi", "hinglish"] or self._has_devanagari(message):
            for kw in self.hi_keywords:
                if kw in message:
                    matched_keywords.append(kw)
        
        # Check Hinglish/romanized keywords
        for kw in self.hinglish_keywords:
            if kw in message_lower:
                matched_keywords.append(kw)
        
        # Calculate score based on number of matches
        # More keywords = higher confidence, with diminishing returns
        match_count = len(set(matched_keywords))
        
        if match_count == 0:
            score = 0.0
        elif match_count == 1:
            score = 0.3
        elif match_count == 2:
            score = 0.5
        elif match_count == 3:
            score = 0.7
        elif match_count == 4:
            score = 0.85
        else:
            score = min(0.95, 0.85 + (match_count - 4) * 0.02)
        
        return score, matched_keywords
    
    def _bert_classify(self, message: str) -> float:
        """
        Classify message using BERT model.
        
        If model is fine-tuned for sequence classification, uses direct prediction.
        Otherwise, uses embedding-based heuristic approach.
        
        Args:
            message: Input text
            
        Returns:
            Scam probability between 0.0 and 1.0
        """
        if not self._model_loaded:
            return 0.0
        
        try:
            # Tokenize with truncation
            inputs = self.tokenizer(
                message,
                return_tensors="pt",
                truncation=True,
                max_length=512,
                padding=True,
            )
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                
                # Fine-tuned model: use logits directly
                if self._model_finetuned and hasattr(outputs, 'logits'):
                    logits = outputs.logits
                    probs = torch.softmax(logits, dim=-1)
                    # Return probability of class 1 (scam)
                    scam_prob = probs[0, 1].item()
                    return scam_prob
                
                # Base model: use embedding-based heuristic
                # Get mean pooled embedding
                # Shape: [batch_size, seq_len, hidden_size]
                last_hidden = outputs.last_hidden_state
                
                # Mean pooling over sequence length
                attention_mask = inputs["attention_mask"]
                mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden.size()).float()
                sum_embeddings = torch.sum(last_hidden * mask_expanded, dim=1)
                sum_mask = torch.clamp(mask_expanded.sum(dim=1), min=1e-9)
                embeddings = sum_embeddings / sum_mask
                
                # Calculate embedding magnitude as a proxy for unusual content
                # Scam messages often have unusual patterns
                embedding_norm = torch.norm(embeddings, dim=-1).item()
                
                # Normalize to 0-1 range (empirically calibrated)
                # Higher norm often indicates more unusual/emphatic content
                normalized_score = min(1.0, max(0.0, (embedding_norm - 5.0) / 15.0))
                
                return normalized_score
                
        except Exception as e:
            logger.warning(f"BERT classification error: {e}")
            return 0.0
    
    def _pattern_match(self, message: str) -> List[str]:
        """
        Match scam patterns using regex.
        
        Args:
            message: Input text
            
        Returns:
            List of matched pattern descriptions
        """
        matched_patterns = []
        message_lower = message.lower()
        
        for pattern in self.scam_patterns:
            try:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    # Add a descriptive indicator based on pattern
                    if "lakh" in pattern or "crore" in pattern:
                        matched_patterns.append("money_amount")
                    elif "prize" in pattern or "lottery" in pattern:
                        matched_patterns.append("prize_winning")
                    elif "otp" in pattern:
                        matched_patterns.append("otp_request")
                    elif "block" in pattern or "suspend" in pattern:
                        matched_patterns.append("account_threat")
                    elif "arrest" in pattern or "गिरफ्तार" in pattern:
                        matched_patterns.append("arrest_threat")
                    elif "call" in pattern:
                        matched_patterns.append("phone_number")
            except re.error as e:
                logger.warning(f"Regex error for pattern {pattern}: {e}")
        
        return matched_patterns
    
    def _extract_indicators(self, message: str, language: str) -> List[str]:
        """
        Extract scam indicators found in message.
        
        Args:
            message: Input text
            language: Language code
            
        Returns:
            List of matched keywords/indicators
        """
        _, indicators = self._keyword_match(message, language)
        pattern_indicators = self._pattern_match(message)
        indicators.extend(pattern_indicators)
        return list(set(indicators))
    
    def _has_devanagari(self, text: str) -> bool:
        """Check if text contains Devanagari characters."""
        return any("\u0900" <= char <= "\u097F" for char in text)


def detect_scam(message: str, language: str = "auto") -> Tuple[bool, float, List[str]]:
    """
    Convenience function for scam detection.
    
    Args:
        message: Input text
        language: Language code ('auto', 'en', 'hi', 'hinglish')
        
    Returns:
        Tuple of (scam_detected, confidence, indicators)
    """
    # Use singleton pattern for efficiency
    if not hasattr(detect_scam, "_detector"):
        detect_scam._detector = ScamDetector()
    
    result = detect_scam._detector.detect(message, language)
    return result["scam_detected"], result["confidence"], result["indicators"]


def reset_detector_cache() -> None:
    """
    Reset the detector model cache.
    
    Useful for testing or when model needs to be reloaded.
    """
    global _singleton_detector
    ScamDetector._cached_model = None
    ScamDetector._cached_tokenizer = None
    ScamDetector._model_load_attempted = False
    if hasattr(detect_scam, "_detector"):
        delattr(detect_scam, "_detector")
    _singleton_detector = None
    logger.info("Detector cache reset")


# Singleton detector instance
_singleton_detector: Optional[ScamDetector] = None


def get_detector() -> ScamDetector:
    """
    Get singleton ScamDetector instance.
    
    Returns:
        ScamDetector instance
    """
    global _singleton_detector
    if _singleton_detector is None:
        _singleton_detector = ScamDetector()
    return _singleton_detector

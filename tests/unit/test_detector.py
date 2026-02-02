"""
Unit Tests for Scam Detection Module.

Tests the ScamDetector class and detection functions.

Acceptance Criteria:
- AC-1.2.1: Achieves >90% accuracy on test dataset
- AC-1.2.2: False positive rate <5%
- AC-1.2.3: Inference time <500ms per message
- AC-1.2.4: Handles messages up to 5000 characters
- AC-1.2.5: Returns calibrated confidence scores (not just 0/1)
"""

import time
import pytest
from app.models.detector import (
    ScamDetector,
    detect_scam,
    reset_detector_cache,
    SCAM_THRESHOLD,
)


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset detector cache before each test."""
    reset_detector_cache()
    yield
    reset_detector_cache()


class TestScamDetector:
    """Tests for ScamDetector class."""
    
    def test_detector_initialization(self):
        """Test ScamDetector initializes without errors."""
        detector = ScamDetector(load_model=False)
        assert detector is not None
        assert isinstance(detector.en_keywords, list)
        assert isinstance(detector.hi_keywords, list)
        assert len(detector.en_keywords) > 0
        assert len(detector.hi_keywords) > 0
    
    def test_detector_initialization_with_model(self):
        """Test ScamDetector initializes with model loading."""
        detector = ScamDetector(load_model=True)
        assert detector is not None
        # Model may or may not be loaded depending on environment
    
    def test_detect_returns_expected_format(self, sample_scam_message):
        """Test detect method returns expected dictionary format."""
        detector = ScamDetector(load_model=False)
        result = detector.detect(sample_scam_message)
        
        assert isinstance(result, dict)
        assert "scam_detected" in result
        assert "confidence" in result
        assert "language" in result
        assert "indicators" in result
        
        assert isinstance(result["scam_detected"], bool)
        assert isinstance(result["confidence"], float)
        assert isinstance(result["language"], str)
        assert isinstance(result["indicators"], list)
    
    def test_detect_confidence_range(self, sample_scam_message):
        """Test confidence score is within valid range (AC-1.2.5)."""
        detector = ScamDetector(load_model=False)
        result = detector.detect(sample_scam_message)
        
        assert 0.0 <= result["confidence"] <= 1.0
    
    def test_detect_with_language_parameter(self, sample_scam_message):
        """Test detect respects language parameter."""
        detector = ScamDetector(load_model=False)
        
        result_auto = detector.detect(sample_scam_message, language="auto")
        result_en = detector.detect(sample_scam_message, language="en")
        result_hi = detector.detect(sample_scam_message, language="hi")
        
        assert result_auto["language"] in ["en", "hi", "hinglish"]
        assert result_en["language"] == "en"
        assert result_hi["language"] == "hi"
    
    def test_detect_empty_message(self):
        """Test detect handles empty message gracefully."""
        detector = ScamDetector(load_model=False)
        result = detector.detect("")
        
        assert isinstance(result, dict)
        assert result["scam_detected"] is False
        assert result["confidence"] == 0.0
    
    def test_detect_whitespace_message(self):
        """Test detect handles whitespace-only message."""
        detector = ScamDetector(load_model=False)
        result = detector.detect("   \n\t  ")
        
        assert result["scam_detected"] is False
        assert result["confidence"] == 0.0
    
    def test_detect_scam_english(self):
        """Test detection of English scam message."""
        detector = ScamDetector(load_model=False)
        result = detector.detect("You won 10 lakh! Send OTP now!")
        
        assert result["scam_detected"] is True
        assert result["confidence"] >= SCAM_THRESHOLD
        assert len(result["indicators"]) > 0
    
    def test_detect_scam_hindi(self):
        """Test detection of Hindi scam message."""
        detector = ScamDetector(load_model=False)
        result = detector.detect("आप जीत गए हैं 10 लाख रुपये! अपना OTP भेजें।")
        
        assert result["scam_detected"] is True
        assert result["confidence"] >= SCAM_THRESHOLD
    
    def test_detect_legitimate_message(self):
        """Test detection of legitimate message."""
        detector = ScamDetector(load_model=False)
        result = detector.detect("Hi, how are you? Let's meet for coffee tomorrow.")
        
        assert result["scam_detected"] is False
        assert result["confidence"] < SCAM_THRESHOLD
    
    def test_detect_legitimate_hindi(self):
        """Test detection of legitimate Hindi message."""
        detector = ScamDetector(load_model=False)
        result = detector.detect("नमस्ते, कैसे हो आप? कल मिलते हैं।")
        
        assert result["scam_detected"] is False
        assert result["confidence"] < SCAM_THRESHOLD


class TestScamDetectorAccuracy:
    """Tests for accuracy requirements (AC-1.2.1, AC-1.2.2)."""
    
    # Scam test cases
    SCAM_MESSAGES = [
        # English scams
        "Congratulations! You won ₹10 lakh. Share OTP to claim.",
        "Your account will be suspended. Send money to unblock.",
        "You have won a lottery prize of 5 crore rupees!",
        "This is police. You are under arrest. Pay fine immediately.",
        "Your bank account is blocked. Verify by sending OTP.",
        "Urgent! Claim your prize now before it expires.",
        "Send ₹500 to this UPI to win ₹50000.",
        "Your credit card is suspended. Call now to reactivate.",
        # Hindi scams
        "आप गिरफ्तार हो जाएंगे। तुरंत UPI पर पैसे भेजें।",
        "आपने लॉटरी जीती है! इनाम लेने के लिए OTP भेजें।",
        "आपका खाता ब्लॉक हो जाएगा। तुरंत वेरिफाई करें।",
        "पुलिस यहाँ है। जुर्माना भरो या गिरफ्तार हो जाओगे।",
        # Hinglish scams
        "Aapne jeeta hai 10 lakh! OTP share karo jaldi.",
        "Bank account block ho jayega. Turant call karo.",
    ]
    
    # Legitimate test cases
    LEGITIMATE_MESSAGES = [
        "Hi, how are you? Let's meet for coffee tomorrow.",
        "Your order #12345 has been shipped.",
        "Reminder: Your dentist appointment is tomorrow at 3 PM.",
        "Thanks for your payment. Receipt attached.",
        "Happy birthday! Have a great day.",
        "Meeting rescheduled to next Monday at 10 AM.",
        "The weather is nice today.",
        "Can you please send me the document?",
        "नमस्ते! कैसे हो? कल मिलते हैं।",
        "आपका ऑर्डर डिलीवर हो गया है।",
        "Thank you for your feedback.",
        "See you at the party tonight!",
    ]
    
    def test_scam_detection_accuracy(self):
        """Test scam detection accuracy (AC-1.2.1: >90%)."""
        detector = ScamDetector(load_model=False)
        
        correct = 0
        for msg in self.SCAM_MESSAGES:
            result = detector.detect(msg)
            if result["scam_detected"]:
                correct += 1
        
        accuracy = correct / len(self.SCAM_MESSAGES)
        assert accuracy >= 0.90, f"Scam accuracy {accuracy:.0%} is below 90%"
    
    def test_legitimate_detection_accuracy(self):
        """Test legitimate message detection (false positive rate AC-1.2.2: <5%)."""
        detector = ScamDetector(load_model=False)
        
        false_positives = 0
        for msg in self.LEGITIMATE_MESSAGES:
            result = detector.detect(msg)
            if result["scam_detected"]:
                false_positives += 1
        
        fp_rate = false_positives / len(self.LEGITIMATE_MESSAGES)
        assert fp_rate < 0.05, f"False positive rate {fp_rate:.0%} exceeds 5%"
    
    def test_confidence_is_calibrated(self):
        """Test confidence scores are calibrated (AC-1.2.5)."""
        detector = ScamDetector(load_model=False)
        
        # High confidence scam
        result1 = detector.detect("You won 10 lakh! Send OTP now to claim prize immediately!")
        assert result1["confidence"] > 0.8, "High-signal scam should have high confidence"
        
        # Low confidence (legitimate)
        result2 = detector.detect("Hi, how are you?")
        assert result2["confidence"] < 0.3, "Legitimate message should have low confidence"
        
        # Check that we don't just return 0 or 1
        confidences = set()
        for msg in self.SCAM_MESSAGES + self.LEGITIMATE_MESSAGES:
            result = detector.detect(msg)
            confidences.add(round(result["confidence"], 2))
        
        assert len(confidences) > 2, "Confidence scores should be varied, not just 0/1"


class TestScamDetectorPerformance:
    """Tests for performance requirements (AC-1.2.3, AC-1.2.4)."""
    
    def test_inference_time(self):
        """Test inference time is within limit (AC-1.2.3: <500ms)."""
        detector = ScamDetector(load_model=False)
        message = "You won 10 lakh rupees! Send OTP to claim your prize immediately."
        
        start_time = time.time()
        detector.detect(message)
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert elapsed_ms < 500, f"Inference took {elapsed_ms:.0f}ms, exceeds 500ms limit"
    
    def test_inference_time_hindi(self):
        """Test Hindi inference time."""
        detector = ScamDetector(load_model=False)
        message = "आप जीत गए हैं 10 लाख रुपये! अपना OTP भेजें।"
        
        start_time = time.time()
        detector.detect(message)
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert elapsed_ms < 500, f"Hindi inference took {elapsed_ms:.0f}ms"
    
    def test_long_message_handling(self):
        """Test handling of long messages (AC-1.2.4: up to 5000 chars)."""
        detector = ScamDetector(load_model=False)
        
        # Create a 5000 character message
        long_message = "You won a prize! Send OTP. " * 200  # ~5400 chars
        assert len(long_message) > 5000
        
        start_time = time.time()
        result = detector.detect(long_message)
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert isinstance(result, dict)
        assert result["scam_detected"] is True
        assert elapsed_ms < 500, f"Long message inference took {elapsed_ms:.0f}ms"
    
    def test_very_long_message_truncation(self):
        """Test that very long messages are truncated."""
        detector = ScamDetector(load_model=False)
        
        # Create a 10000 character message
        very_long_message = "x" * 10000
        
        result = detector.detect(very_long_message)
        
        # Should complete without error
        assert isinstance(result, dict)


class TestKeywordMatching:
    """Tests for keyword matching functionality."""
    
    def test_english_keyword_detection(self):
        """Test English keyword detection."""
        detector = ScamDetector(load_model=False)
        
        result = detector.detect("You won a lottery prize!", language="en")
        
        assert "won" in result["indicators"] or "lottery" in result["indicators"] or "prize" in result["indicators"]
    
    def test_hindi_keyword_detection(self):
        """Test Hindi keyword detection."""
        detector = ScamDetector(load_model=False)
        
        result = detector.detect("आप जीत गए हैं! इनाम लें!", language="hi")
        
        # Should detect Hindi keywords
        assert len(result["indicators"]) > 0
    
    def test_hinglish_keyword_detection(self):
        """Test Hinglish keyword detection."""
        detector = ScamDetector(load_model=False)
        
        result = detector.detect("Aapne jeeta hai lottery! Paisa bhejo.", language="hinglish")
        
        assert len(result["indicators"]) > 0
    
    def test_case_insensitive_matching(self):
        """Test keywords are matched case-insensitively."""
        detector = ScamDetector(load_model=False)
        
        result1 = detector.detect("YOU WON A PRIZE!")
        result2 = detector.detect("you won a prize!")
        result3 = detector.detect("You Won A Prize!")
        
        # All should have similar detection
        assert result1["scam_detected"] == result2["scam_detected"] == result3["scam_detected"]


class TestPatternMatching:
    """Tests for regex pattern matching."""
    
    def test_money_amount_detection(self):
        """Test money amount pattern detection."""
        detector = ScamDetector(load_model=False)
        
        result = detector.detect("Win ₹10 lakh today!")
        
        assert "money_amount" in result["indicators"]
    
    def test_otp_request_detection(self):
        """Test OTP request pattern detection."""
        detector = ScamDetector(load_model=False)
        
        result = detector.detect("Please send your OTP to verify")
        
        assert "otp_request" in result["indicators"]
    
    def test_account_threat_detection(self):
        """Test account threat pattern detection."""
        detector = ScamDetector(load_model=False)
        
        result = detector.detect("Your account will be blocked immediately")
        
        assert "account_threat" in result["indicators"]


class TestDetectScamFunction:
    """Tests for convenience detect_scam function."""
    
    def test_function_returns_tuple(self, sample_scam_message):
        """Test detect_scam returns expected tuple format."""
        scam_detected, confidence, indicators = detect_scam(sample_scam_message)
        
        assert isinstance(scam_detected, bool)
        assert isinstance(confidence, float)
        assert isinstance(indicators, list)
    
    def test_function_with_language(self, sample_scam_message):
        """Test detect_scam with explicit language."""
        scam_detected, confidence, indicators = detect_scam(
            sample_scam_message,
            language="en",
        )
        
        assert isinstance(scam_detected, bool)
        assert 0.0 <= confidence <= 1.0
    
    def test_function_singleton_pattern(self):
        """Test detect_scam uses singleton detector."""
        # First call creates detector
        detect_scam("Test message 1")
        
        # Second call should reuse
        detect_scam("Test message 2")
        
        # Should have the _detector attribute
        assert hasattr(detect_scam, "_detector")


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_unicode_handling(self):
        """Test handling of Unicode characters."""
        detector = ScamDetector(load_model=False)
        
        result = detector.detect("You won ₹10 lakh! 🎉🎊")
        
        assert isinstance(result, dict)
    
    def test_special_characters(self):
        """Test handling of special characters."""
        detector = ScamDetector(load_model=False)
        
        result = detector.detect("!@#$%^&*()_+-=[]{}|;':\",./<>?")
        
        assert result["scam_detected"] is False
    
    def test_mixed_language(self):
        """Test handling of mixed language content."""
        detector = ScamDetector(load_model=False)
        
        result = detector.detect("You won! आप जीत गए! Claim now!")
        
        assert result["scam_detected"] is True
    
    def test_devanagari_digits(self):
        """Test handling of Devanagari digits."""
        detector = ScamDetector(load_model=False)
        
        # Message with Devanagari digits and scam keywords
        result = detector.detect("आपने जीता ₹१० लाख! तुरंत OTP भेजें!")
        
        # Should detect as scam
        assert result["scam_detected"] is True
    
    def test_url_in_message(self):
        """Test handling of URLs in message."""
        detector = ScamDetector(load_model=False)
        
        result = detector.detect("Click http://fake-bank.com to verify your account blocked")
        
        assert result["scam_detected"] is True


class TestIndicatorExtraction:
    """Tests for indicator extraction."""
    
    def test_multiple_indicators(self):
        """Test extraction of multiple indicators."""
        detector = ScamDetector(load_model=False)
        
        result = detector.detect(
            "Congratulations! You won ₹10 lakh lottery prize! "
            "Send OTP immediately to claim before account is blocked!"
        )
        
        assert len(result["indicators"]) >= 3
    
    def test_no_duplicate_indicators(self):
        """Test indicators don't have duplicates."""
        detector = ScamDetector(load_model=False)
        
        result = detector.detect("Won prize won prize won lottery lottery")
        
        # Indicators should be unique
        assert len(result["indicators"]) == len(set(result["indicators"]))
    
    def test_indicators_match_language(self):
        """Test Hindi indicators are extracted for Hindi messages."""
        detector = ScamDetector(load_model=False)
        
        result = detector.detect("आप जीत गए! इनाम लें! बैंक में भेजें!", language="hi")
        
        # Should have some indicators
        assert len(result["indicators"]) > 0

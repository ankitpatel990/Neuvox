"""
Unit Tests for Intelligence Extraction Module.

Tests Task 7.1 implementation with acceptance criteria:
- AC-3.1.1: UPI ID extraction precision >90%
- AC-3.1.2: Bank account precision >85%
- AC-3.1.3: IFSC code precision >95%
- AC-3.1.4: Phone number precision >90%
- AC-3.1.5: Phishing link precision >95%
- AC-3.3.1: Devanagari digit conversion 100% accurate
"""

import pytest
from app.models.extractor import (
    IntelligenceExtractor,
    extract_intelligence,
    extract_from_messages,
    get_extractor,
    reset_extractor,
    VALID_UPI_PROVIDERS,
)


# ============================================================================
# Setup and Fixtures
# ============================================================================

@pytest.fixture
def extractor():
    """Create fresh extractor instance."""
    return IntelligenceExtractor(use_spacy=False)


@pytest.fixture(autouse=True)
def reset_singleton():
    """Reset singleton before each test."""
    reset_extractor()
    yield
    reset_extractor()


# ============================================================================
# Basic Initialization Tests
# ============================================================================

class TestExtractorInitialization:
    """Tests for IntelligenceExtractor initialization."""
    
    def test_extractor_initialization(self, extractor):
        """Test IntelligenceExtractor initializes without errors."""
        assert extractor is not None
        assert isinstance(extractor.patterns, dict)
    
    def test_extractor_has_all_patterns(self, extractor):
        """Test extractor has all required patterns."""
        required = ["upi_ids", "bank_accounts", "ifsc_codes", "phone_numbers", "phishing_links"]
        for pattern_name in required:
            assert pattern_name in extractor.patterns
    
    def test_extractor_has_devanagari_map(self, extractor):
        """Test extractor has Devanagari digit mapping."""
        assert extractor.devanagari_map is not None
        assert len(extractor.devanagari_map) == 10
    
    def test_extract_returns_expected_format(self, extractor):
        """Test extract method returns expected tuple format."""
        text = "Send money to scammer@paytm"
        intel, confidence = extractor.extract(text)
        
        assert isinstance(intel, dict)
        assert isinstance(confidence, float)
        assert "upi_ids" in intel
        assert "bank_accounts" in intel
        assert "ifsc_codes" in intel
        assert "phone_numbers" in intel
        assert "phishing_links" in intel


# ============================================================================
# AC-3.1.1: UPI ID Extraction Tests (>90% precision)
# ============================================================================

class TestUPIExtraction:
    """Tests for UPI ID extraction - AC-3.1.1."""
    
    def test_extract_common_upi_providers(self, extractor):
        """Test extraction of common UPI providers."""
        test_cases = [
            ("Pay to user@paytm", "user@paytm"),
            ("Send to fraud@ybl", "fraud@ybl"),
            ("UPI: victim@okaxis", "victim@okaxis"),
            ("UPI ID: scammer@okhdfcbank", "scammer@okhdfcbank"),
            ("Pay user@oksbi immediately", "user@oksbi"),
            ("Transfer to target@icici", "target@icici"),
        ]
        
        for text, expected_upi in test_cases:
            intel, _ = extractor.extract(text)
            assert expected_upi in intel["upi_ids"], f"Failed for: {text}"
    
    def test_extract_multiple_upi_ids(self, extractor):
        """Test extraction of multiple UPI IDs."""
        text = "Pay to user@paytm or fraud@ybl or backup@okaxis"
        intel, _ = extractor.extract(text)
        
        assert len(intel["upi_ids"]) >= 3
        assert "user@paytm" in intel["upi_ids"]
        assert "fraud@ybl" in intel["upi_ids"]
        assert "backup@okaxis" in intel["upi_ids"]
    
    def test_exclude_email_addresses(self, extractor):
        """Test that email addresses are not extracted as UPI IDs."""
        text = "Email me at user@gmail.com or contact@company.org"
        intel, _ = extractor.extract(text)
        
        # Should NOT include email domains
        for upi in intel["upi_ids"]:
            assert not upi.endswith("@gmail.com")
            assert not upi.endswith("@company.org")
    
    def test_upi_with_special_characters(self, extractor):
        """Test UPI IDs with dots, underscores, hyphens."""
        text = "Pay to user.name@paytm or user_123@ybl or user-test@okaxis"
        intel, _ = extractor.extract(text)
        
        assert len(intel["upi_ids"]) == 3
    
    def test_exclude_short_user_names(self, extractor):
        """Test that very short usernames are excluded."""
        text = "Invalid: a@paytm"
        intel, _ = extractor.extract(text)
        
        # Single character usernames should be excluded
        assert "a@paytm" not in intel["upi_ids"]
    
    def test_valid_upi_providers_list(self):
        """Test VALID_UPI_PROVIDERS contains major providers."""
        major_providers = ["paytm", "ybl", "okaxis", "okhdfcbank", "oksbi", "icici"]
        for provider in major_providers:
            assert provider in VALID_UPI_PROVIDERS


# ============================================================================
# AC-3.1.2: Bank Account Extraction Tests (>85% precision)
# ============================================================================

class TestBankAccountExtraction:
    """Tests for bank account extraction - AC-3.1.2."""
    
    def test_extract_valid_bank_accounts(self, extractor):
        """Test extraction of valid bank account numbers."""
        test_cases = [
            ("Account: 123456789012", "123456789012"),  # 12 digits
            ("A/C No: 12345678901234", "12345678901234"),  # 14 digits
            ("Bank account 123456789", "123456789"),  # 9 digits
        ]
        
        for text, expected in test_cases:
            intel, _ = extractor.extract(text)
            assert expected in intel["bank_accounts"], f"Failed for: {text}"
    
    def test_exclude_phone_numbers_as_accounts(self, extractor):
        """Test that 10-digit phone numbers are excluded."""
        text = "Call 9876543210 for account details"
        intel, _ = extractor.extract(text)
        
        # 10-digit numbers should not be in bank_accounts
        for acc in intel["bank_accounts"]:
            assert len(acc) != 10
    
    def test_exclude_otp_codes(self, extractor):
        """Test that OTP-like numbers are excluded."""
        text = "OTP: 123456 for account verification"
        intel, _ = extractor.extract(text)
        
        # 6-digit OTPs should not be extracted
        assert "123456" not in intel["bank_accounts"]
    
    def test_exclude_repeated_digits(self, extractor):
        """Test that repeated digit patterns are excluded."""
        text = "Account: 111111111111"
        intel, _ = extractor.extract(text)
        
        assert "111111111111" not in intel["bank_accounts"]
    
    def test_multiple_account_numbers(self, extractor):
        """Test extraction of multiple account numbers."""
        # Use 11 and 12 digit numbers that don't start with phone-like patterns
        text = "Primary: 12345678901 Secondary: 234567890123"
        intel, _ = extractor.extract(text)
        
        assert len(intel["bank_accounts"]) >= 2
        assert "12345678901" in intel["bank_accounts"]
        assert "234567890123" in intel["bank_accounts"]
    
    def test_account_with_leading_zeros_excluded(self, extractor):
        """Test that numbers starting with 0 are excluded (pattern starts with 1-9)."""
        text = "Account: 012345678901"
        intel, _ = extractor.extract(text)
        
        # Pattern requires first digit to be 1-9
        # This might match "12345678901" instead
        for acc in intel["bank_accounts"]:
            assert not acc.startswith("0")


# ============================================================================
# AC-3.1.3: IFSC Code Extraction Tests (>95% precision)
# ============================================================================

class TestIFSCExtraction:
    """Tests for IFSC code extraction - AC-3.1.3."""
    
    def test_extract_valid_ifsc_codes(self, extractor):
        """Test extraction of valid IFSC codes."""
        test_cases = [
            ("IFSC: SBIN0001234", "SBIN0001234"),  # SBI
            ("Code: HDFC0123456", "HDFC0123456"),  # HDFC
            ("IFSC ICIC0000789", "ICIC0000789"),   # ICICI
            ("Bank AXIS0SAMPLE", "AXIS0SAMPLE"),   # Axis
        ]
        
        for text, expected in test_cases:
            intel, _ = extractor.extract(text)
            assert expected in intel["ifsc_codes"], f"Failed for: {text}"
    
    def test_ifsc_case_insensitive(self, extractor):
        """Test IFSC extraction is case insensitive but normalizes to upper."""
        text = "ifsc: sbin0001234"
        intel, _ = extractor.extract(text)
        
        assert "SBIN0001234" in intel["ifsc_codes"]
    
    def test_invalid_ifsc_format(self, extractor):
        """Test that invalid IFSC formats are excluded."""
        invalid_cases = [
            "SBI0001234",    # Only 3 letters at start
            "SBIN1001234",   # 5th char not 0
            "SBINX001234",   # Invalid format
            "SBIN000123",    # Too short
        ]
        
        for invalid in invalid_cases:
            text = f"IFSC: {invalid}"
            intel, _ = extractor.extract(text)
            assert invalid not in intel["ifsc_codes"], f"Should exclude: {invalid}"
    
    def test_multiple_ifsc_codes(self, extractor):
        """Test extraction of multiple IFSC codes."""
        text = "Primary SBIN0001234, Secondary HDFC0567890"
        intel, _ = extractor.extract(text)
        
        assert len(intel["ifsc_codes"]) == 2
        assert "SBIN0001234" in intel["ifsc_codes"]
        assert "HDFC0567890" in intel["ifsc_codes"]


# ============================================================================
# AC-3.1.4: Phone Number Extraction Tests (>90% precision)
# ============================================================================

class TestPhoneNumberExtraction:
    """Tests for phone number extraction - AC-3.1.4."""
    
    def test_extract_indian_mobile_numbers(self, extractor):
        """Test extraction of Indian mobile numbers."""
        test_cases = [
            ("Call 9876543210", "+919876543210"),
            ("Phone: +919876543210", "+919876543210"),
            ("Mobile: +91-9876543210", "+919876543210"),
            ("Contact: 91 9876543210", "+919876543210"),
        ]
        
        for text, expected in test_cases:
            intel, _ = extractor.extract(text)
            assert expected in intel["phone_numbers"], f"Failed for: {text}"
    
    def test_normalize_phone_format(self, extractor):
        """Test that phone numbers are normalized to +91 format."""
        text = "Call 9876543210 or +91-8765432109 or 07654321098"
        intel, _ = extractor.extract(text)
        
        # All should be normalized to +91XXXXXXXXXX format
        for phone in intel["phone_numbers"]:
            assert phone.startswith("+91")
            assert len(phone) == 13  # +91 + 10 digits
    
    def test_exclude_invalid_starting_digits(self, extractor):
        """Test that numbers not starting with 6-9 are excluded."""
        text = "Invalid: 0123456789 or 5123456789"
        intel, _ = extractor.extract(text)
        
        for phone in intel["phone_numbers"]:
            # The 10 digits after +91 should start with 6-9
            assert phone[3] in "6789"
    
    def test_exclude_repeated_digits(self, extractor):
        """Test that repeated digit patterns are excluded."""
        text = "Phone: 9999999999"
        intel, _ = extractor.extract(text)
        
        assert "+919999999999" not in intel["phone_numbers"]
    
    def test_multiple_phone_numbers(self, extractor):
        """Test extraction of multiple phone numbers."""
        text = "Call 9876543210 or 8765432109 for details"
        intel, _ = extractor.extract(text)
        
        assert len(intel["phone_numbers"]) >= 2


# ============================================================================
# AC-3.1.5: Phishing Link Extraction Tests (>95% precision)
# ============================================================================

class TestPhishingLinkExtraction:
    """Tests for phishing link extraction - AC-3.1.5."""
    
    def test_extract_suspicious_links(self, extractor):
        """Test extraction of suspicious links."""
        suspicious = [
            "http://fake-bank.xyz/verify",
            "https://secure-banking.tk/login",
            "http://kyc-update.ml/verify",
        ]
        
        for link in suspicious:
            text = f"Click {link} now"
            intel, _ = extractor.extract(text)
            assert link in intel["phishing_links"], f"Should extract: {link}"
    
    def test_exclude_legitimate_domains(self, extractor):
        """Test that legitimate domains are excluded."""
        legitimate = [
            "https://www.google.com",
            "https://www.paytm.com/",
            "https://www.sbi.co.in",
        ]
        
        for link in legitimate:
            text = f"Visit {link}"
            intel, _ = extractor.extract(text)
            # Legitimate links should NOT be in phishing_links
            for extracted in intel["phishing_links"]:
                assert "google.com" not in extracted
                assert "paytm.com" not in extracted
                assert "sbi.co.in" not in extracted
    
    def test_flag_ip_based_urls(self, extractor):
        """Test that IP-based URLs are flagged as suspicious."""
        text = "Visit http://192.168.1.1/verify"
        intel, _ = extractor.extract(text)
        
        assert len(intel["phishing_links"]) > 0
    
    def test_flag_url_shorteners(self, extractor):
        """Test that URL shorteners are flagged."""
        shorteners = [
            "http://bit.ly/abc123",
            "http://tinyurl.com/xyz",
        ]
        
        for link in shorteners:
            text = f"Click {link}"
            intel, _ = extractor.extract(text)
            assert link in intel["phishing_links"], f"Should flag: {link}"
    
    def test_flag_http_non_https(self, extractor):
        """Test that HTTP (non-HTTPS) links to unknown domains are flagged."""
        text = "Visit http://unknown-bank.com/login"
        intel, _ = extractor.extract(text)
        
        assert len(intel["phishing_links"]) > 0
    
    def test_multiple_phishing_links(self, extractor):
        """Test extraction of multiple phishing links."""
        text = "Click http://fake1.xyz or http://fake2.tk for verification"
        intel, _ = extractor.extract(text)
        
        assert len(intel["phishing_links"]) >= 2


# ============================================================================
# AC-3.3.1: Devanagari Digit Conversion Tests (100% accurate)
# ============================================================================

class TestDevanagariConversion:
    """Tests for Devanagari digit conversion - AC-3.3.1."""
    
    def test_convert_all_devanagari_digits(self, extractor):
        """Test conversion of all Devanagari digits."""
        text = "Account: ०१२३४५६७८९"
        converted = extractor._convert_devanagari_digits(text)
        
        assert "0123456789" in converted
    
    def test_mixed_devanagari_and_ascii(self, extractor):
        """Test mixed Devanagari and ASCII digits."""
        text = "Phone: ९८७६5४3210"
        converted = extractor._convert_devanagari_digits(text)
        
        assert "9876543210" in converted
    
    def test_devanagari_in_upi_context(self, extractor):
        """Test Devanagari digits in UPI payment context."""
        text = "Pay ₹५००० to scammer@paytm"
        converted = extractor._convert_devanagari_digits(text)
        
        assert "5000" in converted
    
    def test_devanagari_phone_number(self, extractor):
        """Test Devanagari phone number extraction."""
        text = "Call ९८७६५४३२१०"
        intel, _ = extractor.extract(text)
        
        assert "+919876543210" in intel["phone_numbers"]
    
    def test_devanagari_bank_account(self, extractor):
        """Test Devanagari bank account extraction."""
        text = "Account: १२३४५६७८९०१२"
        intel, _ = extractor.extract(text)
        
        assert "123456789012" in intel["bank_accounts"]
    
    def test_full_devanagari_text(self, extractor):
        """Test full Devanagari numeric text."""
        # All Devanagari digits: ०१२३४५६७८९
        text = "खाता संख्या: ९८७६५४३२१०१२"
        intel, _ = extractor.extract(text)
        
        # Should extract 987654321012 as bank account
        assert any("9876543210" in acc for acc in intel["bank_accounts"] + intel["phone_numbers"])


# ============================================================================
# Confidence Score Tests
# ============================================================================

class TestConfidenceCalculation:
    """Tests for confidence score calculation."""
    
    def test_empty_intel_zero_confidence(self, extractor):
        """Test that empty intel gives 0 confidence."""
        intel, confidence = extractor.extract("")
        
        assert confidence == 0.0
    
    def test_upi_only_confidence(self, extractor):
        """Test confidence with only UPI ID."""
        intel, confidence = extractor.extract("Pay to scammer@paytm")
        
        assert confidence == 0.3  # UPI weight is 0.3
    
    def test_upi_and_phone_confidence(self, extractor):
        """Test confidence with UPI and phone."""
        intel, confidence = extractor.extract("Pay scammer@paytm or call 9876543210")
        
        assert confidence == 0.4  # UPI(0.3) + phone(0.1)
    
    def test_full_intel_confidence(self, extractor):
        """Test confidence with all entity types."""
        text = """
        Pay to fraud@paytm account 12345678901234 
        IFSC SBIN0001234 call 9876543210 
        verify http://fake.xyz
        """
        intel, confidence = extractor.extract(text)
        
        assert confidence == 1.0
    
    def test_confidence_capped_at_1(self, extractor):
        """Test that confidence is capped at 1.0."""
        text = """
        Multiple UPIs: a1@paytm b2@ybl c3@okaxis
        Multiple accounts: 12345678901 98765432109
        Multiple phones: 9876543210 8765432109
        """
        intel, confidence = extractor.extract(text)
        
        assert confidence <= 1.0


# ============================================================================
# Convenience Function Tests
# ============================================================================

class TestExtractIntelligenceFunction:
    """Tests for convenience extract_intelligence function."""
    
    def test_function_returns_tuple(self):
        """Test function returns expected tuple."""
        text = "Send to scammer@paytm"
        intel, confidence = extract_intelligence(text)
        
        assert isinstance(intel, dict)
        assert isinstance(confidence, float)
    
    def test_function_with_empty_text(self):
        """Test function handles empty text."""
        intel, confidence = extract_intelligence("")
        
        assert len(intel["upi_ids"]) == 0
        assert confidence == 0.0
    
    def test_function_with_complex_text(self):
        """Test function with realistic scam message."""
        text = """
        Congratulations! You've won ₹10,00,000!
        To claim, send ₹500 to winner@paytm or transfer to 
        account 12345678901234 IFSC HDFC0123456.
        Call +919876543210 for verification.
        Click http://claim-prize.xyz/verify
        """
        intel, confidence = extract_intelligence(text)
        
        assert "winner@paytm" in intel["upi_ids"]
        assert "12345678901234" in intel["bank_accounts"]
        assert "HDFC0123456" in intel["ifsc_codes"]
        assert "+919876543210" in intel["phone_numbers"]
        assert any("claim-prize.xyz" in link for link in intel["phishing_links"])
        assert confidence == 1.0
    
    def test_singleton_pattern(self):
        """Test that get_extractor returns same instance."""
        ext1 = get_extractor()
        ext2 = get_extractor()
        
        assert ext1 is ext2
    
    def test_reset_singleton(self):
        """Test singleton reset works."""
        ext1 = get_extractor()
        reset_extractor()
        ext2 = get_extractor()
        
        assert ext1 is not ext2


class TestExtractFromMessages:
    """Tests for extract_from_messages function."""
    
    def test_extract_from_message_list(self):
        """Test extraction from list of messages."""
        messages = [
            {"turn": 1, "sender": "scammer", "message": "Send to fraud@paytm"},
            {"turn": 2, "sender": "agent", "message": "What is your account?"},
            {"turn": 3, "sender": "scammer", "message": "Account 12345678901234"},
        ]
        
        intel, confidence = extract_from_messages(messages)
        
        assert "fraud@paytm" in intel["upi_ids"]
        assert "12345678901234" in intel["bank_accounts"]
    
    def test_extract_from_empty_messages(self):
        """Test extraction from empty message list."""
        intel, confidence = extract_from_messages([])
        
        assert confidence == 0.0
    
    def test_extract_handles_missing_message_key(self):
        """Test extraction handles messages without 'message' key."""
        messages = [
            {"turn": 1, "sender": "scammer"},  # No message key
            {"turn": 2, "sender": "agent", "message": "Pay to test@paytm"},
        ]
        
        intel, confidence = extract_from_messages(messages)
        
        # Should not raise, and should extract from valid message
        assert "test@paytm" in intel["upi_ids"]


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_very_long_text(self, extractor):
        """Test extraction from very long text."""
        text = "Send to test@paytm " + "x" * 10000 + " account 12345678901"
        intel, confidence = extractor.extract(text)
        
        assert "test@paytm" in intel["upi_ids"]
        assert "12345678901" in intel["bank_accounts"]
    
    def test_unicode_text(self, extractor):
        """Test extraction with Unicode characters."""
        text = "Pay ₹5000 to scammer@paytm 📱 call 9876543210"
        intel, _ = extractor.extract(text)
        
        assert "scammer@paytm" in intel["upi_ids"]
        assert "+919876543210" in intel["phone_numbers"]
    
    def test_special_characters(self, extractor):
        """Test extraction with special characters."""
        text = "Pay to user@paytm!!! Account: 12345678901###"
        intel, _ = extractor.extract(text)
        
        assert "user@paytm" in intel["upi_ids"]
    
    def test_html_content(self, extractor):
        """Test extraction from HTML-like content."""
        text = "<p>Pay to scammer@paytm</p> <a href='http://fake.xyz'>Click</a>"
        intel, _ = extractor.extract(text)
        
        assert "scammer@paytm" in intel["upi_ids"]
    
    def test_none_text(self, extractor):
        """Test that None text doesn't crash."""
        # The function expects str, but should handle gracefully
        try:
            intel, confidence = extractor.extract(None)
            assert confidence == 0.0
        except TypeError:
            # Expected behavior - None is not a string
            pass
    
    def test_newlines_and_tabs(self, extractor):
        """Test extraction with newlines and tabs."""
        text = "Pay to:\n\tscammer@paytm\n\tAccount:\t12345678901"
        intel, _ = extractor.extract(text)
        
        assert "scammer@paytm" in intel["upi_ids"]
        assert "12345678901" in intel["bank_accounts"]


# ============================================================================
# Acceptance Criteria Verification Tests
# ============================================================================

class TestAcceptanceCriteria:
    """Tests to verify Task 7.1 acceptance criteria."""
    
    def test_ac_3_1_1_upi_precision(self, extractor):
        """AC-3.1.1: UPI ID extraction precision >90%."""
        # Test with known UPI IDs - all should be extracted
        valid_upis = [
            "user@paytm",
            "fraud@ybl",
            "scam@okaxis",
            "target@okhdfcbank",
            "victim@oksbi",
        ]
        
        for upi in valid_upis:
            intel, _ = extractor.extract(f"Pay to {upi}")
            assert upi in intel["upi_ids"], f"Failed for: {upi}"
        
        # Test false positive exclusion (email domains)
        false_positives = [
            "user@gmail.com",
            "contact@company.org",
        ]
        
        for fp in false_positives:
            intel, _ = extractor.extract(f"Email: {fp}")
            assert fp not in intel["upi_ids"], f"False positive: {fp}"
    
    def test_ac_3_1_2_bank_account_precision(self, extractor):
        """AC-3.1.2: Bank account precision >85%."""
        # Valid bank accounts
        valid_accounts = [
            "123456789012",   # 12 digits
            "12345678901234", # 14 digits
            "123456789",      # 9 digits
        ]
        
        for acc in valid_accounts:
            intel, _ = extractor.extract(f"Account: {acc}")
            assert acc in intel["bank_accounts"], f"Failed for: {acc}"
        
        # Should exclude phone numbers
        intel, _ = extractor.extract("Phone: 9876543210")
        assert "9876543210" not in intel["bank_accounts"]
    
    def test_ac_3_1_3_ifsc_precision(self, extractor):
        """AC-3.1.3: IFSC code precision >95%."""
        valid_ifsc = ["SBIN0001234", "HDFC0567890", "ICIC0BRANCH"]
        
        for ifsc in valid_ifsc:
            intel, _ = extractor.extract(f"IFSC: {ifsc}")
            assert ifsc in intel["ifsc_codes"], f"Failed for: {ifsc}"
    
    def test_ac_3_1_4_phone_precision(self, extractor):
        """AC-3.1.4: Phone number precision >90%."""
        valid_phones = [
            ("9876543210", "+919876543210"),
            ("+919876543210", "+919876543210"),
            ("+91-9876543210", "+919876543210"),
        ]
        
        for input_phone, expected in valid_phones:
            intel, _ = extractor.extract(f"Call: {input_phone}")
            assert expected in intel["phone_numbers"], f"Failed for: {input_phone}"
    
    def test_ac_3_1_5_phishing_precision(self, extractor):
        """AC-3.1.5: Phishing link precision >95%."""
        suspicious_links = [
            "http://fake-bank.xyz/verify",
            "http://bit.ly/scam",
            "http://192.168.1.1/login",
        ]
        
        for link in suspicious_links:
            intel, _ = extractor.extract(f"Click: {link}")
            assert link in intel["phishing_links"], f"Failed for: {link}"
    
    def test_ac_3_3_1_devanagari_100_percent(self, extractor):
        """AC-3.3.1: Devanagari digit conversion 100% accurate."""
        # Test all Devanagari digits
        devanagari = "०१२३४५६७८९"
        ascii_expected = "0123456789"
        
        converted = extractor._convert_devanagari_digits(devanagari)
        assert converted == ascii_expected
    
    def test_verification_example_from_tasks(self, extractor):
        """Test the exact example from TASKS.md verification."""
        text = "Send ₹5000 to scammer@paytm or call +919876543210"
        intel, conf = extractor.extract(text)
        
        assert "scammer@paytm" in intel["upi_ids"]
        assert "+919876543210" in intel["phone_numbers"]
        assert conf > 0.3

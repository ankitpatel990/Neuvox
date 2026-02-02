"""
Unit Tests for Validation Module.

Tests input validation functions.
"""

import pytest
from app.utils.validation import (
    validate_message,
    validate_session_id,
    validate_language,
    validate_upi_id,
    validate_bank_account,
    validate_ifsc_code,
    validate_phone_number,
    validate_url,
    validate_all_intelligence,
)


class TestMessageValidation:
    """Tests for message validation."""
    
    def test_valid_message(self):
        """Test valid message passes validation."""
        is_valid, error = validate_message("Hello world")
        assert is_valid == True
        assert error is None
    
    def test_empty_message(self):
        """Test empty message fails validation."""
        is_valid, error = validate_message("")
        assert is_valid == False
        assert error is not None
    
    def test_whitespace_only_message(self):
        """Test whitespace-only message fails validation."""
        is_valid, error = validate_message("   ")
        assert is_valid == False
    
    def test_too_long_message(self):
        """Test message exceeding max length fails."""
        long_message = "x" * 5001
        is_valid, error = validate_message(long_message)
        assert is_valid == False
        assert "5000" in error


class TestSessionIdValidation:
    """Tests for session ID validation."""
    
    def test_valid_uuid(self):
        """Test valid UUID passes validation."""
        is_valid, error = validate_session_id("550e8400-e29b-41d4-a716-446655440000")
        assert is_valid == True
        assert error is None
    
    def test_none_session_id(self):
        """Test None session ID passes (optional)."""
        is_valid, error = validate_session_id(None)
        assert is_valid == True
    
    def test_invalid_uuid(self):
        """Test invalid UUID fails validation."""
        is_valid, error = validate_session_id("invalid-uuid")
        assert is_valid == False


class TestLanguageValidation:
    """Tests for language validation."""
    
    def test_valid_languages(self):
        """Test valid language codes pass."""
        for lang in ["auto", "en", "hi"]:
            is_valid, error = validate_language(lang)
            assert is_valid == True
    
    def test_invalid_language(self):
        """Test invalid language code fails."""
        is_valid, error = validate_language("fr")
        assert is_valid == False


class TestEntityValidation:
    """Tests for entity validation functions."""
    
    def test_valid_upi_id(self):
        """Test valid UPI ID validation."""
        assert validate_upi_id("user@paytm") == True
        assert validate_upi_id("test.user@ybl") == True
    
    def test_invalid_upi_id(self):
        """Test invalid UPI ID validation."""
        assert validate_upi_id("invalid") == False
        assert validate_upi_id("@paytm") == False
    
    def test_valid_bank_account(self):
        """Test valid bank account validation."""
        assert validate_bank_account("12345678901") == True
        assert validate_bank_account("123456789012345") == True
    
    def test_invalid_bank_account(self):
        """Test invalid bank account validation."""
        assert validate_bank_account("12345") == False  # Too short
        assert validate_bank_account("1234567890") == False  # Phone number
    
    def test_valid_ifsc_code(self):
        """Test valid IFSC code validation."""
        assert validate_ifsc_code("SBIN0001234") == True
        assert validate_ifsc_code("HDFC0123456") == True
    
    def test_invalid_ifsc_code(self):
        """Test invalid IFSC code validation."""
        assert validate_ifsc_code("SBIN1234567") == False  # 5th char not 0
        assert validate_ifsc_code("SBI0001234") == False  # Too short
    
    def test_valid_phone_number(self):
        """Test valid phone number validation."""
        assert validate_phone_number("9876543210") == True
        assert validate_phone_number("+919876543210") == True
    
    def test_invalid_phone_number(self):
        """Test invalid phone number validation."""
        assert validate_phone_number("1234567890") == False  # Starts with 1
        assert validate_phone_number("98765") == False  # Too short
    
    def test_valid_url(self):
        """Test valid URL validation."""
        assert validate_url("http://example.com") == True
        assert validate_url("https://secure.example.com/path") == True
    
    def test_invalid_url(self):
        """Test invalid URL validation."""
        assert validate_url("not-a-url") == False
        assert validate_url("ftp://example.com") == False


class TestValidateBankAccountEdgeCases:
    """Additional edge case tests for bank account validation."""
    
    def test_non_digit_bank_account(self):
        """Test bank account with non-digit characters fails."""
        assert validate_bank_account("12345678abc") == False
        assert validate_bank_account("123-456-789") == False
    
    def test_bank_account_at_boundaries(self):
        """Test bank account at length boundaries."""
        assert validate_bank_account("12345678") == False  # 8 digits - too short
        assert validate_bank_account("123456789") == True  # 9 digits - valid
        assert validate_bank_account("123456789012345678") == True  # 18 digits - valid
        assert validate_bank_account("1234567890123456789") == False  # 19 digits - too long


class TestValidatePhoneNumberEdgeCases:
    """Additional edge case tests for phone number validation."""
    
    def test_phone_with_separators(self):
        """Test phone numbers with separators."""
        assert validate_phone_number("987-654-3210") == True
        assert validate_phone_number("987 654 3210") == True
    
    def test_phone_with_non_digit_fails(self):
        """Test phone with non-digit content fails."""
        assert validate_phone_number("98765abc10") == False


class TestValidateAllIntelligence:
    """Tests for validate_all_intelligence function."""
    
    def test_returns_tuple(self):
        """Test function returns tuple of validated intel and errors."""
        intel = {}
        result = validate_all_intelligence(intel)
        
        assert isinstance(result, tuple)
        assert len(result) == 2
    
    def test_empty_intel(self):
        """Test empty intelligence dict."""
        intel = {}
        validated, errors = validate_all_intelligence(intel)
        
        assert validated["upi_ids"] == []
        assert validated["bank_accounts"] == []
        assert validated["ifsc_codes"] == []
        assert validated["phone_numbers"] == []
        assert validated["phishing_links"] == []
        assert errors == []
    
    def test_valid_upi_ids(self):
        """Test valid UPI IDs are kept."""
        intel = {"upi_ids": ["scammer@paytm", "fraud@ybl"]}
        validated, errors = validate_all_intelligence(intel)
        
        assert len(validated["upi_ids"]) == 2
        assert "scammer@paytm" in validated["upi_ids"]
        assert errors == []
    
    def test_invalid_upi_ids_filtered(self):
        """Test invalid UPI IDs are filtered out with errors."""
        intel = {"upi_ids": ["valid@paytm", "invalid-upi"]}
        validated, errors = validate_all_intelligence(intel)
        
        assert len(validated["upi_ids"]) == 1
        assert "valid@paytm" in validated["upi_ids"]
        assert len(errors) == 1
        assert "Invalid UPI ID" in errors[0]
    
    def test_valid_bank_accounts(self):
        """Test valid bank accounts are kept."""
        intel = {"bank_accounts": ["12345678901", "123456789012345"]}
        validated, errors = validate_all_intelligence(intel)
        
        assert len(validated["bank_accounts"]) == 2
        assert errors == []
    
    def test_invalid_bank_accounts_filtered(self):
        """Test invalid bank accounts are filtered out."""
        intel = {"bank_accounts": ["12345678901", "12345"]}  # Second is too short
        validated, errors = validate_all_intelligence(intel)
        
        assert len(validated["bank_accounts"]) == 1
        assert len(errors) == 1
        assert "Invalid bank account" in errors[0]
    
    def test_valid_ifsc_codes(self):
        """Test valid IFSC codes are kept and uppercased."""
        intel = {"ifsc_codes": ["sbin0001234", "HDFC0123456"]}
        validated, errors = validate_all_intelligence(intel)
        
        assert len(validated["ifsc_codes"]) == 2
        assert "SBIN0001234" in validated["ifsc_codes"]
        assert "HDFC0123456" in validated["ifsc_codes"]
        assert errors == []
    
    def test_invalid_ifsc_codes_filtered(self):
        """Test invalid IFSC codes are filtered out."""
        intel = {"ifsc_codes": ["SBIN0001234", "INVALID"]}
        validated, errors = validate_all_intelligence(intel)
        
        assert len(validated["ifsc_codes"]) == 1
        assert len(errors) == 1
        assert "Invalid IFSC code" in errors[0]
    
    def test_valid_phone_numbers(self):
        """Test valid phone numbers are kept."""
        intel = {"phone_numbers": ["9876543210", "+919123456789"]}
        validated, errors = validate_all_intelligence(intel)
        
        assert len(validated["phone_numbers"]) == 2
        assert errors == []
    
    def test_invalid_phone_numbers_filtered(self):
        """Test invalid phone numbers are filtered out."""
        intel = {"phone_numbers": ["9876543210", "1234567890"]}  # Second starts with 1
        validated, errors = validate_all_intelligence(intel)
        
        assert len(validated["phone_numbers"]) == 1
        assert len(errors) == 1
        assert "Invalid phone number" in errors[0]
    
    def test_valid_phishing_links(self):
        """Test valid URLs are kept."""
        intel = {"phishing_links": ["http://scam.com", "https://fake.com/verify"]}
        validated, errors = validate_all_intelligence(intel)
        
        assert len(validated["phishing_links"]) == 2
        assert errors == []
    
    def test_invalid_urls_filtered(self):
        """Test invalid URLs are filtered out."""
        intel = {"phishing_links": ["http://valid.com", "not-a-url"]}
        validated, errors = validate_all_intelligence(intel)
        
        assert len(validated["phishing_links"]) == 1
        assert len(errors) == 1
        assert "Invalid URL" in errors[0]
    
    def test_mixed_valid_and_invalid(self):
        """Test with mix of valid and invalid entities."""
        intel = {
            "upi_ids": ["valid@paytm", "invalid"],
            "bank_accounts": ["12345678901", "short"],
            "ifsc_codes": ["SBIN0001234", "bad"],
            "phone_numbers": ["9876543210", "123"],
            "phishing_links": ["http://scam.com", "noturl"],
        }
        
        validated, errors = validate_all_intelligence(intel)
        
        assert len(validated["upi_ids"]) == 1
        assert len(validated["bank_accounts"]) == 1
        assert len(validated["ifsc_codes"]) == 1
        assert len(validated["phone_numbers"]) == 1
        assert len(validated["phishing_links"]) == 1
        assert len(errors) == 5

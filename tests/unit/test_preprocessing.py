"""
Unit Tests for Text Preprocessing Module.

Tests text cleaning, normalization, and utility functions.
"""

import pytest

from app.utils.preprocessing import (
    clean_text,
    normalize_text,
    convert_devanagari_digits,
    truncate_text,
    remove_urls,
    extract_numbers,
    mask_sensitive_data,
)


class TestCleanText:
    """Tests for clean_text function."""
    
    def test_empty_string(self):
        """Test empty string returns empty string."""
        assert clean_text("") == ""
    
    def test_none_returns_empty(self):
        """Test None or falsy value returns empty string."""
        assert clean_text(None) == ""
    
    def test_removes_extra_whitespace(self):
        """Test extra whitespace is normalized."""
        text = "Hello   world   here"
        result = clean_text(text)
        assert result == "Hello world here"
    
    def test_removes_leading_trailing_whitespace(self):
        """Test leading/trailing whitespace is stripped."""
        text = "   Hello world   "
        result = clean_text(text)
        assert result == "Hello world"
    
    def test_removes_control_characters(self):
        """Test control characters are removed."""
        text = "Hello\x00\x07world"
        result = clean_text(text)
        assert "\x00" not in result
        assert "\x07" not in result
        assert "Hello" in result
        assert "world" in result
    
    def test_preserves_normal_text(self):
        """Test normal text is preserved."""
        text = "Hello, how are you?"
        result = clean_text(text)
        assert result == text
    
    def test_normalizes_newlines_and_tabs(self):
        """Test newlines and tabs are normalized to spaces."""
        text = "Hello\nworld\there"
        result = clean_text(text)
        assert result == "Hello world here"
    
    def test_handles_unicode(self):
        """Test Unicode text is preserved."""
        text = "नमस्ते दुनिया"
        result = clean_text(text)
        assert result == text


class TestNormalizeText:
    """Tests for normalize_text function."""
    
    def test_basic_normalization(self):
        """Test basic text normalization."""
        text = "  Hello   world  "
        result = normalize_text(text)
        assert result == "Hello world"
    
    def test_lowercase_option(self):
        """Test lowercase option."""
        text = "Hello WORLD"
        result = normalize_text(text, lowercase=True)
        assert result == "hello world"
    
    def test_without_lowercase(self):
        """Test preserves case by default."""
        text = "Hello WORLD"
        result = normalize_text(text, lowercase=False)
        assert result == "Hello WORLD"
    
    def test_converts_devanagari_digits(self):
        """Test Devanagari digits are converted."""
        text = "Amount: ५०००"
        result = normalize_text(text)
        assert "5000" in result


class TestConvertDevanagariDigits:
    """Tests for convert_devanagari_digits function."""
    
    def test_converts_all_digits(self):
        """Test all Devanagari digits are converted."""
        text = "०१२३४५६७८९"
        result = convert_devanagari_digits(text)
        assert result == "0123456789"
    
    def test_preserves_latin_digits(self):
        """Test Latin digits are preserved."""
        text = "123456"
        result = convert_devanagari_digits(text)
        assert result == "123456"
    
    def test_mixed_digits(self):
        """Test mixed Devanagari and Latin digits."""
        text = "Phone: ९८76543२१०"
        result = convert_devanagari_digits(text)
        assert result == "Phone: 9876543210"
    
    def test_preserves_non_digit_text(self):
        """Test non-digit text is preserved."""
        text = "नमस्ते"
        result = convert_devanagari_digits(text)
        assert result == "नमस्ते"
    
    def test_empty_string(self):
        """Test empty string returns empty."""
        assert convert_devanagari_digits("") == ""
    
    def test_phone_number_in_hindi(self):
        """Test phone number conversion in Hindi context."""
        text = "कॉल करें ९८७६५४३२१०"
        result = convert_devanagari_digits(text)
        assert "9876543210" in result


class TestTruncateText:
    """Tests for truncate_text function."""
    
    def test_short_text_unchanged(self):
        """Test text shorter than limit is unchanged."""
        text = "Hello world"
        result = truncate_text(text, max_length=100)
        assert result == text
    
    def test_long_text_truncated(self):
        """Test text longer than limit is truncated."""
        text = "a" * 100
        result = truncate_text(text, max_length=50)
        assert len(result) == 50
        assert result.endswith("...")
    
    def test_custom_suffix(self):
        """Test custom truncation suffix."""
        text = "a" * 100
        result = truncate_text(text, max_length=50, suffix="[...]")
        assert result.endswith("[...]")
    
    def test_exact_length(self):
        """Test text at exact length is unchanged."""
        text = "a" * 50
        result = truncate_text(text, max_length=50)
        assert result == text
    
    def test_default_max_length(self):
        """Test default max_length is 5000."""
        text = "a" * 5000
        result = truncate_text(text)
        assert len(result) == 5000


class TestRemoveUrls:
    """Tests for remove_urls function."""
    
    def test_removes_http_url(self):
        """Test HTTP URLs are removed."""
        text = "Visit http://example.com for more info"
        result = remove_urls(text)
        assert "http://example.com" not in result
        assert "Visit" in result
    
    def test_removes_https_url(self):
        """Test HTTPS URLs are removed."""
        text = "Visit https://secure.example.com for more info"
        result = remove_urls(text)
        assert "https://secure.example.com" not in result
    
    def test_removes_multiple_urls(self):
        """Test multiple URLs are removed."""
        text = "Visit http://one.com and http://two.com"
        result = remove_urls(text)
        assert "http://one.com" not in result
        assert "http://two.com" not in result
    
    def test_preserves_non_url_text(self):
        """Test non-URL text is preserved."""
        text = "Hello world, no URLs here"
        result = remove_urls(text)
        assert result == text
    
    def test_removes_complex_url(self):
        """Test complex URLs with paths are removed."""
        text = "Click http://example.com/path/to/page?query=value"
        result = remove_urls(text)
        assert "http://example.com" not in result


class TestExtractNumbers:
    """Tests for extract_numbers function."""
    
    def test_extracts_single_number(self):
        """Test extracts single number."""
        text = "Amount is 5000"
        result = extract_numbers(text)
        assert "5000" in result
    
    def test_extracts_multiple_numbers(self):
        """Test extracts multiple numbers."""
        text = "Account 123456 and phone 9876543210"
        result = extract_numbers(text)
        assert "123456" in result
        assert "9876543210" in result
    
    def test_handles_devanagari_digits(self):
        """Test handles Devanagari digits."""
        text = "Amount ५०००"
        result = extract_numbers(text)
        assert "5000" in result
    
    def test_no_numbers(self):
        """Test returns empty list when no numbers."""
        text = "No numbers here"
        result = extract_numbers(text)
        assert result == []
    
    def test_mixed_devanagari_and_latin(self):
        """Test mixed digit systems."""
        text = "Phone ९८76543२१० account 123"
        result = extract_numbers(text)
        assert "9876543210" in result
        assert "123" in result


class TestMaskSensitiveData:
    """Tests for mask_sensitive_data function."""
    
    def test_masks_upi_id(self):
        """Test UPI ID is masked."""
        text = "Send to scammer@paytm"
        result = mask_sensitive_data(text)
        assert "scammer@paytm" not in result
        assert "[UPI_MASKED]" in result
    
    def test_masks_bank_account(self):
        """Test bank account number is masked."""
        text = "Account: 123456789012345"
        result = mask_sensitive_data(text)
        assert "123456789012345" not in result
        assert "[ACCOUNT_MASKED]" in result
    
    def test_masks_phone_number(self):
        """Test phone number is masked."""
        text = "Call 9876543210"
        result = mask_sensitive_data(text)
        assert "9876543210" not in result
        # Phone number gets masked (either as phone or account since 10 digits)
        assert "[PHONE_MASKED]" in result or "[ACCOUNT_MASKED]" in result
    
    def test_masks_phone_with_plus91(self):
        """Test phone with +91 prefix is masked."""
        text = "Call +91 9876543210"
        result = mask_sensitive_data(text)
        assert "9876543210" not in result
        # Phone number gets masked (either as phone or account)
        assert "[PHONE_MASKED]" in result or "[ACCOUNT_MASKED]" in result
    
    def test_preserves_non_sensitive_text(self):
        """Test non-sensitive text is preserved."""
        text = "Hello, how are you?"
        result = mask_sensitive_data(text)
        assert result == text
    
    def test_masks_multiple_sensitive_items(self):
        """Test masks multiple sensitive items in one text."""
        text = "Send to fraud@ybl, call 9876543210, account 123456789012"
        result = mask_sensitive_data(text)
        
        assert "fraud@ybl" not in result
        assert "9876543210" not in result
        assert "123456789012" not in result


class TestPreprocessingEdgeCases:
    """Edge case tests for preprocessing functions."""
    
    def test_clean_text_with_emojis(self):
        """Test clean_text preserves emojis."""
        text = "Hello 😀 world 🎉"
        result = clean_text(text)
        assert "😀" in result
        assert "🎉" in result
    
    def test_normalize_very_long_text(self):
        """Test normalize handles very long text."""
        text = "word " * 10000
        result = normalize_text(text)
        assert len(result) > 0
    
    def test_devanagari_mixed_with_special_chars(self):
        """Test Devanagari digits with special characters."""
        text = "Amount: ₹५,०००/-"
        result = convert_devanagari_digits(text)
        assert "5" in result
        assert "0" in result
    
    def test_url_with_hindi_text(self):
        """Test URL removal with surrounding Hindi text."""
        text = "यहाँ क्लिक करें http://fake.com जीतने के लिए"
        result = remove_urls(text)
        assert "http://fake.com" not in result
        assert "यहाँ क्लिक करें" in result

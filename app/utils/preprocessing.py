"""
Text Preprocessing Module.

Provides text cleaning and normalization utilities for:
- Message sanitization
- Devanagari digit conversion
- Text normalization
"""

import re
from typing import Optional


def clean_text(text: str) -> str:
    """
    Clean and sanitize input text.
    
    Removes:
    - Extra whitespace
    - Control characters
    - Leading/trailing whitespace
    
    Args:
        text: Input text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove control characters (except newlines and tabs)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)
    
    # Strip leading/trailing whitespace
    text = text.strip()
    
    return text


def normalize_text(text: str, lowercase: bool = False) -> str:
    """
    Normalize text for processing.
    
    Args:
        text: Input text
        lowercase: Convert to lowercase if True
        
    Returns:
        Normalized text
    """
    text = clean_text(text)
    
    if lowercase:
        text = text.lower()
    
    # Convert Devanagari digits to ASCII
    text = convert_devanagari_digits(text)
    
    return text


def convert_devanagari_digits(text: str) -> str:
    """
    Convert Devanagari digits to ASCII digits.
    
    Args:
        text: Input text containing potential Devanagari digits
        
    Returns:
        Text with Devanagari digits converted to ASCII
    """
    devanagari_map = {
        "\u0966": "0",  # 
        "\u0967": "1",  # 
        "\u0968": "2",  # 
        "\u0969": "3",  # 
        "\u096A": "4",  # 
        "\u096B": "5",  # 
        "\u096C": "6",  # 
        "\u096D": "7",  # 
        "\u096E": "8",  # 
        "\u096F": "9",  # 
    }
    
    for devanagari, ascii_digit in devanagari_map.items():
        text = text.replace(devanagari, ascii_digit)
    
    return text


def truncate_text(text: str, max_length: int = 5000, suffix: str = "...") -> str:
    """
    Truncate text to maximum length.
    
    Args:
        text: Input text
        max_length: Maximum allowed length
        suffix: Suffix to add if truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[: max_length - len(suffix)] + suffix


def remove_urls(text: str) -> str:
    """
    Remove URLs from text.
    
    Args:
        text: Input text
        
    Returns:
        Text with URLs removed
    """
    url_pattern = r"https?://[^\s<>\"{}|\\^`\[\]]+"
    return re.sub(url_pattern, "", text)


def extract_numbers(text: str) -> list:
    """
    Extract all number sequences from text.
    
    Args:
        text: Input text
        
    Returns:
        List of number strings
    """
    # First convert Devanagari digits
    text = convert_devanagari_digits(text)
    
    # Extract digit sequences
    return re.findall(r"\d+", text)


def mask_sensitive_data(text: str) -> str:
    """
    Mask sensitive data in text for logging.
    
    Masks:
    - UPI IDs
    - Bank account numbers
    - Phone numbers
    
    Args:
        text: Input text
        
    Returns:
        Text with sensitive data masked
    """
    # Mask UPI IDs
    text = re.sub(r"\b[a-zA-Z0-9._-]+@[a-zA-Z]+\b", "[UPI_MASKED]", text)
    
    # Mask bank accounts (9-18 digits)
    text = re.sub(r"\b\d{9,18}\b", "[ACCOUNT_MASKED]", text)
    
    # Mask phone numbers
    text = re.sub(r"(?:\+91[\s-]?)?[6-9]\d{9}\b", "[PHONE_MASKED]", text)
    
    return text

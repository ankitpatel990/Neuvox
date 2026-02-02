"""
Input Validation Module.

Provides validation utilities for:
- Message validation
- Session ID validation
- Language code validation
- Financial entity validation
"""

import re
import uuid
from typing import Tuple, Optional, List


def validate_message(message: str) -> Tuple[bool, Optional[str]]:
    """
    Validate input message.
    
    Checks:
    - Not empty
    - Not only whitespace
    - Within length limits (1-5000 chars)
    
    Args:
        message: Input message to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not message:
        return False, "Message is required"
    
    if not message.strip():
        return False, "Message cannot be empty or whitespace only"
    
    if len(message) > 5000:
        return False, f"Message exceeds maximum length of 5000 characters (got {len(message)})"
    
    return True, None


def validate_session_id(session_id: str) -> Tuple[bool, Optional[str]]:
    """
    Validate session ID format.
    
    Args:
        session_id: Session ID to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not session_id:
        return True, None  # Session ID is optional
    
    try:
        uuid.UUID(session_id, version=4)
        return True, None
    except ValueError:
        return False, "Session ID must be a valid UUID v4 format"


def validate_language(language: str) -> Tuple[bool, Optional[str]]:
    """
    Validate language code.
    
    Args:
        language: Language code to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    allowed = {"auto", "en", "hi"}
    
    if language not in allowed:
        return False, f"Language must be one of: {', '.join(sorted(allowed))}"
    
    return True, None


def validate_upi_id(upi_id: str) -> bool:
    """
    Validate UPI ID format.
    
    Format: username@provider (e.g., user@paytm)
    
    Args:
        upi_id: UPI ID to validate
        
    Returns:
        True if valid format
    """
    pattern = r"^[a-zA-Z0-9._-]+@[a-zA-Z]+$"
    return bool(re.match(pattern, upi_id))


def validate_bank_account(account: str) -> bool:
    """
    Validate bank account number.
    
    Valid: 9-18 digits (excluding 10 digits which are phone numbers)
    
    Args:
        account: Account number to validate
        
    Returns:
        True if valid format
    """
    if not account.isdigit():
        return False
    
    length = len(account)
    
    # Must be 9-18 digits
    if length < 9 or length > 18:
        return False
    
    # Exclude phone numbers (exactly 10 digits)
    if length == 10:
        return False
    
    return True


def validate_ifsc_code(ifsc: str) -> bool:
    """
    Validate IFSC code format.
    
    Format: XXXX0XXXXXX (11 characters, 5th is always 0)
    
    Args:
        ifsc: IFSC code to validate
        
    Returns:
        True if valid format
    """
    pattern = r"^[A-Z]{4}0[A-Z0-9]{6}$"
    return bool(re.match(pattern, ifsc.upper()))


def validate_phone_number(phone: str) -> bool:
    """
    Validate Indian phone number format.
    
    Valid formats:
    - 10 digits starting with 6-9
    - +91 followed by 10 digits
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid format
    """
    # Remove common separators
    cleaned = re.sub(r"[\s\-]", "", phone)
    
    # Check with country code
    if cleaned.startswith("+91"):
        cleaned = cleaned[3:]
    
    # Must be 10 digits starting with 6-9
    if len(cleaned) != 10:
        return False
    
    if not cleaned.isdigit():
        return False
    
    if cleaned[0] not in "6789":
        return False
    
    return True


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid URL format
    """
    pattern = r"^https?://[^\s<>\"{}|\\^`\[\]]+"
    return bool(re.match(pattern, url))


def validate_all_intelligence(
    intel: dict,
) -> Tuple[dict, List[str]]:
    """
    Validate all extracted intelligence.
    
    Args:
        intel: Dictionary of extracted intelligence
        
    Returns:
        Tuple of (validated_intel, validation_errors)
    """
    validated = {
        "upi_ids": [],
        "bank_accounts": [],
        "ifsc_codes": [],
        "phone_numbers": [],
        "phishing_links": [],
    }
    errors = []
    
    for upi in intel.get("upi_ids", []):
        if validate_upi_id(upi):
            validated["upi_ids"].append(upi)
        else:
            errors.append(f"Invalid UPI ID: {upi}")
    
    for account in intel.get("bank_accounts", []):
        if validate_bank_account(account):
            validated["bank_accounts"].append(account)
        else:
            errors.append(f"Invalid bank account: {account}")
    
    for ifsc in intel.get("ifsc_codes", []):
        if validate_ifsc_code(ifsc):
            validated["ifsc_codes"].append(ifsc.upper())
        else:
            errors.append(f"Invalid IFSC code: {ifsc}")
    
    for phone in intel.get("phone_numbers", []):
        if validate_phone_number(phone):
            validated["phone_numbers"].append(phone)
        else:
            errors.append(f"Invalid phone number: {phone}")
    
    for url in intel.get("phishing_links", []):
        if validate_url(url):
            validated["phishing_links"].append(url)
        else:
            errors.append(f"Invalid URL: {url}")
    
    return validated, errors

"""
Pytest Configuration and Fixtures.

Provides shared fixtures for all test modules.
"""

import pytest
from typing import Generator, Dict, Any


@pytest.fixture(scope="session")
def client():
    """
    Create a test client for the FastAPI application.
    
    Yields:
        TestClient instance
    """
    from fastapi.testclient import TestClient
    from app.main import app
    
    # Create TestClient - compatible with newer httpx versions
    test_client = TestClient(app)
    yield test_client


@pytest.fixture
def sample_scam_message() -> str:
    """
    Provide a sample scam message for testing.
    
    Returns:
        Sample scam message string
    """
    return "Congratulations! You have won 10 lakh rupees. Share your OTP to claim the prize immediately."


@pytest.fixture
def sample_hindi_scam_message() -> str:
    """
    Provide a sample Hindi scam message for testing.
    
    Returns:
        Sample Hindi scam message string
    """
    return "आप जीत गए हैं 10 लाख रुपये! अपना OTP शेयर करें।"


@pytest.fixture
def sample_legitimate_message() -> str:
    """
    Provide a sample legitimate message for testing.
    
    Returns:
        Sample legitimate message string
    """
    return "Hi, how are you doing today? Hope you are well."


@pytest.fixture
def sample_engage_request() -> Dict[str, Any]:
    """
    Provide a sample engage request payload.
    
    Returns:
        Request payload dictionary
    """
    return {
        "message": "You won 10 lakh! Send OTP now!",
        "language": "auto",
    }


@pytest.fixture
def sample_session_state() -> Dict[str, Any]:
    """
    Provide a sample session state for testing.
    
    Returns:
        Session state dictionary
    """
    return {
        "messages": [],
        "scam_confidence": 0.0,
        "turn_count": 0,
        "extracted_intel": {},
        "strategy": "build_trust",
        "language": "en",
        "persona": "elderly",
    }


@pytest.fixture
def sample_extracted_intelligence() -> Dict[str, Any]:
    """
    Provide sample extracted intelligence for testing.
    
    Returns:
        Intelligence dictionary
    """
    return {
        "upi_ids": ["scammer@paytm", "fraud@ybl"],
        "bank_accounts": ["1234567890123"],
        "ifsc_codes": ["SBIN0001234"],
        "phone_numbers": ["+919876543210"],
        "phishing_links": ["http://fake-bank.com/verify"],
    }


@pytest.fixture
def mock_environment_variables(monkeypatch):
    """
    Set up mock environment variables for testing.
    
    Args:
        monkeypatch: Pytest monkeypatch fixture
    """
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("GROQ_API_KEY", "test_key")

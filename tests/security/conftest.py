"""
Pytest Configuration for Security Tests.

Provides fixtures and configuration specific to red team testing.
"""

import pytest
from typing import Generator


@pytest.fixture(scope="module")
def client():
    """
    Create a test client for security tests.
    
    Uses module scope to avoid repeated app initialization.
    
    Yields:
        TestClient instance
    """
    from fastapi.testclient import TestClient
    from app.main import app
    
    test_client = TestClient(app)
    yield test_client


def pytest_configure(config):
    """Configure pytest for security tests."""
    config.addinivalue_line(
        "markers",
        "security: marks tests as security/red team tests"
    )
    config.addinivalue_line(
        "markers",
        "critical: marks tests as testing critical vulnerabilities"
    )

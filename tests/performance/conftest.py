"""
Pytest Configuration for Performance Tests.

Provides fixtures and configuration specific to performance testing.
"""

import pytest
from typing import Generator


@pytest.fixture(scope="module")
def client():
    """
    Create a test client for performance tests.
    
    Uses module scope to avoid repeated app initialization.
    
    Yields:
        TestClient instance
    """
    from fastapi.testclient import TestClient
    from app.main import app
    
    test_client = TestClient(app)
    yield test_client


@pytest.fixture
def load_tester(client):
    """
    Create a LoadTester instance for performance tests.
    
    Args:
        client: FastAPI TestClient fixture
        
    Returns:
        LoadTester instance
    """
    from tests.performance.test_load import LoadTester
    return LoadTester(client)


def pytest_configure(config):
    """Configure pytest for performance tests."""
    config.addinivalue_line(
        "markers",
        "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection for performance tests."""
    # Skip slow tests by default unless explicitly requested
    if config.getoption("-m") != "slow":
        skip_slow = pytest.mark.skip(reason="need -m slow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)

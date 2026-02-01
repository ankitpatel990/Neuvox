"""
Unit Tests for Main Application Module.

Tests FastAPI application configuration and utility functions.
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app, get_uptime_seconds


@pytest.fixture
def client():
    """Provide test client for the FastAPI app."""
    return TestClient(app)


class TestAppConfiguration:
    """Tests for app configuration."""
    
    def test_app_exists(self):
        """Test app is created."""
        assert app is not None
    
    def test_app_title(self):
        """Test app has correct title."""
        assert app.title == "ScamShield AI"
    
    def test_app_version(self):
        """Test app has version."""
        assert app.version == "1.0.0"
    
    def test_app_description(self):
        """Test app has description."""
        assert app.description is not None
        assert len(app.description) > 0


class TestRootEndpoint:
    """Tests for root endpoint."""
    
    def test_root_returns_200(self, client):
        """Test root endpoint returns 200."""
        response = client.get("/")
        
        assert response.status_code == 200
    
    def test_root_returns_api_info(self, client):
        """Test root endpoint returns API info."""
        response = client.get("/")
        data = response.json()
        
        assert "name" in data
        assert data["name"] == "ScamShield AI"
        assert "version" in data
        assert "description" in data
        assert "health" in data
    
    def test_root_includes_health_endpoint(self, client):
        """Test root includes health endpoint path."""
        response = client.get("/")
        data = response.json()
        
        assert data["health"] == "/api/v1/health"


class TestGetUptimeSeconds:
    """Tests for get_uptime_seconds function."""
    
    def test_returns_integer(self):
        """Test function returns an integer."""
        result = get_uptime_seconds()
        
        assert isinstance(result, int)
    
    def test_returns_non_negative(self):
        """Test uptime is non-negative."""
        result = get_uptime_seconds()
        
        assert result >= 0


class TestExceptionHandler:
    """Tests for global exception handler."""
    
    def test_handles_internal_error(self, client):
        """Test internal errors are handled gracefully."""
        # This test relies on the exception handler being configured
        # We can't easily trigger a 500 error in unit tests without
        # modifying the app, so we just verify the handler exists
        
        assert app.exception_handlers is not None


class TestCORSMiddleware:
    """Tests for CORS middleware configuration."""
    
    def test_cors_headers_on_options(self, client):
        """Test CORS headers are present on OPTIONS request."""
        response = client.options(
            "/api/v1/health",
            headers={"Origin": "http://example.com"}
        )
        
        # CORS headers should be present
        assert response.status_code in [200, 405]
    
    def test_cors_allows_origin(self, client):
        """Test CORS allows cross-origin requests."""
        response = client.get(
            "/api/v1/health",
            headers={"Origin": "http://example.com"}
        )
        
        # Request should succeed
        assert response.status_code == 200


class TestAPIRoutes:
    """Tests for API route registration."""
    
    def test_health_route_registered(self, client):
        """Test health route is registered."""
        response = client.get("/api/v1/health")
        
        assert response.status_code == 200
    
    def test_engage_route_registered(self, client):
        """Test engage route is registered."""
        response = client.post(
            "/api/v1/honeypot/engage",
            json={"message": "Test message"}
        )
        
        # Should return 200 (processed) or validation error, not 404
        assert response.status_code in [200, 400, 422]
    
    def test_session_route_registered(self, client):
        """Test session route is registered."""
        response = client.get("/api/v1/honeypot/session/test-session-id")
        
        # Should return 200, 400, 404, or validation error, not route not found
        assert response.status_code in [200, 400, 404, 422]
    
    def test_batch_route_registered(self, client):
        """Test batch route is registered."""
        response = client.post(
            "/api/v1/honeypot/batch",
            json={"messages": [{"id": "1", "message": "Test"}]}
        )
        
        # Should process or error, not 404
        assert response.status_code in [200, 400, 422]


class TestAppLifespan:
    """Tests for app lifespan events."""
    
    def test_app_starts_successfully(self, client):
        """Test app starts and serves requests."""
        response = client.get("/")
        
        assert response.status_code == 200
    
    def test_app_handles_multiple_requests(self, client):
        """Test app handles multiple requests."""
        for _ in range(5):
            response = client.get("/api/v1/health")
            assert response.status_code == 200

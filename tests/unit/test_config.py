"""
Unit Tests for Configuration Module.

Tests Settings class and configuration loading.
"""

import pytest
import os
from unittest.mock import patch

from app.config import Settings, get_settings, settings


class TestSettingsDefaults:
    """Tests for Settings default values."""
    
    def test_settings_instance_exists(self):
        """Test settings instance is created."""
        assert settings is not None
        assert isinstance(settings, Settings)
    
    def test_default_environment(self):
        """Test default environment is development."""
        s = Settings()
        assert s.ENVIRONMENT == "development"
    
    def test_default_debug_false(self):
        """Test default DEBUG is False."""
        s = Settings()
        assert s.DEBUG is False
    
    def test_default_log_level(self):
        """Test default log level is INFO."""
        s = Settings()
        assert s.LOG_LEVEL == "INFO"
    
    def test_default_max_turns(self):
        """Test default max turns is 20."""
        s = Settings()
        assert s.MAX_TURNS == 20
    
    def test_default_session_ttl(self):
        """Test default session TTL is 3600."""
        s = Settings()
        assert s.SESSION_TTL == 3600
    
    def test_default_scam_threshold(self):
        """Test default scam threshold is 0.7."""
        s = Settings()
        assert s.SCAM_THRESHOLD == 0.7
    
    def test_default_api_port(self):
        """Test default API port is 8000."""
        s = Settings()
        assert s.API_PORT == 8000
    
    def test_default_api_host(self):
        """Test default API host is 0.0.0.0."""
        s = Settings()
        assert s.API_HOST == "0.0.0.0"
    
    def test_default_groq_model(self):
        """Test default Groq model."""
        s = Settings()
        assert "llama" in s.GROQ_MODEL.lower()
    
    def test_default_max_message_length(self):
        """Test default max message length is 5000."""
        s = Settings()
        assert s.MAX_MESSAGE_LENGTH == 5000


class TestSettingsEnvironmentProperties:
    """Tests for environment check properties."""
    
    def test_is_production_false_by_default(self):
        """Test is_production is False by default."""
        s = Settings()
        assert s.is_production is False
    
    def test_is_development_true_by_default(self):
        """Test is_development is True by default."""
        s = Settings()
        assert s.is_development is True
    
    def test_is_testing_false_by_default(self):
        """Test is_testing is False by default."""
        s = Settings()
        assert s.is_testing is False
    
    @patch.dict(os.environ, {"ENVIRONMENT": "production"})
    def test_is_production_true_in_production(self):
        """Test is_production is True when ENVIRONMENT=production."""
        s = Settings()
        assert s.is_production is True
        assert s.is_development is False
        assert s.is_testing is False
    
    @patch.dict(os.environ, {"ENVIRONMENT": "testing"})
    def test_is_testing_true_in_testing(self):
        """Test is_testing is True when ENVIRONMENT=testing."""
        s = Settings()
        assert s.is_testing is True
        assert s.is_production is False
        assert s.is_development is False


class TestSettingsValidation:
    """Tests for Settings.validate method."""
    
    def test_validate_returns_list(self):
        """Test validate returns a list."""
        s = Settings()
        result = s.validate()
        
        assert isinstance(result, list)
    
    def test_validate_no_errors_in_development(self):
        """Test validate returns no errors in development."""
        s = Settings()
        s.ENVIRONMENT = "development"
        result = s.validate()
        
        assert result == []
    
    @patch.dict(os.environ, {"ENVIRONMENT": "production"})
    def test_validate_errors_in_production_without_keys(self):
        """Test validate returns errors in production without required keys."""
        s = Settings()
        s.GROQ_API_KEY = None
        s.POSTGRES_URL = None
        s.REDIS_URL = None
        
        result = s.validate()
        
        assert len(result) > 0
        assert any("GROQ_API_KEY" in e for e in result)
        assert any("POSTGRES_URL" in e for e in result)
        assert any("REDIS_URL" in e for e in result)
    
    @patch.dict(os.environ, {
        "ENVIRONMENT": "production",
        "GROQ_API_KEY": "test-key",
        "POSTGRES_URL": "postgresql://test",
        "REDIS_URL": "redis://test"
    })
    def test_validate_no_errors_in_production_with_keys(self):
        """Test validate returns no errors in production with all keys."""
        s = Settings()
        
        result = s.validate()
        
        assert result == []


class TestSettingsFromEnvironment:
    """Tests for loading settings from environment variables."""
    
    @patch.dict(os.environ, {"DEBUG": "true"})
    def test_debug_from_env(self):
        """Test DEBUG is loaded from environment."""
        s = Settings()
        assert s.DEBUG is True
    
    @patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"})
    def test_log_level_from_env(self):
        """Test LOG_LEVEL is loaded from environment."""
        s = Settings()
        assert s.LOG_LEVEL == "DEBUG"
    
    @patch.dict(os.environ, {"MAX_TURNS": "30"})
    def test_max_turns_from_env(self):
        """Test MAX_TURNS is loaded from environment."""
        s = Settings()
        assert s.MAX_TURNS == 30
    
    @patch.dict(os.environ, {"SCAM_THRESHOLD": "0.8"})
    def test_scam_threshold_from_env(self):
        """Test SCAM_THRESHOLD is loaded from environment."""
        s = Settings()
        assert s.SCAM_THRESHOLD == 0.8
    
    @patch.dict(os.environ, {"API_PORT": "9000"})
    def test_api_port_from_env(self):
        """Test API_PORT is loaded from environment."""
        s = Settings()
        assert s.API_PORT == 9000
    
    @patch.dict(os.environ, {"GROQ_API_KEY": "test-key-123"})
    def test_groq_api_key_from_env(self):
        """Test GROQ_API_KEY is loaded from environment."""
        s = Settings()
        assert s.GROQ_API_KEY == "test-key-123"
    
    @patch.dict(os.environ, {"RATE_LIMIT_PER_MINUTE": "50"})
    def test_rate_limit_from_env(self):
        """Test RATE_LIMIT_PER_MINUTE is loaded from environment."""
        s = Settings()
        assert s.RATE_LIMIT_PER_MINUTE == 50


class TestGetSettings:
    """Tests for get_settings function."""
    
    def test_get_settings_returns_settings(self):
        """Test get_settings returns Settings instance."""
        result = get_settings()
        
        assert isinstance(result, Settings)
    
    def test_get_settings_cached(self):
        """Test get_settings returns cached instance."""
        result1 = get_settings()
        result2 = get_settings()
        
        assert result1 is result2


class TestSettingsAttributes:
    """Tests for Settings attribute types."""
    
    def test_groq_max_tokens_is_int(self):
        """Test GROQ_MAX_TOKENS is an integer."""
        s = Settings()
        assert isinstance(s.GROQ_MAX_TOKENS, int)
    
    def test_groq_temperature_is_float(self):
        """Test GROQ_TEMPERATURE is a float."""
        s = Settings()
        assert isinstance(s.GROQ_TEMPERATURE, float)
    
    def test_session_ttl_is_int(self):
        """Test SESSION_TTL is an integer."""
        s = Settings()
        assert isinstance(s.SESSION_TTL, int)
    
    def test_rate_limit_per_hour_is_int(self):
        """Test RATE_LIMIT_PER_HOUR is an integer."""
        s = Settings()
        assert isinstance(s.RATE_LIMIT_PER_HOUR, int)
    
    def test_api_prefix(self):
        """Test API_PREFIX is set correctly."""
        s = Settings()
        assert s.API_PREFIX == "/api/v1"
    
    def test_model_configuration(self):
        """Test model configuration settings."""
        s = Settings()
        
        assert s.INDICBERT_MODEL is not None
        assert s.SPACY_MODEL is not None
        assert s.EMBEDDING_MODEL is not None

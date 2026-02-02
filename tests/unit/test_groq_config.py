"""
Unit Tests for Groq API Configuration.

Tests the Groq API configuration and connectivity.
"""

import os
import pytest
from unittest.mock import patch, MagicMock


class TestGroqConfiguration:
    """Tests for Groq API configuration."""
    
    def test_groq_api_key_in_config(self):
        """Test that config includes GROQ_API_KEY setting."""
        from app.config import Settings
        
        settings = Settings()
        assert hasattr(settings, "GROQ_API_KEY")
    
    def test_groq_model_in_config(self):
        """Test that config includes GROQ_MODEL setting."""
        from app.config import Settings
        
        settings = Settings()
        assert hasattr(settings, "GROQ_MODEL")
        assert settings.GROQ_MODEL == "llama-3.3-70b-versatile"
    
    def test_groq_max_tokens_in_config(self):
        """Test that config includes GROQ_MAX_TOKENS setting."""
        from app.config import Settings
        
        settings = Settings()
        assert hasattr(settings, "GROQ_MAX_TOKENS")
        assert settings.GROQ_MAX_TOKENS == 500
    
    def test_groq_temperature_in_config(self):
        """Test that config includes GROQ_TEMPERATURE setting."""
        from app.config import Settings
        
        settings = Settings()
        assert hasattr(settings, "GROQ_TEMPERATURE")
        assert settings.GROQ_TEMPERATURE == 0.7
    
    @patch.dict(os.environ, {"GROQ_API_KEY": "test_key"})
    def test_groq_api_key_from_env(self):
        """Test that GROQ_API_KEY is read from environment."""
        from app.config import Settings
        
        settings = Settings()
        assert settings.GROQ_API_KEY == "test_key"
    
    @patch.dict(os.environ, {"GROQ_MODEL": "custom-model"})
    def test_groq_model_from_env(self):
        """Test that GROQ_MODEL is read from environment."""
        from app.config import Settings
        
        settings = Settings()
        assert settings.GROQ_MODEL == "custom-model"


class TestGroqClientImport:
    """Tests for Groq client import and initialization."""
    
    def test_groq_library_importable(self):
        """Test that groq library can be imported."""
        try:
            from groq import Groq
            assert Groq is not None
        except ImportError:
            pytest.skip("groq library not installed")
    
    def test_langchain_groq_importable(self):
        """Test that langchain-groq library can be imported."""
        try:
            from langchain_groq import ChatGroq
            assert ChatGroq is not None
        except ImportError:
            pytest.skip("langchain-groq library not installed")
    
    def test_groq_client_initialization_with_api_key(self):
        """Test that Groq client can be initialized with API key."""
        try:
            from groq import Groq
            
            # Test with a dummy key (won't make actual API calls)
            client = Groq(api_key="test_key_123")
            assert client is not None
        except ImportError:
            pytest.skip("groq library not installed")
    
    def test_langchain_groq_initialization(self):
        """Test that ChatGroq can be initialized."""
        try:
            from langchain_groq import ChatGroq
            
            # Test initialization (won't make actual API calls)
            llm = ChatGroq(
                api_key="test_key_123",
                model_name="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=50
            )
            assert llm is not None
        except ImportError:
            pytest.skip("langchain-groq library not installed")


class TestEnvFileConfiguration:
    """Tests for .env file configuration."""
    
    def test_dotenv_importable(self):
        """Test that python-dotenv can be imported."""
        try:
            from dotenv import load_dotenv
            assert load_dotenv is not None
        except ImportError:
            pytest.skip("python-dotenv not installed")
    
    def test_env_example_exists(self):
        """Test that env.example file exists."""
        import os
        env_example_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "env.example"
        )
        assert os.path.exists(env_example_path), "env.example should exist"
    
    def test_env_example_contains_groq_settings(self):
        """Test that env.example contains GROQ settings."""
        import os
        env_example_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "env.example"
        )
        
        with open(env_example_path, "r") as f:
            content = f.read()
        
        assert "GROQ_API_KEY" in content
        assert "GROQ_MODEL" in content


class TestGroqAPIConnectivity:
    """Tests for actual Groq API connectivity (requires valid API key)."""
    
    @pytest.fixture
    def groq_client(self):
        """Create Groq client with API key from environment."""
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key or api_key == "gsk_your_key_here":
            pytest.skip("GROQ_API_KEY not configured")
        
        from groq import Groq
        return Groq(api_key=api_key)
    
    def test_groq_api_call(self, groq_client):
        """Test actual Groq API call."""
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": "Say 'test'"}],
                max_tokens=10
            )
            
            assert response is not None
            assert len(response.choices) > 0
            assert response.choices[0].message.content is not None
            
        except Exception as e:
            if "rate" in str(e).lower():
                pytest.skip("Rate limited")
            raise

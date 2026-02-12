"""
Application Configuration Module.

Provides centralized configuration management using environment variables
and Pydantic settings for type-safe configuration.
"""

import os
from pathlib import Path
from typing import Optional
from functools import lru_cache

# Load .env file BEFORE reading environment variables
try:
    from dotenv import load_dotenv
    
    # Find .env file (check current dir and parent dirs)
    env_path = Path(__file__).parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        # Try current working directory
        load_dotenv()
except ImportError:
    pass  # dotenv not installed, rely on system env vars


class Settings:
    """
    Application settings loaded from environment variables.
    
    Attributes:
        ENVIRONMENT: Current environment (development, production, testing)
        DEBUG: Enable debug mode
        LOG_LEVEL: Logging level
        
        GROQ_API_KEY: Groq LLM API key
        GROQ_MODEL: Groq model name
        
        POSTGRES_URL: PostgreSQL connection URL
        REDIS_URL: Redis connection URL
        
        MAX_MESSAGE_LENGTH: Maximum message length
        MAX_TURNS: Maximum conversation turns
        SESSION_TTL: Session time-to-live in seconds
        SCAM_THRESHOLD: Scam detection confidence threshold
        
        RATE_LIMIT_PER_MINUTE: Rate limit per minute per IP
    """
    
    def __init__(self) -> None:
        """Initialize settings from environment variables."""
        # Environment
        self.ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        
        # Groq LLM Configuration
        self.GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
        self.GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.GROQ_MAX_TOKENS: int = int(os.getenv("GROQ_MAX_TOKENS", "256"))
        self.GROQ_TEMPERATURE: float = float(os.getenv("GROQ_TEMPERATURE", "0.7"))
        
        # Database Configuration
        # Empty string treated as None (disabled) for faster in-memory only mode
        self.POSTGRES_URL: Optional[str] = os.getenv("POSTGRES_URL") or None
        self.REDIS_URL: Optional[str] = os.getenv("REDIS_URL") or None
        self.CHROMADB_PATH: str = os.getenv("CHROMADB_PATH", "./chroma_data")
        
        # API Configuration
        self.API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
        self.API_PORT: int = int(os.getenv("API_PORT", "8000"))
        self.API_PREFIX: str = "/api/v1"
        
        # Scam Detection Configuration
        self.MAX_MESSAGE_LENGTH: int = int(os.getenv("MAX_MESSAGE_LENGTH", "5000"))
        self.MAX_TURNS: int = int(os.getenv("MAX_TURNS", "20"))
        self.SESSION_TTL: int = int(os.getenv("SESSION_TTL", "3600"))
        self.SCAM_THRESHOLD: float = float(os.getenv("SCAM_THRESHOLD", "0.7"))
        
        # Rate Limiting
        self.RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "100"))
        self.RATE_LIMIT_PER_HOUR: int = int(os.getenv("RATE_LIMIT_PER_HOUR", "1000"))
        
        # Model Configuration
        self.INDICBERT_MODEL: str = os.getenv("INDICBERT_MODEL", "ai4bharat/indic-bert")
        self.SPACY_MODEL: str = os.getenv("SPACY_MODEL", "en_core_web_sm")
        self.EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.HUGGINGFACE_TOKEN: Optional[str] = os.getenv("HUGGINGFACE_TOKEN")
        
        # Phase 2: Voice Features (opt-in, default disabled)
        self.PHASE_2_ENABLED: bool = os.getenv("PHASE_2_ENABLED", "false").lower() == "true"
        self.WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")
        self.WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "auto")
        self.TTS_ENGINE: str = os.getenv("TTS_ENGINE", "gtts")
        self.VOICE_FRAUD_DETECTION: bool = os.getenv("VOICE_FRAUD_DETECTION", "false").lower() == "true"
        self.AUDIO_SAMPLE_RATE: int = int(os.getenv("AUDIO_SAMPLE_RATE", "16000"))
        self.AUDIO_CHUNK_DURATION: int = int(os.getenv("AUDIO_CHUNK_DURATION", "5"))
        
        # API Authentication (GUVI Hackathon Requirement)
        self.API_KEY: Optional[str] = os.getenv("API_KEY")
        
        # GUVI Hackathon Integration
        self.GUVI_CALLBACK_URL: Optional[str] = os.getenv(
            "GUVI_CALLBACK_URL",
            "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"
        )
        self.GUVI_CALLBACK_ENABLED: bool = os.getenv("GUVI_CALLBACK_ENABLED", "true").lower() == "true"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.ENVIRONMENT == "development"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.ENVIRONMENT == "testing"
    
    def validate(self) -> list:
        """
        Validate required configuration.
        
        Returns:
            List of validation errors
        """
        errors = []
        
        if self.is_production:
            if not self.GROQ_API_KEY:
                errors.append("GROQ_API_KEY is required in production")
            if not self.POSTGRES_URL:
                errors.append("POSTGRES_URL is required in production")
            if not self.REDIS_URL:
                errors.append("REDIS_URL is required in production")
        
        return errors


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings instance
    """
    return Settings()


# Convenience access to settings
settings = get_settings()

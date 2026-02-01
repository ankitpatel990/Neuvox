"""
SQLAlchemy ORM Models.

Defines database models for:
- Conversation: Honeypot conversation sessions
- Message: Individual messages in conversations
- ExtractedIntelligence: Financial intelligence extracted from conversations
"""

from datetime import datetime
from typing import List, Optional

# Placeholder imports - will be replaced with actual SQLAlchemy
# from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, ARRAY
# from sqlalchemy.orm import relationship, declarative_base

# Base = declarative_base()


class Conversation:
    """
    Conversation model representing a honeypot session.
    
    Attributes:
        id: Primary key
        session_id: Unique session UUID
        language: Detected language (en, hi, hinglish)
        persona: Active persona name
        scam_detected: Whether scam was detected
        confidence: Detection confidence score
        turn_count: Number of conversation turns
        created_at: Session start timestamp
        updated_at: Last update timestamp
    """
    
    def __init__(
        self,
        session_id: str,
        language: str = "en",
        persona: Optional[str] = None,
        scam_detected: bool = False,
        confidence: float = 0.0,
        turn_count: int = 0,
    ) -> None:
        """Initialize Conversation model."""
        self.id: Optional[int] = None
        self.session_id = session_id
        self.language = language
        self.persona = persona
        self.scam_detected = scam_detected
        self.confidence = confidence
        self.turn_count = turn_count
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "language": self.language,
            "persona": self.persona,
            "scam_detected": self.scam_detected,
            "confidence": self.confidence,
            "turn_count": self.turn_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Message:
    """
    Message model representing a single conversation message.
    
    Attributes:
        id: Primary key
        conversation_id: Foreign key to Conversation
        turn_number: Turn number in conversation
        sender: Message sender (scammer/agent)
        message: Message content
        timestamp: Message timestamp
    """
    
    def __init__(
        self,
        conversation_id: int,
        turn_number: int,
        sender: str,
        message: str,
    ) -> None:
        """Initialize Message model."""
        self.id: Optional[int] = None
        self.conversation_id = conversation_id
        self.turn_number = turn_number
        self.sender = sender
        self.message = message
        self.timestamp = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "turn_number": self.turn_number,
            "sender": self.sender,
            "message": self.message,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class ExtractedIntelligence:
    """
    ExtractedIntelligence model for storing financial intelligence.
    
    Attributes:
        id: Primary key
        conversation_id: Foreign key to Conversation
        upi_ids: List of extracted UPI IDs
        bank_accounts: List of extracted bank account numbers
        ifsc_codes: List of extracted IFSC codes
        phone_numbers: List of extracted phone numbers
        phishing_links: List of extracted phishing URLs
        extraction_confidence: Overall extraction confidence
        created_at: Extraction timestamp
    """
    
    def __init__(
        self,
        conversation_id: int,
        upi_ids: Optional[List[str]] = None,
        bank_accounts: Optional[List[str]] = None,
        ifsc_codes: Optional[List[str]] = None,
        phone_numbers: Optional[List[str]] = None,
        phishing_links: Optional[List[str]] = None,
        extraction_confidence: float = 0.0,
    ) -> None:
        """Initialize ExtractedIntelligence model."""
        self.id: Optional[int] = None
        self.conversation_id = conversation_id
        self.upi_ids = upi_ids or []
        self.bank_accounts = bank_accounts or []
        self.ifsc_codes = ifsc_codes or []
        self.phone_numbers = phone_numbers or []
        self.phishing_links = phishing_links or []
        self.extraction_confidence = extraction_confidence
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "upi_ids": self.upi_ids,
            "bank_accounts": self.bank_accounts,
            "ifsc_codes": self.ifsc_codes,
            "phone_numbers": self.phone_numbers,
            "phishing_links": self.phishing_links,
            "extraction_confidence": self.extraction_confidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def has_intelligence(self) -> bool:
        """Check if any intelligence was extracted."""
        return any([
            self.upi_ids,
            self.bank_accounts,
            self.ifsc_codes,
            self.phone_numbers,
            self.phishing_links,
        ])

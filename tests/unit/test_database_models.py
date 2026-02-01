"""
Unit Tests for Database ORM Models.

Tests Conversation, Message, and ExtractedIntelligence models.
"""

import pytest
from datetime import datetime

from app.database.models import Conversation, Message, ExtractedIntelligence


class TestConversationModel:
    """Tests for Conversation model."""
    
    def test_initialization(self):
        """Test Conversation can be initialized."""
        conv = Conversation(session_id="test-session-123")
        
        assert conv is not None
        assert conv.session_id == "test-session-123"
    
    def test_default_values(self):
        """Test Conversation default values."""
        conv = Conversation(session_id="test-123")
        
        assert conv.language == "en"
        assert conv.persona is None
        assert conv.scam_detected is False
        assert conv.confidence == 0.0
        assert conv.turn_count == 0
    
    def test_custom_values(self):
        """Test Conversation with custom values."""
        conv = Conversation(
            session_id="sess-custom",
            language="hi",
            persona="elderly",
            scam_detected=True,
            confidence=0.95,
            turn_count=5
        )
        
        assert conv.language == "hi"
        assert conv.persona == "elderly"
        assert conv.scam_detected is True
        assert conv.confidence == 0.95
        assert conv.turn_count == 5
    
    def test_timestamps_set(self):
        """Test timestamps are set on initialization."""
        conv = Conversation(session_id="test")
        
        assert conv.created_at is not None
        assert conv.updated_at is not None
        assert isinstance(conv.created_at, datetime)
        assert isinstance(conv.updated_at, datetime)
    
    def test_id_is_none_initially(self):
        """Test id is None before database insert."""
        conv = Conversation(session_id="test")
        
        assert conv.id is None
    
    def test_to_dict(self):
        """Test to_dict method."""
        conv = Conversation(
            session_id="sess-dict-test",
            language="en",
            persona="eager",
            scam_detected=True,
            confidence=0.8,
            turn_count=3
        )
        
        result = conv.to_dict()
        
        assert isinstance(result, dict)
        assert result["session_id"] == "sess-dict-test"
        assert result["language"] == "en"
        assert result["persona"] == "eager"
        assert result["scam_detected"] is True
        assert result["confidence"] == 0.8
        assert result["turn_count"] == 3
        assert "created_at" in result
        assert "updated_at" in result
    
    def test_to_dict_includes_id(self):
        """Test to_dict includes id field."""
        conv = Conversation(session_id="test")
        result = conv.to_dict()
        
        assert "id" in result


class TestMessageModel:
    """Tests for Message model."""
    
    def test_initialization(self):
        """Test Message can be initialized."""
        msg = Message(
            conversation_id=1,
            turn_number=1,
            sender="scammer",
            message="Hello, you won!"
        )
        
        assert msg is not None
        assert msg.conversation_id == 1
        assert msg.turn_number == 1
        assert msg.sender == "scammer"
        assert msg.message == "Hello, you won!"
    
    def test_timestamp_set(self):
        """Test timestamp is set on initialization."""
        msg = Message(
            conversation_id=1,
            turn_number=1,
            sender="agent",
            message="Test"
        )
        
        assert msg.timestamp is not None
        assert isinstance(msg.timestamp, datetime)
    
    def test_id_is_none_initially(self):
        """Test id is None before database insert."""
        msg = Message(
            conversation_id=1,
            turn_number=1,
            sender="scammer",
            message="Test"
        )
        
        assert msg.id is None
    
    def test_to_dict(self):
        """Test to_dict method."""
        msg = Message(
            conversation_id=5,
            turn_number=3,
            sender="agent",
            message="How can I claim?"
        )
        
        result = msg.to_dict()
        
        assert isinstance(result, dict)
        assert result["conversation_id"] == 5
        assert result["turn_number"] == 3
        assert result["sender"] == "agent"
        assert result["message"] == "How can I claim?"
        assert "timestamp" in result
    
    def test_to_dict_includes_id(self):
        """Test to_dict includes id field."""
        msg = Message(
            conversation_id=1,
            turn_number=1,
            sender="scammer",
            message="Test"
        )
        result = msg.to_dict()
        
        assert "id" in result
    
    def test_scammer_sender(self):
        """Test message from scammer."""
        msg = Message(
            conversation_id=1,
            turn_number=1,
            sender="scammer",
            message="Scam message"
        )
        
        assert msg.sender == "scammer"
    
    def test_agent_sender(self):
        """Test message from agent."""
        msg = Message(
            conversation_id=1,
            turn_number=1,
            sender="agent",
            message="Agent response"
        )
        
        assert msg.sender == "agent"


class TestExtractedIntelligenceModel:
    """Tests for ExtractedIntelligence model."""
    
    def test_initialization(self):
        """Test ExtractedIntelligence can be initialized."""
        intel = ExtractedIntelligence(conversation_id=1)
        
        assert intel is not None
        assert intel.conversation_id == 1
    
    def test_default_empty_lists(self):
        """Test default empty lists for all fields."""
        intel = ExtractedIntelligence(conversation_id=1)
        
        assert intel.upi_ids == []
        assert intel.bank_accounts == []
        assert intel.ifsc_codes == []
        assert intel.phone_numbers == []
        assert intel.phishing_links == []
    
    def test_default_confidence(self):
        """Test default extraction confidence is 0.0."""
        intel = ExtractedIntelligence(conversation_id=1)
        
        assert intel.extraction_confidence == 0.0
    
    def test_custom_values(self):
        """Test ExtractedIntelligence with custom values."""
        intel = ExtractedIntelligence(
            conversation_id=5,
            upi_ids=["scammer@paytm", "fraud@ybl"],
            bank_accounts=["123456789012"],
            ifsc_codes=["SBIN0001234"],
            phone_numbers=["+919876543210"],
            phishing_links=["http://fake.com"],
            extraction_confidence=0.9
        )
        
        assert intel.conversation_id == 5
        assert len(intel.upi_ids) == 2
        assert "scammer@paytm" in intel.upi_ids
        assert len(intel.bank_accounts) == 1
        assert len(intel.ifsc_codes) == 1
        assert len(intel.phone_numbers) == 1
        assert len(intel.phishing_links) == 1
        assert intel.extraction_confidence == 0.9
    
    def test_timestamp_set(self):
        """Test created_at timestamp is set."""
        intel = ExtractedIntelligence(conversation_id=1)
        
        assert intel.created_at is not None
        assert isinstance(intel.created_at, datetime)
    
    def test_id_is_none_initially(self):
        """Test id is None before database insert."""
        intel = ExtractedIntelligence(conversation_id=1)
        
        assert intel.id is None
    
    def test_to_dict(self):
        """Test to_dict method."""
        intel = ExtractedIntelligence(
            conversation_id=10,
            upi_ids=["test@upi"],
            bank_accounts=["999888777666"],
            extraction_confidence=0.75
        )
        
        result = intel.to_dict()
        
        assert isinstance(result, dict)
        assert result["conversation_id"] == 10
        assert result["upi_ids"] == ["test@upi"]
        assert result["bank_accounts"] == ["999888777666"]
        assert result["extraction_confidence"] == 0.75
        assert "created_at" in result
    
    def test_to_dict_includes_all_fields(self):
        """Test to_dict includes all intelligence fields."""
        intel = ExtractedIntelligence(conversation_id=1)
        result = intel.to_dict()
        
        assert "id" in result
        assert "upi_ids" in result
        assert "bank_accounts" in result
        assert "ifsc_codes" in result
        assert "phone_numbers" in result
        assert "phishing_links" in result
    
    def test_has_intelligence_true(self):
        """Test has_intelligence returns True when data exists."""
        intel = ExtractedIntelligence(
            conversation_id=1,
            upi_ids=["test@paytm"]
        )
        
        assert intel.has_intelligence() is True
    
    def test_has_intelligence_false(self):
        """Test has_intelligence returns False when empty."""
        intel = ExtractedIntelligence(conversation_id=1)
        
        assert intel.has_intelligence() is False
    
    def test_has_intelligence_with_bank_account(self):
        """Test has_intelligence with bank account."""
        intel = ExtractedIntelligence(
            conversation_id=1,
            bank_accounts=["123456789012"]
        )
        
        assert intel.has_intelligence() is True
    
    def test_has_intelligence_with_phone(self):
        """Test has_intelligence with phone number."""
        intel = ExtractedIntelligence(
            conversation_id=1,
            phone_numbers=["+919876543210"]
        )
        
        assert intel.has_intelligence() is True
    
    def test_has_intelligence_with_phishing_link(self):
        """Test has_intelligence with phishing link."""
        intel = ExtractedIntelligence(
            conversation_id=1,
            phishing_links=["http://scam.com"]
        )
        
        assert intel.has_intelligence() is True


class TestModelIntegration:
    """Integration tests for model relationships."""
    
    def test_message_references_conversation(self):
        """Test Message references Conversation by ID."""
        conv = Conversation(session_id="test-integration")
        conv.id = 100  # Simulate database-assigned ID
        
        msg = Message(
            conversation_id=conv.id,
            turn_number=1,
            sender="scammer",
            message="Test"
        )
        
        assert msg.conversation_id == conv.id
    
    def test_intelligence_references_conversation(self):
        """Test ExtractedIntelligence references Conversation by ID."""
        conv = Conversation(session_id="test-intel")
        conv.id = 200  # Simulate database-assigned ID
        
        intel = ExtractedIntelligence(conversation_id=conv.id)
        
        assert intel.conversation_id == conv.id
    
    def test_multiple_messages_per_conversation(self):
        """Test multiple messages can reference same conversation."""
        conv_id = 50
        
        msg1 = Message(
            conversation_id=conv_id,
            turn_number=1,
            sender="scammer",
            message="First message"
        )
        
        msg2 = Message(
            conversation_id=conv_id,
            turn_number=1,
            sender="agent",
            message="First response"
        )
        
        msg3 = Message(
            conversation_id=conv_id,
            turn_number=2,
            sender="scammer",
            message="Second message"
        )
        
        assert msg1.conversation_id == msg2.conversation_id == msg3.conversation_id

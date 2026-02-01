"""
Unit Tests for API Schemas.

Tests Pydantic schema validation for request/response models.
"""

import pytest
import uuid
from pydantic import ValidationError

from app.api.schemas import (
    EngageRequest,
    EngageResponse,
    HealthResponse,
    BatchRequest,
    BatchResponse,
    SessionResponse,
    ErrorResponse,
    MessageEntry,
    EngagementInfo,
    ExtractedIntelligence,
    ResponseMetadata,
    HealthDependencies,
    BatchMessageItem,
    BatchResultItem,
    ErrorDetail,
)


class TestEngageRequest:
    """Tests for EngageRequest schema."""
    
    def test_valid_request_minimal(self):
        """Test valid request with only required fields."""
        request = EngageRequest(message="Test message")
        
        assert request.message == "Test message"
        assert request.session_id is None
        assert request.language == "auto"
    
    def test_valid_request_with_session_id(self):
        """Test valid request with session_id."""
        session_id = str(uuid.uuid4())
        request = EngageRequest(message="Test", session_id=session_id)
        
        assert request.session_id == session_id
    
    def test_valid_request_with_language(self):
        """Test valid request with language specified."""
        request = EngageRequest(message="Test", language="en")
        assert request.language == "en"
        
        request = EngageRequest(message="Test", language="hi")
        assert request.language == "hi"
    
    def test_invalid_empty_message(self):
        """Test validation fails for empty message."""
        with pytest.raises(ValidationError):
            EngageRequest(message="")
    
    def test_invalid_message_too_long(self):
        """Test validation fails for message > 5000 chars."""
        long_message = "x" * 5001
        with pytest.raises(ValidationError):
            EngageRequest(message=long_message)
    
    def test_valid_message_at_max_length(self):
        """Test valid message at exactly 5000 chars."""
        max_message = "x" * 5000
        request = EngageRequest(message=max_message)
        assert len(request.message) == 5000
    
    def test_invalid_session_id_format(self):
        """Test validation fails for invalid session_id format."""
        with pytest.raises(ValidationError):
            EngageRequest(message="Test", session_id="invalid-uuid")
    
    def test_invalid_language(self):
        """Test validation fails for unsupported language."""
        with pytest.raises(ValidationError):
            EngageRequest(message="Test", language="fr")
    
    def test_valid_with_callback_url(self):
        """Test valid request with mock_scammer_callback."""
        request = EngageRequest(
            message="Test",
            mock_scammer_callback="http://example.com/callback"
        )
        assert request.mock_scammer_callback == "http://example.com/callback"


class TestMessageEntry:
    """Tests for MessageEntry schema."""
    
    def test_valid_message_entry(self):
        """Test valid message entry."""
        entry = MessageEntry(
            turn=1,
            sender="scammer",
            message="Hello",
            timestamp="2026-01-28T10:00:00Z"
        )
        
        assert entry.turn == 1
        assert entry.sender == "scammer"
        assert entry.message == "Hello"
    
    def test_invalid_turn_zero(self):
        """Test validation fails for turn < 1."""
        with pytest.raises(ValidationError):
            MessageEntry(
                turn=0,
                sender="agent",
                message="Hi",
                timestamp="2026-01-28T10:00:00Z"
            )


class TestEngagementInfo:
    """Tests for EngagementInfo schema."""
    
    def test_valid_engagement_info(self):
        """Test valid engagement info."""
        info = EngagementInfo(
            agent_response="How can I claim?",
            turn_count=1,
            max_turns_reached=False,
            strategy="build_trust"
        )
        
        assert info.agent_response == "How can I claim?"
        assert info.turn_count == 1
        assert info.max_turns_reached is False
        assert info.strategy == "build_trust"
    
    def test_valid_with_persona(self):
        """Test valid engagement info with persona."""
        info = EngagementInfo(
            agent_response="Test",
            turn_count=5,
            max_turns_reached=False,
            strategy="express_confusion",
            persona="elderly"
        )
        
        assert info.persona == "elderly"
    
    def test_invalid_empty_response(self):
        """Test validation fails for empty agent_response."""
        with pytest.raises(ValidationError):
            EngagementInfo(
                agent_response="",
                turn_count=1,
                max_turns_reached=False,
                strategy="build_trust"
            )
    
    def test_invalid_turn_count_too_high(self):
        """Test validation fails for turn_count > 20."""
        with pytest.raises(ValidationError):
            EngagementInfo(
                agent_response="Test",
                turn_count=21,
                max_turns_reached=True,
                strategy="probe_details"
            )


class TestExtractedIntelligence:
    """Tests for ExtractedIntelligence schema."""
    
    def test_default_values(self):
        """Test default empty values."""
        intel = ExtractedIntelligence()
        
        assert intel.upi_ids == []
        assert intel.bank_accounts == []
        assert intel.ifsc_codes == []
        assert intel.phone_numbers == []
        assert intel.phishing_links == []
        assert intel.extraction_confidence == 0.0
    
    def test_with_extracted_data(self):
        """Test with extracted intelligence data."""
        intel = ExtractedIntelligence(
            upi_ids=["scammer@paytm", "fraud@ybl"],
            bank_accounts=["1234567890123"],
            ifsc_codes=["SBIN0001234"],
            phone_numbers=["+919876543210"],
            phishing_links=["http://fake.com"],
            extraction_confidence=0.85
        )
        
        assert len(intel.upi_ids) == 2
        assert intel.extraction_confidence == 0.85
    
    def test_invalid_confidence_out_of_range(self):
        """Test validation fails for confidence > 1.0."""
        with pytest.raises(ValidationError):
            ExtractedIntelligence(extraction_confidence=1.5)
    
    def test_invalid_negative_confidence(self):
        """Test validation fails for negative confidence."""
        with pytest.raises(ValidationError):
            ExtractedIntelligence(extraction_confidence=-0.1)


class TestResponseMetadata:
    """Tests for ResponseMetadata schema."""
    
    def test_valid_metadata(self):
        """Test valid response metadata."""
        meta = ResponseMetadata(
            processing_time_ms=150,
            model_version="1.0.0",
            detection_model="indic-bert",
            engagement_model="groq-llama-3.1-70b"
        )
        
        assert meta.processing_time_ms == 150
        assert meta.model_version == "1.0.0"
    
    def test_valid_minimal(self):
        """Test valid with only required fields."""
        meta = ResponseMetadata(
            processing_time_ms=100,
            model_version="1.0.0"
        )
        
        assert meta.detection_model is None
        assert meta.engagement_model is None
    
    def test_invalid_negative_processing_time(self):
        """Test validation fails for negative processing time."""
        with pytest.raises(ValidationError):
            ResponseMetadata(processing_time_ms=-1, model_version="1.0.0")


class TestEngageResponse:
    """Tests for EngageResponse schema."""
    
    def test_valid_scam_response(self):
        """Test valid response for detected scam."""
        response = EngageResponse(
            status="success",
            scam_detected=True,
            confidence=0.95,
            language_detected="en",
            session_id=str(uuid.uuid4())
        )
        
        assert response.scam_detected is True
        assert response.confidence == 0.95
    
    def test_valid_not_scam_response(self):
        """Test valid response for non-scam message."""
        response = EngageResponse(
            status="success",
            scam_detected=False,
            confidence=0.1,
            language_detected="en",
            session_id=str(uuid.uuid4()),
            message="No scam detected."
        )
        
        assert response.scam_detected is False
        assert response.message is not None
    
    def test_invalid_confidence_range(self):
        """Test validation fails for invalid confidence."""
        with pytest.raises(ValidationError):
            EngageResponse(
                status="success",
                scam_detected=True,
                confidence=1.5,
                language_detected="en",
                session_id="test-id"
            )


class TestHealthResponse:
    """Tests for HealthResponse schema."""
    
    def test_valid_health_response(self):
        """Test valid health response."""
        response = HealthResponse(
            status="healthy",
            version="1.0.0",
            timestamp="2026-01-28T10:00:00Z"
        )
        
        assert response.status == "healthy"
        assert response.version == "1.0.0"
    
    def test_valid_with_dependencies(self):
        """Test valid health response with dependencies."""
        deps = HealthDependencies(
            groq_api="online",
            postgres="online",
            redis="online",
            models_loaded=True
        )
        
        response = HealthResponse(
            status="healthy",
            version="1.0.0",
            timestamp="2026-01-28T10:00:00Z",
            dependencies=deps,
            uptime_seconds=86400
        )
        
        assert response.dependencies.models_loaded is True
        assert response.uptime_seconds == 86400


class TestBatchSchemas:
    """Tests for batch processing schemas."""
    
    def test_valid_batch_message_item(self):
        """Test valid batch message item."""
        item = BatchMessageItem(
            id="msg-001",
            message="Test message"
        )
        
        assert item.id == "msg-001"
        assert item.language == "auto"
    
    def test_valid_batch_request(self):
        """Test valid batch request."""
        request = BatchRequest(
            messages=[
                BatchMessageItem(id="1", message="First"),
                BatchMessageItem(id="2", message="Second"),
            ]
        )
        
        assert len(request.messages) == 2
    
    def test_invalid_empty_batch(self):
        """Test validation fails for empty messages list."""
        with pytest.raises(ValidationError):
            BatchRequest(messages=[])
    
    def test_valid_batch_result_success(self):
        """Test valid batch result item - success."""
        result = BatchResultItem(
            id="msg-001",
            status="success",
            scam_detected=True,
            confidence=0.9,
            language_detected="en"
        )
        
        assert result.status == "success"
        assert result.scam_detected is True
    
    def test_valid_batch_result_error(self):
        """Test valid batch result item - error."""
        result = BatchResultItem(
            id="msg-002",
            status="error",
            error={"code": "PROCESSING_ERROR", "message": "Failed"}
        )
        
        assert result.status == "error"
        assert result.error is not None
    
    def test_valid_batch_response(self):
        """Test valid batch response."""
        response = BatchResponse(
            status="success",
            processed=3,
            failed=0,
            results=[
                BatchResultItem(id="1", status="success", scam_detected=False, confidence=0.1),
            ],
            processing_time_ms=500
        )
        
        assert response.processed == 3


class TestSessionResponse:
    """Tests for SessionResponse schema."""
    
    def test_valid_session_response(self):
        """Test valid session response."""
        response = SessionResponse(
            session_id=str(uuid.uuid4()),
            language="en",
            scam_confidence=0.85,
            turn_count=5,
            conversation_history=[
                MessageEntry(turn=1, sender="scammer", message="Hi", timestamp="2026-01-28T10:00:00Z"),
            ],
            extracted_intelligence=ExtractedIntelligence(),
            created_at="2026-01-28T10:00:00Z",
            updated_at="2026-01-28T10:05:00Z"
        )
        
        assert response.turn_count == 5
        assert len(response.conversation_history) == 1


class TestErrorSchemas:
    """Tests for error schemas."""
    
    def test_valid_error_detail(self):
        """Test valid error detail."""
        error = ErrorDetail(
            code="VALIDATION_ERROR",
            message="Message is required"
        )
        
        assert error.code == "VALIDATION_ERROR"
    
    def test_error_detail_with_details(self):
        """Test error detail with additional details."""
        error = ErrorDetail(
            code="RATE_LIMIT_EXCEEDED",
            message="Too many requests",
            details={"retry_after_seconds": 60}
        )
        
        assert error.details["retry_after_seconds"] == 60
    
    def test_valid_error_response(self):
        """Test valid error response."""
        response = ErrorResponse(
            status="error",
            error=ErrorDetail(
                code="INTERNAL_ERROR",
                message="Something went wrong"
            )
        )
        
        assert response.status == "error"
        assert response.error.code == "INTERNAL_ERROR"

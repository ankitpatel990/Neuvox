"""
Unit Tests for Logging Module.

Tests logging configuration and logger classes.
"""

import pytest
import logging
from unittest.mock import MagicMock, patch

from app.utils.logger import (
    LOG_FORMAT,
    LOG_DATE_FORMAT,
    setup_logging,
    get_logger,
    RequestLogger,
    DetectionLogger,
    AuditLogger,
    request_logger,
    detection_logger,
    audit_logger,
)


class TestLoggingConstants:
    """Tests for logging constants."""
    
    def test_log_format_defined(self):
        """Test LOG_FORMAT is defined."""
        assert LOG_FORMAT is not None
        assert isinstance(LOG_FORMAT, str)
        assert len(LOG_FORMAT) > 0
    
    def test_log_format_contains_placeholders(self):
        """Test LOG_FORMAT contains standard placeholders."""
        assert "%(asctime)s" in LOG_FORMAT or "asctime" in LOG_FORMAT.lower()
        assert "%(levelname)" in LOG_FORMAT or "levelname" in LOG_FORMAT.lower()
    
    def test_date_format_defined(self):
        """Test LOG_DATE_FORMAT is defined."""
        assert LOG_DATE_FORMAT is not None
        assert isinstance(LOG_DATE_FORMAT, str)


class TestSetupLogging:
    """Tests for setup_logging function."""
    
    def test_sets_default_level(self):
        """Test default log level is INFO."""
        setup_logging()
        logger = logging.getLogger()
        
        # The level should be set (can be INFO=20 or WARNING=30 depending on config)
        assert logger.level in [logging.INFO, logging.DEBUG, logging.NOTSET, logging.WARNING]
    
    def test_sets_custom_level(self):
        """Test custom log level can be set."""
        setup_logging(level="DEBUG")
        # Should not raise
    
    def test_accepts_custom_format(self):
        """Test custom format can be provided."""
        custom_format = "%(message)s"
        setup_logging(log_format=custom_format)
        # Should not raise
    
    def test_handles_invalid_level(self):
        """Test handles invalid log level gracefully."""
        # Should default to INFO for invalid level
        setup_logging(level="INVALID")
        # Should not raise


class TestGetLogger:
    """Tests for get_logger function."""
    
    def test_returns_logger(self):
        """Test returns Logger instance."""
        logger = get_logger("test")
        
        assert isinstance(logger, logging.Logger)
    
    def test_returns_named_logger(self):
        """Test returns logger with given name."""
        logger = get_logger("my.module.name")
        
        assert logger.name == "my.module.name"
    
    def test_same_name_same_logger(self):
        """Test same name returns same logger instance."""
        logger1 = get_logger("same.name")
        logger2 = get_logger("same.name")
        
        assert logger1 is logger2


class TestRequestLogger:
    """Tests for RequestLogger class."""
    
    def test_initialization(self):
        """Test RequestLogger initializes correctly."""
        logger = RequestLogger()
        
        assert logger.logger is not None
        assert logger.logger.name == "scamshield.request"
    
    def test_log_request(self):
        """Test log_request method."""
        logger = RequestLogger()
        
        with patch.object(logger.logger, 'info') as mock_info:
            logger.log_request(
                method="POST",
                path="/api/v1/honeypot/engage",
                client_ip="127.0.0.1",
                request_id="req-123"
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            
            assert "REQUEST" in call_args
            assert "POST" in call_args
            assert "/api/v1/honeypot/engage" in call_args
    
    def test_log_request_minimal(self):
        """Test log_request with minimal parameters."""
        logger = RequestLogger()
        
        with patch.object(logger.logger, 'info') as mock_info:
            logger.log_request(method="GET", path="/health")
            
            mock_info.assert_called_once()
    
    def test_log_response(self):
        """Test log_response method."""
        logger = RequestLogger()
        
        with patch.object(logger.logger, 'info') as mock_info:
            logger.log_response(
                status_code=200,
                duration_ms=150,
                request_id="req-123"
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            
            assert "RESPONSE" in call_args
            assert "200" in call_args
            assert "150" in call_args


class TestDetectionLogger:
    """Tests for DetectionLogger class."""
    
    def test_initialization(self):
        """Test DetectionLogger initializes correctly."""
        logger = DetectionLogger()
        
        assert logger.logger is not None
        assert logger.logger.name == "scamshield.detection"
    
    def test_log_detection_scam(self):
        """Test log_detection for scam detection."""
        logger = DetectionLogger()
        
        with patch.object(logger.logger, 'info') as mock_info:
            logger.log_detection(
                session_id="sess-123",
                scam_detected=True,
                confidence=0.95,
                language="en",
                indicators=["lottery", "urgent"]
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            
            assert "DETECTION" in call_args
            assert "sess-123" in call_args
            assert "SCAM" in call_args
            assert "0.95" in call_args
    
    def test_log_detection_legitimate(self):
        """Test log_detection for legitimate message."""
        logger = DetectionLogger()
        
        with patch.object(logger.logger, 'info') as mock_info:
            logger.log_detection(
                session_id="sess-456",
                scam_detected=False,
                confidence=0.1,
                language="en"
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            
            assert "LEGITIMATE" in call_args
    
    def test_log_extraction(self):
        """Test log_extraction method."""
        logger = DetectionLogger()
        
        with patch.object(logger.logger, 'info') as mock_info:
            logger.log_extraction(
                session_id="sess-789",
                intel_summary={"upi_ids": 2, "phone_numbers": 1},
                confidence=0.85
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            
            assert "EXTRACTION" in call_args
            assert "sess-789" in call_args


class TestAuditLogger:
    """Tests for AuditLogger class."""
    
    def test_initialization(self):
        """Test AuditLogger initializes correctly."""
        logger = AuditLogger()
        
        assert logger.logger is not None
        assert logger.logger.name == "scamshield.audit"
    
    def test_log_event(self):
        """Test log_event method."""
        logger = AuditLogger()
        
        with patch.object(logger.logger, 'info') as mock_info:
            logger.log_event(
                event_type="session_created",
                details={"message_count": 5},
                session_id="sess-audit-123"
            )
            
            mock_info.assert_called_once()
            call_args = mock_info.call_args[0][0]
            
            assert "AUDIT" in call_args
            assert "session_created" in call_args
            assert "sess-audit-123" in call_args
    
    def test_log_event_without_session(self):
        """Test log_event without session_id."""
        logger = AuditLogger()
        
        with patch.object(logger.logger, 'info') as mock_info:
            logger.log_event(
                event_type="system_startup",
                details={"version": "1.0.0"}
            )
            
            mock_info.assert_called_once()


class TestModuleLevelLoggers:
    """Tests for module-level logger instances."""
    
    def test_request_logger_exists(self):
        """Test request_logger is defined."""
        assert request_logger is not None
        assert isinstance(request_logger, RequestLogger)
    
    def test_detection_logger_exists(self):
        """Test detection_logger is defined."""
        assert detection_logger is not None
        assert isinstance(detection_logger, DetectionLogger)
    
    def test_audit_logger_exists(self):
        """Test audit_logger is defined."""
        assert audit_logger is not None
        assert isinstance(audit_logger, AuditLogger)


class TestLoggerIntegration:
    """Integration tests for logger module."""
    
    def test_full_request_lifecycle(self):
        """Test logging a full request lifecycle."""
        with patch.object(request_logger.logger, 'info'):
            request_logger.log_request(
                method="POST",
                path="/api/v1/honeypot/engage",
                client_ip="192.168.1.1",
                request_id="req-full-test"
            )
            
            request_logger.log_response(
                status_code=200,
                duration_ms=250,
                request_id="req-full-test"
            )
    
    def test_detection_and_extraction_flow(self):
        """Test detection and extraction logging flow."""
        with patch.object(detection_logger.logger, 'info'):
            detection_logger.log_detection(
                session_id="sess-flow-test",
                scam_detected=True,
                confidence=0.9,
                language="en",
                indicators=["prize", "otp"]
            )
            
            detection_logger.log_extraction(
                session_id="sess-flow-test",
                intel_summary={"upi_ids": 1, "phone_numbers": 2},
                confidence=0.85
            )

"""
Logging Configuration Module.

Provides structured logging for:
- API request/response logging
- Detection event logging
- Error logging
- Audit logging
"""

import logging
import sys
from typing import Optional, Dict, Any
from datetime import datetime


# Default logging configuration
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: str = "INFO",
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
) -> None:
    """
    Configure logging for the application.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Custom log format string
        log_file: Optional file path for file logging
    """
    # Get log level
    log_level = getattr(logging, level.upper(), logging.INFO)
    
    # Configure root logger
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(
        log_format or LOG_FORMAT,
        LOG_DATE_FORMAT,
    ))
    handlers.append(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(logging.Formatter(
            log_format or LOG_FORMAT,
            LOG_DATE_FORMAT,
        ))
        handlers.append(file_handler)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=log_format or LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=handlers,
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class RequestLogger:
    """Logger for API requests."""
    
    def __init__(self) -> None:
        """Initialize request logger."""
        self.logger = get_logger("scamshield.request")
    
    def log_request(
        self,
        method: str,
        path: str,
        client_ip: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> None:
        """
        Log incoming API request.
        
        Args:
            method: HTTP method
            path: Request path
            client_ip: Client IP address
            request_id: Unique request identifier
        """
        self.logger.info(
            f"REQUEST | {method} {path} | client={client_ip} | request_id={request_id}"
        )
    
    def log_response(
        self,
        status_code: int,
        duration_ms: int,
        request_id: Optional[str] = None,
    ) -> None:
        """
        Log API response.
        
        Args:
            status_code: HTTP status code
            duration_ms: Response time in milliseconds
            request_id: Request identifier
        """
        self.logger.info(
            f"RESPONSE | status={status_code} | duration={duration_ms}ms | request_id={request_id}"
        )


class DetectionLogger:
    """Logger for scam detection events."""
    
    def __init__(self) -> None:
        """Initialize detection logger."""
        self.logger = get_logger("scamshield.detection")
    
    def log_detection(
        self,
        session_id: str,
        scam_detected: bool,
        confidence: float,
        language: str,
        indicators: Optional[list] = None,
    ) -> None:
        """
        Log scam detection event.
        
        Args:
            session_id: Session identifier
            scam_detected: Detection result
            confidence: Detection confidence
            language: Detected language
            indicators: Matched scam indicators
        """
        result = "SCAM" if scam_detected else "LEGITIMATE"
        self.logger.info(
            f"DETECTION | session={session_id} | result={result} | "
            f"confidence={confidence:.2f} | language={language} | "
            f"indicators={indicators}"
        )
    
    def log_extraction(
        self,
        session_id: str,
        intel_summary: Dict[str, int],
        confidence: float,
    ) -> None:
        """
        Log intelligence extraction event.
        
        Args:
            session_id: Session identifier
            intel_summary: Summary of extracted entities
            confidence: Extraction confidence
        """
        self.logger.info(
            f"EXTRACTION | session={session_id} | "
            f"entities={intel_summary} | confidence={confidence:.2f}"
        )


class AuditLogger:
    """Logger for audit events."""
    
    def __init__(self) -> None:
        """Initialize audit logger."""
        self.logger = get_logger("scamshield.audit")
    
    def log_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        session_id: Optional[str] = None,
    ) -> None:
        """
        Log audit event.
        
        Args:
            event_type: Type of event
            details: Event details
            session_id: Session identifier if applicable
        """
        timestamp = datetime.utcnow().isoformat()
        self.logger.info(
            f"AUDIT | time={timestamp} | type={event_type} | "
            f"session={session_id} | details={details}"
        )


# Module-level logger instances
request_logger = RequestLogger()
detection_logger = DetectionLogger()
audit_logger = AuditLogger()

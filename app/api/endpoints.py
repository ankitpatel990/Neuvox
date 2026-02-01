"""
FastAPI endpoints for the ScamShield AI API.

Implements Task 8.1: FastAPI Endpoints

Acceptance Criteria:
- AC-4.1.1: Returns 200 OK for valid requests
- AC-4.1.2: Returns 400 for invalid input
- AC-4.1.3: Response matches schema
- AC-4.1.5: Response time <2s (p95)
"""

from typing import Optional, List
from datetime import datetime
import uuid
import time

from fastapi import APIRouter, HTTPException, Request

from app.api.schemas import (
    EngageRequest,
    EngageResponse,
    HealthResponse,
    BatchRequest,
    BatchResponse,
    SessionResponse,
    ErrorResponse,
    ExtractedIntelligence,
    EngagementInfo,
    MessageEntry,
    ResponseMetadata,
    HealthDependencies,
    BatchResultItem,
)
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["honeypot"])


@router.post("/honeypot/engage", response_model=EngageResponse)
async def engage_honeypot(request: EngageRequest) -> EngageResponse:
    """
    Detect scam messages and engage scammers with AI personas to extract intelligence.
    
    This is the primary endpoint for the ScamShield AI system. It:
    1. Analyzes the incoming message for scam indicators
    2. If scam detected, engages using an appropriate persona
    3. Extracts financial intelligence from the conversation
    4. Returns structured response with engagement and intelligence data
    
    Args:
        request: EngageRequest containing the message and optional session info
        
    Returns:
        EngageResponse with detection results, engagement, and extracted intelligence
        
    Raises:
        HTTPException: For validation errors or internal failures
    """
    start_time = time.time()
    
    try:
        # Import required modules
        from app.models.detector import ScamDetector, get_detector
        from app.models.language import detect_language
        from app.models.extractor import extract_intelligence
        from app.agent.honeypot import HoneypotAgent
        from app.agent.personas import select_persona
        from app.database.redis_client import (
            get_session_state_with_fallback,
            save_session_state_with_fallback,
        )
        
        # Generate session ID if not provided
        session_id = request.session_id or str(uuid.uuid4())
        
        # Detect language if auto
        if request.language == "auto":
            detected_language, _ = detect_language(request.message)
        else:
            detected_language = request.language
        
        # Retrieve existing session state if session_id was provided
        session_state = None
        is_ongoing_scam_session = False
        if request.session_id:
            session_state = get_session_state_with_fallback(request.session_id)
            # Check if this is an ongoing scam conversation
            if session_state and session_state.get("turn_count", 0) > 0:
                is_ongoing_scam_session = True
                logger.info(f"Continuing existing scam session {session_id}, turn={session_state.get('turn_count', 0)}")
        
        # Run scam detection
        detector = get_detector()
        detection_result = detector.detect(request.message, detected_language)
        
        scam_detected = detection_result.get("scam_detected", False)
        confidence = detection_result.get("confidence", 0.0)
        
        # Calculate processing time so far
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # If not a scam AND not part of an ongoing scam conversation, return simple response
        if not scam_detected and not is_ongoing_scam_session:
            logger.info(f"No scam detected for session {session_id}, confidence={confidence:.2f}")
            
            return EngageResponse(
                status="success",
                scam_detected=False,
                confidence=confidence,
                language_detected=detected_language,
                session_id=session_id,
                message="No scam detected. Message appears legitimate.",
                metadata=ResponseMetadata(
                    processing_time_ms=processing_time_ms,
                    model_version="1.0.0",
                    detection_model="indic-bert",
                    engagement_model=None,
                ),
            )
        
        # Scam detected OR continuing an ongoing scam conversation - engage with honeypot agent
        if is_ongoing_scam_session:
            logger.info(f"Continuing scam conversation for session {session_id}")
            # Use the higher confidence from detection or existing session
            existing_confidence = session_state.get("scam_confidence", 0.0)
            confidence = max(confidence, existing_confidence)
            scam_detected = True  # It's a scam conversation
        else:
            logger.info(f"Scam detected for session {session_id}, confidence={confidence:.2f}")
        
        # Create honeypot agent and engage
        agent = HoneypotAgent()
        
        # Engage the agent
        result = agent.engage(request.message, session_state)
        
        # Extract intelligence from conversation
        full_text = " ".join(msg.get("message", "") for msg in result.get("messages", []))
        intel, extraction_confidence = extract_intelligence(full_text)
        
        # Update result with extracted intelligence
        result["extracted_intel"] = intel
        result["extraction_confidence"] = extraction_confidence
        result["scam_confidence"] = confidence
        
        # Save session state to Redis (with in-memory fallback)
        save_session_state_with_fallback(session_id, result)
        
        # Save conversation to PostgreSQL (optional, graceful degradation)
        try:
            from app.database.postgres import save_conversation
            
            conversation_data = {
                "language": detected_language,
                "persona": result.get("persona"),
                "scam_confidence": confidence,
                "turn_count": result.get("turn_count", 1),
                "messages": result.get("messages", []),
                "extracted_intel": intel,
                "extraction_confidence": extraction_confidence,
            }
            
            conversation_id = save_conversation(session_id, conversation_data)
            if conversation_id > 0:
                logger.debug(f"Conversation saved to PostgreSQL: id={conversation_id}")
        except Exception as e:
            # PostgreSQL save failed, but continue - Redis already saved the session
            logger.warning(f"Failed to save conversation to PostgreSQL: {e}")
            logger.info("Session state saved to Redis, continuing without PostgreSQL persistence")
        
        # Build conversation history for response
        conversation_history = [
            MessageEntry(
                turn=msg.get("turn", 0),
                sender=msg.get("sender", "unknown"),
                message=msg.get("message", ""),
                timestamp=msg.get("timestamp", datetime.utcnow().isoformat() + "Z"),
            )
            for msg in result.get("messages", [])
        ]
        
        # Get the agent's response (last message from agent)
        agent_messages = [m for m in result.get("messages", []) if m.get("sender") == "agent"]
        agent_response = agent_messages[-1]["message"] if agent_messages else "Engaged with scammer."
        
        # Build engagement info
        turn_count = result.get("turn_count", 1)
        max_turns = settings.MAX_TURNS
        
        engagement = EngagementInfo(
            agent_response=agent_response[:500],  # Limit to 500 chars
            turn_count=turn_count,
            max_turns_reached=turn_count >= max_turns,
            strategy=result.get("strategy", "build_trust"),
            persona=result.get("persona"),
        )
        
        # Build extracted intelligence
        extracted_intelligence = ExtractedIntelligence(
            upi_ids=intel.get("upi_ids", []),
            bank_accounts=intel.get("bank_accounts", []),
            ifsc_codes=intel.get("ifsc_codes", []),
            phone_numbers=intel.get("phone_numbers", []),
            phishing_links=intel.get("phishing_links", []),
            extraction_confidence=extraction_confidence,
        )
        
        # Calculate final processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"Engagement complete for session {session_id}: "
            f"turn={turn_count}, strategy={engagement.strategy}, "
            f"intel_count={len(intel.get('upi_ids', [])) + len(intel.get('phone_numbers', []))}"
        )
        
        return EngageResponse(
            status="success",
            scam_detected=True,
            confidence=confidence,
            language_detected=detected_language,
            session_id=session_id,
            engagement=engagement,
            extracted_intelligence=extracted_intelligence,
            conversation_history=conversation_history,
            metadata=ResponseMetadata(
                processing_time_ms=processing_time_ms,
                model_version="1.0.0",
                detection_model="indic-bert",
                engagement_model="groq-llama-3.1-70b",
            ),
        )
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(
            status_code=400,
            detail={
                "code": "VALIDATION_ERROR",
                "message": str(e),
            },
        )
    except Exception as e:
        logger.error(f"Error processing engage request: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "An error occurred while processing your request",
                "details": str(e) if settings.DEBUG else None,
            },
        )


@router.get("/honeypot/session/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str) -> SessionResponse:
    """
    Retrieve complete conversation history for a session.
    
    Args:
        session_id: UUID of the session to retrieve
        
    Returns:
        SessionResponse with conversation history and extracted intelligence
        
    Raises:
        HTTPException: 404 if session not found, 400 if invalid session ID
    """
    # Validate session_id format
    try:
        uuid.UUID(session_id)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_SESSION_ID",
                "message": "Session ID format invalid. Must be a valid UUID.",
            },
        )
    
    try:
        from app.database.redis_client import get_session_state_with_fallback
        from app.database.postgres import get_conversation
        
        # Try Redis first (active sessions)
        session_state = get_session_state_with_fallback(session_id)
        
        if session_state:
            # Build response from Redis session state
            messages = session_state.get("messages", [])
            conversation_history = [
                MessageEntry(
                    turn=msg.get("turn", 0),
                    sender=msg.get("sender", "unknown"),
                    message=msg.get("message", ""),
                    timestamp=msg.get("timestamp", datetime.utcnow().isoformat() + "Z"),
                )
                for msg in messages
            ]
            
            intel = session_state.get("extracted_intel", {})
            extracted_intelligence = ExtractedIntelligence(
                upi_ids=intel.get("upi_ids", []),
                bank_accounts=intel.get("bank_accounts", []),
                ifsc_codes=intel.get("ifsc_codes", []),
                phone_numbers=intel.get("phone_numbers", []),
                phishing_links=intel.get("phishing_links", []),
                extraction_confidence=session_state.get("extraction_confidence", 0.0),
            )
            
            # Get timestamps from first and last messages
            created_at = messages[0].get("timestamp") if messages else datetime.utcnow().isoformat() + "Z"
            updated_at = messages[-1].get("timestamp") if messages else datetime.utcnow().isoformat() + "Z"
            
            return SessionResponse(
                session_id=session_id,
                language=session_state.get("language", "en"),
                persona=session_state.get("persona"),
                scam_confidence=session_state.get("scam_confidence", 0.0),
                turn_count=session_state.get("turn_count", 0),
                conversation_history=conversation_history,
                extracted_intelligence=extracted_intelligence,
                created_at=created_at,
                updated_at=updated_at,
            )
        
        # Try PostgreSQL for archived sessions
        conversation = get_conversation(session_id)
        
        if conversation:
            messages = conversation.get("messages", [])
            conversation_history = [
                MessageEntry(
                    turn=msg.get("turn", 0),
                    sender=msg.get("sender", "unknown"),
                    message=msg.get("message", ""),
                    timestamp=msg.get("timestamp", datetime.utcnow().isoformat() + "Z"),
                )
                for msg in messages
            ]
            
            intel = conversation.get("extracted_intel", {})
            extracted_intelligence = ExtractedIntelligence(
                upi_ids=intel.get("upi_ids", []),
                bank_accounts=intel.get("bank_accounts", []),
                ifsc_codes=intel.get("ifsc_codes", []),
                phone_numbers=intel.get("phone_numbers", []),
                phishing_links=intel.get("phishing_links", []),
                extraction_confidence=conversation.get("extraction_confidence", 0.0),
            )
            
            return SessionResponse(
                session_id=session_id,
                language=conversation.get("language", "en"),
                persona=conversation.get("persona"),
                scam_confidence=conversation.get("scam_confidence", 0.0),
                turn_count=conversation.get("turn_count", 0),
                conversation_history=conversation_history,
                extracted_intelligence=extracted_intelligence,
                created_at=conversation.get("created_at", datetime.utcnow().isoformat() + "Z"),
                updated_at=conversation.get("updated_at", datetime.utcnow().isoformat() + "Z"),
            )
        
        # Session not found in either Redis or PostgreSQL
        raise HTTPException(
            status_code=404,
            detail={
                "code": "SESSION_NOT_FOUND",
                "message": "No conversation found for the provided session ID",
                "session_id": session_id,
            },
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving session {session_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "INTERNAL_ERROR",
                "message": "An error occurred while retrieving the session",
            },
        )


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Service health check for monitoring and load balancing.
    
    Returns:
        HealthResponse with service status and dependency health
    """
    from app.main import get_uptime_seconds
    
    # Check dependency health
    groq_status = "online"
    postgres_status = "offline"
    redis_status = "offline"
    models_loaded = False
    
    # Check Redis
    try:
        from app.database.redis_client import health_check as redis_health
        redis_status = "online" if redis_health() else "offline"
    except Exception as e:
        logger.warning(f"Redis health check failed: {e}")
        redis_status = "offline"
    
    # Check PostgreSQL
    try:
        from app.database.postgres import verify_schema
        postgres_status = "online" if verify_schema() else "degraded"
    except Exception as e:
        logger.warning(f"PostgreSQL health check failed: {e}")
        postgres_status = "offline"
    
    # Check Groq API (just check if API key is configured)
    try:
        groq_status = "online" if settings.GROQ_API_KEY else "not_configured"
    except Exception:
        groq_status = "unknown"
    
    # Check if models are loaded
    try:
        from app.models.detector import get_detector
        detector = get_detector()
        models_loaded = detector is not None
    except Exception:
        models_loaded = False
    
    # Determine overall status
    if redis_status == "offline" and postgres_status == "offline":
        overall_status = "unhealthy"
    elif redis_status == "offline" or postgres_status == "offline":
        overall_status = "degraded"
    else:
        overall_status = "healthy"
    
    return HealthResponse(
        status=overall_status,
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat() + "Z",
        dependencies=HealthDependencies(
            groq_api=groq_status,
            postgres=postgres_status,
            redis=redis_status,
            models_loaded=models_loaded,
        ),
        uptime_seconds=get_uptime_seconds(),
    )


@router.post("/honeypot/batch", response_model=BatchResponse)
async def batch_process(request: BatchRequest) -> BatchResponse:
    """
    Process multiple messages in batch mode.
    
    Args:
        request: BatchRequest containing array of messages to process
        
    Returns:
        BatchResponse with processing results for each message
    """
    start_time = time.time()
    
    try:
        from app.models.detector import get_detector
        from app.models.language import detect_language
        
        detector = get_detector()
        results: List[BatchResultItem] = []
        failed_count = 0
        
        for msg_item in request.messages:
            try:
                # Detect language
                if msg_item.language == "auto":
                    detected_language, _ = detect_language(msg_item.message)
                else:
                    detected_language = msg_item.language
                
                # Run scam detection
                detection_result = detector.detect(msg_item.message, detected_language)
                
                results.append(
                    BatchResultItem(
                        id=msg_item.id,
                        status="success",
                        scam_detected=detection_result.get("scam_detected", False),
                        confidence=detection_result.get("confidence", 0.0),
                        language_detected=detected_language,
                    )
                )
                
            except Exception as e:
                logger.warning(f"Batch item {msg_item.id} failed: {e}")
                failed_count += 1
                results.append(
                    BatchResultItem(
                        id=msg_item.id,
                        status="error",
                        error={
                            "code": "PROCESSING_ERROR",
                            "message": str(e),
                        },
                    )
                )
        
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        return BatchResponse(
            status="success" if failed_count == 0 else "partial",
            processed=len(results) - failed_count,
            failed=failed_count,
            results=results,
            processing_time_ms=processing_time_ms,
        )
        
    except Exception as e:
        logger.error(f"Batch processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={
                "code": "BATCH_PROCESSING_ERROR",
                "message": "Failed to process batch request",
            },
        )

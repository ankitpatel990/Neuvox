"""
GUVI Hackathon Final Result Callback Module.

Implements the mandatory callback to GUVI's evaluation endpoint
as specified in the problem statement.

Requirement: "Once the system detects scam intent and the AI Agent
completes the engagement, participants must send the final extracted
intelligence to the GUVI evaluation endpoint."

Callback Endpoint: POST https://hackathon.guvi.in/api/updateHoneyPotFinalResult
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Default GUVI callback URL
DEFAULT_GUVI_CALLBACK_URL = "https://hackathon.guvi.in/api/updateHoneyPotFinalResult"


def generate_agent_notes(
    messages: List[Dict],
    extracted_intel: Dict,
    scam_indicators: List[str],
) -> str:
    """
    Generate a summary of scammer behavior for agent notes.
    
    Analyzes the conversation and extracted intelligence to create
    a human-readable summary of the scammer's tactics.
    
    Args:
        messages: List of conversation messages
        extracted_intel: Extracted intelligence dictionary
        scam_indicators: List of detected scam indicators/keywords
        
    Returns:
        Agent notes string summarizing scammer behavior
    """
    notes_parts = []
    
    # Analyze scammer messages for tactics
    scammer_messages = [m.get("message", "") for m in messages if m.get("sender") == "scammer"]
    full_scammer_text = " ".join(scammer_messages).lower()
    
    # Check for urgency tactics
    urgency_words = ["urgent", "immediately", "now", "today", "hurry", "quick", "fast", "expire", "last chance"]
    if any(word in full_scammer_text for word in urgency_words):
        notes_parts.append("Scammer used urgency tactics")
    
    # Check for authority impersonation
    authority_words = ["police", "court", "government", "bank official", "rbi", "investigation", "arrest", "legal"]
    if any(word in full_scammer_text for word in authority_words):
        notes_parts.append("attempted authority impersonation")
    
    # Check for prize/lottery scam
    prize_words = ["won", "winner", "prize", "lottery", "jackpot", "lucky", "congratulations", "reward"]
    if any(word in full_scammer_text for word in prize_words):
        notes_parts.append("used prize/lottery lure")
    
    # Check for payment redirection attempts
    payment_words = ["upi", "transfer", "send money", "pay", "account number", "bank details"]
    if any(word in full_scammer_text for word in payment_words):
        notes_parts.append("attempted payment redirection")
    
    # Check for OTP/credential harvesting
    credential_words = ["otp", "password", "pin", "cvv", "verify", "confirm"]
    if any(word in full_scammer_text for word in credential_words):
        notes_parts.append("attempted credential harvesting")
    
    # Check for threat tactics
    threat_words = ["block", "suspend", "deactivate", "arrest", "fine", "penalty", "legal action"]
    if any(word in full_scammer_text for word in threat_words):
        notes_parts.append("used threat/fear tactics")
    
    # Add intelligence summary
    intel_items = []
    if extracted_intel.get("upi_ids"):
        intel_items.append(f"{len(extracted_intel['upi_ids'])} UPI ID(s)")
    if extracted_intel.get("phone_numbers"):
        intel_items.append(f"{len(extracted_intel['phone_numbers'])} phone number(s)")
    if extracted_intel.get("bank_accounts"):
        intel_items.append(f"{len(extracted_intel['bank_accounts'])} bank account(s)")
    if extracted_intel.get("phishing_links"):
        intel_items.append(f"{len(extracted_intel['phishing_links'])} phishing link(s)")
    
    if intel_items:
        notes_parts.append(f"Extracted: {', '.join(intel_items)}")
    
    # Build final notes
    if notes_parts:
        return ". ".join(notes_parts) + "."
    else:
        return "Scam engagement completed. Limited intelligence extracted."


def extract_suspicious_keywords(
    messages: List[Dict],
    scam_indicators: List[str],
) -> List[str]:
    """
    Extract suspicious keywords from the conversation.
    
    Args:
        messages: List of conversation messages
        scam_indicators: List of detected scam indicators from detector
        
    Returns:
        List of suspicious keywords found in messages
    """
    # Base keywords from detector
    keywords = set(scam_indicators) if scam_indicators else set()
    
    # Additional suspicious keyword patterns to check
    suspicious_patterns = [
        "urgent", "immediately", "now", "today", "hurry",
        "won", "winner", "prize", "lottery", "jackpot",
        "otp", "verify", "confirm", "blocked", "suspended",
        "police", "arrest", "court", "legal", "investigation",
        "transfer", "send money", "pay now", "account blocked",
        "free", "gift", "reward", "selected", "lucky",
        "click here", "call now", "limited time",
    ]
    
    # Check scammer messages for keywords
    scammer_messages = [m.get("message", "") for m in messages if m.get("sender") == "scammer"]
    full_text = " ".join(scammer_messages).lower()
    
    for pattern in suspicious_patterns:
        if pattern in full_text:
            keywords.add(pattern)
    
    return list(keywords)[:20]  # Limit to 20 keywords


def send_final_result_to_guvi(
    session_id: str,
    scam_detected: bool,
    total_messages: int,
    extracted_intel: Dict,
    messages: List[Dict],
    scam_indicators: List[str] = None,
    agent_notes: str = None,
) -> bool:
    """
    Send final result to GUVI evaluation endpoint.
    
    This is MANDATORY for the hackathon submission. The platform uses
    this data to measure engagement depth, intelligence quality, and
    agent effectiveness.
    
    Args:
        session_id: Unique session ID for the conversation
        scam_detected: Whether scam intent was confirmed
        total_messages: Total number of messages exchanged
        extracted_intel: Dictionary of extracted intelligence
        messages: Full conversation history
        scam_indicators: Optional list of detected scam indicators
        agent_notes: Optional pre-generated agent notes
        
    Returns:
        True if callback was successful, False otherwise
    """
    # Check if callback is enabled
    if not settings.GUVI_CALLBACK_ENABLED:
        logger.info("GUVI callback disabled, skipping")
        return True
    
    # Get callback URL from settings or use default
    callback_url = settings.GUVI_CALLBACK_URL or DEFAULT_GUVI_CALLBACK_URL
    
    # Generate suspicious keywords
    suspicious_keywords = extract_suspicious_keywords(
        messages,
        scam_indicators or [],
    )
    
    # Generate agent notes if not provided
    if not agent_notes:
        agent_notes = generate_agent_notes(
            messages,
            extracted_intel,
            scam_indicators or [],
        )
    
    # Build payload in GUVI's expected format (camelCase)
    payload = {
        "sessionId": session_id,
        "scamDetected": scam_detected,
        "totalMessagesExchanged": total_messages,
        "extractedIntelligence": {
            "bankAccounts": extracted_intel.get("bank_accounts", []),
            "upiIds": extracted_intel.get("upi_ids", []),
            "phishingLinks": extracted_intel.get("phishing_links", []),
            "phoneNumbers": extracted_intel.get("phone_numbers", []),
            "suspiciousKeywords": suspicious_keywords,
        },
        "agentNotes": agent_notes,
    }
    
    logger.info(f"Sending GUVI callback for session {session_id}")
    logger.debug(f"GUVI callback payload: {payload}")
    
    try:
        response = requests.post(
            callback_url,
            json=payload,
            timeout=10,
            headers={
                "Content-Type": "application/json",
            },
        )
        
        if response.status_code == 200:
            logger.info(f"GUVI callback successful for session {session_id}")
            return True
        else:
            logger.warning(
                f"GUVI callback returned status {response.status_code}: {response.text}"
            )
            return False
            
    except requests.exceptions.Timeout:
        logger.error(f"GUVI callback timed out for session {session_id}")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"GUVI callback failed for session {session_id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in GUVI callback: {e}")
        return False


def should_send_callback(
    turn_count: int,
    max_turns_reached: bool,
    extraction_confidence: float,
    terminated: bool,
) -> bool:
    """
    Determine if GUVI callback should be sent based on conversation state.
    
    Callback should be sent when:
    - Max turns (20) is reached
    - High extraction confidence (>= 0.85) achieved
    - Session is explicitly terminated
    
    Args:
        turn_count: Current turn count
        max_turns_reached: Whether max turns limit was hit
        extraction_confidence: Confidence in extracted intelligence
        terminated: Whether session is terminated
        
    Returns:
        True if callback should be sent
    """
    # Send if max turns reached
    if max_turns_reached or turn_count >= 20:
        logger.info(f"Callback trigger: max turns reached ({turn_count})")
        return True
    
    # Send if high extraction confidence
    if extraction_confidence >= 0.85:
        logger.info(f"Callback trigger: high extraction confidence ({extraction_confidence:.2f})")
        return True
    
    # Send if explicitly terminated
    if terminated:
        logger.info("Callback trigger: session terminated")
        return True
    
    return False

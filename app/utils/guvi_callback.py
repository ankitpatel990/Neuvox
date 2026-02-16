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
    Generate a detailed summary of scammer behavior for agent notes.

    Produces a law-enforcement-friendly summary covering:
    - Identified scam type
    - Tactics used (urgency, threats, impersonation, etc.)
    - Extracted intelligence summary
    - Conversation depth

    Args:
        messages: List of conversation messages
        extracted_intel: Extracted intelligence dictionary
        scam_indicators: List of detected scam indicators/keywords

    Returns:
        Agent notes string summarizing scammer behavior
    """
    notes_parts: List[str] = []

    scammer_messages = [
        m.get("message", "") for m in messages if m.get("sender") == "scammer"
    ]
    full_scammer_text = " ".join(scammer_messages).lower()
    full_scammer_raw = " ".join(scammer_messages)

    # ---- Scam type identification ----
    scam_type = _identify_scam_type(full_scammer_text, full_scammer_raw)
    if scam_type:
        notes_parts.append(f"Scam type: {scam_type}")

    # ---- Tactic detection ----
    urgency_words = [
        "urgent", "immediately", "now", "today", "hurry", "quick",
        "fast", "expire", "last chance", "turant", "jaldi", "abhi",
        "\u0924\u0941\u0930\u0902\u0924", "\u091c\u0932\u094d\u0926\u0940",
    ]
    if any(w in full_scammer_text or w in full_scammer_raw for w in urgency_words):
        notes_parts.append("Used urgency tactics to pressure victim")

    authority_words = [
        "police", "court", "government", "bank official", "rbi",
        "investigation", "arrest", "legal", "warrant", "department",
        "\u092a\u0941\u0932\u093f\u0938",
        "\u0917\u093f\u0930\u092b\u094d\u0924\u093e\u0930",
    ]
    if any(w in full_scammer_text or w in full_scammer_raw for w in authority_words):
        notes_parts.append("Attempted authority/official impersonation")

    prize_words = [
        "won", "winner", "prize", "lottery", "jackpot", "lucky",
        "congratulations", "reward", "jeeta", "jeet", "inaam",
        "\u091c\u0940\u0924\u093e", "\u0907\u0928\u093e\u092e",
    ]
    if any(w in full_scammer_text or w in full_scammer_raw for w in prize_words):
        notes_parts.append("Used prize/lottery lure")

    payment_words = [
        "upi", "transfer", "send money", "pay", "account number",
        "bank details", "paise bhejo", "transfer karo",
        "\u092a\u0948\u0938\u0947 \u092d\u0947\u091c\u094b",
    ]
    if any(w in full_scammer_text or w in full_scammer_raw for w in payment_words):
        notes_parts.append("Attempted payment/money redirection")

    credential_words = [
        "otp", "password", "pin", "cvv", "verify", "confirm",
        "otp bhejo", "verify karo", "\u0913\u091f\u0940\u092a\u0940",
    ]
    if any(w in full_scammer_text or w in full_scammer_raw for w in credential_words):
        notes_parts.append("Attempted OTP/credential harvesting")

    threat_words = [
        "block", "suspend", "deactivate", "arrest", "fine",
        "penalty", "legal action", "case file", "fir",
        "\u092c\u094d\u0932\u0949\u0915", "\u092c\u0902\u0926",
    ]
    if any(w in full_scammer_text or w in full_scammer_raw for w in threat_words):
        notes_parts.append("Used threat/fear tactics")

    kyc_words = ["kyc", "aadhaar", "pan card", "pan number", "link expired", "update kyc"]
    if any(w in full_scammer_text for w in kyc_words):
        notes_parts.append("Used KYC/document verification lure")

    loan_words = ["loan approved", "pre-approved", "emi", "interest rate", "loan offer"]
    if any(w in full_scammer_text for w in loan_words):
        notes_parts.append("Used fake loan/credit offer")

    delivery_words = ["delivery failed", "customs", "parcel", "courier", "shipment"]
    if any(w in full_scammer_text for w in delivery_words):
        notes_parts.append("Used fake delivery/parcel scam")

    # ---- Intelligence summary ----
    intel_items: List[str] = []
    if extracted_intel.get("upi_ids"):
        items = extracted_intel["upi_ids"]
        intel_items.append(f"{len(items)} UPI ID(s): {', '.join(items[:3])}")
    if extracted_intel.get("bank_accounts"):
        items = extracted_intel["bank_accounts"]
        intel_items.append(f"{len(items)} bank account(s)")
    if extracted_intel.get("ifsc_codes"):
        items = extracted_intel["ifsc_codes"]
        intel_items.append(f"{len(items)} IFSC code(s): {', '.join(items[:3])}")
    if extracted_intel.get("phone_numbers"):
        items = extracted_intel["phone_numbers"]
        intel_items.append(f"{len(items)} phone number(s): {', '.join(items[:3])}")
    if extracted_intel.get("phishing_links"):
        items = extracted_intel["phishing_links"]
        intel_items.append(f"{len(items)} phishing link(s)")
    if extracted_intel.get("email_addresses"):
        items = extracted_intel["email_addresses"]
        intel_items.append(f"{len(items)} email address(es): {', '.join(items[:3])}")

    if intel_items:
        notes_parts.append(f"Extracted intelligence: {'; '.join(intel_items)}")

    # ---- Conversation depth ----
    total_turns = len(scammer_messages)
    if total_turns > 0:
        notes_parts.append(f"Conversation depth: {total_turns} scammer message(s) analyzed")

    if notes_parts:
        return ". ".join(notes_parts) + "."
    return "Scam engagement completed. Limited intelligence extracted."


def _identify_scam_type(text_lower: str, text_raw: str) -> Optional[str]:
    """
    Identify the primary scam type from scammer text.

    Returns a human-readable scam type label or None if unknown.
    """
    # Order matters: more specific checks first
    if any(w in text_lower for w in ["kyc", "aadhaar", "pan card", "update kyc"]):
        return "KYC/Document Verification Fraud"
    if any(w in text_lower for w in ["loan approved", "pre-approved", "emi", "loan offer"]):
        return "Fake Loan/Credit Offer"
    if any(w in text_lower for w in ["delivery failed", "customs", "parcel", "courier"]):
        return "Fake Delivery/Parcel Scam"
    if any(w in text_lower for w in ["won", "winner", "prize", "lottery", "jackpot"]):
        return "Prize/Lottery Scam"
    if any(w in text_lower for w in [
        "police", "arrest", "warrant", "court", "legal action", "investigation",
        "\u092a\u0941\u0932\u093f\u0938", "\u0917\u093f\u0930\u092b\u094d\u0924\u093e\u0930",
    ]) or any(w in text_raw for w in [
        "\u092a\u0941\u0932\u093f\u0938", "\u0917\u093f\u0930\u092b\u094d\u0924\u093e\u0930",
    ]):
        return "Authority/Police Impersonation"
    if any(w in text_lower for w in [
        "bank official", "rbi", "bank manager", "account blocked", "account suspended",
    ]):
        return "Bank Official Impersonation"
    if any(w in text_lower for w in ["otp", "password", "pin", "cvv"]):
        return "Credential/OTP Harvesting"
    if any(w in text_lower for w in ["refund", "cashback", "insurance claim"]):
        return "Refund/Insurance Scam"
    if any(w in text_lower for w in ["investment", "returns", "crypto", "trading", "profit"]):
        return "Investment/Trading Scam"
    if any(w in text_lower for w in ["upi", "send money", "transfer", "pay"]):
        return "Payment Redirection Fraud"
    return None


def extract_suspicious_keywords(
    messages: List[Dict],
    scam_indicators: List[str],
) -> List[str]:
    """
    Extract suspicious keywords from the conversation.

    Checks scammer messages for English, Hindi, and Hinglish scam keywords
    so that multilingual conversations produce meaningful keyword lists.

    Args:
        messages: List of conversation messages
        scam_indicators: List of detected scam indicators from detector

    Returns:
        List of suspicious keywords found in messages (up to 25)
    """
    keywords = set(scam_indicators) if scam_indicators else set()

    # English suspicious patterns
    en_patterns = [
        "urgent", "immediately", "now", "today", "hurry", "fast", "quick",
        "won", "winner", "prize", "lottery", "jackpot", "congratulations",
        "otp", "verify", "confirm", "blocked", "suspended", "deactivated",
        "police", "arrest", "court", "legal", "investigation", "warrant",
        "transfer", "send money", "pay now", "account blocked",
        "free", "gift", "reward", "selected", "lucky",
        "click here", "call now", "limited time", "expire",
        "kyc", "aadhaar", "pan card", "link expired",
        "upi", "bank account", "ifsc", "cvv", "pin",
        "loan approved", "credit card", "insurance", "refund",
        "delivery failed", "customs", "parcel",
    ]

    # Hindi / Hinglish suspicious patterns
    hi_patterns = [
        "turant", "jaldi", "abhi",
        "jeeta", "jeet", "inaam", "lottery",
        "otp bhejo", "verify karo", "confirm karo",
        "block", "suspend", "band",
        "police", "giraftaar", "giraftari", "court", "kanoon",
        "paise bhejo", "transfer karo", "pay karo",
        "muft", "free", "gift",
        "link pe click", "call karo",
        "kyc update", "aadhaar", "pan",
        "loan", "insurance", "refund",
        # Devanagari
        "\u0924\u0941\u0930\u0902\u0924",           # turant
        "\u091c\u0932\u094d\u0926\u0940",           # jaldi
        "\u0905\u092d\u0940",                       # abhi
        "\u091c\u0940\u0924\u093e",                 # jeeta
        "\u0907\u0928\u093e\u092e",                 # inaam
        "\u0932\u0949\u091f\u0930\u0940",           # lottery
        "\u092a\u0941\u0932\u093f\u0938",           # police
        "\u0917\u093f\u0930\u092b\u094d\u0924\u093e\u0930", # giraftaar
        "\u092a\u0948\u0938\u0947 \u092d\u0947\u091c\u094b", # paise bhejo
        "\u091f\u094d\u0930\u093e\u0902\u0938\u092b\u0930",  # transfer
        "\u092c\u094d\u0932\u0949\u0915",           # block
        "\u092c\u0948\u0902\u0915",                 # bank
        "\u0916\u093e\u0924\u093e",                 # khaata
        "\u092f\u0942\u092a\u0940\u0906\u0908",     # UPI
        "\u0913\u091f\u0940\u092a\u0940",           # OTP
    ]

    scammer_messages = [
        m.get("message", "") for m in messages if m.get("sender") == "scammer"
    ]
    full_text = " ".join(scammer_messages).lower()

    for pattern in en_patterns:
        if pattern in full_text:
            keywords.add(pattern)

    # Hindi patterns need original-case text for Devanagari matching
    full_text_raw = " ".join(scammer_messages)
    for pattern in hi_patterns:
        if pattern.lower() in full_text or pattern in full_text_raw:
            keywords.add(pattern)

    return sorted(keywords)[:25]


def send_final_result_to_guvi(
    session_id: str,
    scam_detected: bool,
    total_messages: int,
    extracted_intel: Dict,
    messages: List[Dict],
    scam_indicators: List[str] = None,
    agent_notes: str = None,
    engagement_duration_seconds: int = 0,
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
        engagement_duration_seconds: Duration of engagement in seconds
        
    Returns:
        True if callback was successful, False otherwise
    """
    if not settings.GUVI_CALLBACK_ENABLED:
        logger.info("GUVI callback disabled, skipping")
        return True
    
    callback_url = settings.GUVI_CALLBACK_URL or DEFAULT_GUVI_CALLBACK_URL
    
    suspicious_keywords = extract_suspicious_keywords(
        messages,
        scam_indicators or [],
    )
    
    if not agent_notes:
        agent_notes = generate_agent_notes(
            messages,
            extracted_intel,
            scam_indicators or [],
        )
    
    # Build payload in GUVI's expected format (camelCase)
    payload = {
        "sessionId": session_id,
        "status": "success",
        "scamDetected": scam_detected,
        "totalMessagesExchanged": total_messages,
        "extractedIntelligence": {
            "bankAccounts": extracted_intel.get("bank_accounts", []),
            "upiIds": extracted_intel.get("upi_ids", []),
            "phishingLinks": extracted_intel.get("phishing_links", []),
            "phoneNumbers": extracted_intel.get("phone_numbers", []),
            "emailAddresses": extracted_intel.get("email_addresses", []),
            "suspiciousKeywords": suspicious_keywords,
        },
        "engagementMetrics": {
            "engagementDurationSeconds": engagement_duration_seconds,
            "totalMessagesExchanged": total_messages,
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

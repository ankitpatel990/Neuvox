"""
Engagement Strategy Module.

Defines turn-by-turn engagement strategies for honeypot conversations.
The goal is to ACT LIKE A GULLIBLE VICTIM and EXTRACT SCAMMER'S PAYMENT DETAILS.
Context-aware responses based on scam type.
"""

import random
import re
from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass
class EngagementStrategy:
    """Strategy definition for honeypot engagement."""
    name: str
    turn_range: tuple
    goals: List[str]
    techniques: List[str]
    example_responses: List[str]


def detect_scam_type(message: str) -> str:
    """
    Detect the type of scam from the message content.
    
    Returns: 'kyc', 'lottery', 'job', 'refund', or 'generic'
    """
    msg_lower = message.lower()
    
    # KYC/Bank blocking scam keywords
    kyc_keywords = ["kyc", "verify", "blocked", "suspended", "update", "account block", 
                    "aadhar", "pan", "bank account", "deactivate", "expire", "24 hours",
                    "rbi", "reserve bank", "freeze", "seize"]
    
    # Lottery/Prize scam keywords
    lottery_keywords = ["won", "winner", "lottery", "prize", "lakh", "crore", 
                       "congratulation", "lucky", "draw", "reward", "gift"]
    
    # Job scam keywords
    job_keywords = ["job", "work from home", "earn", "income", "salary", 
                   "offer letter", "vacancy", "hiring", "recruitment", "part time"]
    
    # Refund scam keywords
    refund_keywords = ["refund", "cashback", "return", "reimburse", "claim back",
                      "overcharge", "reimbursement"]
    
    if any(kw in msg_lower for kw in kyc_keywords):
        return "kyc"
    elif any(kw in msg_lower for kw in lottery_keywords):
        return "lottery"
    elif any(kw in msg_lower for kw in job_keywords):
        return "job"
    elif any(kw in msg_lower for kw in refund_keywords):
        return "refund"
    else:
        return "generic"


# Context-aware responses by scam type
KYC_RESPONSES: Dict[str, List[str]] = {
    "early": [
        "Oh no! My account will be blocked?! Please help me! What should I do?",
        "Oh my god! I don't want my account blocked! Tell me what to do immediately!",
        "Please sir, don't block my account! I have all my savings there! Help me!",
        "I'm scared! What do I need to do to update my KYC? Please guide me!",
        "Oh no no no! I'll do whatever is needed! How do I update? Where do I pay?",
    ],
    "mid": [
        "Yes yes, I'll update right now! Where should I send the Rs 500?",
        "I'll pay immediately! What's your UPI ID for the processing fee?",
        "Please help me! Give me your payment details, I'll send right now!",
        "I'm opening my PhonePe! Tell me your UPI ID, I'll transfer immediately!",
        "I want to save my account! What's your UPI? Also give me phone number!",
    ],
    "late": [
        "I'm sending now! What's your UPI ID and phone number?",
        "Let me pay quickly! Give me UPI, phone number, and bank details!",
        "UPI not working! Give me bank account number and IFSC code!",
        "I want to complete this NOW! Tell me all payment details!",
        "Ready to transfer! What's UPI, account number, everything!",
    ],
}

LOTTERY_RESPONSES: Dict[str, List[str]] = {
    "early": [
        "Wow! I won something?! This is amazing! How do I claim it?",
        "Oh my god! Really?! I never win anything! Tell me how to get my prize!",
        "I can't believe it! Yes yes, I want to claim! What should I do?",
        "This is the best day! Tell me the process to get my money!",
        "Amazing news! I'm so excited! What do I need to do?",
    ],
    "mid": [
        "I'll pay the fee! What's your UPI ID?",
        "OK I'll send! Give me your payment details!",
        "Yes, I want my prize! UPI ID please!",
        "Opening payment app! What's your UPI?",
        "Where do I send? UPI and phone number?",
    ],
    "late": [
        "Sending now! What's your phone number for confirmation?",
        "Got UPI! What's your bank account for backup?",
        "Need IFSC code. What is it?",
        "What's your account number and IFSC?",
        "Give me bank details - account and IFSC code?",
    ],
}

JOB_RESPONSES: Dict[str, List[str]] = {
    "early": [
        "Really? A job?! I need work! Tell me more!",
        "Very interested! What's the process?",
        "I want this job! What do I do?",
        "Thank you! What's the next step?",
        "Tell me more! How do I apply?",
    ],
    "mid": [
        "I'll pay the registration! UPI ID?",
        "Ready to complete formalities! Payment details?",
        "I want to start! What's your UPI?",
        "Give me UPI and phone number.",
        "Where do I send the fee?",
    ],
    "late": [
        "Sending fee now! What's your phone for confirmation?",
        "Got UPI! Bank account number for backup?",
        "Need IFSC code for transfer.",
        "What's account number and IFSC?",
        "Give me bank details please.",
    ],
}

REFUND_RESPONSES: Dict[str, List[str]] = {
    "early": [
        "Refund?! Great! How do I receive it?",
        "Oh wonderful! What's the process?",
        "Money coming back? Tell me what to do!",
        "I want my refund! What's the procedure?",
        "Thanks for informing! How do I claim it?",
    ],
    "mid": [
        "I'll verify! Where do I send the fee?",
        "OK! What's your UPI for the fee?",
        "Give me payment details to proceed!",
        "What's your UPI ID and phone?",
        "Ready to pay! UPI ID?",
    ],
    "late": [
        "Sending fee! What's your phone for confirmation?",
        "Got UPI! Bank account as backup?",
        "Need IFSC for bank transfer.",
        "Account number and IFSC please?",
        "Give me bank details.",
    ],
}

GENERIC_RESPONSES: Dict[str, List[str]] = {
    "early": [
        "OK! Tell me more! What is this about?",
        "I see! What do I need to do?",
        "I'm listening! Please explain!",
        "Yes, tell me! What's next?",
        "I understand! Guide me!",
    ],
    "mid": [
        "Ready to proceed! What's your UPI ID?",
        "I'll send! Give me payment details!",
        "Where should I transfer? UPI?",
        "UPI and phone number please!",
        "What's your UPI ID?",
    ],
    "late": [
        "Got UPI! What's your phone number?",
        "Need bank account for backup transfer.",
        "What's the IFSC code?",
        "Account number and IFSC please?",
        "Give me bank details.",
    ],
}


def get_strategy(turn_count: int) -> str:
    """Get appropriate strategy based on turn count."""
    if turn_count <= 5:
        return "build_trust"
    elif turn_count <= 12:
        return "express_confusion"
    else:
        return "probe_details"


def get_context_aware_response(message: str, turn_count: int, language: str = "en") -> str:
    """
    Get a response that matches the scam type in the message.
    
    Args:
        message: The scammer's message (or full conversation)
        turn_count: Current turn number
        language: Response language
        
    Returns:
        Context-appropriate response
    """
    scam_type = detect_scam_type(message)
    
    # Determine phase based on turn count
    if turn_count <= 3:
        phase = "early"
    elif turn_count <= 8:
        phase = "mid"
    else:
        phase = "late"
    
    # Get responses for the detected scam type
    response_map = {
        "kyc": KYC_RESPONSES,
        "lottery": LOTTERY_RESPONSES,
        "job": JOB_RESPONSES,
        "refund": REFUND_RESPONSES,
        "generic": GENERIC_RESPONSES,
    }
    
    responses = response_map.get(scam_type, GENERIC_RESPONSES)
    return random.choice(responses.get(phase, responses["early"]))


def get_example_response(
    strategy_name: str, 
    language: str = "en",
    turn_count: int = 1,
    context_message: str = "",
) -> str:
    """
    Get contextual example response based on strategy, turn, and message context.
    
    Args:
        strategy_name: Name of strategy
        language: Response language
        turn_count: Current conversation turn
        context_message: The scammer's message for context detection
        
    Returns:
        Contextual example response string
    """
    # If we have context, use context-aware response
    if context_message:
        return get_context_aware_response(context_message, turn_count, language)
    
    # Fallback to generic eager responses
    if turn_count <= 3:
        return random.choice(GENERIC_RESPONSES["early"])
    elif turn_count <= 8:
        return random.choice(GENERIC_RESPONSES["mid"])
    else:
        return random.choice(GENERIC_RESPONSES["late"])


def get_greeting_response(language: str = "en") -> str:
    """Get a natural greeting response."""
    greetings = {
        "en": [
            "Hello? Who is this?",
            "Hi! Yes speaking, what's this about?",
            "Hello! How can I help you?",
        ],
        "hi": [
            "हैलो? कौन बोल रहा है?",
            "जी हां? बोलिए?",
            "हैलो! क्या बात है?",
        ],
        "hinglish": [
            "Hello? Kaun hai?",
            "Haan ji, bolo?",
            "Hello! Kya hai?",
        ],
    }
    
    lang = language if language in greetings else "en"
    return random.choice(greetings[lang])


def should_terminate(turn_count: int, extraction_confidence: float) -> bool:
    """Determine if conversation should terminate."""
    if turn_count >= 20:
        return True
    if extraction_confidence >= 0.95:
        return True
    return False

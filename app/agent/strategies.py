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
        "I'm ready to pay the fee! Just tell me where - what's your UPI ID?",
        "Okay okay! I'll send the processing fee! Give me your payment details!",
        "Yes, I want my prize! Tell me your UPI, I'll send right now!",
        "I'm opening my app! What's your UPI ID? I'll transfer immediately!",
        "Tell me where to send! UPI ID and phone number please!",
    ],
    "late": [
        "I'm trying to send but need your details! UPI ID and phone number please!",
        "Let me complete this! Give me UPI, phone number, and bank account!",
        "UPI failed! What's your bank account number and IFSC code?",
        "Tell me everything - UPI ID, bank account, IFSC - I'll send today!",
        "I'm ready! Give me all your details so I can get my prize!",
    ],
}

JOB_RESPONSES: Dict[str, List[str]] = {
    "early": [
        "Really? A job opportunity?! I really need work! Tell me more!",
        "I'm very interested! What do I need to do to start?",
        "This sounds perfect for me! What's the process to join?",
        "I want this job! Please tell me all the details!",
        "Thank you so much! I'll do whatever is needed! What's next?",
    ],
    "mid": [
        "I'm ready to pay the registration fee! Where should I send it?",
        "Yes, I'll complete the formalities! What's your UPI ID?",
        "I want to start immediately! Give me your payment details!",
        "Tell me your UPI and phone number, I'll send the fee now!",
        "I'll pay right away! What's the account details for the fee?",
    ],
    "late": [
        "I'm sending the fee now! What's your UPI ID and phone number?",
        "Let me pay! Give me UPI, phone, and bank account details!",
        "UPI not working! Give me bank account and IFSC code!",
        "I want to join quickly! Tell me all payment options!",
        "Ready to transfer! What's everything - UPI, bank, phone?",
    ],
}

REFUND_RESPONSES: Dict[str, List[str]] = {
    "early": [
        "I'm getting a refund?! That's great! How do I receive it?",
        "Oh wonderful! I forgot about that! What do I need to do?",
        "Really? Money coming back to me? Tell me the process!",
        "Yes yes, I want my refund! What should I do to get it?",
        "Thank you for informing me! How do I claim this refund?",
    ],
    "mid": [
        "I'll verify right away! Where should I send the processing fee?",
        "Okay I understand! What's your UPI for the verification fee?",
        "I want my refund! Tell me your payment details to proceed!",
        "Let me complete this! Give me your UPI ID and phone number!",
        "I'm ready to pay the fee! What's your UPI?",
    ],
    "late": [
        "I'm sending the verification fee! What's your UPI and phone?",
        "Let me pay now! Give me UPI, phone number, and bank account!",
        "UPI failed! What's your bank account number and IFSC?",
        "I want my refund! Tell me all your payment details!",
        "Ready to complete! What's UPI, account, IFSC, phone?",
    ],
}

GENERIC_RESPONSES: Dict[str, List[str]] = {
    "early": [
        "Oh okay! Tell me more! What is this about?",
        "I see! What do I need to do?",
        "Okay, I'm listening! Please explain!",
        "Yes yes, tell me! What should I do?",
        "I understand! Guide me please!",
    ],
    "mid": [
        "I'm ready to proceed! What's your UPI ID?",
        "Okay, I'll send the money! Give me your payment details!",
        "Yes, I want to do this! Where should I transfer?",
        "Tell me your UPI and phone number, I'll send!",
        "I'm opening my app! What's the UPI ID?",
    ],
    "late": [
        "I'm trying to send! What's your UPI ID and phone number?",
        "Let me complete this! Give me UPI, phone, and bank account!",
        "UPI failed! What's your bank account and IFSC?",
        "Tell me all details - UPI, bank, IFSC, phone!",
        "I'm ready! Give me all payment details!",
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

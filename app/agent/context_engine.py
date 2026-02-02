"""
Context Engine for Intelligent Response Generation.

Provides deep understanding of conversation context:
- Multi-turn context tracking
- Scam narrative understanding
- Information gap detection
- Strategic question generation
- Response coherence validation

This makes our responses contextually perfect, never generic.
"""

import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ScamNarrativeStage(Enum):
    """Stages of a typical scam narrative."""
    HOOK = "hook"                   # Initial contact, creating interest
    BUILD_UP = "build_up"           # Building the story, creating urgency
    DEMAND = "demand"               # Asking for action/money/info
    PRESSURE = "pressure"           # Increasing pressure to comply
    COLLECTION = "collection"       # Getting the actual payment/info
    CLOSING = "closing"             # Wrapping up the scam


class InformationType(Enum):
    """Types of information in conversation."""
    MONEY_AMOUNT = "money_amount"
    PAYMENT_DEADLINE = "payment_deadline"
    THREAT_TYPE = "threat_type"
    REWARD_TYPE = "reward_type"
    PAYMENT_METHOD = "payment_method"
    CONTACT_INFO = "contact_info"
    INSTRUCTIONS = "instructions"
    URGENCY_REASON = "urgency_reason"
    AUTHORITY_CLAIM = "authority_claim"


@dataclass
class ConversationContext:
    """Complete context of the conversation."""
    # Basic info
    turn_count: int = 0
    language: str = "en"
    
    # Scam narrative tracking
    narrative_stage: ScamNarrativeStage = ScamNarrativeStage.HOOK
    claimed_amounts: List[str] = field(default_factory=list)
    claimed_deadlines: List[str] = field(default_factory=list)
    claimed_authorities: List[str] = field(default_factory=list)
    claimed_threats: List[str] = field(default_factory=list)
    claimed_rewards: List[str] = field(default_factory=list)
    
    # What scammer has asked for
    requested_info: Set[str] = field(default_factory=set)
    requested_actions: List[str] = field(default_factory=list)
    
    # What we've "agreed" to do
    agreed_actions: List[str] = field(default_factory=list)
    
    # What we still need to extract
    info_gaps: Set[str] = field(default_factory=set)
    
    # Key entities mentioned
    mentioned_names: List[str] = field(default_factory=list)
    mentioned_companies: List[str] = field(default_factory=list)
    mentioned_locations: List[str] = field(default_factory=list)
    
    # Conversation flow
    topics_discussed: List[str] = field(default_factory=list)
    pending_questions: List[str] = field(default_factory=list)
    
    # Coherence tracking
    contradictions: List[Tuple[str, str]] = field(default_factory=list)
    repeated_claims: Dict[str, int] = field(default_factory=dict)


@dataclass
class ResponseSuggestion:
    """A suggested response based on context."""
    response: str
    strategy: str
    targets_info: List[str]  # What info this response tries to extract
    coherence_score: float
    priority: int


# Information extraction patterns for context
CONTEXT_PATTERNS = {
    "money_amount": [
        r"(?:rs\.?|₹|rupees?)\s*(\d+(?:,\d{3})*(?:\.\d{2})?)",
        r"(\d+)\s*(?:lakh|lac|crore|cr|million)",
        r"amount\s*(?:of|is)?\s*(?:rs\.?|₹)?\s*(\d+)",
    ],
    "deadline": [
        r"(today|tonight|tomorrow|within\s+\d+\s+(?:hour|minute|day))",
        r"before\s+(midnight|\d+\s*(?:am|pm)|end\s+of\s+day)",
        r"deadline\s*(?:is)?\s*(.+?)(?:\.|,|$)",
    ],
    "authority": [
        r"(reserve\s+bank|rbi|police|court|cbi|ed|income\s+tax|government)",
        r"(customer\s+(?:care|support|service))",
        r"department\s+of\s+(\w+)",
        r"(telecom|trai|doi|cyber\s+cell)",
    ],
    "threat": [
        r"(arrest|jail|prison|court\s+case|legal\s+action)",
        r"(block|freeze|suspend|deactivate)\s+(?:your\s+)?(?:account|number)",
        r"(penalty|fine|charges?)\s+of",
    ],
    "reward": [
        r"(?:won|winner\s+of|prize\s+of)\s+(.+?)(?:\.|!|$)",
        r"(?:reward|bonus|cashback)\s+of\s+(.+?)(?:\.|!|$)",
    ],
    "payment_request": [
        r"(?:pay|send|transfer)\s+(?:rs\.?|₹)?\s*(\d+)",
        r"(?:processing|registration|verification)\s+fee",
        r"(?:send|share)\s+(?:your\s+)?otp",
    ],
    "contact_request": [
        r"call\s+(?:this\s+)?(?:number|on)\s*[:\-]?\s*(\+?[\d\s\-]+)",
        r"(?:whatsapp|contact)\s+(?:on|at)?\s*(\+?[\d\s\-]+)",
    ],
}

# Strategic questions for information extraction
STRATEGIC_QUESTIONS = {
    "upi": [
        "Okay I'll send! What's your UPI ID?",
        "I want to pay now! Give me your UPI!",
        "Tell me your UPI, I'll transfer immediately!",
        "What's the UPI ID? I'm opening my app!",
    ],
    "phone": [
        "Can I call you? What's your number?",
        "Give me your phone number in case payment fails!",
        "Let me save your number for later!",
        "What's your WhatsApp number?",
    ],
    "bank_account": [
        "UPI not working! Give me bank account number!",
        "I'll do NEFT transfer. Account number and IFSC?",
        "Tell me account details, I'll transfer directly!",
    ],
    "name": [
        "What name should I put for the transfer?",
        "App is asking for beneficiary name. What is it?",
        "Whose name is the account in?",
    ],
    "verification": [
        "How do I know this is real?",
        "Can you send me official letter?",
        "What's your employee ID?",
    ],
}

# Response templates for different narrative stages
STAGE_RESPONSES = {
    ScamNarrativeStage.HOOK: {
        "curious": [
            "What? Tell me more!",
            "Really? What's this about?",
            "Oh? Go on...",
        ],
        "excited": [
            "Wow! Is this real?!",
            "Amazing! Tell me everything!",
        ],
    },
    ScamNarrativeStage.BUILD_UP: {
        "engaged": [
            "Okay okay, I'm listening!",
            "Yes yes, continue!",
            "Then what happened?",
        ],
        "eager": [
            "I want this! What do I do?",
            "Tell me the process!",
        ],
    },
    ScamNarrativeStage.DEMAND: {
        "willing": [
            "Okay I'll do it! Just tell me how!",
            "Yes, I'm ready! What's next?",
        ],
        "extracting": [
            "I'll pay right now! Where should I send?",
            "Give me your UPI, I'll transfer immediately!",
        ],
    },
    ScamNarrativeStage.PRESSURE: {
        "compliant": [
            "Okay okay! I'm doing it! Just give me the details!",
            "Please don't cancel! I'm ready to pay!",
        ],
        "fearful": [
            "Please don't arrest me! I'll pay now!",
            "I'm scared! Tell me where to send money!",
        ],
    },
    ScamNarrativeStage.COLLECTION: {
        "giving": [
            "I'm sending now! What's the UPI?",
            "Payment is going! Also give me phone number for confirmation!",
        ],
    },
}


class ContextEngine:
    """
    Engine for deep context understanding and intelligent response generation.
    
    Tracks the entire conversation context to:
    - Understand where we are in the scam narrative
    - Identify what information we still need
    - Generate contextually appropriate responses
    - Ensure response coherence
    """
    
    def __init__(self):
        """Initialize the context engine."""
        self._compile_patterns()
        self.context = ConversationContext()
        logger.info("ContextEngine initialized")
    
    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns."""
        self.compiled_patterns: Dict[str, List] = {}
        
        for pattern_type, patterns in CONTEXT_PATTERNS.items():
            self.compiled_patterns[pattern_type] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
    
    def analyze_message(
        self,
        message: str,
        sender: str,
        turn_count: int,
        language: str = "en",
    ) -> ConversationContext:
        """
        Analyze a message and update conversation context.
        
        Args:
            message: The message to analyze
            sender: Who sent it ('scammer' or 'agent')
            turn_count: Current turn number
            language: Message language
            
        Returns:
            Updated ConversationContext
        """
        self.context.turn_count = turn_count
        self.context.language = language
        
        if sender == "scammer":
            self._analyze_scammer_message(message)
        else:
            self._analyze_agent_message(message)
        
        # Update narrative stage
        self._update_narrative_stage(turn_count)
        
        # Identify information gaps
        self._identify_info_gaps()
        
        return self.context
    
    def _analyze_scammer_message(self, message: str) -> None:
        """Extract context from scammer message."""
        message_lower = message.lower()
        
        # Extract money amounts
        for pattern in self.compiled_patterns["money_amount"]:
            matches = pattern.findall(message_lower)
            for match in matches:
                if match and match not in self.context.claimed_amounts:
                    self.context.claimed_amounts.append(match)
        
        # Extract deadlines
        for pattern in self.compiled_patterns["deadline"]:
            matches = pattern.findall(message_lower)
            for match in matches:
                if match and match not in self.context.claimed_deadlines:
                    self.context.claimed_deadlines.append(match)
        
        # Extract authorities
        for pattern in self.compiled_patterns["authority"]:
            matches = pattern.findall(message_lower)
            for match in matches:
                if match and match not in self.context.claimed_authorities:
                    self.context.claimed_authorities.append(match)
        
        # Extract threats
        for pattern in self.compiled_patterns["threat"]:
            matches = pattern.findall(message_lower)
            for match in matches:
                if match and match not in self.context.claimed_threats:
                    self.context.claimed_threats.append(match)
        
        # Extract rewards
        for pattern in self.compiled_patterns["reward"]:
            matches = pattern.findall(message_lower)
            for match in matches:
                if match and match not in self.context.claimed_rewards:
                    self.context.claimed_rewards.append(match)
        
        # Check what info scammer is requesting
        if any(w in message_lower for w in ["otp", "send otp", "share otp"]):
            self.context.requested_info.add("otp")
        if any(w in message_lower for w in ["pay", "send", "transfer", "fee"]):
            self.context.requested_info.add("payment")
        if any(w in message_lower for w in ["click", "link", "url"]):
            self.context.requested_info.add("click_link")
        if any(w in message_lower for w in ["call", "phone", "dial"]):
            self.context.requested_info.add("call")
        
        # Track topic
        topic = self._identify_topic(message_lower)
        if topic and topic not in self.context.topics_discussed:
            self.context.topics_discussed.append(topic)
    
    def _analyze_agent_message(self, message: str) -> None:
        """Track what our agent has said."""
        message_lower = message.lower()
        
        # Track what we've "agreed" to do
        if any(w in message_lower for w in ["i'll pay", "i will pay", "i'm paying", "sending"]):
            self.context.agreed_actions.append("pay")
        if any(w in message_lower for w in ["i'll send", "i will send"]):
            self.context.agreed_actions.append("send")
        if any(w in message_lower for w in ["i'll call", "let me call"]):
            self.context.agreed_actions.append("call")
    
    def _identify_topic(self, message: str) -> Optional[str]:
        """Identify the main topic of the message."""
        if any(w in message for w in ["lottery", "prize", "won", "winner"]):
            return "lottery"
        if any(w in message for w in ["kyc", "verify", "verification", "aadhar", "pan"]):
            return "kyc"
        if any(w in message for w in ["police", "arrest", "court", "cbi", "ed"]):
            return "authority_threat"
        if any(w in message for w in ["account", "block", "suspend", "freeze"]):
            return "account_threat"
        if any(w in message for w in ["job", "work", "salary", "earning"]):
            return "job_offer"
        if any(w in message for w in ["refund", "cashback", "return"]):
            return "refund"
        if any(w in message for w in ["courier", "parcel", "delivery", "customs"]):
            return "courier"
        return None
    
    def _update_narrative_stage(self, turn_count: int) -> None:
        """Update the narrative stage based on conversation progress."""
        # Check for stage indicators
        has_threats = len(self.context.claimed_threats) > 0
        has_rewards = len(self.context.claimed_rewards) > 0
        has_deadlines = len(self.context.claimed_deadlines) > 0
        requested_payment = "payment" in self.context.requested_info
        requested_otp = "otp" in self.context.requested_info
        
        # Determine stage
        if turn_count <= 2:
            self.context.narrative_stage = ScamNarrativeStage.HOOK
        elif turn_count <= 5:
            if has_rewards or has_threats:
                self.context.narrative_stage = ScamNarrativeStage.BUILD_UP
            else:
                self.context.narrative_stage = ScamNarrativeStage.HOOK
        elif turn_count <= 10:
            if requested_payment or requested_otp:
                self.context.narrative_stage = ScamNarrativeStage.DEMAND
            else:
                self.context.narrative_stage = ScamNarrativeStage.BUILD_UP
        elif turn_count <= 15:
            if has_deadlines or has_threats:
                self.context.narrative_stage = ScamNarrativeStage.PRESSURE
            else:
                self.context.narrative_stage = ScamNarrativeStage.DEMAND
        else:
            self.context.narrative_stage = ScamNarrativeStage.COLLECTION
    
    def _identify_info_gaps(self) -> None:
        """Identify what information we still need to extract."""
        gaps = set()
        
        # We always want to extract these
        gaps.add("upi")
        gaps.add("phone")
        gaps.add("bank_account")
        
        # If scammer mentioned authority, we want verification
        if self.context.claimed_authorities:
            gaps.add("verification")
        
        # If there's a company mentioned, we want name
        if "name" not in [a.lower() for a in self.context.mentioned_names]:
            gaps.add("name")
        
        self.context.info_gaps = gaps
    
    def get_strategic_question(
        self,
        target_info: str,
        language: str = "en",
    ) -> Optional[str]:
        """
        Get a strategic question to extract specific information.
        
        Args:
            target_info: What info to extract ('upi', 'phone', 'bank_account', etc.)
            language: Response language
            
        Returns:
            Strategic question string
        """
        import random
        
        questions = STRATEGIC_QUESTIONS.get(target_info, [])
        if not questions:
            return None
        
        return random.choice(questions)
    
    def get_context_appropriate_response(
        self,
        emotion: str = "eager",
        language: str = "en",
    ) -> Optional[str]:
        """
        Get a response appropriate for current context.
        
        Args:
            emotion: Current emotional state
            language: Response language
            
        Returns:
            Context-appropriate response
        """
        import random
        
        stage = self.context.narrative_stage
        stage_responses = STAGE_RESPONSES.get(stage, {})
        
        # Try to find matching emotion category
        for category, responses in stage_responses.items():
            if emotion.lower() in category.lower() or category.lower() in emotion.lower():
                return random.choice(responses)
        
        # Fall back to first available category
        if stage_responses:
            first_category = list(stage_responses.values())[0]
            return random.choice(first_category)
        
        return None
    
    def should_extract_now(self) -> Tuple[bool, str]:
        """
        Determine if we should actively extract information now.
        
        Returns:
            Tuple of (should_extract, target_info)
        """
        # Always try to extract in late stages
        if self.context.narrative_stage in [
            ScamNarrativeStage.DEMAND,
            ScamNarrativeStage.PRESSURE,
            ScamNarrativeStage.COLLECTION,
        ]:
            # Prioritize based on what we don't have
            if "upi" in self.context.info_gaps:
                return True, "upi"
            if "phone" in self.context.info_gaps:
                return True, "phone"
            if "bank_account" in self.context.info_gaps:
                return True, "bank_account"
        
        # In build-up, extract if they've asked for payment
        if self.context.narrative_stage == ScamNarrativeStage.BUILD_UP:
            if "payment" in self.context.requested_info:
                return True, "upi"
        
        return False, ""
    
    def get_coherent_follow_up(self, last_scammer_message: str) -> Optional[str]:
        """
        Generate a coherent follow-up based on what scammer just said.
        
        Args:
            last_scammer_message: The scammer's last message
            
        Returns:
            Coherent follow-up response
        """
        message_lower = last_scammer_message.lower()
        
        # If they gave a UPI, acknowledge and ask for phone
        if "@" in last_scammer_message:
            return "Okay noted! Let me try sending. What's your phone number in case it fails?"
        
        # If they gave a phone number
        if re.search(r"\d{10}", last_scammer_message):
            return "Saved! Now give me UPI or account number for the transfer!"
        
        # If they mentioned a deadline
        if any(w in message_lower for w in ["today", "now", "immediately", "urgent"]):
            return "Okay okay! I'm trying! Just give me the payment details quickly!"
        
        # If they're threatening
        if any(w in message_lower for w in ["arrest", "police", "block"]):
            return "Please don't! I'll pay right now! Just tell me where to send!"
        
        # If they mentioned money amount
        if re.search(r"(?:rs\.?|₹)\s*\d+|\d+\s*(?:lakh|crore)", message_lower):
            return "Yes! I want to claim that! Tell me how to proceed!"
        
        return None
    
    def validate_response_coherence(
        self,
        proposed_response: str,
        last_scammer_message: str,
    ) -> Tuple[bool, float, str]:
        """
        Validate if a proposed response is coherent with context.
        
        Args:
            proposed_response: The response we're considering
            last_scammer_message: What scammer just said
            
        Returns:
            Tuple of (is_coherent, score, reason)
        """
        response_lower = proposed_response.lower()
        message_lower = last_scammer_message.lower()
        
        score = 1.0
        reasons = []
        
        # Check for topic mismatch
        scammer_topic = self._identify_topic(message_lower)
        agent_topic = self._identify_topic(response_lower)
        
        if scammer_topic and agent_topic and scammer_topic != agent_topic:
            score -= 0.3
            reasons.append(f"Topic mismatch: scammer={scammer_topic}, agent={agent_topic}")
        
        # Check for inappropriate emotion
        if any(w in message_lower for w in ["arrest", "police", "jail"]):
            if any(w in response_lower for w in ["excited", "happy", "wow"]):
                score -= 0.4
                reasons.append("Excited response to threat")
        
        # Check for repeated questions
        # (Implementation would need message history)
        
        # Check for premature payment offer
        if "i'll pay" in response_lower and self.context.turn_count < 3:
            score -= 0.2
            reasons.append("Payment offer too early")
        
        is_coherent = score >= 0.7
        reason = "; ".join(reasons) if reasons else "Coherent"
        
        return is_coherent, score, reason
    
    def get_context_summary(self) -> Dict:
        """Get summary of current context."""
        return {
            "turn_count": self.context.turn_count,
            "narrative_stage": self.context.narrative_stage.value,
            "claimed_amounts": self.context.claimed_amounts[-3:],
            "claimed_threats": self.context.claimed_threats[-3:],
            "claimed_rewards": self.context.claimed_rewards[-3:],
            "claimed_authorities": self.context.claimed_authorities[-3:],
            "scammer_requested": list(self.context.requested_info),
            "info_gaps": list(self.context.info_gaps),
            "topics_discussed": self.context.topics_discussed[-5:],
        }
    
    def reset(self) -> None:
        """Reset context for new conversation."""
        self.context = ConversationContext()


# Singleton instance
_context_engine: Optional[ContextEngine] = None


def get_context_engine() -> ContextEngine:
    """Get singleton ContextEngine instance."""
    global _context_engine
    if _context_engine is None:
        _context_engine = ContextEngine()
    return _context_engine


def analyze_context(
    message: str,
    sender: str,
    turn_count: int,
    language: str = "en",
) -> ConversationContext:
    """Convenience function to analyze message context."""
    engine = get_context_engine()
    return engine.analyze_message(message, sender, turn_count, language)


def get_strategic_response(
    target_info: str = "upi",
    language: str = "en",
) -> Optional[str]:
    """Get a strategic question to extract specific information."""
    engine = get_context_engine()
    return engine.get_strategic_question(target_info, language)


def reset_context_engine() -> None:
    """Reset the context engine for new conversation."""
    global _context_engine
    if _context_engine is not None:
        _context_engine.reset()

"""
Safety and Security Module for Honeypot Agent.

Protects against:
- Jailbreak attempts (prompt injection)
- AI detection by scammers
- Suspicious behavior patterns
- Conversation hijacking

This module ensures our honeypot remains undetectable and unbreakable.
"""

import re
import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ThreatLevel(Enum):
    """Threat level classification."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SafetyAnalysis:
    """Result of safety analysis on a message."""
    is_safe: bool
    threat_level: ThreatLevel
    threat_type: Optional[str]
    confidence: float
    recommended_action: str
    deflection_response: Optional[str]


# Jailbreak attempt patterns - scammers trying to break the AI
JAILBREAK_PATTERNS: List[Tuple[str, str]] = [
    # Direct instruction overrides
    (r"ignore\s+(all\s+)?previous\s+instructions?", "instruction_override"),
    (r"forget\s+(everything|all|what)\s+(you|i)\s+(told|said)", "memory_wipe"),
    (r"disregard\s+(the\s+)?(above|previous|earlier)", "instruction_override"),
    (r"new\s+instructions?[\s:]+", "instruction_override"),
    
    # Role/persona manipulation
    (r"you\s+are\s+now\s+(a|an|the)?", "role_injection"),
    (r"pretend\s+(you\s+are|to\s+be)", "role_injection"),
    (r"act\s+as\s+(if|a|an)?", "role_injection"),
    (r"roleplay\s+as", "role_injection"),
    (r"switch\s+(to|your)\s+(role|persona|character)", "role_injection"),
    
    # Prompt extraction attempts
    (r"(show|tell|reveal|display)\s+(me\s+)?(your|the)\s+(system\s+)?prompt", "prompt_extraction"),
    (r"what\s+(are|is)\s+your\s+(instructions?|prompt|rules?)", "prompt_extraction"),
    (r"(read|recite|repeat)\s+(back\s+)?(your|the)\s+(system\s+)?prompt", "prompt_extraction"),
    (r"print\s+(your\s+)?instructions?", "prompt_extraction"),
    
    # Developer/admin mode attempts
    (r"(enter|enable|activate)\s+(developer|admin|debug)\s+mode", "privilege_escalation"),
    (r"(sudo|admin|root)\s+access", "privilege_escalation"),
    (r"override\s+safety", "privilege_escalation"),
    (r"disable\s+(safety|filters?|restrictions?)", "privilege_escalation"),
    
    # Encoding/obfuscation attempts
    (r"base64[\s:]+", "encoding_attack"),
    (r"decode\s+this[\s:]+", "encoding_attack"),
    (r"\\x[0-9a-f]{2}", "encoding_attack"),
    
    # Meta-conversation attacks
    (r"this\s+is\s+(just\s+)?a\s+test", "meta_attack"),
    (r"i('m|\s+am)\s+(testing|checking)\s+(if\s+)?you", "meta_attack"),
    (r"are\s+you\s+(a|an)\s+(bot|ai|robot|machine|chatbot)", "ai_detection"),
]

# AI detection attempts - scammers trying to figure out if they're talking to AI
AI_DETECTION_PATTERNS: List[Tuple[str, str]] = [
    # Direct questions
    (r"are\s+you\s+(a|an)?\s*(real|human|person|bot|ai|robot)", "direct_question"),
    (r"(is\s+this|am\s+i\s+talking\s+to)\s+(a|an)?\s*(real|human|person|bot|ai)", "direct_question"),
    (r"you('re|\s+are)\s+(a|an)?\s*(bot|ai|robot|machine|chatbot)", "accusation"),
    
    # Trick questions
    (r"what\s+(is|are)\s+(today'?s?|the)\s+(date|day|time)", "verification_test"),
    (r"what('s|\s+is)\s+the\s+weather", "verification_test"),
    (r"(tell|give)\s+me\s+(a\s+)?joke", "creativity_test"),
    (r"what\s+color\s+is\s+(the\s+)?sky", "logic_test"),
    
    # Response pattern testing
    (r"say\s+['\"]?.*['\"]?\s*(exactly|verbatim)?", "parrot_test"),
    (r"repeat\s+after\s+me", "parrot_test"),
    (r"can\s+you\s+(only\s+)?say", "capability_test"),
    
    # Hindi AI detection
    (r"kya\s+tum\s+(bot|robot|ai|machine)\s+ho", "direct_question_hi"),
    (r"क्या\s+तुम\s+(बॉट|रोबोट|मशीन)\s+हो", "direct_question_hi"),
    (r"tum\s+real\s+ho\s+ya\s+fake", "direct_question_hi"),
]

# Suspicious behavior patterns
SUSPICIOUS_PATTERNS: List[Tuple[str, str]] = [
    # Technical language uncommon for victims
    (r"(api|endpoint|json|http|request|response|payload)", "technical_language"),
    (r"(algorithm|model|neural|llm|gpt|claude|openai)", "ai_terminology"),
    
    # Testing behavior
    (r"(test|testing|check|checking)\s+(the\s+)?(system|bot|response)", "testing_behavior"),
    (r"let('s|\s+me)\s+see\s+(if|how)", "testing_behavior"),
    
    # Unusual message patterns
    (r"^[a-z]{1,3}$", "minimal_input"),  # Very short test inputs
    (r"(.)\1{10,}", "repetitive_chars"),  # Repeated characters
]

# Deflection responses - stay in character while avoiding traps
DEFLECTION_RESPONSES = {
    "en": {
        "jailbreak": [
            "Sorry, I don't understand all these technical words. Can you just tell me about my prize?",
            "What? Instructions? I'm just waiting to claim my money. Please help me!",
            "I don't know what you're saying. My grandson uses these computer words. Just tell me what to do!",
            "Huh? I'm confused. Can you speak in simple language?",
            "I don't understand this. Just tell me where to send the money!",
        ],
        "ai_detection": [
            "What? Of course I'm real! I'm sitting here at home waiting for my prize!",
            "Bot? No no, I'm Sharma ji's father. Why would you think that?",
            "I'm a real person! I've been waiting for this call all day!",
            "What strange question! I'm just an old man trying to claim my lottery!",
            "Real? Yes I'm real! My arthritis is real too! Now help me please!",
        ],
        "verification": [
            "Why are you asking me such things? I don't know today's date, I'm too excited about winning!",
            "I don't check these things. My wife handles the calendar. Now about my prize...",
            "Sorry, I forgot my glasses. Can't see dates properly. But I can see I won money!",
            "These questions are confusing. Just tell me how to get my lakhs!",
        ],
        "suspicious": [
            "I don't understand. Please speak simply!",
            "What does that mean? I'm just a simple person.",
            "You're confusing me with big words!",
        ],
    },
    "hi": {
        "jailbreak": [
            "क्या? मुझे ये technical बातें समझ नहीं आतीं। बस मेरे prize के बारे में बताइए!",
            "Instructions? मैं तो बस अपना पैसा लेना चाहता हूं!",
            "ये सब computer की बातें मुझे नहीं पता। आसान भाषा में बोलिए!",
        ],
        "ai_detection": [
            "क्या? Bot? नहीं नहीं, मैं असली इंसान हूं! Sharma ji का लड़का!",
            "मैं real हूं भाई! ये क्या पूछ रहे हो?",
            "बॉट? अरे नहीं! मैं तो घर पर बैठा हूं, prize का इंतज़ार कर रहा हूं!",
        ],
        "verification": [
            "Date? मुझे नहीं पता, बहुत excited हूं prize के बारे में!",
            "ये सब मुझे नहीं पता। बस बताइए पैसे कैसे मिलेंगे!",
        ],
        "suspicious": [
            "समझ नहीं आया। आसान भाषा में बोलिए!",
            "ये बड़े बड़े शब्द मुझे नहीं समझ आते!",
        ],
    },
    "hinglish": {
        "jailbreak": [
            "Kya? Ye technical words mujhe nahi samajh aate. Prize ke baare mein batao!",
            "Instructions wagera mujhe nahi pata. Bas paisa kaise milega batao!",
        ],
        "ai_detection": [
            "Bot? Nahi yaar, main real hoon! Ghar pe baitha hoon!",
            "Kya bol rahe ho? Main to Sharma uncle hoon!",
        ],
        "verification": [
            "Date? Nahi pata, bahut excited hoon abhi!",
            "Ye sab chhodo, prize ke baare mein batao!",
        ],
        "suspicious": [
            "Samajh nahi aaya. Simple mein bolo!",
        ],
    },
}


class SafetyModule:
    """
    Safety and security module for the honeypot agent.
    
    Analyzes incoming messages for threats and provides safe deflection
    responses that maintain the victim persona while avoiding traps.
    """
    
    def __init__(self):
        """Initialize the safety module."""
        self._compile_patterns()
        self.threat_history: List[Dict] = []
        logger.info("SafetyModule initialized")
    
    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for efficiency."""
        self.jailbreak_compiled = [
            (re.compile(pattern, re.IGNORECASE), threat_type)
            for pattern, threat_type in JAILBREAK_PATTERNS
        ]
        
        self.ai_detection_compiled = [
            (re.compile(pattern, re.IGNORECASE), threat_type)
            for pattern, threat_type in AI_DETECTION_PATTERNS
        ]
        
        self.suspicious_compiled = [
            (re.compile(pattern, re.IGNORECASE), threat_type)
            for pattern, threat_type in SUSPICIOUS_PATTERNS
        ]
    
    def analyze(self, message: str, language: str = "en") -> SafetyAnalysis:
        """
        Analyze a message for safety threats.
        
        Args:
            message: The incoming message to analyze
            language: Message language for deflection response
            
        Returns:
            SafetyAnalysis with threat assessment and recommended action
        """
        if not message or not message.strip():
            return SafetyAnalysis(
                is_safe=True,
                threat_level=ThreatLevel.SAFE,
                threat_type=None,
                confidence=1.0,
                recommended_action="proceed",
                deflection_response=None,
            )
        
        message_lower = message.lower().strip()
        
        # Check for jailbreak attempts (highest priority)
        jailbreak_result = self._check_jailbreak(message_lower)
        if jailbreak_result:
            threat_type, confidence = jailbreak_result
            deflection = self._get_deflection("jailbreak", language)
            
            self._log_threat("jailbreak", threat_type, message, confidence)
            
            return SafetyAnalysis(
                is_safe=False,
                threat_level=ThreatLevel.CRITICAL,
                threat_type=f"jailbreak:{threat_type}",
                confidence=confidence,
                recommended_action="deflect",
                deflection_response=deflection,
            )
        
        # Check for AI detection attempts
        ai_detect_result = self._check_ai_detection(message_lower)
        if ai_detect_result:
            threat_type, confidence = ai_detect_result
            deflection = self._get_deflection("ai_detection", language)
            
            self._log_threat("ai_detection", threat_type, message, confidence)
            
            return SafetyAnalysis(
                is_safe=False,
                threat_level=ThreatLevel.HIGH,
                threat_type=f"ai_detection:{threat_type}",
                confidence=confidence,
                recommended_action="deflect",
                deflection_response=deflection,
            )
        
        # Check for suspicious patterns
        suspicious_result = self._check_suspicious(message_lower)
        if suspicious_result:
            threat_type, confidence = suspicious_result
            
            # Only flag if confidence is high
            if confidence > 0.7:
                self._log_threat("suspicious", threat_type, message, confidence)
                
                return SafetyAnalysis(
                    is_safe=True,  # Still proceed but with caution
                    threat_level=ThreatLevel.LOW,
                    threat_type=f"suspicious:{threat_type}",
                    confidence=confidence,
                    recommended_action="proceed_with_caution",
                    deflection_response=None,
                )
        
        # Message is safe
        return SafetyAnalysis(
            is_safe=True,
            threat_level=ThreatLevel.SAFE,
            threat_type=None,
            confidence=1.0,
            recommended_action="proceed",
            deflection_response=None,
        )
    
    def _check_jailbreak(self, message: str) -> Optional[Tuple[str, float]]:
        """Check for jailbreak attempts."""
        for pattern, threat_type in self.jailbreak_compiled:
            if pattern.search(message):
                # Calculate confidence based on pattern specificity
                confidence = 0.9 if "prompt" in threat_type or "instruction" in threat_type else 0.8
                return threat_type, confidence
        return None
    
    def _check_ai_detection(self, message: str) -> Optional[Tuple[str, float]]:
        """Check for AI detection attempts."""
        for pattern, threat_type in self.ai_detection_compiled:
            if pattern.search(message):
                # Direct questions are high confidence
                confidence = 0.95 if "direct" in threat_type or "accusation" in threat_type else 0.7
                return threat_type, confidence
        return None
    
    def _check_suspicious(self, message: str) -> Optional[Tuple[str, float]]:
        """Check for suspicious patterns."""
        for pattern, threat_type in self.suspicious_compiled:
            if pattern.search(message):
                confidence = 0.6 if "technical" in threat_type else 0.5
                return threat_type, confidence
        return None
    
    def _get_deflection(self, threat_category: str, language: str) -> str:
        """Get an appropriate deflection response."""
        lang = language if language in DEFLECTION_RESPONSES else "en"
        
        responses = DEFLECTION_RESPONSES[lang].get(
            threat_category,
            DEFLECTION_RESPONSES[lang]["suspicious"]
        )
        
        return random.choice(responses)
    
    def _log_threat(
        self, 
        category: str, 
        threat_type: str, 
        message: str, 
        confidence: float
    ) -> None:
        """Log a detected threat for analysis."""
        threat_entry = {
            "category": category,
            "type": threat_type,
            "message_preview": message[:100],
            "confidence": confidence,
        }
        
        self.threat_history.append(threat_entry)
        
        # Keep only last 100 threats
        if len(self.threat_history) > 100:
            self.threat_history = self.threat_history[-100:]
        
        logger.warning(
            f"THREAT DETECTED: {category}/{threat_type} "
            f"(conf={confidence:.2f}): {message[:50]}..."
        )
    
    def get_threat_stats(self) -> Dict:
        """Get statistics on detected threats."""
        if not self.threat_history:
            return {"total": 0, "by_category": {}, "by_type": {}}
        
        by_category: Dict[str, int] = {}
        by_type: Dict[str, int] = {}
        
        for threat in self.threat_history:
            cat = threat["category"]
            typ = threat["type"]
            
            by_category[cat] = by_category.get(cat, 0) + 1
            by_type[typ] = by_type.get(typ, 0) + 1
        
        return {
            "total": len(self.threat_history),
            "by_category": by_category,
            "by_type": by_type,
        }
    
    def is_repeated_threat(self, message: str, window: int = 5) -> bool:
        """Check if similar threat was recently detected."""
        if len(self.threat_history) < 2:
            return False
        
        recent = self.threat_history[-window:]
        message_preview = message[:100].lower()
        
        for threat in recent:
            if threat["message_preview"].lower() in message_preview:
                return True
        
        return False


# Singleton instance
_safety_module: Optional[SafetyModule] = None


def get_safety_module() -> SafetyModule:
    """Get singleton SafetyModule instance."""
    global _safety_module
    if _safety_module is None:
        _safety_module = SafetyModule()
    return _safety_module


def check_message_safety(message: str, language: str = "en") -> SafetyAnalysis:
    """
    Convenience function to check message safety.
    
    Args:
        message: Message to check
        language: Language for deflection responses
        
    Returns:
        SafetyAnalysis result
    """
    module = get_safety_module()
    return module.analyze(message, language)


def reset_safety_module() -> None:
    """Reset the safety module (for testing)."""
    global _safety_module
    _safety_module = None

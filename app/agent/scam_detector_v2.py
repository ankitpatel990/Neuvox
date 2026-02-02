"""
Advanced Scam Type Detector v2.

Enhanced scam detection with:
- 15+ scam type classification
- Real-time type updating during conversation
- Confidence-based type switching
- Compound scam detection (multiple types)
- Regional scam pattern recognition

Better scam understanding = better persona matching = longer engagement.
"""

import re
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ScamType(Enum):
    """Comprehensive scam type classification."""
    # Prize/Reward Scams
    LOTTERY = "lottery"
    LUCKY_DRAW = "lucky_draw"
    PRIZE_WINNER = "prize_winner"
    GIFT_CARD = "gift_card"
    
    # Authority Impersonation
    POLICE_THREAT = "police_threat"
    DIGITAL_ARREST = "digital_arrest"
    CBI_ED = "cbi_ed"
    TAX_THREAT = "tax_threat"
    COURT_SUMMONS = "court_summons"
    
    # Financial Scams
    KYC_UPDATE = "kyc_update"
    ACCOUNT_BLOCKED = "account_blocked"
    BANK_VERIFICATION = "bank_verification"
    CREDIT_CARD_FRAUD = "credit_card_fraud"
    LOAN_OFFER = "loan_offer"
    
    # Service Scams
    COURIER_CUSTOMS = "courier_customs"
    TELECOM_DISCONNECT = "telecom_disconnect"
    TECH_SUPPORT = "tech_support"
    
    # Investment Scams
    INVESTMENT_FRAUD = "investment_fraud"
    CRYPTO_SCAM = "crypto_scam"
    TRADING_SCAM = "trading_scam"
    
    # Employment Scams
    JOB_OFFER = "job_offer"
    WORK_FROM_HOME = "work_from_home"
    PART_TIME_JOB = "part_time_job"
    
    # Refund/Cashback Scams
    REFUND_SCAM = "refund_scam"
    CASHBACK_SCAM = "cashback_scam"
    
    # Romance/Social
    ROMANCE_SCAM = "romance_scam"
    CHARITY_SCAM = "charity_scam"
    
    # Unknown/Other
    UNKNOWN = "unknown"


@dataclass
class ScamTypeResult:
    """Result of scam type detection."""
    primary_type: ScamType
    primary_confidence: float
    secondary_types: List[Tuple[ScamType, float]]
    is_compound: bool  # Multiple scam types detected
    keywords_matched: List[str]
    threat_level: str  # low, medium, high, critical
    recommended_persona: str


@dataclass
class ScamTypeHistory:
    """Track scam type detection across conversation."""
    detections: List[Tuple[ScamType, float]] = field(default_factory=list)
    type_changes: int = 0
    stable_type: Optional[ScamType] = None
    compound_detected: bool = False


# Comprehensive scam type patterns
SCAM_TYPE_PATTERNS: Dict[ScamType, Dict] = {
    ScamType.LOTTERY: {
        "keywords_en": [
            "lottery", "won", "winner", "jackpot", "prize money",
            "lucky winner", "congratulations you won", "claim your prize",
        ],
        "keywords_hi": [
            "लॉटरी", "जीत", "विजेता", "इनाम", "पुरस्कार",
        ],
        "patterns": [
            r"(won|winner).{0,30}(lakh|crore|million)",
            r"lottery.{0,20}(winner|prize)",
            r"lucky\s+(draw|winner|number)",
        ],
        "weight": 1.0,
        "persona": "eager",
        "threat_level": "low",
    },
    ScamType.LUCKY_DRAW: {
        "keywords_en": [
            "lucky draw", "spin the wheel", "random selection",
            "selected for", "chosen as winner",
        ],
        "keywords_hi": [
            "लकी ड्रॉ", "भाग्यशाली", "चुने गए",
        ],
        "patterns": [
            r"lucky\s+draw",
            r"(selected|chosen)\s+(for|as)",
        ],
        "weight": 0.9,
        "persona": "eager",
        "threat_level": "low",
    },
    ScamType.POLICE_THREAT: {
        "keywords_en": [
            "police", "arrest", "warrant", "fir", "crime branch",
            "cyber police", "cyber crime", "illegal activity",
        ],
        "keywords_hi": [
            "पुलिस", "गिरफ्तार", "वारंट", "एफआईआर", "अपराध",
        ],
        "patterns": [
            r"(police|cops?)\s+(will\s+)?(arrest|come)",
            r"(arrest|warrant).{0,20}(issued|registered)",
            r"(illegal|criminal)\s+(activity|transaction)",
        ],
        "weight": 1.0,
        "persona": "elderly",
        "threat_level": "high",
    },
    ScamType.DIGITAL_ARREST: {
        "keywords_en": [
            "digital arrest", "online arrest", "video call arrest",
            "stay on video", "don't disconnect", "house arrest",
            "verification call", "interrogation",
        ],
        "keywords_hi": [
            "डिजिटल अरेस्ट", "वीडियो कॉल", "घर पर नजरबंद",
        ],
        "patterns": [
            r"digital\s+arrest",
            r"(stay|remain)\s+(on|in)\s+video",
            r"house\s+arrest",
            r"don'?t\s+(cut|disconnect|hang)",
        ],
        "weight": 1.0,
        "persona": "elderly",
        "threat_level": "critical",
    },
    ScamType.CBI_ED: {
        "keywords_en": [
            "cbi", "ed", "enforcement directorate", "central bureau",
            "investigation", "money laundering", "hawala",
            "narcotics", "drug money",
        ],
        "keywords_hi": [
            "सीबीआई", "ईडी", "प्रवर्तन निदेशालय", "मनी लॉन्ड्रिंग",
        ],
        "patterns": [
            r"\b(cbi|ed)\b",
            r"enforcement\s+directorate",
            r"money\s+laundering",
            r"(hawala|narcotics|drug)",
        ],
        "weight": 1.0,
        "persona": "elderly",
        "threat_level": "critical",
    },
    ScamType.KYC_UPDATE: {
        "keywords_en": [
            "kyc", "know your customer", "update kyc", "kyc verification",
            "aadhar", "pan card", "id verification", "documents pending",
        ],
        "keywords_hi": [
            "केवाईसी", "आधार", "पैन कार्ड", "दस्तावेज",
        ],
        "patterns": [
            r"kyc.{0,10}(update|verify|pending|expired)",
            r"(aadhar|aadhaar|pan).{0,15}(link|verify|update)",
            r"(document|id).{0,10}(verify|upload|submit)",
        ],
        "weight": 1.0,
        "persona": "confused",
        "threat_level": "medium",
    },
    ScamType.ACCOUNT_BLOCKED: {
        "keywords_en": [
            "account blocked", "account suspended", "account frozen",
            "deactivated", "restricted", "will be closed",
            "transaction blocked", "hold on account",
        ],
        "keywords_hi": [
            "खाता ब्लॉक", "खाता बंद", "सस्पेंड", "फ्रीज",
        ],
        "patterns": [
            r"account.{0,10}(block|suspend|freez|deactivat|close)",
            r"(block|suspend|freez).{0,10}(account|number)",
            r"(transaction|access).{0,10}(block|restrict)",
        ],
        "weight": 1.0,
        "persona": "confused",
        "threat_level": "medium",
    },
    ScamType.COURIER_CUSTOMS: {
        "keywords_en": [
            "courier", "parcel", "package", "customs", "delivery",
            "fedex", "dhl", "bluedart", "shipment", "import duty",
            "customs clearance", "held at customs",
        ],
        "keywords_hi": [
            "कूरियर", "पार्सल", "कस्टम्स", "डिलीवरी",
        ],
        "patterns": [
            r"(courier|parcel|package).{0,15}(held|stopped|customs)",
            r"customs.{0,10}(duty|fee|clearance)",
            r"(fedex|dhl|bluedart).{0,15}(delivery|parcel)",
        ],
        "weight": 1.0,
        "persona": "eager",
        "threat_level": "medium",
    },
    ScamType.TELECOM_DISCONNECT: {
        "keywords_en": [
            "telecom", "trai", "sim", "number disconnected",
            "mobile disconnected", "telecom department",
            "illegal sim", "number blocked",
        ],
        "keywords_hi": [
            "टेलीकॉम", "मोबाइल बंद", "सिम ब्लॉक",
        ],
        "patterns": [
            r"(telecom|trai|doi).{0,15}(disconnect|block)",
            r"(sim|number|mobile).{0,10}(disconnect|block|suspend)",
            r"illegal\s+sim",
        ],
        "weight": 1.0,
        "persona": "confused",
        "threat_level": "medium",
    },
    ScamType.JOB_OFFER: {
        "keywords_en": [
            "job", "employment", "hiring", "vacancy", "offer letter",
            "salary", "work from home", "part time", "income",
            "earn from home", "online job",
        ],
        "keywords_hi": [
            "नौकरी", "रोजगार", "वैकेंसी", "सैलरी", "कमाई",
        ],
        "patterns": [
            r"(job|work).{0,15}(offer|opportunity|home)",
            r"earn.{0,10}(from\s+home|online|daily)",
            r"(salary|income).{0,10}(\d+|lakh|thousand)",
        ],
        "weight": 1.0,
        "persona": "eager",
        "threat_level": "low",
    },
    ScamType.REFUND_SCAM: {
        "keywords_en": [
            "refund", "return", "reimburse", "cashback",
            "overpayment", "excess payment", "credit back",
            "money back", "refund processing",
        ],
        "keywords_hi": [
            "रिफंड", "वापसी", "कैशबैक",
        ],
        "patterns": [
            r"refund.{0,15}(pending|process|initiat)",
            r"(over|excess)\s*payment",
            r"money\s+back",
        ],
        "weight": 1.0,
        "persona": "eager",
        "threat_level": "low",
    },
    ScamType.INVESTMENT_FRAUD: {
        "keywords_en": [
            "investment", "mutual fund", "stock", "trading",
            "guaranteed returns", "double your money",
            "high returns", "profit", "earn daily",
        ],
        "keywords_hi": [
            "निवेश", "रिटर्न", "प्रॉफिट", "कमाई",
        ],
        "patterns": [
            r"(invest|trading).{0,15}(profit|return|earn)",
            r"(guaranteed|assured).{0,10}return",
            r"(double|triple).{0,10}money",
        ],
        "weight": 1.0,
        "persona": "eager",
        "threat_level": "medium",
    },
    ScamType.CRYPTO_SCAM: {
        "keywords_en": [
            "crypto", "bitcoin", "ethereum", "blockchain",
            "mining", "crypto investment", "nft", "token",
        ],
        "patterns": [
            r"(crypto|bitcoin|ethereum|nft)",
            r"blockchain.{0,10}(invest|mining)",
        ],
        "weight": 1.0,
        "persona": "eager",
        "threat_level": "medium",
    },
    ScamType.TAX_THREAT: {
        "keywords_en": [
            "income tax", "tax department", "tax notice",
            "tax evasion", "tax pending", "it department",
        ],
        "keywords_hi": [
            "इनकम टैक्स", "टैक्स विभाग", "टैक्स नोटिस",
        ],
        "patterns": [
            r"(income\s+)?tax.{0,10}(department|notice|pending|evasion)",
            r"it\s+department",
        ],
        "weight": 1.0,
        "persona": "elderly",
        "threat_level": "high",
    },
}

# Persona mapping based on scam type
SCAM_PERSONA_MAP: Dict[ScamType, str] = {
    ScamType.LOTTERY: "eager",
    ScamType.LUCKY_DRAW: "eager",
    ScamType.PRIZE_WINNER: "eager",
    ScamType.POLICE_THREAT: "elderly",
    ScamType.DIGITAL_ARREST: "elderly",
    ScamType.CBI_ED: "elderly",
    ScamType.TAX_THREAT: "elderly",
    ScamType.COURT_SUMMONS: "elderly",
    ScamType.KYC_UPDATE: "confused",
    ScamType.ACCOUNT_BLOCKED: "confused",
    ScamType.BANK_VERIFICATION: "confused",
    ScamType.COURIER_CUSTOMS: "eager",
    ScamType.TELECOM_DISCONNECT: "confused",
    ScamType.JOB_OFFER: "eager",
    ScamType.WORK_FROM_HOME: "eager",
    ScamType.REFUND_SCAM: "eager",
    ScamType.INVESTMENT_FRAUD: "eager",
    ScamType.CRYPTO_SCAM: "eager",
    ScamType.UNKNOWN: "confused",
}


class AdvancedScamDetector:
    """
    Advanced scam type detection with 15+ scam categories.
    
    Features:
    - Multi-pattern matching
    - Confidence scoring
    - Compound scam detection
    - Real-time type updating
    - Persona recommendation
    """
    
    def __init__(self):
        """Initialize the advanced scam detector."""
        self._compile_patterns()
        self.history = ScamTypeHistory()
        logger.info("AdvancedScamDetector initialized")
    
    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for all scam types."""
        self.compiled_patterns: Dict[ScamType, List] = {}
        
        for scam_type, config in SCAM_TYPE_PATTERNS.items():
            patterns = config.get("patterns", [])
            self.compiled_patterns[scam_type] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
    
    def detect(
        self,
        message: str,
        conversation_history: Optional[List[Dict]] = None,
    ) -> ScamTypeResult:
        """
        Detect scam type from message.
        
        Args:
            message: The message to analyze
            conversation_history: Optional previous messages for context
            
        Returns:
            ScamTypeResult with detailed classification
        """
        message_lower = message.lower()
        
        # Score each scam type
        type_scores: Dict[ScamType, Tuple[float, List[str]]] = {}
        
        for scam_type, config in SCAM_TYPE_PATTERNS.items():
            score, keywords = self._score_scam_type(message_lower, scam_type, config)
            if score > 0:
                type_scores[scam_type] = (score, keywords)
        
        # If conversation history provided, boost consistent types
        if conversation_history:
            type_scores = self._apply_history_boost(type_scores, conversation_history)
        
        # Sort by score
        sorted_types = sorted(
            type_scores.items(),
            key=lambda x: x[1][0],
            reverse=True
        )
        
        # Determine primary type
        if sorted_types:
            primary_type = sorted_types[0][0]
            primary_confidence = min(sorted_types[0][1][0], 1.0)
            keywords = sorted_types[0][1][1]
        else:
            primary_type = ScamType.UNKNOWN
            primary_confidence = 0.5
            keywords = []
        
        # Get secondary types
        secondary_types = [
            (t, min(s, 1.0)) for t, (s, k) in sorted_types[1:4]
        ]
        
        # Check for compound scam
        is_compound = len([s for t, (s, k) in sorted_types if s > 0.5]) > 1
        
        # Get threat level and persona
        config = SCAM_TYPE_PATTERNS.get(primary_type, {})
        threat_level = config.get("threat_level", "medium")
        persona = SCAM_PERSONA_MAP.get(primary_type, "confused")
        
        # Update history
        self._update_history(primary_type, primary_confidence)
        
        return ScamTypeResult(
            primary_type=primary_type,
            primary_confidence=round(primary_confidence, 3),
            secondary_types=secondary_types,
            is_compound=is_compound,
            keywords_matched=keywords,
            threat_level=threat_level,
            recommended_persona=persona,
        )
    
    def _score_scam_type(
        self,
        message: str,
        scam_type: ScamType,
        config: Dict,
    ) -> Tuple[float, List[str]]:
        """Score how likely a message matches a scam type."""
        score = 0.0
        matched_keywords = []
        
        weight = config.get("weight", 1.0)
        
        # Check English keywords
        for kw in config.get("keywords_en", []):
            if kw.lower() in message:
                score += 0.2
                matched_keywords.append(kw)
        
        # Check Hindi keywords
        for kw in config.get("keywords_hi", []):
            if kw in message:
                score += 0.25  # Slightly higher for specific Hindi
                matched_keywords.append(kw)
        
        # Check regex patterns
        compiled = self.compiled_patterns.get(scam_type, [])
        for pattern in compiled:
            if pattern.search(message):
                score += 0.3
        
        # Apply weight
        score *= weight
        
        # Cap at 1.0
        return min(score, 1.0), matched_keywords
    
    def _apply_history_boost(
        self,
        type_scores: Dict[ScamType, Tuple[float, List[str]]],
        history: List[Dict],
    ) -> Dict[ScamType, Tuple[float, List[str]]]:
        """Boost scores for types that appeared in conversation history."""
        # Analyze history for consistent types
        history_text = " ".join(
            m.get("message", "").lower()
            for m in history
            if m.get("sender") == "scammer"
        )
        
        history_types: Dict[ScamType, int] = {}
        for scam_type, config in SCAM_TYPE_PATTERNS.items():
            count = 0
            for kw in config.get("keywords_en", []):
                if kw.lower() in history_text:
                    count += 1
            if count > 0:
                history_types[scam_type] = count
        
        # Boost current scores based on history
        boosted = {}
        for scam_type, (score, keywords) in type_scores.items():
            history_count = history_types.get(scam_type, 0)
            boost = min(history_count * 0.1, 0.3)
            boosted[scam_type] = (score + boost, keywords)
        
        return boosted
    
    def _update_history(self, scam_type: ScamType, confidence: float) -> None:
        """Update detection history."""
        self.history.detections.append((scam_type, confidence))
        
        # Keep only last 10 detections
        if len(self.history.detections) > 10:
            self.history.detections = self.history.detections[-10:]
        
        # Check for type stability
        if len(self.history.detections) >= 3:
            recent_types = [t for t, c in self.history.detections[-3:]]
            if len(set(recent_types)) == 1:
                if self.history.stable_type != recent_types[0]:
                    self.history.stable_type = recent_types[0]
            elif self.history.stable_type is not None:
                self.history.type_changes += 1
                self.history.stable_type = None
    
    def get_stable_type(self) -> Optional[ScamType]:
        """Get the stable scam type if conversation is consistent."""
        return self.history.stable_type
    
    def get_history_summary(self) -> Dict:
        """Get summary of detection history."""
        if not self.history.detections:
            return {"count": 0, "stable_type": None}
        
        type_counts: Dict[str, int] = {}
        for scam_type, conf in self.history.detections:
            name = scam_type.value
            type_counts[name] = type_counts.get(name, 0) + 1
        
        return {
            "count": len(self.history.detections),
            "type_counts": type_counts,
            "stable_type": self.history.stable_type.value if self.history.stable_type else None,
            "type_changes": self.history.type_changes,
            "compound_detected": self.history.compound_detected,
        }
    
    def reset(self) -> None:
        """Reset detection history for new conversation."""
        self.history = ScamTypeHistory()


# Singleton instance
_detector: Optional[AdvancedScamDetector] = None


def get_advanced_detector() -> AdvancedScamDetector:
    """Get singleton AdvancedScamDetector instance."""
    global _detector
    if _detector is None:
        _detector = AdvancedScamDetector()
    return _detector


def detect_scam_type(
    message: str,
    conversation_history: Optional[List[Dict]] = None,
) -> ScamTypeResult:
    """
    Convenience function to detect scam type.
    
    Args:
        message: Message to analyze
        conversation_history: Optional previous messages
        
    Returns:
        ScamTypeResult with classification
    """
    detector = get_advanced_detector()
    return detector.detect(message, conversation_history)


def get_recommended_persona(message: str) -> str:
    """Get recommended persona for a message."""
    result = detect_scam_type(message)
    return result.recommended_persona


def reset_advanced_detector() -> None:
    """Reset the detector for new conversation."""
    global _detector
    if _detector is not None:
        _detector.reset()

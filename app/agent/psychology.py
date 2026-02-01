"""
Scammer Psychology Tracking Module.

Analyzes scammer behavior patterns to optimize engagement strategy:
- Urgency level detection
- Aggression/pressure tactics
- Manipulation techniques identification
- Trust building attempts
- Extraction timing optimization

Understanding scammer psychology = better intelligence extraction.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ScammerTactic(Enum):
    """Types of manipulation tactics used by scammers."""
    URGENCY = "urgency"              # Creating time pressure
    FEAR = "fear"                    # Threatening consequences
    GREED = "greed"                  # Promising rewards
    AUTHORITY = "authority"          # Impersonating officials
    SOCIAL_PROOF = "social_proof"    # Claiming others have done it
    SCARCITY = "scarcity"            # Limited time/availability
    RECIPROCITY = "reciprocity"      # You owe me/I helped you
    FLATTERY = "flattery"            # Compliments to lower guard
    CONFUSION = "confusion"          # Overwhelming with info


class PressureLevel(Enum):
    """Level of pressure being applied by scammer."""
    GENTLE = "gentle"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    EXTREME = "extreme"


@dataclass
class PsychologyState:
    """Current psychological state analysis of the scammer."""
    urgency_level: float  # 0.0 to 1.0
    aggression_level: float  # 0.0 to 1.0
    persistence_level: float  # 0.0 to 1.0
    frustration_level: float  # 0.0 to 1.0
    primary_tactic: ScammerTactic
    secondary_tactics: List[ScammerTactic]
    pressure_level: PressureLevel
    extraction_readiness: float  # 0.0 to 1.0 - how ready scammer is to give info
    recommended_strategy: str


@dataclass
class ConversationPsychology:
    """Track psychology across entire conversation."""
    turn_count: int = 0
    urgency_history: List[float] = field(default_factory=list)
    aggression_history: List[float] = field(default_factory=list)
    tactics_used: Dict[str, int] = field(default_factory=dict)
    pressure_escalations: int = 0
    topic_changes: int = 0
    repeated_demands: int = 0


# Urgency indicators - scammer creating time pressure
URGENCY_PATTERNS = {
    "high": [
        (r"(right\s+)?now", 0.8),
        (r"immediately", 0.9),
        (r"urgent(ly)?", 0.9),
        (r"hurry(\s+up)?", 0.85),
        (r"(last|final)\s+chance", 0.95),
        (r"(deadline|expires?|expiring)", 0.85),
        (r"(today|tonight)\s+only", 0.9),
        (r"within\s+\d+\s+(hour|minute)", 0.95),
        (r"before\s+midnight", 0.9),
        (r"time\s+is\s+running", 0.9),
        (r"तुरंत|फौरन|जल्दी", 0.85),  # Hindi urgency
        (r"abhi\s*(ke\s*)?abhi", 0.85),  # Hinglish
    ],
    "medium": [
        (r"as\s+soon\s+as", 0.6),
        (r"quickly", 0.5),
        (r"don't\s+delay", 0.6),
        (r"waiting\s+for", 0.4),
        (r"pending", 0.4),
    ],
}

# Aggression/fear indicators
AGGRESSION_PATTERNS = {
    "high": [
        (r"(will\s+be\s+)?arrest(ed)?", 0.95),
        (r"police|पुलिस", 0.9),
        (r"court\s+(case|order|summon)", 0.9),
        (r"(legal|criminal)\s+action", 0.9),
        (r"warrant", 0.95),
        (r"jail|prison|गिरफ्तार", 0.95),
        (r"(seize|freeze)\s+(your\s+)?account", 0.85),
        (r"permanent(ly)?\s+(block|ban|close)", 0.8),
        (r"(cbi|ed|enforcement)", 0.9),
        (r"money\s+laundering", 0.85),
    ],
    "medium": [
        (r"block(ed)?", 0.5),
        (r"suspend(ed)?", 0.5),
        (r"penalty|fine|जुर्माना", 0.6),
        (r"problem|issue|trouble", 0.4),
        (r"consequences", 0.6),
        (r"serious\s+matter", 0.6),
    ],
}

# Greed/reward indicators
GREED_PATTERNS = [
    (r"(\d+)\s*(lakh|lac|crore|million|लाख|करोड़)", 0.9),
    (r"(won|winner|जीत)", 0.85),
    (r"prize|reward|इनाम", 0.8),
    (r"lottery|लॉटरी", 0.9),
    (r"jackpot", 0.9),
    (r"lucky\s+(winner|draw|number)", 0.85),
    (r"congratulations?|बधाई", 0.7),
    (r"free\s+(gift|money|iphone)", 0.8),
    (r"(guaranteed|assured)\s+returns?", 0.8),
    (r"(double|triple)\s+your\s+money", 0.9),
]

# Authority impersonation indicators
AUTHORITY_PATTERNS = [
    (r"(reserve\s+)?bank\s+of\s+india|rbi", 0.9),
    (r"government\s+(of\s+india|official)", 0.9),
    (r"income\s+tax\s+(department|officer)", 0.9),
    (r"(cyber|police)\s+cell", 0.85),
    (r"customer\s+(care|support|service)", 0.7),
    (r"official\s+(notice|letter|communication)", 0.8),
    (r"central\s+bureau|cbi", 0.9),
    (r"enforcement\s+directorate|ed", 0.9),
    (r"telecom\s+department|trai|doi", 0.85),
]

# Persistence indicators - scammer not giving up
PERSISTENCE_PATTERNS = [
    (r"(i\s+)?(already|again)\s+(told|said|mentioned)", 0.7),
    (r"(listen|hear)\s+me\s+(carefully|properly)", 0.6),
    (r"why\s+(are\s+)?you\s+not", 0.7),
    (r"(just|simply)\s+(do|follow|send)", 0.5),
    (r"don't\s+(waste|delay)", 0.6),
    (r"(last|final)\s+time", 0.8),
    (r"i\s+('m\s+)?telling\s+you", 0.5),
    (r"one\s+more\s+(time|chance)", 0.7),
]


class ScammerPsychologyTracker:
    """
    Tracks and analyzes scammer psychology throughout conversation.
    
    Uses pattern matching and sentiment analysis to understand:
    - What tactics the scammer is using
    - How aggressive/urgent they are
    - When they're most vulnerable to revealing information
    - When our victim should "break" and offer payment details
    """
    
    def __init__(self):
        """Initialize the psychology tracker."""
        self._compile_patterns()
        self.conversation_state = ConversationPsychology()
        logger.info("ScammerPsychologyTracker initialized")
    
    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns."""
        self.urgency_high = [(re.compile(p, re.IGNORECASE), s) for p, s in URGENCY_PATTERNS["high"]]
        self.urgency_medium = [(re.compile(p, re.IGNORECASE), s) for p, s in URGENCY_PATTERNS["medium"]]
        self.aggression_high = [(re.compile(p, re.IGNORECASE), s) for p, s in AGGRESSION_PATTERNS["high"]]
        self.aggression_medium = [(re.compile(p, re.IGNORECASE), s) for p, s in AGGRESSION_PATTERNS["medium"]]
        self.greed_patterns = [(re.compile(p, re.IGNORECASE), s) for p, s in GREED_PATTERNS]
        self.authority_patterns = [(re.compile(p, re.IGNORECASE), s) for p, s in AUTHORITY_PATTERNS]
        self.persistence_patterns = [(re.compile(p, re.IGNORECASE), s) for p, s in PERSISTENCE_PATTERNS]
    
    def analyze_message(
        self, 
        message: str, 
        turn_count: int = 1,
        previous_messages: Optional[List[Dict]] = None
    ) -> PsychologyState:
        """
        Analyze a scammer message for psychological patterns.
        
        Args:
            message: The scammer's message
            turn_count: Current turn in conversation
            previous_messages: Previous messages for context
            
        Returns:
            PsychologyState with detailed analysis
        """
        message_lower = message.lower()
        
        # Calculate individual metrics
        urgency = self._calculate_urgency(message_lower)
        aggression = self._calculate_aggression(message_lower)
        persistence = self._calculate_persistence(message_lower)
        
        # Detect tactics
        tactics = self._detect_tactics(message_lower)
        primary_tactic = tactics[0] if tactics else ScammerTactic.GREED
        secondary_tactics = tactics[1:] if len(tactics) > 1 else []
        
        # Calculate frustration (based on persistence + turn count)
        frustration = self._calculate_frustration(persistence, turn_count)
        
        # Determine pressure level
        pressure = self._determine_pressure_level(urgency, aggression)
        
        # Calculate extraction readiness
        # High frustration + high persistence = scammer might reveal info to get results
        extraction_readiness = self._calculate_extraction_readiness(
            urgency, aggression, frustration, turn_count
        )
        
        # Get recommended strategy
        strategy = self._recommend_strategy(
            urgency, aggression, frustration, extraction_readiness, turn_count
        )
        
        # Update conversation state
        self._update_conversation_state(
            turn_count, urgency, aggression, primary_tactic, pressure
        )
        
        return PsychologyState(
            urgency_level=urgency,
            aggression_level=aggression,
            persistence_level=persistence,
            frustration_level=frustration,
            primary_tactic=primary_tactic,
            secondary_tactics=secondary_tactics,
            pressure_level=pressure,
            extraction_readiness=extraction_readiness,
            recommended_strategy=strategy,
        )
    
    def _calculate_urgency(self, message: str) -> float:
        """Calculate urgency level from message."""
        score = 0.0
        matches = 0
        
        # Check high urgency patterns
        for pattern, weight in self.urgency_high:
            if pattern.search(message):
                score += weight
                matches += 1
        
        # Check medium urgency patterns
        for pattern, weight in self.urgency_medium:
            if pattern.search(message):
                score += weight * 0.5
                matches += 1
        
        if matches == 0:
            return 0.0
        
        # Normalize to 0-1 range
        return min(score / max(matches, 1), 1.0)
    
    def _calculate_aggression(self, message: str) -> float:
        """Calculate aggression level from message."""
        score = 0.0
        matches = 0
        
        # Check high aggression patterns
        for pattern, weight in self.aggression_high:
            if pattern.search(message):
                score += weight
                matches += 1
        
        # Check medium aggression patterns
        for pattern, weight in self.aggression_medium:
            if pattern.search(message):
                score += weight * 0.5
                matches += 1
        
        if matches == 0:
            return 0.0
        
        return min(score / max(matches, 1), 1.0)
    
    def _calculate_persistence(self, message: str) -> float:
        """Calculate persistence level from message."""
        score = 0.0
        matches = 0
        
        for pattern, weight in self.persistence_patterns:
            if pattern.search(message):
                score += weight
                matches += 1
        
        if matches == 0:
            return 0.0
        
        return min(score / max(matches, 1), 1.0)
    
    def _calculate_frustration(self, persistence: float, turn_count: int) -> float:
        """
        Calculate scammer frustration level.
        
        Frustration increases with:
        - High persistence (they keep repeating themselves)
        - High turn count (victim not complying)
        """
        # Base frustration from persistence
        base = persistence * 0.6
        
        # Add frustration from turn count (more turns without success = more frustration)
        turn_factor = min(turn_count / 15, 1.0) * 0.4
        
        return min(base + turn_factor, 1.0)
    
    def _detect_tactics(self, message: str) -> List[ScammerTactic]:
        """Detect manipulation tactics being used."""
        tactics = []
        tactic_scores: Dict[ScammerTactic, float] = {}
        
        # Check urgency -> URGENCY tactic
        urgency_score = self._calculate_urgency(message)
        if urgency_score > 0.3:
            tactic_scores[ScammerTactic.URGENCY] = urgency_score
        
        # Check aggression -> FEAR tactic
        aggression_score = self._calculate_aggression(message)
        if aggression_score > 0.3:
            tactic_scores[ScammerTactic.FEAR] = aggression_score
        
        # Check greed patterns -> GREED tactic
        greed_score = 0.0
        for pattern, weight in self.greed_patterns:
            if pattern.search(message):
                greed_score = max(greed_score, weight)
        if greed_score > 0.3:
            tactic_scores[ScammerTactic.GREED] = greed_score
        
        # Check authority patterns -> AUTHORITY tactic
        authority_score = 0.0
        for pattern, weight in self.authority_patterns:
            if pattern.search(message):
                authority_score = max(authority_score, weight)
        if authority_score > 0.3:
            tactic_scores[ScammerTactic.AUTHORITY] = authority_score
        
        # Check for scarcity indicators
        if re.search(r"(only|just)\s+\d+\s+(left|remaining|available)", message, re.IGNORECASE):
            tactic_scores[ScammerTactic.SCARCITY] = 0.7
        
        # Sort tactics by score
        sorted_tactics = sorted(
            tactic_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [t for t, s in sorted_tactics]
    
    def _determine_pressure_level(
        self, 
        urgency: float, 
        aggression: float
    ) -> PressureLevel:
        """Determine overall pressure level."""
        combined = (urgency + aggression) / 2
        
        if combined < 0.25:
            return PressureLevel.GENTLE
        elif combined < 0.5:
            return PressureLevel.MODERATE
        elif combined < 0.75:
            return PressureLevel.AGGRESSIVE
        else:
            return PressureLevel.EXTREME
    
    def _calculate_extraction_readiness(
        self,
        urgency: float,
        aggression: float,
        frustration: float,
        turn_count: int,
    ) -> float:
        """
        Calculate how ready the scammer is to reveal their own info.
        
        Scammers are more likely to give their payment details when:
        - They've been at it for a while (turn_count > 5)
        - They're frustrated (victim not complying quickly)
        - They sense the victim is about to pay (high urgency)
        
        This helps us time when to ask for THEIR details.
        """
        # Base readiness increases with turn count
        turn_factor = min(turn_count / 10, 1.0) * 0.3
        
        # Frustration increases readiness (they want to close the deal)
        frustration_factor = frustration * 0.3
        
        # High urgency on their part means they want quick resolution
        urgency_factor = urgency * 0.2
        
        # If aggression is very high, they might be more willing to give details
        # to "prove" their legitimacy
        aggression_factor = aggression * 0.2 if aggression > 0.5 else 0
        
        return min(turn_factor + frustration_factor + urgency_factor + aggression_factor, 1.0)
    
    def _recommend_strategy(
        self,
        urgency: float,
        aggression: float,
        frustration: float,
        extraction_readiness: float,
        turn_count: int,
    ) -> str:
        """
        Recommend optimal response strategy based on psychology analysis.
        
        Returns strategy name that the agent should use.
        """
        # If extraction readiness is high, actively extract
        if extraction_readiness > 0.7:
            return "extract_aggressively"
        
        # If scammer is very aggressive, show fear and compliance
        if aggression > 0.7:
            return "show_fear_comply"
        
        # If urgency is high, act confused to slow them down
        if urgency > 0.7 and turn_count < 10:
            return "act_confused"
        
        # If frustration is high, start offering to pay (to get their details)
        if frustration > 0.6:
            return "offer_payment"
        
        # Early turns: build trust
        if turn_count <= 5:
            return "build_rapport"
        
        # Mid turns: express eagerness
        if turn_count <= 12:
            return "express_eagerness"
        
        # Late turns: actively extract
        return "probe_for_details"
    
    def _update_conversation_state(
        self,
        turn_count: int,
        urgency: float,
        aggression: float,
        tactic: ScammerTactic,
        pressure: PressureLevel,
    ) -> None:
        """Update conversation-level tracking."""
        self.conversation_state.turn_count = turn_count
        self.conversation_state.urgency_history.append(urgency)
        self.conversation_state.aggression_history.append(aggression)
        
        # Track tactics used
        tactic_name = tactic.value
        self.conversation_state.tactics_used[tactic_name] = \
            self.conversation_state.tactics_used.get(tactic_name, 0) + 1
        
        # Track pressure escalations
        if len(self.conversation_state.aggression_history) >= 2:
            if aggression > self.conversation_state.aggression_history[-2] + 0.2:
                self.conversation_state.pressure_escalations += 1
    
    def get_conversation_summary(self) -> Dict:
        """Get summary of conversation psychology."""
        state = self.conversation_state
        
        avg_urgency = sum(state.urgency_history) / max(len(state.urgency_history), 1)
        avg_aggression = sum(state.aggression_history) / max(len(state.aggression_history), 1)
        
        # Find dominant tactic
        dominant_tactic = max(
            state.tactics_used.items(),
            key=lambda x: x[1],
            default=("unknown", 0)
        )[0] if state.tactics_used else "unknown"
        
        return {
            "turns_analyzed": state.turn_count,
            "average_urgency": round(avg_urgency, 2),
            "average_aggression": round(avg_aggression, 2),
            "dominant_tactic": dominant_tactic,
            "tactics_used": state.tactics_used,
            "pressure_escalations": state.pressure_escalations,
            "urgency_trend": self._calculate_trend(state.urgency_history),
            "aggression_trend": self._calculate_trend(state.aggression_history),
        }
    
    def _calculate_trend(self, history: List[float]) -> str:
        """Calculate if metric is increasing, decreasing, or stable."""
        if len(history) < 3:
            return "stable"
        
        recent = history[-3:]
        if recent[-1] > recent[0] + 0.1:
            return "increasing"
        elif recent[-1] < recent[0] - 0.1:
            return "decreasing"
        return "stable"
    
    def reset(self) -> None:
        """Reset conversation state for new conversation."""
        self.conversation_state = ConversationPsychology()


# Singleton instance
_psychology_tracker: Optional[ScammerPsychologyTracker] = None


def get_psychology_tracker() -> ScammerPsychologyTracker:
    """Get singleton psychology tracker instance."""
    global _psychology_tracker
    if _psychology_tracker is None:
        _psychology_tracker = ScammerPsychologyTracker()
    return _psychology_tracker


def analyze_scammer_psychology(
    message: str,
    turn_count: int = 1,
    previous_messages: Optional[List[Dict]] = None,
) -> PsychologyState:
    """
    Convenience function to analyze scammer psychology.
    
    Args:
        message: Scammer's message
        turn_count: Current turn number
        previous_messages: Previous conversation messages
        
    Returns:
        PsychologyState with analysis results
    """
    tracker = get_psychology_tracker()
    return tracker.analyze_message(message, turn_count, previous_messages)


def reset_psychology_tracker() -> None:
    """Reset the psychology tracker (for new conversations)."""
    global _psychology_tracker
    if _psychology_tracker is not None:
        _psychology_tracker.reset()

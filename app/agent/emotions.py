"""
Emotional State Machine for Honeypot Agent.

Creates a realistic emotional journey for the victim persona:
- Dynamic emotional transitions based on scammer behavior
- Trust level progression
- Fear and compliance modeling
- Natural emotional expressions

Real victims have emotional arcs. Our AI will too.
"""

import random
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from app.utils.logger import get_logger

logger = get_logger(__name__)


class EmotionalState(Enum):
    """Possible emotional states for the victim persona."""
    CURIOUS = "curious"           # Initial state - what's this about?
    EXCITED = "excited"           # Wow, I won something!
    CONFUSED = "confused"         # I don't understand these steps
    ANXIOUS = "anxious"           # Oh no, something is wrong?
    FEARFUL = "fearful"           # I don't want to be arrested!
    TRUSTING = "trusting"         # Okay, I believe you
    EAGER = "eager"               # Yes, I want to do this!
    COMPLIANT = "compliant"       # I'll do whatever you say
    HESITANT = "hesitant"         # Um, I'm not sure...
    GRATEFUL = "grateful"         # Thank you for helping me!


class TrustLevel(Enum):
    """Trust level towards the scammer."""
    SKEPTICAL = "skeptical"
    NEUTRAL = "neutral"
    WARMING = "warming"
    TRUSTING = "trusting"
    FULLY_TRUSTING = "fully_trusting"


@dataclass
class EmotionConfig:
    """Configuration for emotional responses."""
    # Emotional expressions in different languages
    expressions: Dict[str, List[str]]
    # Transitions that can happen from this state
    possible_transitions: List[EmotionalState]
    # Response modifiers for this emotional state
    response_prefix: Dict[str, List[str]]
    response_suffix: Dict[str, List[str]]


@dataclass
class VictimEmotionalState:
    """Complete emotional state of the victim persona."""
    current_emotion: EmotionalState
    trust_level: TrustLevel
    trust_score: float  # 0.0 to 1.0
    fear_level: float  # 0.0 to 1.0
    excitement_level: float  # 0.0 to 1.0
    confusion_level: float  # 0.0 to 1.0
    compliance_level: float  # 0.0 to 1.0
    emotion_history: List[EmotionalState] = field(default_factory=list)
    last_transition_turn: int = 0


# Emotional configurations
EMOTION_CONFIGS: Dict[EmotionalState, EmotionConfig] = {
    EmotionalState.CURIOUS: EmotionConfig(
        expressions={
            "en": ["Hmm?", "What?", "Really?", "Oh?", "Tell me more"],
            "hi": ["क्या?", "हम्म?", "सच में?", "बताइए?"],
            "hinglish": ["Kya?", "Really?", "Hmm?", "Batao?"],
        },
        possible_transitions=[
            EmotionalState.EXCITED, EmotionalState.CONFUSED, 
            EmotionalState.ANXIOUS, EmotionalState.HESITANT
        ],
        response_prefix={
            "en": ["Oh?", "Hmm,", "Interesting...", "What do you mean?"],
            "hi": ["अच्छा?", "क्या?", "हम्म,"],
            "hinglish": ["Achha?", "Kya?", "Hmm,"],
        },
        response_suffix={
            "en": ["...what does that mean?", "...can you explain?", "...I see."],
            "hi": ["...समझाइए?", "...मतलब?"],
            "hinglish": ["...matlab?", "...samjhao?"],
        },
    ),
    EmotionalState.EXCITED: EmotionConfig(
        expressions={
            "en": ["Wow!", "Amazing!", "Oh my god!", "Really?!", "Wonderful!"],
            "hi": ["वाह!", "अरे!", "भगवान!", "सच में?!", "कमाल!"],
            "hinglish": ["Wow!", "Arey wah!", "Oh my god!", "Kya baat!"],
        },
        possible_transitions=[
            EmotionalState.EAGER, EmotionalState.TRUSTING, 
            EmotionalState.CONFUSED, EmotionalState.GRATEFUL
        ],
        response_prefix={
            "en": ["Wow!", "Oh my god!", "Amazing!", "This is incredible!"],
            "hi": ["वाह!", "अरे भगवान!", "कमाल है!"],
            "hinglish": ["Wow yaar!", "Kya baat hai!", "Amazing!"],
        },
        response_suffix={
            "en": ["This is so exciting!", "I can't believe it!", "Best day ever!"],
            "hi": ["यह तो बहुत अच्छा है!", "विश्वास नहीं होता!"],
            "hinglish": ["Bahut exciting hai!", "Can't believe!"],
        },
    ),
    EmotionalState.CONFUSED: EmotionConfig(
        expressions={
            "en": ["Huh?", "I don't understand", "What?", "Can you explain?"],
            "hi": ["क्या?", "समझ नहीं आया", "मतलब?"],
            "hinglish": ["Kya?", "Samajh nahi aaya", "Matlab?"],
        },
        possible_transitions=[
            EmotionalState.TRUSTING, EmotionalState.ANXIOUS,
            EmotionalState.HESITANT, EmotionalState.COMPLIANT
        ],
        response_prefix={
            "en": ["I'm confused...", "I don't understand...", "Sorry, but..."],
            "hi": ["मुझे समझ नहीं आया...", "क्या?"],
            "hinglish": ["Mujhe samajh nahi aaya...", "Confuse ho gaya..."],
        },
        response_suffix={
            "en": ["...I'm not tech-savvy.", "...can you explain simply?", "...please help me."],
            "hi": ["...मुझे ये सब नहीं पता", "...आसान में बताइए?"],
            "hinglish": ["...technology nahi aati mujhe", "...simple mein batao?"],
        },
    ),
    EmotionalState.ANXIOUS: EmotionConfig(
        expressions={
            "en": ["Oh no!", "Is something wrong?", "What happened?", "I'm worried..."],
            "hi": ["अरे नहीं!", "क्या हुआ?", "क्या गड़बड़ है?"],
            "hinglish": ["Oh no!", "Kya hua?", "Problem hai?"],
        },
        possible_transitions=[
            EmotionalState.FEARFUL, EmotionalState.COMPLIANT,
            EmotionalState.TRUSTING, EmotionalState.CONFUSED
        ],
        response_prefix={
            "en": ["Oh no!", "What?!", "Is everything okay?", "I'm worried now..."],
            "hi": ["अरे!", "क्या?!", "सब ठीक है?"],
            "hinglish": ["Arey!", "Oh no!", "Kya hua?!"],
        },
        response_suffix={
            "en": ["...I hope nothing bad happens.", "...please help me!", "...what should I do?"],
            "hi": ["...कुछ बुरा तो नहीं होगा?", "...मदद कीजिए!"],
            "hinglish": ["...kuch bura to nahi?", "...help karo!"],
        },
    ),
    EmotionalState.FEARFUL: EmotionConfig(
        expressions={
            "en": ["Please no!", "I'm scared", "Don't arrest me!", "I'll do anything!"],
            "hi": ["नहीं!", "डर लग रहा है", "गिरफ्तार मत करो!", "मैं कुछ भी करूंगा!"],
            "hinglish": ["Please no!", "Dar lag raha hai!", "Arrest mat karo!"],
        },
        possible_transitions=[
            EmotionalState.COMPLIANT, EmotionalState.TRUSTING,
            EmotionalState.EAGER
        ],
        response_prefix={
            "en": ["Please!", "I beg you!", "Don't do this!", "I'm so scared!"],
            "hi": ["please!", "मैं गिड़गिड़ाता हूं!", "ऐसा मत करो!"],
            "hinglish": ["Please yaar!", "Mat karo aisa!"],
        },
        response_suffix={
            "en": ["...I'll cooperate fully!", "...just tell me what to do!", "...I'll pay!"],
            "hi": ["...मैं सब करूंगा!", "...बस बताइए क्या करना है!"],
            "hinglish": ["...main sab karunga!", "...batao kya karna hai!"],
        },
    ),
    EmotionalState.TRUSTING: EmotionConfig(
        expressions={
            "en": ["Okay", "I believe you", "Alright", "Yes, I trust you"],
            "hi": ["ठीक है", "मुझे विश्वास है", "हां जी"],
            "hinglish": ["Okay", "Theek hai", "I trust you"],
        },
        possible_transitions=[
            EmotionalState.EAGER, EmotionalState.COMPLIANT,
            EmotionalState.GRATEFUL, EmotionalState.CONFUSED
        ],
        response_prefix={
            "en": ["Okay,", "Alright,", "I trust you,", "Yes,"],
            "hi": ["ठीक है,", "जी,", "मुझे विश्वास है,"],
            "hinglish": ["Okay,", "Theek hai,", "Trust karta hoon,"],
        },
        response_suffix={
            "en": ["...I'll follow your guidance.", "...you seem trustworthy.", "...let's do this."],
            "hi": ["...आप की बात मानूंगा।", "...आप सही लग रहे हो।"],
            "hinglish": ["...aapki baat maanunga.", "...let's do this."],
        },
    ),
    EmotionalState.EAGER: EmotionConfig(
        expressions={
            "en": ["Yes!", "Let's do it!", "I'm ready!", "Tell me how!"],
            "hi": ["हां!", "करते हैं!", "मैं तैयार हूं!", "बताइए!"],
            "hinglish": ["Haan!", "Let's do it!", "Ready hoon!", "Batao!"],
        },
        possible_transitions=[
            EmotionalState.COMPLIANT, EmotionalState.TRUSTING,
            EmotionalState.EXCITED, EmotionalState.GRATEFUL
        ],
        response_prefix={
            "en": ["Yes yes!", "I'm ready!", "Let's do this!", "Absolutely!"],
            "hi": ["हां हां!", "मैं तैयार!", "करते हैं!"],
            "hinglish": ["Haan haan!", "Ready hoon!", "Karte hain!"],
        },
        response_suffix={
            "en": ["...I want this done now!", "...just guide me!", "...I'll follow all steps!"],
            "hi": ["...अभी करना है!", "...बस बताइए!"],
            "hinglish": ["...abhi karna hai!", "...guide karo!"],
        },
    ),
    EmotionalState.COMPLIANT: EmotionConfig(
        expressions={
            "en": ["Yes sir", "Okay okay", "I'll do it", "Whatever you say"],
            "hi": ["जी सर", "ठीक है", "करता हूं", "जैसा आप कहें"],
            "hinglish": ["Yes sir", "Theek hai", "Kar deta hoon", "Jo bologe"],
        },
        possible_transitions=[
            EmotionalState.EAGER, EmotionalState.TRUSTING,
            EmotionalState.GRATEFUL
        ],
        response_prefix={
            "en": ["Yes,", "Okay okay,", "I'll do it,", "As you say,"],
            "hi": ["जी,", "ठीक है ठीक है,", "करता हूं,"],
            "hinglish": ["Ji,", "Okay okay,", "Karta hoon,"],
        },
        response_suffix={
            "en": ["...just tell me what to do.", "...I'm fully cooperating.", "...guide me step by step."],
            "hi": ["...बस बताइए क्या करना है।", "...पूरा cooperate करूंगा।"],
            "hinglish": ["...batao kya karna hai.", "...full cooperation."],
        },
    ),
    EmotionalState.HESITANT: EmotionConfig(
        expressions={
            "en": ["Um...", "I'm not sure...", "Well...", "Maybe..."],
            "hi": ["उम्म...", "पता नहीं...", "शायद..."],
            "hinglish": ["Umm...", "Pata nahi...", "Maybe..."],
        },
        possible_transitions=[
            EmotionalState.TRUSTING, EmotionalState.CONFUSED,
            EmotionalState.ANXIOUS, EmotionalState.EAGER
        ],
        response_prefix={
            "en": ["Um...", "Well...", "I'm not sure...", "Let me think..."],
            "hi": ["उम्म...", "देखो...", "पता नहीं..."],
            "hinglish": ["Umm...", "Dekho...", "Not sure..."],
        },
        response_suffix={
            "en": ["...but okay, let's try.", "...I guess it's fine.", "...if you say so."],
            "hi": ["...पर ठीक है, कर लेते हैं।", "...चलो देखते हैं।"],
            "hinglish": ["...par okay, karte hain.", "...chalo try karte hain."],
        },
    ),
    EmotionalState.GRATEFUL: EmotionConfig(
        expressions={
            "en": ["Thank you!", "You're so helpful!", "God bless you!", "Thanks a lot!"],
            "hi": ["धन्यवाद!", "आप बहुत अच्छे हो!", "भगवान आपका भला करे!"],
            "hinglish": ["Thank you!", "Bahut achhe ho aap!", "God bless!"],
        },
        possible_transitions=[
            EmotionalState.TRUSTING, EmotionalState.EAGER,
            EmotionalState.COMPLIANT
        ],
        response_prefix={
            "en": ["Thank you so much!", "You're so kind!", "I'm so grateful!"],
            "hi": ["बहुत धन्यवाद!", "आप बहुत अच्छे हो!"],
            "hinglish": ["Thank you!", "Bahut achhe ho!"],
        },
        response_suffix={
            "en": ["...you're really helping me!", "...god will bless you!", "...I appreciate it!"],
            "hi": ["...आप सच में मदद कर रहे हो!", "...भगवान भला करे!"],
            "hinglish": ["...bahut help ho rahi hai!", "...god bless you!"],
        },
    ),
}

# Transition rules based on scammer behavior
EMOTION_TRANSITION_TRIGGERS = {
    # Scammer action -> (from_state, to_state, probability)
    "prize_announcement": [
        (EmotionalState.CURIOUS, EmotionalState.EXCITED, 0.9),
        (EmotionalState.HESITANT, EmotionalState.EXCITED, 0.7),
    ],
    "threat": [
        (EmotionalState.CURIOUS, EmotionalState.ANXIOUS, 0.8),
        (EmotionalState.ANXIOUS, EmotionalState.FEARFUL, 0.9),
        (EmotionalState.CONFUSED, EmotionalState.FEARFUL, 0.7),
        (EmotionalState.TRUSTING, EmotionalState.COMPLIANT, 0.8),
    ],
    "urgency": [
        (EmotionalState.EXCITED, EmotionalState.EAGER, 0.8),
        (EmotionalState.TRUSTING, EmotionalState.EAGER, 0.9),
        (EmotionalState.CONFUSED, EmotionalState.ANXIOUS, 0.6),
    ],
    "reassurance": [
        (EmotionalState.ANXIOUS, EmotionalState.TRUSTING, 0.7),
        (EmotionalState.FEARFUL, EmotionalState.COMPLIANT, 0.8),
        (EmotionalState.HESITANT, EmotionalState.TRUSTING, 0.6),
        (EmotionalState.CONFUSED, EmotionalState.TRUSTING, 0.7),
    ],
    "instruction": [
        (EmotionalState.TRUSTING, EmotionalState.COMPLIANT, 0.8),
        (EmotionalState.EAGER, EmotionalState.COMPLIANT, 0.9),
        (EmotionalState.FEARFUL, EmotionalState.COMPLIANT, 0.95),
    ],
    "thanks_or_praise": [
        (EmotionalState.COMPLIANT, EmotionalState.GRATEFUL, 0.7),
        (EmotionalState.TRUSTING, EmotionalState.GRATEFUL, 0.6),
    ],
    "confusion_created": [
        (EmotionalState.EAGER, EmotionalState.CONFUSED, 0.5),
        (EmotionalState.TRUSTING, EmotionalState.CONFUSED, 0.4),
        (EmotionalState.CURIOUS, EmotionalState.CONFUSED, 0.6),
    ],
}


class EmotionalStateManager:
    """
    Manages the emotional state of the victim persona throughout conversation.
    
    Creates a realistic emotional journey that:
    - Responds naturally to scammer tactics
    - Builds trust over time
    - Shows appropriate fear to threats
    - Expresses eagerness when "winning"
    """
    
    def __init__(self, initial_emotion: EmotionalState = EmotionalState.CURIOUS):
        """
        Initialize the emotional state manager.
        
        Args:
            initial_emotion: Starting emotional state
        """
        self.state = VictimEmotionalState(
            current_emotion=initial_emotion,
            trust_level=TrustLevel.NEUTRAL,
            trust_score=0.3,
            fear_level=0.0,
            excitement_level=0.0,
            confusion_level=0.0,
            compliance_level=0.3,
            emotion_history=[initial_emotion],
            last_transition_turn=0,
        )
        logger.info(f"EmotionalStateManager initialized with {initial_emotion.value}")
    
    def process_scammer_message(
        self,
        message: str,
        turn_count: int,
        psychology_state: Optional[Dict] = None,
    ) -> VictimEmotionalState:
        """
        Process a scammer message and update emotional state.
        
        Args:
            message: The scammer's message
            turn_count: Current turn number
            psychology_state: Optional psychology analysis for better transitions
            
        Returns:
            Updated VictimEmotionalState
        """
        message_lower = message.lower()
        
        # Detect what kind of action the scammer is taking
        action = self._detect_scammer_action(message_lower)
        
        # Calculate level updates
        self._update_levels(message_lower, action, psychology_state)
        
        # Determine if we should transition to a new emotion
        new_emotion = self._determine_transition(action, turn_count)
        
        if new_emotion and new_emotion != self.state.current_emotion:
            self._transition_to(new_emotion, turn_count)
        
        # Natural emotional progression based on turn count
        self._apply_turn_based_progression(turn_count)
        
        return self.state
    
    def _detect_scammer_action(self, message: str) -> str:
        """Detect what action/tactic the scammer is using."""
        # Prize/reward announcement
        if any(w in message for w in ["won", "winner", "prize", "lakh", "crore", "lottery", "जीत", "इनाम"]):
            return "prize_announcement"
        
        # Threat/fear
        if any(w in message for w in ["arrest", "police", "court", "jail", "block", "freeze", "गिरफ्तार", "पुलिस"]):
            return "threat"
        
        # Urgency
        if any(w in message for w in ["now", "immediately", "urgent", "hurry", "today", "तुरंत", "जल्दी"]):
            return "urgency"
        
        # Reassurance
        if any(w in message for w in ["don't worry", "safe", "secure", "trust", "help", "relax", "चिंता मत"]):
            return "reassurance"
        
        # Instruction
        if any(w in message for w in ["click", "send", "enter", "go to", "open", "भेजो", "करो"]):
            return "instruction"
        
        # Praise/thanks
        if any(w in message for w in ["good", "great", "thank", "smart", "अच्छा", "धन्यवाद"]):
            return "thanks_or_praise"
        
        # Confusing technical stuff
        if any(w in message for w in ["otp", "kyc", "verification", "process", "procedure"]):
            return "confusion_created"
        
        return "neutral"
    
    def _update_levels(
        self, 
        message: str, 
        action: str,
        psychology_state: Optional[Dict] = None,
    ) -> None:
        """Update emotional level scores."""
        # Get psychology scores if available
        urgency = 0.5
        aggression = 0.0
        
        if psychology_state:
            urgency = psychology_state.get("urgency_level", 0.5)
            aggression = psychology_state.get("aggression_level", 0.0)
        
        # Update fear based on threats
        if action == "threat":
            self.state.fear_level = min(1.0, self.state.fear_level + 0.3 + aggression * 0.2)
        elif action == "reassurance":
            self.state.fear_level = max(0.0, self.state.fear_level - 0.2)
        
        # Update excitement based on rewards
        if action == "prize_announcement":
            self.state.excitement_level = min(1.0, self.state.excitement_level + 0.4)
        
        # Update confusion
        if action == "confusion_created":
            self.state.confusion_level = min(1.0, self.state.confusion_level + 0.2)
        elif action == "reassurance":
            self.state.confusion_level = max(0.0, self.state.confusion_level - 0.1)
        
        # Update trust over time
        if action in ["prize_announcement", "reassurance"]:
            self._increase_trust(0.1)
        elif action == "thanks_or_praise":
            self._increase_trust(0.15)
        
        # Update compliance
        if self.state.fear_level > 0.5:
            self.state.compliance_level = min(1.0, self.state.compliance_level + 0.1)
        if action == "instruction" and self.state.trust_score > 0.5:
            self.state.compliance_level = min(1.0, self.state.compliance_level + 0.1)
    
    def _increase_trust(self, amount: float) -> None:
        """Increase trust score and update trust level."""
        self.state.trust_score = min(1.0, self.state.trust_score + amount)
        
        # Update trust level enum
        if self.state.trust_score < 0.2:
            self.state.trust_level = TrustLevel.SKEPTICAL
        elif self.state.trust_score < 0.4:
            self.state.trust_level = TrustLevel.NEUTRAL
        elif self.state.trust_score < 0.6:
            self.state.trust_level = TrustLevel.WARMING
        elif self.state.trust_score < 0.8:
            self.state.trust_level = TrustLevel.TRUSTING
        else:
            self.state.trust_level = TrustLevel.FULLY_TRUSTING
    
    def _determine_transition(
        self, 
        action: str, 
        turn_count: int
    ) -> Optional[EmotionalState]:
        """Determine if we should transition to a new emotional state."""
        current = self.state.current_emotion
        
        # Get possible transitions for this action
        triggers = EMOTION_TRANSITION_TRIGGERS.get(action, [])
        
        for from_state, to_state, probability in triggers:
            if current == from_state:
                if random.random() < probability:
                    return to_state
        
        # If no trigger matched, check if we should transition naturally
        config = EMOTION_CONFIGS.get(current)
        if config and config.possible_transitions:
            # Natural transition based on turn count and levels
            if turn_count - self.state.last_transition_turn >= 3:
                # Consider transitioning based on emotional levels
                if self.state.fear_level > 0.7 and EmotionalState.FEARFUL in config.possible_transitions:
                    return EmotionalState.FEARFUL
                elif self.state.excitement_level > 0.7 and EmotionalState.EXCITED in config.possible_transitions:
                    return EmotionalState.EXCITED
                elif self.state.trust_score > 0.7 and EmotionalState.TRUSTING in config.possible_transitions:
                    return EmotionalState.TRUSTING
        
        return None
    
    def _transition_to(self, new_emotion: EmotionalState, turn_count: int) -> None:
        """Transition to a new emotional state."""
        old_emotion = self.state.current_emotion
        self.state.current_emotion = new_emotion
        self.state.emotion_history.append(new_emotion)
        self.state.last_transition_turn = turn_count
        
        logger.debug(
            f"Emotion transition: {old_emotion.value} -> {new_emotion.value} at turn {turn_count}"
        )
    
    def _apply_turn_based_progression(self, turn_count: int) -> None:
        """Apply natural emotional progression based on conversation length."""
        # As conversation progresses, victim becomes more trusting/compliant
        if turn_count > 5:
            self._increase_trust(0.05)
        
        if turn_count > 10:
            self.state.compliance_level = min(1.0, self.state.compliance_level + 0.05)
        
        # Fear decays slightly over time (they're getting used to it)
        if self.state.fear_level > 0.3 and turn_count % 3 == 0:
            self.state.fear_level = max(0.3, self.state.fear_level - 0.05)
    
    def get_emotional_expression(self, language: str = "en") -> str:
        """Get an emotional expression for the current state."""
        config = EMOTION_CONFIGS.get(self.state.current_emotion)
        if not config:
            return ""
        
        lang = language if language in config.expressions else "en"
        expressions = config.expressions.get(lang, config.expressions["en"])
        
        return random.choice(expressions) if expressions else ""
    
    def get_response_modifier(self, language: str = "en") -> Tuple[str, str]:
        """
        Get prefix and suffix modifiers for response based on emotion.
        
        Returns:
            Tuple of (prefix, suffix)
        """
        config = EMOTION_CONFIGS.get(self.state.current_emotion)
        if not config:
            return "", ""
        
        lang = language if language in config.response_prefix else "en"
        
        prefix = random.choice(config.response_prefix.get(lang, [""])) if random.random() > 0.3 else ""
        suffix = random.choice(config.response_suffix.get(lang, [""])) if random.random() > 0.5 else ""
        
        return prefix, suffix
    
    def apply_emotion_to_response(self, response: str, language: str = "en") -> str:
        """
        Apply emotional modifiers to a response.
        
        Args:
            response: The base response
            language: Response language
            
        Returns:
            Emotionally modified response
        """
        prefix, suffix = self.get_response_modifier(language)
        
        # Add expression sometimes
        if random.random() > 0.6:
            expression = self.get_emotional_expression(language)
            if expression:
                response = f"{expression} {response}"
        
        # Apply prefix
        if prefix:
            response = f"{prefix} {response}"
        
        # Apply suffix (less frequently)
        if suffix and random.random() > 0.7:
            response = f"{response} {suffix}"
        
        return response
    
    def get_state_summary(self) -> Dict:
        """Get summary of current emotional state."""
        return {
            "current_emotion": self.state.current_emotion.value,
            "trust_level": self.state.trust_level.value,
            "trust_score": round(self.state.trust_score, 2),
            "fear_level": round(self.state.fear_level, 2),
            "excitement_level": round(self.state.excitement_level, 2),
            "confusion_level": round(self.state.confusion_level, 2),
            "compliance_level": round(self.state.compliance_level, 2),
            "emotions_experienced": [e.value for e in self.state.emotion_history[-5:]],
        }
    
    def reset(self, initial_emotion: EmotionalState = EmotionalState.CURIOUS) -> None:
        """Reset emotional state for new conversation."""
        self.state = VictimEmotionalState(
            current_emotion=initial_emotion,
            trust_level=TrustLevel.NEUTRAL,
            trust_score=0.3,
            fear_level=0.0,
            excitement_level=0.0,
            confusion_level=0.0,
            compliance_level=0.3,
            emotion_history=[initial_emotion],
            last_transition_turn=0,
        )


# Singleton instance
_emotion_manager: Optional[EmotionalStateManager] = None


def get_emotion_manager() -> EmotionalStateManager:
    """Get singleton EmotionalStateManager instance."""
    global _emotion_manager
    if _emotion_manager is None:
        _emotion_manager = EmotionalStateManager()
    return _emotion_manager


def process_emotional_response(
    message: str,
    turn_count: int,
    language: str = "en",
    psychology_state: Optional[Dict] = None,
) -> Tuple[VictimEmotionalState, str]:
    """
    Process a scammer message and get emotional response modifier.
    
    Args:
        message: Scammer's message
        turn_count: Current turn
        language: Response language
        psychology_state: Optional psychology analysis
        
    Returns:
        Tuple of (emotional_state, emotional_expression)
    """
    manager = get_emotion_manager()
    state = manager.process_scammer_message(message, turn_count, psychology_state)
    expression = manager.get_emotional_expression(language)
    
    return state, expression


def apply_emotion_to_response(response: str, language: str = "en") -> str:
    """Apply emotional modifiers to a response."""
    manager = get_emotion_manager()
    return manager.apply_emotion_to_response(response, language)


def reset_emotion_manager() -> None:
    """Reset the emotion manager for new conversation."""
    global _emotion_manager
    if _emotion_manager is not None:
        _emotion_manager.reset()

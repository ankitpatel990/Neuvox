"""
Response Quality Scorer.

Evaluates and scores responses for:
- Extraction likelihood (will this get us info?)
- Believability (does this sound human?)
- Coherence (does this fit the context?)
- Engagement (will scammer keep talking?)

Helps select the BEST response from multiple options.
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ResponseQuality(Enum):
    """Quality rating for responses."""
    EXCELLENT = "excellent"
    GOOD = "good"
    ACCEPTABLE = "acceptable"
    POOR = "poor"
    REJECT = "reject"


@dataclass
class ResponseScore:
    """Complete scoring of a response."""
    overall_score: float  # 0.0 to 1.0
    quality: ResponseQuality
    extraction_score: float
    believability_score: float
    coherence_score: float
    engagement_score: float
    issues: List[str]
    recommendations: List[str]


# Bot-like patterns that reduce believability
BOT_PATTERNS = [
    # Direct info requests (too obvious)
    r"what('s| is) your upi",
    r"share your (upi|account|phone)",
    r"give me your (upi|account|phone)",
    r"tell me your (upi|account|phone)",
    r"your (upi|phone|account) (id|number)?[\?\.]",
    
    # Suspicious/robotic language
    r"i am an ai",
    r"as an ai",
    r"i cannot",
    r"i don't have the ability",
    r"i'm programmed",
    
    # Too formal
    r"dear (sir|madam|customer)",
    r"please be advised",
    r"kindly note",
    r"for your (information|reference)",
    
    # Repetitive/template-like
    r"^(yes|no|okay)[\.\!]?$",
]

# Good extraction patterns that are natural
GOOD_EXTRACTION_PATTERNS = [
    # Offering to pay (gets their UPI)
    r"i('ll| will) (send|pay|transfer)",
    r"where (should|do) i (send|pay|transfer)",
    r"let me (send|pay|transfer)",
    
    # Asking for backup (gets phone)
    r"(if|in case).*(fail|problem|issue)",
    r"phone.*(backup|emergency|case)",
    r"call.*(help|guide|problem)",
    
    # Confusion about methods (gets alternatives)
    r"(upi|app).*(not working|problem|issue|confusing)",
    r"(bank|account|neft|imps).*(instead|alternative)",
]

# Engagement boosters - keep conversation going
ENGAGEMENT_PATTERNS = [
    # Questions that invite response
    r"\?$",
    r"what (should|do|will|can)",
    r"how (do|can|should|will)",
    r"tell me (more|about)",
    
    # Showing interest
    r"(really|wow|amazing|incredible)",
    r"(excited|happy|eager|ready)",
    
    # Commitment phrases
    r"i('m| am) (ready|willing|prepared)",
    r"i want to",
    r"i('ll| will) do",
]

# Red flags that should lower score
RED_FLAGS = [
    # Suspicious/skeptical (breaks persona)
    r"(sounds|seems) (like a |)scam",
    r"(this is|you are) (a )?scam",
    r"i don(')?t (trust|believe)",
    r"how (do i|can i) (know|verify|trust)",
    r"(prove|show) (me|it|that)",
    r"(suspicious|fishy|shady)",
    
    # Breaking character
    r"just kidding",
    r"i('m| am) (joking|testing)",
    r"this (is|was) a test",
    
    # Off-topic
    r"(weather|sports|politics|movie)",
    
    # Empty/useless
    r"^[\.\?\!]+$",
    r"^(ok|okay|yes|no|hmm)+$",
]

# Emotional authenticity patterns
EMOTIONAL_PATTERNS = {
    "excited": [
        r"(wow|amazing|incredible|wonderful)[\!\?]?",
        r"(oh my god|omg|oh no)",
        r"(really|truly|actually)\?",
    ],
    "fearful": [
        r"(please|plz) (don't|no)",
        r"(scared|afraid|worried|nervous)",
        r"(i beg|please help)",
    ],
    "confused": [
        r"(don't|didn't) understand",
        r"(confused|confusing)",
        r"(what|how|why) (do|does|is|are)",
    ],
    "eager": [
        r"(yes|haan|ji) (yes|haan|ji)",
        r"(ready|prepared|willing)",
        r"(want|need) (to|this)",
    ],
}


class ResponseScorer:
    """
    Scores responses for quality, believability, and extraction potential.
    
    Helps the agent select the best response from multiple options
    by evaluating each on multiple criteria.
    """
    
    def __init__(self):
        """Initialize the response scorer."""
        self._compile_patterns()
        logger.info("ResponseScorer initialized")
    
    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns."""
        self.bot_patterns = [re.compile(p, re.IGNORECASE) for p in BOT_PATTERNS]
        self.good_extraction = [re.compile(p, re.IGNORECASE) for p in GOOD_EXTRACTION_PATTERNS]
        self.engagement_patterns = [re.compile(p, re.IGNORECASE) for p in ENGAGEMENT_PATTERNS]
        self.red_flags = [re.compile(p, re.IGNORECASE) for p in RED_FLAGS]
        
        self.emotional_compiled = {
            emotion: [re.compile(p, re.IGNORECASE) for p in patterns]
            for emotion, patterns in EMOTIONAL_PATTERNS.items()
        }
    
    def score_response(
        self,
        response: str,
        context: Optional[Dict] = None,
        target_emotion: str = "eager",
        last_scammer_message: str = "",
    ) -> ResponseScore:
        """
        Score a response on multiple criteria.
        
        Args:
            response: The response to score
            context: Optional conversation context
            target_emotion: What emotion the response should convey
            last_scammer_message: What the scammer just said
            
        Returns:
            ResponseScore with detailed breakdown
        """
        issues = []
        recommendations = []
        
        # Calculate individual scores
        extraction_score = self._score_extraction(response)
        believability_score = self._score_believability(response, issues)
        coherence_score = self._score_coherence(response, last_scammer_message, context, issues)
        engagement_score = self._score_engagement(response)
        
        # Check for red flags
        red_flag_penalty = self._check_red_flags(response, issues)
        
        # Check emotional alignment
        emotion_score = self._score_emotion(response, target_emotion)
        
        # Calculate overall score with weights
        overall_score = (
            extraction_score * 0.30 +
            believability_score * 0.25 +
            coherence_score * 0.20 +
            engagement_score * 0.15 +
            emotion_score * 0.10
        )
        
        # Apply red flag penalty
        overall_score = max(0.0, overall_score - red_flag_penalty)
        
        # Determine quality rating
        quality = self._determine_quality(overall_score)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            extraction_score,
            believability_score,
            coherence_score,
            engagement_score,
        )
        
        return ResponseScore(
            overall_score=round(overall_score, 3),
            quality=quality,
            extraction_score=round(extraction_score, 3),
            believability_score=round(believability_score, 3),
            coherence_score=round(coherence_score, 3),
            engagement_score=round(engagement_score, 3),
            issues=issues,
            recommendations=recommendations,
        )
    
    def _score_extraction(self, response: str) -> float:
        """Score how likely this response is to extract information."""
        score = 0.5  # Base score
        
        # Check for good extraction patterns
        for pattern in self.good_extraction:
            if pattern.search(response):
                score += 0.15
        
        # Asking for payment details is good
        if re.search(r"(upi|account|phone|number|ifsc)", response, re.IGNORECASE):
            score += 0.1
        
        # Offering to send money is great
        if re.search(r"(i'll|let me|i will) (send|pay|transfer)", response, re.IGNORECASE):
            score += 0.15
        
        # Asking for backup/alternative is good
        if re.search(r"(backup|alternative|another|if.*fail)", response, re.IGNORECASE):
            score += 0.1
        
        return min(1.0, score)
    
    def _score_believability(self, response: str, issues: List[str]) -> float:
        """Score how believable/human the response sounds."""
        score = 1.0  # Start high, deduct for issues
        
        # Check for bot patterns
        for pattern in self.bot_patterns:
            if pattern.search(response):
                score -= 0.15
                issues.append(f"Bot-like pattern detected")
        
        # Check response length (too short or too long is suspicious)
        word_count = len(response.split())
        if word_count < 3:
            score -= 0.2
            issues.append("Response too short")
        elif word_count > 50:
            score -= 0.1
            issues.append("Response too long")
        
        # Check for natural language features
        if re.search(r"[!?]", response):
            score += 0.05  # Punctuation is good
        
        if re.search(r"(um|uh|hmm|oh|ah)", response, re.IGNORECASE):
            score += 0.05  # Fillers are natural
        
        # Check for contractions (more natural)
        if re.search(r"(i'm|i'll|don't|can't|won't|it's)", response, re.IGNORECASE):
            score += 0.05
        
        return max(0.0, min(1.0, score))
    
    def _score_coherence(
        self,
        response: str,
        last_message: str,
        context: Optional[Dict],
        issues: List[str],
    ) -> float:
        """Score how coherent the response is with context."""
        if not last_message:
            return 0.7  # No context to compare
        
        score = 0.8  # Base score
        
        response_lower = response.lower()
        message_lower = last_message.lower()
        
        # Check topic alignment
        # If scammer mentions arrest, we shouldn't talk about winning
        if any(w in message_lower for w in ["arrest", "police", "court", "jail"]):
            if any(w in response_lower for w in ["won", "winner", "prize", "lottery"]):
                score -= 0.3
                issues.append("Topic mismatch: threat vs prize")
        
        # If scammer asks for OTP, we should address it
        if "otp" in message_lower:
            if "otp" not in response_lower and "send" not in response_lower:
                score -= 0.1
                issues.append("Didn't address OTP request")
        
        # If scammer gave info (UPI, phone), acknowledge it
        if "@" in last_message or re.search(r"\d{10}", last_message):
            if not any(w in response_lower for w in ["got", "noted", "okay", "received", "saved", "trying"]):
                score -= 0.1
                issues.append("Didn't acknowledge scammer's info")
        
        return max(0.0, min(1.0, score))
    
    def _score_engagement(self, response: str) -> float:
        """Score how likely this response keeps the conversation going."""
        score = 0.5  # Base score
        
        # Check for engagement patterns
        for pattern in self.engagement_patterns:
            if pattern.search(response):
                score += 0.1
        
        # Questions keep conversation going
        if response.strip().endswith("?"):
            score += 0.15
        
        # Multiple sentences show engagement
        sentence_count = len(re.split(r"[.!?]+", response.strip()))
        if sentence_count >= 2:
            score += 0.1
        
        # Showing emotion is engaging
        if re.search(r"[!]{1,3}", response):
            score += 0.05
        
        return min(1.0, score)
    
    def _score_emotion(self, response: str, target_emotion: str) -> float:
        """Score emotional alignment with target."""
        if target_emotion not in self.emotional_compiled:
            return 0.5  # Unknown emotion
        
        patterns = self.emotional_compiled[target_emotion]
        matches = sum(1 for p in patterns if p.search(response))
        
        # More matches = better alignment
        return min(1.0, 0.5 + matches * 0.2)
    
    def _check_red_flags(self, response: str, issues: List[str]) -> float:
        """Check for red flags and return penalty amount."""
        penalty = 0.0
        
        for pattern in self.red_flags:
            if pattern.search(response):
                penalty += 0.15
                issues.append("Red flag detected")
        
        return min(0.5, penalty)  # Cap penalty
    
    def _determine_quality(self, score: float) -> ResponseQuality:
        """Determine quality rating from score."""
        if score >= 0.85:
            return ResponseQuality.EXCELLENT
        elif score >= 0.7:
            return ResponseQuality.GOOD
        elif score >= 0.5:
            return ResponseQuality.ACCEPTABLE
        elif score >= 0.3:
            return ResponseQuality.POOR
        else:
            return ResponseQuality.REJECT
    
    def _generate_recommendations(
        self,
        extraction: float,
        believability: float,
        coherence: float,
        engagement: float,
    ) -> List[str]:
        """Generate recommendations for improvement."""
        recommendations = []
        
        if extraction < 0.6:
            recommendations.append("Add offer to pay/send to extract payment details")
        
        if believability < 0.7:
            recommendations.append("Use more natural language and contractions")
        
        if coherence < 0.7:
            recommendations.append("Address scammer's last message more directly")
        
        if engagement < 0.6:
            recommendations.append("End with a question to keep conversation going")
        
        return recommendations
    
    def select_best_response(
        self,
        responses: List[str],
        context: Optional[Dict] = None,
        target_emotion: str = "eager",
        last_scammer_message: str = "",
    ) -> Tuple[str, ResponseScore]:
        """
        Select the best response from multiple options.
        
        Args:
            responses: List of response options
            context: Conversation context
            target_emotion: Target emotional state
            last_scammer_message: Last scammer message
            
        Returns:
            Tuple of (best_response, score)
        """
        if not responses:
            return "", ResponseScore(
                overall_score=0.0,
                quality=ResponseQuality.REJECT,
                extraction_score=0.0,
                believability_score=0.0,
                coherence_score=0.0,
                engagement_score=0.0,
                issues=["No responses provided"],
                recommendations=[],
            )
        
        scored_responses = []
        
        for response in responses:
            score = self.score_response(
                response,
                context,
                target_emotion,
                last_scammer_message,
            )
            scored_responses.append((response, score))
        
        # Sort by overall score
        scored_responses.sort(key=lambda x: x[1].overall_score, reverse=True)
        
        best_response, best_score = scored_responses[0]
        
        logger.debug(
            f"Selected best response with score {best_score.overall_score:.2f} "
            f"({best_score.quality.value})"
        )
        
        return best_response, best_score
    
    def improve_response(
        self,
        response: str,
        score: ResponseScore,
        language: str = "en",
    ) -> str:
        """
        Attempt to improve a response based on its score.
        
        Args:
            response: Original response
            score: The score it received
            language: Response language
            
        Returns:
            Improved response
        """
        improved = response
        
        # If extraction is low, add payment offer
        if score.extraction_score < 0.5:
            suffixes = {
                "en": " Where should I send the money?",
                "hi": " पैसे कहां भेजूं?",
                "hinglish": " Paisa kahan bhejun?",
            }
            improved = improved.rstrip("!?.") + suffixes.get(language, suffixes["en"])
        
        # If engagement is low, add question
        if score.engagement_score < 0.5 and not improved.endswith("?"):
            improved = improved.rstrip("!.") + "?"
        
        # If believability is low, remove formal language
        improved = re.sub(r"dear (sir|madam|customer)", "", improved, flags=re.IGNORECASE)
        improved = re.sub(r"kindly note", "", improved, flags=re.IGNORECASE)
        improved = re.sub(r"please be advised", "", improved, flags=re.IGNORECASE)
        
        return improved.strip()


# Singleton instance
_scorer: Optional[ResponseScorer] = None


def get_response_scorer() -> ResponseScorer:
    """Get singleton ResponseScorer instance."""
    global _scorer
    if _scorer is None:
        _scorer = ResponseScorer()
    return _scorer


def score_response(
    response: str,
    context: Optional[Dict] = None,
    target_emotion: str = "eager",
    last_scammer_message: str = "",
) -> ResponseScore:
    """Convenience function to score a response."""
    scorer = get_response_scorer()
    return scorer.score_response(response, context, target_emotion, last_scammer_message)


def select_best_response(
    responses: List[str],
    context: Optional[Dict] = None,
    target_emotion: str = "eager",
    last_scammer_message: str = "",
) -> Tuple[str, ResponseScore]:
    """Convenience function to select best response."""
    scorer = get_response_scorer()
    return scorer.select_best_response(responses, context, target_emotion, last_scammer_message)

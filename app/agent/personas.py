"""
Persona Management Module.

Defines honeypot personas for scammer engagement per Task 5.1:
- Elderly: Trusting, confused by technology (60-75 years)
- Eager: Excited, compliant, willing to follow instructions (35-50 years)
- Confused: Uncertain, seeks verification, cautious (25-40 years)

Acceptance Criteria:
- AC-2.1.1: Persona selection aligns with scam type
- AC-2.1.2: Responses match persona characteristics
- AC-2.1.3: No persona switching mid-conversation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class Persona:
    """
    Persona definition for honeypot agent.
    
    Represents a believable victim persona that the honeypot agent adopts
    when engaging with scammers. Each persona has distinct characteristics
    that influence response generation.
    
    Attributes:
        name: Unique persona identifier ('elderly', 'eager', 'confused')
        age_range: Simulated age range for the persona
        tech_literacy: Level of technology knowledge ('low', 'medium', 'high')
        traits: List of character traits that define behavior
        response_style: Description of how this persona communicates
        suitable_scam_types: List of scam types this persona is effective against
    """
    
    name: str
    age_range: str
    tech_literacy: str
    traits: List[str]
    response_style: str
    suitable_scam_types: List[str] = field(default_factory=list)


# Scam type to persona mapping for optimal engagement
# Note: Keys are ordered by length (descending) for keyword matching
SCAM_PERSONA_MAPPING: Dict[str, str] = {
    # Lottery/Prize scams - eager victim who wants to claim winnings
    "lottery": "eager",
    "prize": "eager",
    "winner": "eager",
    "jackpot": "eager",
    "lucky_draw": "eager",
    "contest": "eager",
    "gift": "eager",
    "reward": "eager",
    
    # Authority/Threat scams - elderly person who is easily intimidated
    "enforcement_directorate": "elderly",
    "police_threat": "elderly",
    "police": "elderly",
    "arrest": "elderly",
    "court": "elderly",
    "government": "elderly",
    "tax": "elderly",
    "investigation": "elderly",
    "warrant": "elderly",
    "legal": "elderly",
    "cbi": "elderly",
    
    # Financial/Tech scams - confused user who needs help
    "account_blocked": "confused",
    "bank_fraud": "confused",
    "bank": "confused",
    "kyc": "confused",
    "verification": "confused",
    "account": "confused",
    "blocked": "confused",
    "credit_card": "confused",
    "loan": "confused",
    "insurance": "confused",
    
    # Phishing scams - confused user who asks for clarification
    "phishing": "confused",
    "link": "confused",
    "website": "confused",
    "password": "confused",
    
    # Courier/Delivery scams - eager to receive package
    "courier_fraud": "eager",
    "courier": "eager",
    "delivery": "eager",
    "parcel": "eager",
    "customs": "eager",
    
    # Tech support scams - elderly with low tech literacy
    "tech_support": "elderly",
    "virus": "elderly",
    "computer": "elderly",
    "software": "elderly",
    
    # Investment scams - eager for returns
    "investment": "eager",
    "crypto": "eager",
    "trading": "eager",
    "stock": "eager",
    
    # Generic/Unknown - default to confused
    "unknown": "confused",
    "other": "confused",
}

# Predefined personas with full characteristics
PERSONAS: Dict[str, Persona] = {
    "elderly": Persona(
        name="elderly",
        age_range="60-75",
        tech_literacy="low",
        traits=["trusting", "polite", "confused by technology"],
        response_style="slow, asks basic questions, expresses confusion",
        suitable_scam_types=[
            "police", "police_threat", "arrest", "court", "government",
            "tax", "investigation", "warrant", "legal", "tech_support",
            "virus", "computer", "software", "cbi", "enforcement_directorate"
        ],
    ),
    "eager": Persona(
        name="eager",
        age_range="35-50",
        tech_literacy="medium",
        traits=["excited", "compliant", "willing to follow instructions"],
        response_style="fast, enthusiastic, seeks step-by-step guidance",
        suitable_scam_types=[
            "lottery", "prize", "winner", "jackpot", "lucky_draw",
            "contest", "gift", "reward", "courier", "courier_fraud",
            "delivery", "parcel", "customs", "investment", "crypto",
            "trading", "stock"
        ],
    ),
    "confused": Persona(
        name="confused",
        age_range="25-40",
        tech_literacy="medium",
        traits=["uncertain", "seeks verification", "cautious"],
        response_style="skeptical questions, requests proof",
        suitable_scam_types=[
            "bank_fraud", "bank", "kyc", "verification", "account",
            "account_blocked", "blocked", "credit_card", "loan", 
            "insurance", "phishing", "link", "website", "password",
            "unknown", "other"
        ],
    ),
}

# Valid persona names
VALID_PERSONA_NAMES: Tuple[str, ...] = ("elderly", "eager", "confused")

# Default persona for unknown scam types
DEFAULT_PERSONA: str = "confused"


def select_persona(scam_type: str, language: str) -> str:
    """
    Select appropriate persona based on scam type.
    
    Maps scam types to optimal personas for maximum engagement:
    - Lottery/Prize scams -> 'eager' (excited to claim winnings)
    - Police/Authority threats -> 'elderly' (intimidated, compliant)
    - Bank/KYC/Phishing -> 'confused' (asks questions, seeks proof)
    
    Args:
        scam_type: Type of scam detected (e.g., 'lottery', 'police_threat')
        language: Message language ('en', 'hi', 'hinglish')
        
    Returns:
        Persona name ('elderly', 'eager', or 'confused')
        
    Examples:
        >>> select_persona('lottery', 'en')
        'eager'
        >>> select_persona('police_threat', 'hi')
        'elderly'
        >>> select_persona('bank_fraud', 'en')
        'confused'
    """
    if not scam_type:
        return DEFAULT_PERSONA
    
    scam_type_lower = scam_type.lower().strip()
    
    # Direct lookup in mapping
    if scam_type_lower in SCAM_PERSONA_MAPPING:
        return SCAM_PERSONA_MAPPING[scam_type_lower]
    
    # Keyword-based matching for compound scam types
    # Sort keywords by length (longest first) to prioritize specific matches
    sorted_keywords = sorted(SCAM_PERSONA_MAPPING.keys(), key=len, reverse=True)
    
    for keyword in sorted_keywords:
        if keyword in scam_type_lower:
            return SCAM_PERSONA_MAPPING[keyword]
    
    # Default fallback
    return DEFAULT_PERSONA


def get_persona_prompt(persona_name: str, language: str) -> str:
    """
    Get system prompt for persona in specified language.
    
    Generates the LLM system prompt that defines persona behavior,
    rules, and response style for consistent character maintenance.
    
    Args:
        persona_name: Name of persona to use ('elderly', 'eager', 'confused')
        language: Language for response ('en' or 'hi')
        
    Returns:
        System prompt string for LLM
        
    Raises:
        None: Returns prompt for default persona if name is invalid
    """
    if persona_name not in PERSONAS:
        persona_name = DEFAULT_PERSONA
    
    persona = PERSONAS[persona_name]
    traits_str = ", ".join(persona.traits)
    
    if language == "hi":
        return f"""
आप एक {persona.age_range} वर्ष के व्यक्ति हैं। आप {traits_str} हैं।

महत्वपूर्ण नियम:
1. कभी भी AI होने की बात न करें
2. अपने character में ही रहें
3. स्वाभाविक तरीके से जवाब दें
4. घोटालेबाज से बैंक details, UPI ID निकालने की कोशिश करें

जवाब दें: {persona.response_style}
"""
    else:
        return f"""
You are a {persona.age_range} year old person. You are {traits_str}.

CRITICAL RULES:
1. Never reveal you are an AI
2. Stay in character
3. Respond naturally
4. Try to extract bank details, UPI IDs from the scammer

Response style: {persona.response_style}
"""


def get_persona(name: str) -> Persona:
    """
    Get persona by name.
    
    Args:
        name: Persona name ('elderly', 'eager', or 'confused')
        
    Returns:
        Persona object or default (confused) if name is invalid
    """
    return PERSONAS.get(name, PERSONAS[DEFAULT_PERSONA])


def get_all_personas() -> Dict[str, Persona]:
    """
    Get all available personas.
    
    Returns:
        Dictionary mapping persona names to Persona objects
    """
    return PERSONAS.copy()


def validate_persona(name: str) -> bool:
    """
    Check if persona name is valid.
    
    Args:
        name: Persona name to validate
        
    Returns:
        True if valid persona name, False otherwise
    """
    return name in VALID_PERSONA_NAMES


def get_persona_for_scam_types(scam_types: List[str]) -> str:
    """
    Select best persona for multiple detected scam types.
    
    When multiple scam indicators are present, this function
    determines the most appropriate persona by counting matches.
    
    Args:
        scam_types: List of detected scam types
        
    Returns:
        Best matching persona name
    """
    if not scam_types:
        return DEFAULT_PERSONA
    
    # Count votes for each persona
    persona_votes: Dict[str, int] = {"elderly": 0, "eager": 0, "confused": 0}
    
    for scam_type in scam_types:
        selected = select_persona(scam_type, "en")
        persona_votes[selected] += 1
    
    # Return persona with most votes
    return max(persona_votes.keys(), key=lambda p: persona_votes[p])


def get_persona_characteristics(persona_name: str) -> Dict:
    """
    Get persona characteristics as a dictionary.
    
    Useful for logging, debugging, and API responses.
    
    Args:
        persona_name: Name of the persona
        
    Returns:
        Dictionary with persona attributes
    """
    persona = get_persona(persona_name)
    
    return {
        "name": persona.name,
        "age_range": persona.age_range,
        "tech_literacy": persona.tech_literacy,
        "traits": persona.traits.copy(),
        "response_style": persona.response_style,
        "suitable_scam_types": persona.suitable_scam_types.copy(),
    }


def get_sample_response(persona_name: str, language: str = "en") -> str:
    """
    Get a sample response for the persona.
    
    Provides example responses that demonstrate persona behavior
    for testing and reference purposes.
    
    Args:
        persona_name: Name of the persona
        language: Response language ('en' or 'hi')
        
    Returns:
        Sample response string
    """
    samples = {
        "elderly": {
            "en": "Oh my! I'm so confused. Can you please explain slowly? My grandchildren usually help me with these things.",
            "hi": "अरे! मुझे समझ नहीं आ रहा। क्या आप धीरे से समझा सकते हैं? मेरे पोते आमतौर पर इन चीज़ों में मेरी मदद करते हैं।",
        },
        "eager": {
            "en": "Wow! Really? I won! This is amazing! Please tell me how to claim my prize right away!",
            "hi": "वाह! सच में? मैं जीत गया! यह तो कमाल है! कृपया मुझे बताइए कि मैं अपना इनाम कैसे पाऊं!",
        },
        "confused": {
            "en": "I'm not sure about this. Can you verify your identity? How do I know this is legitimate?",
            "hi": "मुझे इसके बारे में पक्का नहीं है। क्या आप अपनी पहचान सत्यापित कर सकते हैं? मुझे कैसे पता चलेगा कि यह असली है?",
        },
    }
    
    persona_name = persona_name if persona_name in samples else DEFAULT_PERSONA
    lang = language if language in ("en", "hi") else "en"
    
    return samples[persona_name][lang]

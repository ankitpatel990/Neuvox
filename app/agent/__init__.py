"""
Agent Layer - LangGraph-based agentic honeypot system.

This module contains the multi-turn conversation agent that engages scammers
using dynamic personas and strategic response generation.

ENHANCED with:
- Safety/Jailbreak Detection
- Scammer Psychology Tracking
- Emotional State Machine
- Context Engine
- Advanced Scam Detection
"""

from app.agent.honeypot import (
    HoneypotAgent,
    HoneypotState,
    get_honeypot_agent,
    reset_honeypot_agent,
    MAX_TURNS,
    EXTRACTION_CONFIDENCE_THRESHOLD,
)
from app.agent.personas import (
    Persona,
    PERSONAS,
    SCAM_PERSONA_MAPPING,
    VALID_PERSONA_NAMES,
    DEFAULT_PERSONA,
    select_persona,
    get_persona_prompt,
    get_persona,
    get_all_personas,
    validate_persona,
    get_persona_for_scam_types,
    get_persona_characteristics,
    get_sample_response,
)
from app.agent.strategies import EngagementStrategy, get_strategy
from app.agent.prompts import get_system_prompt, get_response_prompt

# NEW: Safety Module
from app.agent.safety import (
    SafetyModule,
    SafetyAnalysis,
    ThreatLevel,
    get_safety_module,
    check_message_safety,
    reset_safety_module,
)

# NEW: Psychology Module
from app.agent.psychology import (
    ScammerPsychologyTracker,
    PsychologyState,
    ScammerTactic,
    PressureLevel,
    get_psychology_tracker,
    analyze_scammer_psychology,
    reset_psychology_tracker,
)

# NEW: Emotions Module
from app.agent.emotions import (
    EmotionalStateManager,
    VictimEmotionalState,
    EmotionalState,
    TrustLevel,
    get_emotion_manager,
    process_emotional_response,
    apply_emotion_to_response,
    reset_emotion_manager,
)

# NEW: Context Engine
from app.agent.context_engine import (
    ContextEngine,
    ConversationContext,
    ScamNarrativeStage,
    get_context_engine,
    analyze_context,
    get_strategic_response,
    reset_context_engine,
)

# NEW: Advanced Scam Detector
from app.agent.scam_detector_v2 import (
    AdvancedScamDetector,
    ScamType,
    ScamTypeResult,
    get_advanced_detector,
    detect_scam_type,
    get_recommended_persona,
    reset_advanced_detector,
)

# NEW: Enhanced Honeypot (THE WINNING AGENT)
from app.agent.enhanced_honeypot import (
    EnhancedHoneypotAgent,
    get_enhanced_agent,
    reset_enhanced_agent,
)

__all__ = [
    # Honeypot Agent
    "HoneypotAgent",
    "HoneypotState",
    "get_honeypot_agent",
    "reset_honeypot_agent",
    "MAX_TURNS",
    "EXTRACTION_CONFIDENCE_THRESHOLD",
    
    # Persona System
    "Persona",
    "PERSONAS",
    "SCAM_PERSONA_MAPPING",
    "VALID_PERSONA_NAMES",
    "DEFAULT_PERSONA",
    "select_persona",
    "get_persona_prompt",
    "get_persona",
    "get_all_personas",
    "validate_persona",
    "get_persona_for_scam_types",
    "get_persona_characteristics",
    "get_sample_response",
    
    # Strategies
    "EngagementStrategy",
    "get_strategy",
    
    # Prompts
    "get_system_prompt",
    "get_response_prompt",
    
    # NEW: Safety
    "SafetyModule",
    "SafetyAnalysis",
    "ThreatLevel",
    "get_safety_module",
    "check_message_safety",
    "reset_safety_module",
    
    # NEW: Psychology
    "ScammerPsychologyTracker",
    "PsychologyState",
    "ScammerTactic",
    "PressureLevel",
    "get_psychology_tracker",
    "analyze_scammer_psychology",
    "reset_psychology_tracker",
    
    # NEW: Emotions
    "EmotionalStateManager",
    "VictimEmotionalState",
    "EmotionalState",
    "TrustLevel",
    "get_emotion_manager",
    "process_emotional_response",
    "apply_emotion_to_response",
    "reset_emotion_manager",
    
    # NEW: Context
    "ContextEngine",
    "ConversationContext",
    "ScamNarrativeStage",
    "get_context_engine",
    "analyze_context",
    "get_strategic_response",
    "reset_context_engine",
    
    # NEW: Advanced Scam Detection
    "AdvancedScamDetector",
    "ScamType",
    "ScamTypeResult",
    "get_advanced_detector",
    "detect_scam_type",
    "get_recommended_persona",
    "reset_advanced_detector",
    
    # NEW: Enhanced Honeypot (THE WINNING AGENT)
    "EnhancedHoneypotAgent",
    "get_enhanced_agent",
    "reset_enhanced_agent",
]

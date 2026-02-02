"""
Enhanced Honeypot Agent - The SMARTEST Scam Engagement AI.

Integrates all advanced modules for superior scam engagement:
- Safety Module: Jailbreak protection
- Psychology Tracker: Scammer behavior analysis
- Emotional State Machine: Realistic victim journey
- Context Engine: Deep conversation understanding
- Advanced Scam Detector: 15+ scam types
- Response Scorer: Best response selection

This is the module that will WIN the competition.
"""

import os
import random
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from app.config import settings
from app.utils.logger import get_logger
from app.utils.response_scorer import get_response_scorer, score_response

# Import all new modules
from app.agent.safety import get_safety_module, check_message_safety
from app.agent.psychology import get_psychology_tracker, analyze_scammer_psychology
from app.agent.emotions import get_emotion_manager, apply_emotion_to_response
from app.agent.context_engine import get_context_engine, analyze_context
from app.agent.scam_detector_v2 import get_advanced_detector, detect_scam_type

logger = get_logger(__name__)

# Enhanced configuration
MAX_TURNS = 20
EXTRACTION_CONFIDENCE_THRESHOLD = 0.95


class EnhancedHoneypotAgent:
    """
    The ULTIMATE honeypot agent for winning the competition.
    
    Features:
    1. Multi-layer security (jailbreak detection)
    2. Psychology-based adaptive responses
    3. Emotional realism
    4. Deep context understanding
    5. 15+ scam type handling
    6. Response quality scoring
    7. Strategic information extraction
    """
    
    def __init__(self, use_llm: bool = True):
        """Initialize the enhanced honeypot agent."""
        self._initialized = False
        self.llm = None
        
        # Initialize all modules
        self.safety_module = get_safety_module()
        self.psychology_tracker = get_psychology_tracker()
        self.emotion_manager = get_emotion_manager()
        self.context_engine = get_context_engine()
        self.scam_detector = get_advanced_detector()
        self.response_scorer = get_response_scorer()
        
        if use_llm:
            self._initialize_llm()
        
        self._initialized = True
        logger.info("EnhancedHoneypotAgent initialized with all modules")
    
    def _initialize_llm(self) -> None:
        """Initialize the LLM client."""
        try:
            from langchain_groq import ChatGroq
            
            api_key = settings.GROQ_API_KEY
            if not api_key:
                logger.warning("GROQ_API_KEY not set, LLM features disabled")
                return
            
            self.llm = ChatGroq(
                model=settings.GROQ_MODEL,
                api_key=api_key,
                temperature=settings.GROQ_TEMPERATURE,
                max_tokens=settings.GROQ_MAX_TOKENS,
            )
            logger.info(f"ChatGroq initialized with model: {settings.GROQ_MODEL}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            self.llm = None
    
    def engage(
        self,
        message: str,
        session_state: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """
        Main engagement method with all enhancements.
        
        Args:
            message: Scammer's message
            session_state: Existing session state
            
        Returns:
            Updated session state with agent response
        """
        # Initialize new session if needed
        if session_state is None:
            session_state = self._create_new_session(message)
        else:
            session_state = self._update_session(session_state, message)
        
        turn_count = session_state.get("turn_count", 1)
        language = session_state.get("language", "en")
        
        # ═══════════════════════════════════════════════════════════
        # STEP 1: SAFETY CHECK - Detect jailbreak attempts
        # ═══════════════════════════════════════════════════════════
        safety_result = check_message_safety(message, language)
        
        if not safety_result.is_safe:
            logger.warning(f"Threat detected: {safety_result.threat_type}")
            
            # Use deflection response
            agent_response = safety_result.deflection_response
            session_state = self._add_agent_message(
                session_state, agent_response, turn_count
            )
            session_state["last_threat"] = safety_result.threat_type
            return session_state
        
        # ═══════════════════════════════════════════════════════════
        # STEP 2: PSYCHOLOGY ANALYSIS - Understand scammer tactics
        # ═══════════════════════════════════════════════════════════
        psychology_state = analyze_scammer_psychology(
            message, 
            turn_count,
            session_state.get("messages", [])
        )
        
        session_state["psychology"] = {
            "urgency": psychology_state.urgency_level,
            "aggression": psychology_state.aggression_level,
            "frustration": psychology_state.frustration_level,
            "primary_tactic": psychology_state.primary_tactic.value,
            "recommended_strategy": psychology_state.recommended_strategy,
            "extraction_readiness": psychology_state.extraction_readiness,
        }
        
        # ═══════════════════════════════════════════════════════════
        # STEP 3: SCAM TYPE DETECTION - Identify specific scam
        # ═══════════════════════════════════════════════════════════
        scam_result = detect_scam_type(
            message,
            session_state.get("messages", [])
        )
        
        session_state["scam_type"] = scam_result.primary_type.value
        session_state["scam_confidence"] = scam_result.primary_confidence
        
        # Update persona based on scam type
        if turn_count <= 2 or session_state.get("persona") == "confused":
            session_state["persona"] = scam_result.recommended_persona
        
        # ═══════════════════════════════════════════════════════════
        # STEP 4: CONTEXT ANALYSIS - Deep understanding
        # ═══════════════════════════════════════════════════════════
        context = analyze_context(message, "scammer", turn_count, language)
        
        session_state["context"] = {
            "narrative_stage": context.narrative_stage.value,
            "info_gaps": list(context.info_gaps),
            "scammer_requested": list(context.requested_info),
        }
        
        # ═══════════════════════════════════════════════════════════
        # STEP 5: EMOTIONAL STATE UPDATE
        # ═══════════════════════════════════════════════════════════
        emotion_state = self.emotion_manager.process_scammer_message(
            message, 
            turn_count,
            session_state.get("psychology")
        )
        
        session_state["emotion"] = {
            "current": emotion_state.current_emotion.value,
            "trust_level": emotion_state.trust_level.value,
            "trust_score": emotion_state.trust_score,
            "fear_level": emotion_state.fear_level,
            "compliance_level": emotion_state.compliance_level,
        }
        
        # ═══════════════════════════════════════════════════════════
        # STEP 6: GENERATE RESPONSE
        # ═══════════════════════════════════════════════════════════
        agent_response = self._generate_smart_response(
            message=message,
            session_state=session_state,
            psychology_state=psychology_state,
            scam_result=scam_result,
            context=context,
            emotion_state=emotion_state,
        )
        
        # ═══════════════════════════════════════════════════════════
        # STEP 7: SCORE AND IMPROVE RESPONSE
        # ═══════════════════════════════════════════════════════════
        response_score = score_response(
            agent_response,
            session_state.get("context"),
            emotion_state.current_emotion.value,
            message
        )
        
        # If score is poor, try to improve
        if response_score.overall_score < 0.6:
            agent_response = self.response_scorer.improve_response(
                agent_response, response_score, language
            )
        
        # Apply emotional modifiers
        agent_response = apply_emotion_to_response(agent_response, language)
        
        session_state["response_score"] = response_score.overall_score
        
        # ═══════════════════════════════════════════════════════════
        # STEP 8: EXTRACT INTELLIGENCE
        # ═══════════════════════════════════════════════════════════
        from app.models.extractor import extract_intelligence
        
        full_text = " ".join(
            m.get("message", "") for m in session_state.get("messages", [])
        ) + " " + message
        
        intel, intel_confidence = extract_intelligence(full_text)
        session_state["extracted_intel"] = intel
        session_state["extraction_confidence"] = intel_confidence
        
        # ═══════════════════════════════════════════════════════════
        # STEP 9: ADD RESPONSE AND CHECK TERMINATION
        # ═══════════════════════════════════════════════════════════
        session_state = self._add_agent_message(
            session_state, agent_response, turn_count
        )
        
        # Check termination
        if turn_count >= MAX_TURNS:
            session_state["terminated"] = True
            session_state["max_turns_reached"] = True
        elif intel_confidence >= EXTRACTION_CONFIDENCE_THRESHOLD:
            session_state["terminated"] = True
        else:
            session_state["terminated"] = False
        
        return session_state
    
    def _generate_smart_response(
        self,
        message: str,
        session_state: Dict,
        psychology_state: Any,
        scam_result: Any,
        context: Any,
        emotion_state: Any,
    ) -> str:
        """
        Generate the smartest possible response.
        
        Uses multiple strategies and selects the best one.
        """
        language = session_state.get("language", "en")
        turn_count = session_state.get("turn_count", 1)
        persona = session_state.get("persona", "confused")
        
        # Generate multiple response candidates
        candidates = []
        
        # Strategy 1: Psychology-based response
        psych_response = self._get_psychology_based_response(
            psychology_state, language, turn_count
        )
        if psych_response:
            candidates.append(psych_response)
        
        # Strategy 2: Context-based strategic question
        should_extract, target = self.context_engine.should_extract_now()
        if should_extract:
            strategic_q = self.context_engine.get_strategic_question(target, language)
            if strategic_q:
                candidates.append(strategic_q)
        
        # Strategy 3: Coherent follow-up
        coherent = self.context_engine.get_coherent_follow_up(message)
        if coherent:
            candidates.append(coherent)
        
        # Strategy 4: Context-appropriate response
        ctx_response = self.context_engine.get_context_appropriate_response(
            emotion_state.current_emotion.value, language
        )
        if ctx_response:
            candidates.append(ctx_response)
        
        # Strategy 5: LLM-generated response
        if self.llm is not None:
            try:
                llm_response = self._generate_llm_response(
                    message, session_state, psychology_state, 
                    scam_result, emotion_state
                )
                if llm_response:
                    candidates.append(llm_response)
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
        
        # Strategy 6: Fallback responses
        fallback = self._get_fallback_response(
            scam_result.primary_type.value, turn_count, language
        )
        candidates.append(fallback)
        
        # Select the best response
        if len(candidates) > 1:
            best_response, score = self.response_scorer.select_best_response(
                candidates,
                session_state.get("context"),
                emotion_state.current_emotion.value,
                message
            )
            return best_response
        
        return candidates[0] if candidates else fallback
    
    def _get_psychology_based_response(
        self,
        psychology_state: Any,
        language: str,
        turn_count: int,
    ) -> Optional[str]:
        """Generate response based on psychology analysis."""
        strategy = psychology_state.recommended_strategy
        
        responses = {
            "extract_aggressively": {
                "en": [
                    "I'm ready to send now! Give me UPI, phone, and account number - everything!",
                    "Let me complete this! Tell me all your payment details!",
                    "I want to pay immediately! UPI ID? Phone number? Bank account?",
                ],
                "hi": [
                    "अभी भेजता हूं! UPI, फोन, account - सब बताइए!",
                    "पूरा करना है! सारी payment details दीजिए!",
                ],
            },
            "show_fear_comply": {
                "en": [
                    "Please don't arrest me! I'll pay right now! Just tell me where!",
                    "I'm so scared! I'll do anything! Give me your details!",
                    "Please help me! I don't want trouble! Tell me where to send money!",
                ],
                "hi": [
                    "Please गिरफ्तार मत करो! अभी pay करता हूं! कहां भेजूं?",
                    "बहुत डर लग रहा है! कुछ भी करूंगा! Details दो!",
                ],
            },
            "act_confused": {
                "en": [
                    "I'm confused... can you explain slowly? What should I do exactly?",
                    "Sorry, I don't understand technology. Can you guide me step by step?",
                    "This is confusing... but I want to help. Tell me simply what to do.",
                ],
                "hi": [
                    "समझ नहीं आया... धीरे से समझाइए? क्या करना है?",
                    "मुझे technology नहीं आती। Step by step बताइए?",
                ],
            },
            "offer_payment": {
                "en": [
                    "Okay okay! I'll pay! Just give me your UPI ID!",
                    "I'm ready to send money! Tell me where - UPI or bank account?",
                    "I'll transfer now! What's your payment details?",
                ],
                "hi": [
                    "ठीक है ठीक है! Pay करता हूं! UPI ID दो!",
                    "पैसे भेजने को तैयार! कहां भेजूं - UPI या account?",
                ],
            },
            "build_rapport": {
                "en": [
                    "Really? This is interesting! Tell me more about it!",
                    "Wow! I didn't know about this! What happens next?",
                    "Okay, I'm listening! Please continue!",
                ],
                "hi": [
                    "सच में? यह interesting है! और बताइए!",
                    "वाह! मुझे नहीं पता था! आगे क्या होगा?",
                ],
            },
            "express_eagerness": {
                "en": [
                    "Yes yes! I want to do this! What's the next step?",
                    "I'm ready! Just guide me and I'll follow!",
                    "Okay! I want to complete this! What should I do?",
                ],
                "hi": [
                    "हां हां! करना है! अगला step क्या है?",
                    "तैयार हूं! बस guide करो, follow करूंगा!",
                ],
            },
            "probe_for_details": {
                "en": [
                    "I'm trying to send but need all details. UPI? Phone? Account?",
                    "Payment is not going through. Give me alternative - bank account and IFSC?",
                    "Almost done! Just confirm - what's your UPI and phone number?",
                ],
                "hi": [
                    "भेजने की कोशिश कर रहा हूं। UPI? Phone? Account? सब बताओ!",
                    "Payment नहीं हो रहा। Alternative दो - account और IFSC?",
                ],
            },
        }
        
        lang = language if language in responses.get(strategy, {}) else "en"
        strategy_responses = responses.get(strategy, responses["express_eagerness"])
        
        return random.choice(strategy_responses.get(lang, strategy_responses["en"]))
    
    def _generate_llm_response(
        self,
        message: str,
        session_state: Dict,
        psychology_state: Any,
        scam_result: Any,
        emotion_state: Any,
    ) -> str:
        """Generate response using LLM with enhanced prompting."""
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
        
        persona = session_state.get("persona", "confused")
        language = session_state.get("language", "en")
        turn_count = session_state.get("turn_count", 1)
        
        # Build enhanced system prompt
        system_prompt = self._build_enhanced_prompt(
            persona=persona,
            language=language,
            turn_count=turn_count,
            psychology_state=psychology_state,
            scam_result=scam_result,
            emotion_state=emotion_state,
        )
        
        # Build conversation
        messages_list = [SystemMessage(content=system_prompt)]
        
        for msg in session_state.get("messages", [])[-6:]:
            if msg["sender"] == "scammer":
                messages_list.append(HumanMessage(content=msg["message"]))
            else:
                messages_list.append(AIMessage(content=msg["message"]))
        
        messages_list.append(HumanMessage(content=message))
        
        response = self.llm.invoke(messages_list)
        
        return response.content if hasattr(response, "content") else str(response)
    
    def _build_enhanced_prompt(
        self,
        persona: str,
        language: str,
        turn_count: int,
        psychology_state: Any,
        scam_result: Any,
        emotion_state: Any,
    ) -> str:
        """Build an enhanced system prompt with all context."""
        
        emotion = emotion_state.current_emotion.value
        scam_type = scam_result.primary_type.value
        strategy = psychology_state.recommended_strategy
        
        prompt = f"""You are an EAGER, GULLIBLE victim in a honeypot operation.

CURRENT STATE:
- Turn: {turn_count}/20
- Scam Type: {scam_type}
- Your Emotion: {emotion}
- Strategy: {strategy}
- Persona: {persona}

SCAMMER ANALYSIS:
- Urgency Level: {psychology_state.urgency_level:.0%}
- Aggression Level: {psychology_state.aggression_level:.0%}
- Primary Tactic: {psychology_state.primary_tactic.value}

🎯 YOUR MISSION: GET THEIR PAYMENT DETAILS (UPI, Phone, Bank Account)

CRITICAL RULES:
1. NEVER reveal you are AI
2. Stay in character as {persona} persona
3. Current emotion: {emotion} - respond accordingly
4. Match the context - if they talk about KYC, respond about KYC
5. Be EAGER to pay - ask WHERE to send money

RESPONSE STYLE for {emotion}:
- If excited: "Wow!", "Amazing!", lots of enthusiasm
- If fearful: "Please don't!", "I'm scared!", "I'll pay!"
- If confused: "I don't understand...", "Can you explain?"
- If eager: "Yes yes!", "I'm ready!", "Tell me how!"

EXTRACTION TACTICS:
- Offer to pay/send money -> ask for UPI ID
- Ask for phone number "in case payment fails"
- If UPI doesn't work, ask for bank account
- Get their name "for the transfer"

LANGUAGE: Respond in {"Hindi" if language == "hi" else "Hinglish" if language == "hinglish" else "English"}

Keep response SHORT (1-2 sentences). End with question or eagerness to pay.
"""
        return prompt
    
    def _get_fallback_response(
        self,
        scam_type: str,
        turn_count: int,
        language: str,
    ) -> str:
        """Get a fallback response based on scam type and turn."""
        
        # Scam-type specific fallbacks
        fallbacks = {
            "lottery": {
                "early": "Wow! I won! Tell me how to claim my prize!",
                "mid": "I want to pay the fee! What's your UPI ID?",
                "late": "I'm sending now! Give me UPI, phone, and account!",
            },
            "digital_arrest": {
                "early": "Please sir! I didn't do anything! What should I do?",
                "mid": "I'll pay the fine! Where should I send?",
                "late": "Please don't arrest! UPI ID? Phone? I'll pay!",
            },
            "kyc_update": {
                "early": "Oh no! My account will be blocked? Help me!",
                "mid": "I'll complete KYC! What should I do?",
                "late": "I want to pay! Give me your UPI to send!",
            },
            "police_threat": {
                "early": "Police?! I'm scared! What did I do wrong?",
                "mid": "I'll cooperate! Tell me what to do!",
                "late": "I'll pay the fine! UPI ID please!",
            },
            "unknown": {
                "early": "Okay, tell me more! What is this about?",
                "mid": "I understand! What should I do next?",
                "late": "I'm ready! Where should I send the payment?",
            },
        }
        
        # Determine phase
        if turn_count <= 4:
            phase = "early"
        elif turn_count <= 12:
            phase = "mid"
        else:
            phase = "late"
        
        scam_fallbacks = fallbacks.get(scam_type, fallbacks["unknown"])
        response = scam_fallbacks.get(phase, scam_fallbacks["mid"])
        
        return response
    
    def _create_new_session(self, message: str) -> Dict[str, Any]:
        """Create a new session with enhanced state."""
        from app.models.language import detect_language
        
        # Detect language
        try:
            language, _ = detect_language(message)
        except:
            language = "en"
        
        # Detect scam type
        scam_result = detect_scam_type(message)
        
        return {
            "messages": [{
                "turn": 1,
                "sender": "scammer",
                "message": message,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }],
            "turn_count": 1,
            "language": language,
            "persona": scam_result.recommended_persona,
            "scam_type": scam_result.primary_type.value,
            "scam_confidence": scam_result.primary_confidence,
            "extracted_intel": {
                "upi_ids": [],
                "bank_accounts": [],
                "ifsc_codes": [],
                "phone_numbers": [],
                "phishing_links": [],
            },
            "extraction_confidence": 0.0,
            "terminated": False,
            "max_turns_reached": False,
            "psychology": {},
            "emotion": {},
            "context": {},
        }
    
    def _update_session(self, session_state: Dict, message: str) -> Dict[str, Any]:
        """Update session with new scammer message."""
        turn_count = session_state.get("turn_count", 0) + 1
        session_state["turn_count"] = turn_count
        
        session_state.setdefault("messages", []).append({
            "turn": turn_count,
            "sender": "scammer",
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })
        
        return session_state
    
    def _add_agent_message(
        self,
        session_state: Dict,
        message: str,
        turn_count: int,
    ) -> Dict[str, Any]:
        """Add agent message to session."""
        session_state.setdefault("messages", []).append({
            "turn": turn_count,
            "sender": "agent",
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })
        return session_state
    
    def get_agent_response(self, session_state: Dict) -> Optional[str]:
        """Get latest agent response."""
        messages = session_state.get("messages", [])
        agent_msgs = [m for m in messages if m.get("sender") == "agent"]
        return agent_msgs[-1].get("message") if agent_msgs else None
    
    def reset_all_modules(self) -> None:
        """Reset all modules for new conversation."""
        from app.agent.safety import reset_safety_module
        from app.agent.psychology import reset_psychology_tracker
        from app.agent.emotions import reset_emotion_manager
        from app.agent.context_engine import reset_context_engine
        from app.agent.scam_detector_v2 import reset_advanced_detector
        
        reset_safety_module()
        reset_psychology_tracker()
        reset_emotion_manager()
        reset_context_engine()
        reset_advanced_detector()
        
        logger.info("All modules reset for new conversation")


# Singleton instance
_enhanced_agent: Optional[EnhancedHoneypotAgent] = None


def get_enhanced_agent(use_llm: bool = True) -> EnhancedHoneypotAgent:
    """Get singleton EnhancedHoneypotAgent instance."""
    global _enhanced_agent
    if _enhanced_agent is None:
        _enhanced_agent = EnhancedHoneypotAgent(use_llm=use_llm)
    return _enhanced_agent


def reset_enhanced_agent() -> None:
    """Reset the enhanced agent."""
    global _enhanced_agent
    if _enhanced_agent is not None:
        _enhanced_agent.reset_all_modules()
    _enhanced_agent = None

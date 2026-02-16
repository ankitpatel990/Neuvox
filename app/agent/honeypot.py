"""
Honeypot Agent Module using LangGraph.

Implements the agentic honeypot system (Task 5.2) that:
- Engages scammers in multi-turn conversations
- Uses dynamic personas to maintain believability
- Progressively extracts intelligence through strategic questioning

Acceptance Criteria:
- AC-2.2.1: Engagement averages >10 turns
- AC-2.2.2: Strategy progression works
- AC-2.2.3: Termination logic correct
- AC-2.2.4: No infinite loops
"""

import os
import re
from typing import Dict, List, Optional, TypedDict, Any, Literal
from datetime import datetime

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Maximum turns to prevent infinite loops (AC-2.2.4)
MAX_TURNS = 20

# Extraction confidence threshold for termination
# UPI(0.3) + Bank(0.3) + Phone(0.1) = 0.7, add IFSC(0.2) = 0.9
# Terminate at 0.85 to match GUVI callback trigger requirement
EXTRACTION_CONFIDENCE_THRESHOLD = 0.85


class HoneypotState(TypedDict, total=False):
    """
    State schema for the honeypot agent workflow.
    
    Attributes:
        messages: List of conversation messages
        scam_confidence: Detection confidence score
        turn_count: Current turn number
        extracted_intel: Extracted financial intelligence
        extraction_confidence: Confidence in extracted intel
        strategy: Current engagement strategy
        language: Conversation language
        persona: Active persona name
        max_turns_reached: Whether max turns limit was hit
        terminated: Whether the conversation has ended
    """
    
    messages: List[Dict]
    scam_confidence: float
    turn_count: int
    extracted_intel: Dict
    extraction_confidence: float
    strategy: str
    language: str
    persona: str
    max_turns_reached: bool
    terminated: bool


class HoneypotAgent:
    """
    LangGraph-based agentic honeypot for scammer engagement.
    
    Uses a ReAct-style workflow with three nodes:
    1. Plan: Decide engagement strategy based on turn count
    2. Generate: Generate persona-appropriate responses using LLM
    3. Extract: Extract financial intelligence from conversation
    
    Attributes:
        llm: Groq LLM client (ChatGroq)
        workflow: Compiled LangGraph workflow
        _initialized: Whether the agent is properly initialized
    """
    
    def __init__(self, use_llm: bool = True) -> None:
        """
        Initialize the HoneypotAgent with LLM and workflow.
        
        Args:
            use_llm: Whether to initialize the LLM (can be False for testing)
        """
        self._initialized = False
        self.llm = None
        self.workflow = None
        
        if use_llm:
            self._initialize_llm()
        
        self._build_workflow()
        self._initialized = True
        logger.info("HoneypotAgent initialized successfully")
    
    def _initialize_llm(self) -> None:
        """
        Initialize the Groq LLM client.
        
        Uses configuration from settings for API key, model, and parameters.
        """
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
            
        except ImportError as e:
            logger.error(f"Failed to import langchain_groq: {e}")
            self.llm = None
        except Exception as e:
            logger.error(f"Failed to initialize ChatGroq: {e}")
            self.llm = None
    
    def _build_workflow(self) -> None:
        """
        Build the LangGraph workflow.
        
        Creates a state machine with nodes for:
        - plan: Decide engagement strategy
        - generate: Generate response using LLM
        - extract: Extract intelligence from conversation
        
        The workflow continues until termination conditions are met.
        """
        try:
            from langgraph.graph import StateGraph, END
            
            workflow = StateGraph(HoneypotState)
            
            # Add nodes
            workflow.add_node("plan", self._plan_response)
            workflow.add_node("generate", self._generate_response)
            workflow.add_node("extract", self._extract_intelligence)
            
            # Add edges
            workflow.add_edge("plan", "generate")
            workflow.add_edge("generate", "extract")
            
            # Add conditional edge for termination
            workflow.add_conditional_edges(
                "extract",
                self._should_continue,
                {
                    "continue": END,  # Single turn per invoke, return to caller
                    "end": END,
                }
            )
            
            # Set entry point
            workflow.set_entry_point("plan")
            
            # Compile workflow
            self.workflow = workflow.compile()
            logger.debug("LangGraph workflow compiled successfully")
            
        except ImportError as e:
            logger.error(f"Failed to import langgraph: {e}")
            self.workflow = None
        except Exception as e:
            logger.error(f"Failed to build workflow: {e}")
            self.workflow = None
    
    def _plan_response(self, state: HoneypotState) -> Dict[str, Any]:
        """
        Decide engagement strategy based on turn count.
        
        Strategy progression (AC-2.2.2):
        - Turns 1-5: build_trust (establish rapport)
        - Turns 6-12: express_confusion (stall and extract)
        - Turns 13-20: probe_details (actively extract intel)
        
        Args:
            state: Current honeypot state
            
        Returns:
            Dict with updated strategy
        """
        from app.agent.strategies import get_strategy
        
        turn = state.get("turn_count", 0)
        strategy = get_strategy(turn)
        
        logger.debug(f"Turn {turn}: Selected strategy '{strategy}'")
        
        return {"strategy": strategy}
    
    def _generate_response(self, state: HoneypotState) -> Dict[str, Any]:
        """
        Generate agent response using LLM.
        
        Uses the persona and strategy to craft believable responses
        that encourage scammers to reveal financial details.
        
        CRITICAL: Now extracts intel FIRST so we know what we already have
        and can avoid asking for the same information repeatedly.
        
        Args:
            state: Current honeypot state
            
        Returns:
            Dict with updated messages list
        """
        from app.agent.personas import get_persona_prompt
        from app.agent.prompts import get_system_prompt
        from app.models.extractor import extract_intelligence
        
        persona = state.get("persona", "confused")
        language = state.get("language", "en")
        strategy = state.get("strategy", "build_trust")
        turn_count = state.get("turn_count", 1)
        messages = state.get("messages", [])
        
        # Get last scammer message
        scammer_messages = [m for m in messages if m.get("sender") == "scammer"]
        last_message = scammer_messages[-1]["message"] if scammer_messages else ""
        
        # CRITICAL: Extract intel FIRST so we know what we already have
        # This prevents asking for UPI/phone when scammer already gave it
        full_text = " ".join(m.get("message", "") for m in messages)
        try:
            current_intel, _ = extract_intelligence(full_text)
        except Exception as e:
            logger.warning(f"Pre-generation intel extraction failed: {e}")
            current_intel = {
                "upi_ids": [],
                "bank_accounts": [],
                "ifsc_codes": [],
                "phone_numbers": [],
                "phishing_links": [],
                "email_addresses": [],
            }
        
        # Generate response - pass current intel so we don't repeat questions
        if self.llm is not None:
            try:
                agent_message = self._generate_llm_response(
                    persona=persona,
                    language=language,
                    strategy=strategy,
                    turn_count=turn_count,
                    last_message=last_message,
                    messages=messages,
                    extracted_intel=current_intel,
                )
            except Exception as e:
                logger.error(f"LLM generation failed: {e}")
                agent_message = self._generate_fallback_response(
                    persona, language, strategy, turn_count, last_message, messages, current_intel
                )
        else:
            agent_message = self._generate_fallback_response(
                persona, language, strategy, turn_count, last_message, messages, current_intel
            )
        
        # Add to conversation
        new_message = {
            "turn": turn_count,
            "sender": "agent",
            "message": agent_message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        
        updated_messages = messages.copy()
        updated_messages.append(new_message)
        
        return {"messages": updated_messages}
    
    def _generate_llm_response(
        self,
        persona: str,
        language: str,
        strategy: str,
        turn_count: int,
        last_message: str,
        messages: List[Dict],
        extracted_intel: Dict = None,
    ) -> str:
        """
        Generate response using the LLM.
        
        Args:
            persona: Active persona
            language: Conversation language
            strategy: Current strategy
            turn_count: Current turn
            last_message: Last scammer message
            messages: Full conversation history
            extracted_intel: Already extracted intelligence to avoid redundant questions
            
        Returns:
            Generated agent response
        """
        from app.agent.prompts import (
            get_system_prompt, is_greeting_message, get_greeting_response,
            extract_phone_from_message, validate_phone_number, get_invalid_phone_response
        )
        from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
        
        # Check if this is just a greeting (works for first few turns)
        if turn_count <= 2 and is_greeting_message(last_message):
            logger.debug(f"Detected greeting message at turn {turn_count}, responding naturally")
            return get_greeting_response(language, turn_count)
        
        # Check if scammer provided an invalid phone number
        phone_in_message = extract_phone_from_message(last_message)
        if phone_in_message and not validate_phone_number(phone_in_message):
            logger.debug(f"Detected invalid phone number: {phone_in_message}")
            return get_invalid_phone_response(language)
        
        # Build context about what we already have
        intel_context = ""
        if extracted_intel:
            has_items = []
            missing_items = []
            
            if extracted_intel.get("upi_ids"):
                has_items.append(f"✅ UPI: {extracted_intel['upi_ids']}")
            else:
                missing_items.append("UPI ID")
                
            if extracted_intel.get("phone_numbers"):
                has_items.append(f"✅ Phone: {extracted_intel['phone_numbers']}")
            else:
                missing_items.append("Phone Number")
                
            if extracted_intel.get("bank_accounts"):
                has_items.append(f"✅ Bank Account: {extracted_intel['bank_accounts']}")
            else:
                missing_items.append("Bank Account Number")
                
            if extracted_intel.get("ifsc_codes"):
                has_items.append(f"✅ IFSC: {extracted_intel['ifsc_codes']}")
            else:
                missing_items.append("IFSC Code")
            
            if has_items:
                intel_context = f"\n\n" + "="*60 + "\n"
                intel_context += "📋 EXTRACTED DATA - DO NOT ASK FOR THESE AGAIN:\n"
                intel_context += "\n".join(has_items)
                if missing_items:
                    intel_context += f"\n\n❌ STILL NEED: {', '.join(missing_items)}"
                    intel_context += f"\n\n👉 YOUR NEXT GOAL: Get {missing_items[0]} from scammer!"
                else:
                    intel_context += "\n\n✅ YOU HAVE EVERYTHING! Just confirm and pretend to send payment."
                intel_context += "\n" + "="*60
        
        # Build system prompt with intel context
        system_prompt = get_system_prompt(
            persona=persona,
            language=language,
            strategy=strategy,
            turn_count=turn_count,
        ) + intel_context
        
        # Build conversation history for context
        llm_messages = [SystemMessage(content=system_prompt)]
        
        # Include ALL messages - we need full context for 20 turns
        # Modern LLMs like Llama 3.1 have 128K context, so this is fine
        context_messages = messages
        
        for msg in context_messages:
            if msg["sender"] == "scammer":
                llm_messages.append(HumanMessage(content=msg["message"]))
            else:
                llm_messages.append(AIMessage(content=msg["message"]))
        
        # If the last message isn't from scammer, add it
        if context_messages and context_messages[-1]["sender"] != "scammer":
            llm_messages.append(HumanMessage(content=last_message))
        
        # Generate response
        response = self.llm.invoke(llm_messages)
        
        # Extract content
        if hasattr(response, "content"):
            generated = response.content
        else:
            generated = str(response)
        
        # CRITICAL: Filter out bot-like responses and replace with context-aware ones
        # Pass extracted intel so we know what NOT to ask for again
        natural_response = self._filter_bot_response(
            generated, turn_count, language, last_message, messages, extracted_intel
        )
        return natural_response
    
    def _filter_bot_response(
        self, 
        response: str, 
        turn_count: int, 
        language: str,
        last_message: str,
        messages: List[Dict] = None,
        extracted_intel: Dict = None,
    ) -> str:
        """
        Minimal filtering - only block truly problematic responses.
        
        PHILOSOPHY: Trust the LLM! The system prompt already provides:
        - What has been extracted (via intel_context)
        - What to ask for next (via strategy prompts)
        - Clear instructions not to ask for info we already have
        
        We only filter out:
        1. Suspicious/scam-detection language (breaks character)
        2. Empty or very short responses
        
        Args:
            response: Generated response from LLM
            turn_count: Current turn number
            language: Conversation language
            last_message: Scammer's last message
            messages: Full conversation history for context detection
            extracted_intel: Already extracted intelligence
            
        Returns:
            LLM response (only filtered if truly problematic)
        """
        import random
        
        response_lower = response.lower()
        
        # ONLY filter truly problematic responses that break character
        suspicious_patterns = [
            "sounds like a scam", "this is a scam", "you are a scammer",
            "i don't trust", "seems suspicious", "i'm worried about fraud",
            "i don't believe", "prove it", "show me proof",
            "i will report you", "police", "cyber crime",
            "this is fraud", "you're trying to scam",
        ]
        
        is_suspicious = any(pattern in response_lower for pattern in suspicious_patterns)
        
        # Check for empty or too short responses
        is_too_short = len(response.strip()) < 10
        
        # If response is good, return it - TRUST THE LLM!
        if not is_suspicious and not is_too_short:
            return response
        
        logger.warning(f"Filtering problematic response: '{response[:50]}...' (suspicious={is_suspicious}, short={is_too_short})")
        
        # Only generate fallback for truly problematic responses
        # Use a simple, context-aware fallback based on extracted intel
        has_upi = bool(extracted_intel and extracted_intel.get("upi_ids"))
        has_phone = bool(extracted_intel and extracted_intel.get("phone_numbers"))
        has_bank = bool(extracted_intel and extracted_intel.get("bank_accounts"))
        has_ifsc = bool(extracted_intel and extracted_intel.get("ifsc_codes"))
        
        # Simple fallback: ask for what we don't have, in order
        if not has_upi:
            return random.choice([
                "OK! Where should I send the money? UPI ID?",
                "I'm ready to pay! What's your UPI?",
            ])
        elif not has_phone:
            return random.choice([
                "Got it! What's your phone number for confirmation?",
                "Noted! Give me your number in case of issues.",
            ])
        elif not has_bank:
            return random.choice([
                "UPI has limit. What's your bank account number?",
                "Can I do bank transfer? Account number please?",
            ])
        elif not has_ifsc:
            return random.choice([
                "Got account! What's the IFSC code?",
                "My bank needs IFSC code. What is it?",
            ])
        else:
            return random.choice([
                "Got all details! Processing payment now.",
                "All noted! Sending the money now.",
            ])
    
    def _generate_fallback_response(
        self, 
        persona: str, 
        language: str, 
        strategy: str,
        turn_count: int = 1,
        last_message: str = "",
        all_messages: List[Dict] = None,
        extracted_intel: Dict = None,
    ) -> str:
        """
        Generate fallback response when LLM is unavailable.
        
        Simple, context-aware responses based on what we have vs what we need.
        Follows the logical order: UPI -> Phone -> Bank -> IFSC -> Name
        
        Args:
            persona: Active persona
            language: Conversation language
            strategy: Current strategy
            turn_count: Current conversation turn
            last_message: The last message from scammer
            all_messages: Full conversation history for context detection
            extracted_intel: Already extracted info to avoid redundant questions
            
        Returns:
            Fallback response string
        """
        import random
        from app.agent.prompts import (
            is_greeting_message, get_greeting_response,
            extract_phone_from_message, validate_phone_number, get_invalid_phone_response
        )
        
        # Check if this is just a greeting - respond naturally
        if turn_count <= 2 and last_message and is_greeting_message(last_message):
            return get_greeting_response(language, turn_count)
        
        # Check if scammer provided an invalid phone number
        if last_message:
            phone_in_message = extract_phone_from_message(last_message)
            if phone_in_message and not validate_phone_number(phone_in_message):
                return get_invalid_phone_response(language)
        
        # Track what we already have
        has_upi = bool(extracted_intel and extracted_intel.get("upi_ids"))
        has_phone = bool(extracted_intel and extracted_intel.get("phone_numbers"))
        has_bank = bool(extracted_intel and extracted_intel.get("bank_accounts"))
        has_ifsc = bool(extracted_intel and extracted_intel.get("ifsc_codes"))
        
        last_msg_lower = last_message.lower() if last_message else ""
        
        # Handle OTP requests - acknowledge and redirect
        scammer_asking_otp = "otp" in last_msg_lower
        if scammer_asking_otp:
            # Ask for what we need next
            if has_bank and not has_ifsc:
                return "OTP not coming! I'll do bank transfer. What's the IFSC code?"
            elif not has_bank and has_upi:
                return "Forget OTP! UPI failing. What's your bank account number?"
            elif not has_phone and has_upi:
                return "OTP problem! Let me call you. What's your phone number?"
            elif not has_upi:
                return "No OTP received. Just give me your UPI ID, I'll pay directly!"
            else:
                return "OTP not needed! I have all details. Sending payment now!"
        
        # Simple flow: ask for what we don't have, in order
        if not has_upi:
            return random.choice([
                "OK! Where should I send the money? UPI ID?",
                "I'm ready to pay! What's your UPI?",
                "Tell me your UPI ID and I'll transfer!",
            ])
        elif not has_phone:
            return random.choice([
                "Got UPI! What's your phone number for confirmation?",
                "Noted! Give me your number in case of issues.",
                "UPI saved! What's your contact number?",
            ])
        elif not has_bank:
            return random.choice([
                "UPI has limit. What's your bank account number?",
                "Can I do bank transfer instead? Account number?",
                "For larger amount, give me bank account number.",
            ])
        elif not has_ifsc:
            return random.choice([
                "Got account! What's the IFSC code?",
                "My bank needs IFSC code for the transfer. What is it?",
                "Account noted! IFSC code please?",
            ])
        else:
            return random.choice([
                "Got all details! Sending payment now.",
                "All noted! Processing the transfer.",
                "Perfect! Making the payment now.",
            ])
    
    def _extract_intelligence(self, state: HoneypotState) -> Dict[str, Any]:
        """
        Extract financial details from conversation.
        
        Uses regex patterns and NER to identify:
        - UPI IDs
        - Bank account numbers
        - IFSC codes
        - Phone numbers
        - Phishing links
        
        Args:
            state: Current honeypot state
            
        Returns:
            Dict with extracted_intel and extraction_confidence
        """
        from app.models.extractor import extract_intelligence
        
        messages = state.get("messages", [])
        
        # Extract from all messages
        full_text = " ".join(m.get("message", "") for m in messages)
        
        try:
            intel, confidence = extract_intelligence(full_text)
        except Exception as e:
            logger.error(f"Intelligence extraction failed: {e}")
            intel = {
                "upi_ids": [],
                "bank_accounts": [],
                "ifsc_codes": [],
                "phone_numbers": [],
                "phishing_links": [],
                "email_addresses": [],
            }
            confidence = 0.0
        
        return {
            "extracted_intel": intel,
            "extraction_confidence": confidence,
        }
    
    def _should_continue(self, state: HoneypotState) -> Literal["continue", "end"]:
        """
        Determine if engagement should continue.
        
        Termination conditions (AC-2.2.3):
        1. Maximum turns reached (20) - prevents infinite loops (AC-2.2.4)
        2. High confidence extraction achieved (>0.85)
        3. Explicit termination flag set
        
        Args:
            state: Current honeypot state
            
        Returns:
            "continue" or "end"
        """
        turn_count = state.get("turn_count", 0)
        extraction_confidence = state.get("extraction_confidence", 0.0)
        
        # Check max turns (AC-2.2.4: No infinite loops)
        if turn_count >= MAX_TURNS:
            logger.info(f"Max turns ({MAX_TURNS}) reached, terminating")
            return "end"
        
        # Check extraction confidence
        if extraction_confidence >= EXTRACTION_CONFIDENCE_THRESHOLD:
            logger.info(
                f"High confidence extraction ({extraction_confidence:.2f}), terminating"
            )
            return "end"
        
        return "continue"
    
    def engage(
        self, 
        message: str, 
        session_state: Optional[Dict] = None,
        scam_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Main engagement method.
        
        Processes a scammer message and generates an appropriate response
        using the configured persona and strategy.
        
        Args:
            message: Scammer's message
            session_state: Existing session state (optional)
            scam_type: Detected scam type for persona selection
            
        Returns:
            Updated session state with agent response
        """
        if session_state is None:
            session_state = self._create_new_session(message, scam_type)
        else:
            session_state = self._update_session(session_state, message)
        
        # Check if already terminated - don't keep adding termination messages
        if session_state.get("terminated", False):
            # Already terminated, generate a varied "still busy" response
            varied_responses = [
                "Sorry, I'm still busy. Will message you later.",
                "Still at the door, one minute please.",
                "My phone is dying, I'll call you back.",
                "Give me some time, I'm busy right now.",
                "I'll get back to you soon.",
            ]
            import random
            busy_msg = random.choice(varied_responses)
            session_state["messages"].append({
                "turn": session_state.get("turn_count", 20),
                "sender": "agent",
                "message": busy_msg,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            })
            return session_state
        
        # Check termination before processing
        if self._check_termination(session_state):
            session_state["terminated"] = True
            # Add termination message
            termination_msg = self._generate_termination_message(session_state)
            session_state["messages"].append({
                "turn": session_state.get("turn_count", 20),
                "sender": "agent",
                "message": termination_msg,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            })
            return session_state
        
        # Run workflow
        if self.workflow is not None:
            try:
                result = self.workflow.invoke(session_state)
                # Merge result into session state
                session_state.update(result)
            except Exception as e:
                logger.error(f"Workflow execution failed: {e}")
                # Generate fallback response
                session_state = self._generate_fallback_turn(session_state)
        else:
            # No workflow, use fallback
            session_state = self._generate_fallback_turn(session_state)
        
        # Update termination status
        continuation = self._should_continue(session_state)
        session_state["terminated"] = (continuation == "end")
        session_state["max_turns_reached"] = (
            session_state.get("turn_count", 0) >= MAX_TURNS
        )
        
        return session_state
    
    def _create_new_session(
        self, 
        message: str, 
        scam_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new session state.
        
        Detects language and selects appropriate persona.
        
        Args:
            message: Initial scammer message
            scam_type: Optional scam type for persona selection
            
        Returns:
            New session state dict
        """
        from app.models.language import detect_language
        from app.agent.personas import select_persona
        
        # Detect language
        try:
            language, lang_confidence = detect_language(message)
        except Exception as e:
            logger.warning(f"Language detection failed: {e}")
            language = "en"
        
        # Select persona based on scam type
        persona = select_persona(scam_type or "unknown", language)
        
        # Create initial state
        session_state: Dict[str, Any] = {
            "messages": [{
                "turn": 1,
                "sender": "scammer",
                "message": message,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }],
            "scam_confidence": 0.0,
            "turn_count": 1,
            "extracted_intel": {
                "upi_ids": [],
                "bank_accounts": [],
                "ifsc_codes": [],
                "phone_numbers": [],
                "phishing_links": [],
                "email_addresses": [],
            },
            "extraction_confidence": 0.0,
            "strategy": "build_trust",
            "language": language,
            "persona": persona,
            "max_turns_reached": False,
            "terminated": False,
        }
        
        logger.info(
            f"New session created: language={language}, persona={persona}"
        )
        
        return session_state
    
    def _update_session(
        self, 
        session_state: Dict[str, Any], 
        message: str
    ) -> Dict[str, Any]:
        """
        Update existing session with new scammer message.
        
        Args:
            session_state: Current session state
            message: New scammer message
            
        Returns:
            Updated session state
        """
        # Increment turn count
        turn_count = session_state.get("turn_count", 0) + 1
        session_state["turn_count"] = turn_count
        
        # Add scammer message
        messages = session_state.get("messages", [])
        messages.append({
            "turn": turn_count,
            "sender": "scammer",
            "message": message,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        })
        session_state["messages"] = messages
        
        return session_state
    
    def _check_termination(self, session_state: Dict[str, Any]) -> bool:
        """
        Check if session should be terminated before processing.
        
        Args:
            session_state: Current session state
            
        Returns:
            True if session should terminate
        """
        turn_count = session_state.get("turn_count", 0)
        
        # Check max turns
        if turn_count >= MAX_TURNS:
            return True
        
        # Check if already terminated
        if session_state.get("terminated", False):
            return True
        
        return False
    
    def _generate_termination_message(self, session_state: Dict[str, Any]) -> str:
        """
        Generate a graceful termination message with intelligence summary.
        
        Args:
            session_state: Current session state
            
        Returns:
            Termination message string
        """
        import random
        
        intel = session_state.get("extracted_intel", {})
        
        # Count extracted items
        upi_count = len(intel.get("upi_ids", []))
        phone_count = len(intel.get("phone_numbers", []))
        account_count = len(intel.get("bank_accounts", []))
        
        total_items = upi_count + phone_count + account_count
        
        # Varied termination messages to avoid repetition
        if total_items > 3:
            messages = [
                "Sorry, my phone battery is dying. I'll try to send the money later. Thanks for your help!",
                "Oh no, battery is at 2%! I noted everything down, will send money tomorrow morning.",
                "My phone is about to switch off. I saved your details, will complete payment later.",
                "Low battery! I've written everything, will do the transfer from my laptop.",
            ]
        elif total_items > 0:
            messages = [
                "Hold on, someone is at the door. Let me check and come back.",
                "Wait, my son just came home. I'll ask him to help me with the payment.",
                "One minute, there's someone at the door. I'll message you in 5 minutes.",
                "My daughter is calling me. Let me see what she wants and I'll complete this.",
                "Sorry, I need to take another call. I'll get back to you shortly.",
            ]
        else:
            messages = [
                "I need to go now, my family is calling. Can you call me back later?",
                "Sorry, something urgent came up. Can we continue later?",
                "I have to go, but I'm interested. Please call me tomorrow.",
                "My lunch is getting cold! Let me eat and I'll message you.",
            ]
        
        return random.choice(messages)
    
    def _generate_fallback_turn(
        self, 
        session_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate a complete turn using fallback logic.
        
        Used when workflow is unavailable.
        
        Args:
            session_state: Current session state
            
        Returns:
            Updated session state
        """
        # Plan
        plan_result = self._plan_response(session_state)
        session_state.update(plan_result)
        
        # Generate
        generate_result = self._generate_response(session_state)
        session_state.update(generate_result)
        
        # Extract
        extract_result = self._extract_intelligence(session_state)
        session_state.update(extract_result)
        
        return session_state
    
    def get_agent_response(self, session_state: Dict[str, Any]) -> Optional[str]:
        """
        Get the latest agent response from session state.
        
        Args:
            session_state: Session state dict
            
        Returns:
            Latest agent message or None
        """
        messages = session_state.get("messages", [])
        agent_messages = [m for m in messages if m.get("sender") == "agent"]
        
        if agent_messages:
            return agent_messages[-1].get("message")
        return None
    
    def get_extracted_intelligence(
        self, 
        session_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Get extracted intelligence from session state.
        
        Args:
            session_state: Session state dict
            
        Returns:
            Intelligence dict with all extracted entities
        """
        intel = session_state.get("extracted_intel", {})
        confidence = session_state.get("extraction_confidence", 0.0)
        
        return {
            **intel,
            "extraction_confidence": confidence,
        }


# Singleton instance for convenience
_agent_instance: Optional[HoneypotAgent] = None


def get_honeypot_agent(use_llm: bool = True) -> HoneypotAgent:
    """
    Get singleton honeypot agent instance.
    
    Args:
        use_llm: Whether to enable LLM features
        
    Returns:
        HoneypotAgent instance
    """
    global _agent_instance
    
    if _agent_instance is None:
        _agent_instance = HoneypotAgent(use_llm=use_llm)
    
    return _agent_instance


def reset_honeypot_agent() -> None:
    """Reset the singleton agent instance."""
    global _agent_instance
    _agent_instance = None

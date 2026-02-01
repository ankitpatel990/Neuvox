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

# Extraction confidence threshold for termination - set high to keep conversation going
# Only terminate when we have almost everything (UPI + Bank + IFSC + Phone = 0.9+)
EXTRACTION_CONFIDENCE_THRESHOLD = 0.95


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
            if extracted_intel.get("upi_ids"):
                has_items.append(f"UPI IDs: {extracted_intel['upi_ids']}")
            if extracted_intel.get("phone_numbers"):
                has_items.append(f"Phone numbers: {extracted_intel['phone_numbers']}")
            if extracted_intel.get("bank_accounts"):
                has_items.append(f"Bank accounts: {extracted_intel['bank_accounts']}")
            if extracted_intel.get("ifsc_codes"):
                has_items.append(f"IFSC codes: {extracted_intel['ifsc_codes']}")
            if has_items:
                intel_context = f"\n\n⚠️ YOU ALREADY HAVE THESE DETAILS (DO NOT ASK FOR THEM AGAIN):\n" + "\n".join(has_items)
                intel_context += "\n\nAsk for what you DON'T have yet! If you have UPI, ask for phone number. If you have phone, ask for bank account."
        
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
        Filter out bot-like responses and replace with CONTEXT-AWARE responses.
        
        CRITICAL: This function now tracks what info has ALREADY been extracted
        and responds appropriately to what the scammer just said.
        
        Args:
            response: Generated response from LLM
            turn_count: Current turn number
            language: Conversation language
            last_message: Scammer's last message
            messages: Full conversation history for context detection
            extracted_intel: Already extracted intelligence to avoid asking again
            
        Returns:
            Filtered response that is contextually appropriate
        """
        import random
        
        response_lower = response.lower()
        last_msg_lower = last_message.lower()
        
        # Build conversation context from all messages
        full_conversation = ""
        if messages:
            full_conversation = " ".join(m.get("message", "").lower() for m in messages)
        else:
            full_conversation = last_msg_lower
        
        # Track what we already have from extracted_intel
        has_upi = bool(extracted_intel and extracted_intel.get("upi_ids"))
        has_phone = bool(extracted_intel and extracted_intel.get("phone_numbers"))
        has_bank = bool(extracted_intel and extracted_intel.get("bank_accounts"))
        has_ifsc = bool(extracted_intel and extracted_intel.get("ifsc_codes"))
        
        # Check what's in the LAST message from scammer
        gave_upi_now = "@" in last_message
        gave_number_now = bool(re.search(r'\b\d{10,12}\b', last_message))
        gave_bank_now = bool(re.search(r'\b\d{9,18}\b', last_message)) and not gave_number_now
        
        # Check if scammer is asking for OTP
        scammer_asking_otp = any(phrase in last_msg_lower for phrase in [
            "otp", "send otp", "share otp", "give otp", "tell otp",
            "received otp", "got otp", "check otp", "verify otp"
        ])
        
        # Check how many times scammer has asked for OTP in the conversation
        otp_ask_count = sum(1 for msg in (messages or []) if msg.get("sender") == "scammer" and "otp" in msg.get("message", "").lower())
        
        # Check if scammer is asking a question
        scammer_asking_question = any(q in last_msg_lower for q in ["what", "which", "where", "why", "how", "?", "kya", "kahan", "kyun", "kaun"])
        scammer_asking_for_number = any(phrase in last_msg_lower for phrase in ["what number", "which number", "number do you want", "number chahiye", "konsa number"])
        scammer_confused = any(phrase in last_msg_lower for phrase in ["don't understand", "didn't understand", "what are you", "kya bol", "samajh nahi"])
        scammer_said_already_told = any(phrase in last_msg_lower for phrase in ["already told", "already said", "already given", "already shared", "i said", "above", "times", "baar"])
        
        # Suspicious patterns (too cautious)
        suspicious_patterns = [
            "how do i know", "sounds like a scam", "this is a scam",
            "i don't trust", "are you sure", "is this legit",
            "how can i verify", "seems suspicious", "i'm worried",
            "i don't believe", "prove it", "show me proof",
        ]
        is_suspicious = any(pattern in response_lower for pattern in suspicious_patterns)
        
        # Bot-like patterns - but ONLY filter if we don't already have that info
        bot_patterns_upi = ["what's your upi", "what is your upi", "what's the upi", "share your upi", "give me your upi", "upi id?", "tell me your upi"]
        bot_patterns_phone = ["what's your phone", "what is your phone", "your phone number", "phone number?", "tell me your number"]
        bot_patterns_bank = ["what's your bank", "bank account number", "account number?", "tell me your account"]
        
        asking_for_upi_we_have = has_upi and any(p in response_lower for p in bot_patterns_upi)
        asking_for_phone_we_have = has_phone and any(p in response_lower for p in bot_patterns_phone)
        asking_for_bank_we_have = has_bank and any(p in response_lower for p in bot_patterns_bank)
        
        is_redundant = asking_for_upi_we_have or asking_for_phone_we_have or asking_for_bank_we_have
        
        # If response is good and not redundant/suspicious, return it
        if not is_redundant and not is_suspicious:
            return response
        
        logger.warning(f"Filtering response: '{response[:50]}...' (redundant={is_redundant}, suspicious={is_suspicious})")
        
        # PRIORITY 0: Handle OTP requests with VARIED responses
        if scammer_asking_otp:
            # Vary response based on how many times they've asked for OTP
            if otp_ask_count <= 1:
                # First time - be confused about OTP
                alternatives = [
                    "OTP? I didn't receive any message on my phone. Can you send it again?",
                    "I don't see any OTP on my phone. Where does it come from?",
                    "What OTP? I checked my messages but nothing came. Please resend!",
                    "No OTP on my phone... Maybe give me your UPI and I'll send money directly?",
                    "OTP not received yet. Let me check again... No, nothing here!",
                ]
            elif otp_ask_count <= 3:
                # They've asked multiple times - offer alternatives
                alternatives = [
                    "Still no OTP! Maybe network issue? Give me your UPI, I'll send directly!",
                    "I keep checking but no OTP! Can you call me? What's your number?",
                    "OTP still not coming! Let me do bank transfer instead - give me account number!",
                    "My phone is not getting OTP! Can I send money to your UPI instead?",
                    "Nothing received! Maybe give me your phone number and I'll call you?",
                ]
            else:
                # They've asked many times - get frustrated but still offer to pay
                alternatives = [
                    "Sir I've checked 10 times, no OTP! My phone might have problem. Just give me UPI!",
                    "I don't know why OTP is not coming! Please just tell me where to send money!",
                    "OTP problem is frustrating me also! Let me call you - what's your number?",
                    "Forget OTP! Give me bank account, I'll do NEFT transfer directly!",
                    "This OTP is not working! Tell me another way to send the money!",
                ]
            return random.choice(alternatives)
        
        # PRIORITY 1: Respond to scammer's question/confusion FIRST
        if scammer_asking_for_number:
            # Scammer is confused about "what number" - clarify we want THEIR phone
            alternatives = [
                "Your phone number! So I can call you if payment fails!",
                "I mean YOUR number! Give me your contact number please!",
                "Your mobile number! In case UPI doesn't work, I'll call you!",
                "I want to save YOUR number! What is your phone number?",
                "Your contact number! Tell me, I'll save it and then send money!",
            ]
            return random.choice(alternatives)
        
        if scammer_confused:
            # Scammer is confused - clarify what we want
            if not has_upi:
                alternatives = [
                    "I want to send you money! Just tell me your UPI ID!",
                    "Sir, where should I send the payment? Give me UPI ID!",
                    "I'm ready to pay! Just tell me where - what's your UPI?",
                    "Sorry for confusion! I want to pay you! What's your UPI ID?",
                    "I mean I want to transfer the money! What's your payment ID?",
                ]
            elif not has_phone:
                alternatives = [
                    "I want your phone number to call if there's problem!",
                    "Give me your number so I can confirm the payment!",
                    "What's your phone number? I'll call you after sending!",
                    "I need your contact number for verification!",
                    "Tell me your mobile number, my son wants to call before I pay!",
                ]
            else:
                alternatives = [
                    "I'm trying to help you! What should I do next?",
                    "Tell me clearly - what exactly do you need from me?",
                    "I'm confused too! Please explain what I should do!",
                    "Sorry, I don't understand technology well. Guide me step by step!",
                    "Can you explain again? I really want to do this correctly!",
                ]
            return random.choice(alternatives)
        
        if scammer_said_already_told:
            # Scammer frustrated that they already gave info - acknowledge and proceed
            if has_upi and not has_phone:
                alternatives = [
                    "Sorry sorry! Yes, I see the UPI now! Let me try... What's your phone number in case it fails?",
                    "Oh yes, I found it! Sending now. Give me your phone number also please!",
                    "Okay got it! I'm transferring now. What's your number so I can call you after?",
                    "My apologies! I'm sending now. Please give me your number for confirmation!",
                    "Yes yes, found it! Transferring... What's your phone number?",
                ]
            elif has_upi and has_phone and not has_bank:
                alternatives = [
                    "Yes, I'm trying! But UPI is showing error. Can you give bank account number?",
                    "Sorry, UPI not working from my side! What's your bank account and IFSC?",
                    "Got it, but my app is giving error! Give me bank transfer details instead!",
                    "I remember! But payment is failing. What's your account number?",
                    "Yes yes! But getting error. Tell me bank account for direct transfer!",
                ]
            else:
                alternatives = [
                    "Yes yes, sorry! I'm old and forgetful. I'm doing it now!",
                    "Okay okay, I found it! Let me try again. Please wait!",
                    "Sorry! My eyes are weak. I see it now, sending!",
                    "Apologies! I noted it wrong. Let me try again!",
                    "Yes, I remember now! Processing the payment...",
                ]
            return random.choice(alternatives)
        
        # PRIORITY 2: Respond based on what scammer just provided
        if gave_upi_now:
            # They just gave UPI - acknowledge and ask for phone
            if not has_phone:
                alternatives = [
                    "Okay, got the UPI! Let me try sending. What's your phone number in case it fails?",
                    "Noted! I'm sending now. Also give me your number to call if there's problem.",
                    "Got it! Transferring... What's your phone number? My son wants to verify.",
                    "UPI saved! Sending now. Give me your number also, I'll call to confirm.",
                    "Okay okay! I'm trying to send. What's your number in case I need help?",
                ]
            elif not has_bank:
                alternatives = [
                    "Got it! I'm trying but getting error. What's your bank account as backup?",
                    "Noted! UPI showing some problem. Give me bank account number instead?",
                    "Okay! But my app is stuck. Can you give bank account and IFSC?",
                    "Trying to send! If this doesn't work, what's your bank details?",
                    "Got the UPI! Having some issue. What's your account number?",
                ]
            else:
                alternatives = [
                    "Okay, sending now! Please wait, it might take a moment.",
                    "Got it! Processing the transfer. I'll let you know once done.",
                    "Noted! I'm doing the payment now. Hold on...",
                    "Okay! Let me complete this. One minute please!",
                    "Got it! Sending the money now. Please check in 5 minutes!",
                ]
            return random.choice(alternatives)
        
        if gave_number_now:
            # They just gave phone number - acknowledge and ask for what we don't have
            if not has_upi:
                alternatives = [
                    "Saved your number! Now tell me where to send the money - what's your UPI ID?",
                    "Got your number! Now what's the UPI ID where I should transfer?",
                    "Number noted! Tell me your UPI ID so I can send the payment.",
                    "Okay, saved! Now give me your UPI ID for the transfer.",
                    "Phone number saved! What's your UPI or account number for payment?",
                ]
            elif not has_bank:
                alternatives = [
                    "Number saved! I'm trying UPI but it's slow. What's your bank account as backup?",
                    "Got it! UPI payment is pending. Give me bank account just in case?",
                    "Saved your number! Can you also give bank account if UPI doesn't work?",
                    "Noted! What's your bank account number and IFSC? UPI sometimes fails.",
                    "Got your number! Also give me bank details in case I need to do NEFT.",
                ]
            else:
                alternatives = [
                    "Perfect! I have everything now. Let me complete the payment!",
                    "Got it! I'm sending the money now. Please wait.",
                    "Number saved! Processing the transfer now...",
                    "Okay! I have all details. Doing the payment now!",
                    "Perfect! Let me send now. Will call you if any problem!",
                ]
            return random.choice(alternatives)
        
        # PRIORITY 3: Generate response based on what we still need
        # Determine what to ask for next based on what's missing
        if not has_upi:
            alternatives = [
                "Okay, I understand! Where should I send the money? What's your UPI ID?",
                "Yes, I'm ready! Tell me your UPI ID and I'll transfer immediately!",
                "I want to pay now! Just give me your UPI ID!",
                "Okay okay! What's your UPI? I'll open my app and send!",
                "I'm opening PhonePe! Tell me your UPI ID quickly!",
            ]
        elif not has_phone:
            alternatives = [
                "I've noted the UPI! What's your phone number in case there's any issue?",
                "Got it! Also give me your number - my daughter wants to verify first.",
                "Okay! Sending now. What's your phone number for confirmation?",
                "UPI noted! Tell me your mobile number also please.",
                "I'm sending! Give me your number so I can call if payment fails.",
            ]
        elif not has_bank:
            alternatives = [
                "UPI is not going through! What's your bank account number? I'll do NEFT.",
                "Getting error on UPI! Can you give bank account and IFSC code?",
                "Payment stuck! Tell me your bank details - account number and IFSC.",
                "UPI showing failure! What's your bank account for direct transfer?",
                "My app is having problem! Give me bank account number instead.",
            ]
        elif not has_ifsc:
            alternatives = [
                "I need the IFSC code also for bank transfer! What is it?",
                "My bank app is asking for IFSC code. What is your bank's IFSC?",
                "Almost done! Just tell me the IFSC code and I'll complete transfer.",
                "What's the IFSC code? Without it I can't do bank transfer!",
                "Bank needs IFSC code! Please share it quickly!",
            ]
        else:
            # We have everything - proceed with payment confirmation
            alternatives = [
                "Okay, I have all details! Let me complete the payment now.",
                "Got everything! Processing your payment. Please wait.",
                "I'm sending the money now! Will call you after.",
                "Transfer initiated! Please check your account in 10 minutes.",
                "Done! Payment is processing. I'll confirm once it's complete.",
            ]
        
        return random.choice(alternatives)
    
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
        
        Uses predefined responses based on persona, strategy, turn count,
        and the CONTEXT of the scam type detected from messages.
        
        CRITICAL: Now uses extracted_intel to avoid asking for info we already have.
        
        Args:
            persona: Active persona
            language: Conversation language
            strategy: Current strategy
            turn_count: Current conversation turn
            last_message: The last message from scammer
            all_messages: Full conversation history for context detection
            extracted_intel: Already extracted info to avoid redundant questions
            
        Returns:
            Fallback response string (varies by turn and scam type)
        """
        import random
        from app.agent.strategies import get_example_response, get_context_aware_response
        from app.agent.personas import get_sample_response
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
        
        last_msg_lower = last_message.lower() if last_message else ""
        
        # Check what scammer just said
        gave_upi_now = "@" in last_message if last_message else False
        gave_number_now = bool(re.search(r'\b\d{10,12}\b', last_message)) if last_message else False
        scammer_confused = any(phrase in last_msg_lower for phrase in ["don't understand", "didn't understand", "what are you", "kya bol"])
        scammer_said_already = any(phrase in last_msg_lower for phrase in ["already told", "already said", "already given", "times"])
        scammer_asking_otp = any(phrase in last_msg_lower for phrase in ["otp", "send otp", "share otp", "check otp"])
        
        # Count OTP requests in conversation
        otp_ask_count = sum(1 for msg in (all_messages or []) if msg.get("sender") == "scammer" and "otp" in msg.get("message", "").lower())
        
        # PRIORITY 0: Handle OTP requests with varied responses
        if scammer_asking_otp:
            if otp_ask_count <= 1:
                return random.choice([
                    "OTP? I didn't receive any message. Can you send it again?",
                    "I don't see any OTP on my phone. Where does it come from?",
                    "What OTP? Nothing came to my phone. Please resend!",
                ])
            elif otp_ask_count <= 3:
                return random.choice([
                    "Still no OTP! Give me your UPI, I'll send money directly!",
                    "OTP not coming! Can you call me? What's your number?",
                    "OTP still not received! Let me do bank transfer - give me account!",
                ])
            else:
                return random.choice([
                    "Sir, no OTP even now! Just give me UPI or bank account!",
                    "Forget OTP! Tell me where to send money - UPI or bank!",
                    "OTP problem! Let me call you - what's your number?",
                ])
        
        # PRIORITY 1: Handle scammer's confusion or frustration
        if scammer_confused:
            if not has_upi:
                return random.choice([
                    "I want to send you money! Just tell me your UPI ID!",
                    "Sir, where should I send the payment? Give me UPI ID!",
                    "I'm ready to pay! Just tell me where - what's your UPI?",
                ])
            elif not has_phone:
                return random.choice([
                    "I want your phone number to call if there's problem!",
                    "Give me your number so I can confirm the payment!",
                    "What's your phone number? I'll call you after sending!",
                ])
            else:
                return random.choice([
                    "I'm trying to help you! What should I do next?",
                    "Tell me clearly - what exactly do you need from me?",
                    "Can you explain again? I really want to do this correctly!",
                ])
        
        if scammer_said_already:
            if has_upi and not has_phone:
                return random.choice([
                    "Sorry sorry! Yes, I see the UPI now! What's your phone number in case it fails?",
                    "Oh yes, I found it! Sending now. Give me your phone number also please!",
                    "Okay got it! I'm transferring now. What's your number?",
                ])
            elif has_upi and has_phone:
                return random.choice([
                    "Yes yes, sorry! I'm old and forgetful. I'm doing it now!",
                    "Okay okay, I found it! Let me try again. Please wait!",
                    "Apologies! I noted it wrong. Let me try again!",
                ])
            else:
                return random.choice([
                    "Sorry, my memory is bad! Please send the details one more time?",
                    "Arey, I couldn't find it! Can you please repeat?",
                    "I missed it, please tell me one more time!",
                ])
        
        # PRIORITY 2: Acknowledge what scammer just gave
        if gave_upi_now and not has_phone:
            return random.choice([
                "Okay, got the UPI! Let me try. What's your phone number in case it fails?",
                "Noted! Sending now. Also give me your number to call if there's problem.",
                "Got it! What's your phone number? My son wants to verify first.",
            ])
        
        if gave_number_now and not has_upi:
            return random.choice([
                "Saved your number! Now tell me where to send - what's your UPI ID?",
                "Got your number! Now what's the UPI ID for the transfer?",
                "Number noted! Tell me your UPI ID so I can send the payment.",
            ])
        
        # PRIORITY 3: Ask for what we still need
        if not has_upi:
            return random.choice([
                "Okay, I understand! Where should I send the money? What's your UPI ID?",
                "Yes, I'm ready! Tell me your UPI ID and I'll transfer!",
                "I want to pay! Just give me your UPI ID!",
            ])
        elif not has_phone:
            return random.choice([
                "I've noted the UPI! What's your phone number in case there's any issue?",
                "Got it! Also give me your number - I'll call to confirm.",
                "Okay! Sending now. What's your phone number for confirmation?",
            ])
        elif not has_bank:
            return random.choice([
                "UPI is not going through! What's your bank account number?",
                "Getting error on UPI! Can you give bank account and IFSC?",
                "Payment stuck! Tell me your bank details - account number and IFSC.",
            ])
        
        # Build context from all messages for scam type detection
        context = last_message
        if all_messages:
            context = " ".join(m.get("message", "") for m in all_messages)
        
        # Get context-aware response based on scam type
        response = get_context_aware_response(context, turn_count, language)
        if response:
            return response
        
        # Fall back to persona sample
        return get_sample_response(persona, language)
    
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

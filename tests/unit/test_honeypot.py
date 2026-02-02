"""
Unit Tests for Honeypot Agent Module (Task 5.2).

Tests the LangGraph-based agentic honeypot system:
- Workflow initialization and execution
- Strategy progression
- Termination logic
- Persona and language integration

Acceptance Criteria:
- AC-2.2.1: Engagement averages >10 turns
- AC-2.2.2: Strategy progression works
- AC-2.2.3: Termination logic correct
- AC-2.2.4: No infinite loops
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from app.agent.honeypot import (
    HoneypotAgent,
    HoneypotState,
    get_honeypot_agent,
    reset_honeypot_agent,
    MAX_TURNS,
    EXTRACTION_CONFIDENCE_THRESHOLD,
)


@pytest.fixture(autouse=True)
def reset_agent():
    """Reset singleton agent before each test."""
    reset_honeypot_agent()
    yield
    reset_honeypot_agent()


class TestHoneypotState:
    """Tests for HoneypotState TypedDict."""
    
    def test_state_has_required_fields(self):
        """Test HoneypotState has all required fields."""
        state: HoneypotState = {
            "messages": [],
            "scam_confidence": 0.0,
            "turn_count": 0,
            "extracted_intel": {},
            "extraction_confidence": 0.0,
            "strategy": "build_trust",
            "language": "en",
            "persona": "elderly",
            "max_turns_reached": False,
            "terminated": False,
        }
        
        assert "messages" in state
        assert "scam_confidence" in state
        assert "turn_count" in state
        assert "extracted_intel" in state
        assert "strategy" in state
        assert "language" in state
        assert "persona" in state


class TestHoneypotAgentInitialization:
    """Tests for HoneypotAgent initialization."""
    
    def test_agent_initializes_without_llm(self):
        """Test agent initializes without LLM (for testing)."""
        agent = HoneypotAgent(use_llm=False)
        
        assert agent is not None
        assert agent._initialized is True
        assert agent.llm is None
    
    def test_agent_has_workflow(self):
        """Test agent has workflow after initialization."""
        agent = HoneypotAgent(use_llm=False)
        
        # Workflow should be built even without LLM
        assert agent.workflow is not None
    
    @patch.dict("os.environ", {"GROQ_API_KEY": ""})
    def test_agent_without_api_key(self):
        """Test agent handles missing API key gracefully."""
        agent = HoneypotAgent(use_llm=True)
        
        assert agent._initialized is True
        # LLM should be None without API key
        assert agent.llm is None


class TestStrategyProgression:
    """Tests for strategy progression (AC-2.2.2)."""
    
    def test_build_trust_strategy_for_early_turns(self):
        """Test build_trust strategy for turns 1-5."""
        agent = HoneypotAgent(use_llm=False)
        
        for turn in [1, 2, 3, 4, 5]:
            state = {"turn_count": turn}
            result = agent._plan_response(state)
            
            assert result["strategy"] == "build_trust", f"Turn {turn} should use build_trust"
    
    def test_express_confusion_strategy_for_middle_turns(self):
        """Test express_confusion strategy for turns 6-12."""
        agent = HoneypotAgent(use_llm=False)
        
        for turn in [6, 7, 8, 9, 10, 11, 12]:
            state = {"turn_count": turn}
            result = agent._plan_response(state)
            
            assert result["strategy"] == "express_confusion", f"Turn {turn} should use express_confusion"
    
    def test_probe_details_strategy_for_late_turns(self):
        """Test probe_details strategy for turns 13+."""
        agent = HoneypotAgent(use_llm=False)
        
        for turn in [13, 14, 15, 16, 17, 18, 19, 20]:
            state = {"turn_count": turn}
            result = agent._plan_response(state)
            
            assert result["strategy"] == "probe_details", f"Turn {turn} should use probe_details"
    
    def test_strategy_progression_full_conversation(self):
        """Test strategy progression through a full conversation."""
        agent = HoneypotAgent(use_llm=False)
        
        strategies_seen = []
        for turn in range(1, 21):
            state = {"turn_count": turn}
            result = agent._plan_response(state)
            strategies_seen.append(result["strategy"])
        
        # Should have all three strategies
        assert "build_trust" in strategies_seen
        assert "express_confusion" in strategies_seen
        assert "probe_details" in strategies_seen
        
        # First 5 should be build_trust
        assert all(s == "build_trust" for s in strategies_seen[:5])
        
        # Turns 6-12 should be express_confusion
        assert all(s == "express_confusion" for s in strategies_seen[5:12])
        
        # Turns 13-20 should be probe_details
        assert all(s == "probe_details" for s in strategies_seen[12:])


class TestTerminationLogic:
    """Tests for termination logic (AC-2.2.3, AC-2.2.4)."""
    
    def test_max_turns_constant(self):
        """Test MAX_TURNS is 20."""
        assert MAX_TURNS == 20
    
    def test_extraction_threshold_constant(self):
        """Test extraction confidence threshold."""
        assert EXTRACTION_CONFIDENCE_THRESHOLD == 0.85
    
    def test_termination_at_max_turns(self):
        """Test termination when max turns reached (AC-2.2.4)."""
        agent = HoneypotAgent(use_llm=False)
        
        state = {
            "turn_count": 20,
            "extraction_confidence": 0.0,
        }
        
        result = agent._should_continue(state)
        
        assert result == "end"
    
    def test_termination_at_high_confidence(self):
        """Test termination when high extraction confidence."""
        agent = HoneypotAgent(use_llm=False)
        
        state = {
            "turn_count": 5,
            "extraction_confidence": 0.9,
        }
        
        result = agent._should_continue(state)
        
        assert result == "end"
    
    def test_termination_exactly_at_threshold(self):
        """Test termination at exactly 0.85 confidence."""
        agent = HoneypotAgent(use_llm=False)
        
        state = {
            "turn_count": 5,
            "extraction_confidence": 0.85,
        }
        
        result = agent._should_continue(state)
        
        assert result == "end"
    
    def test_continuation_below_threshold(self):
        """Test continuation when below threshold."""
        agent = HoneypotAgent(use_llm=False)
        
        state = {
            "turn_count": 5,
            "extraction_confidence": 0.5,
        }
        
        result = agent._should_continue(state)
        
        assert result == "continue"
    
    def test_continuation_at_turn_19(self):
        """Test continuation at turn 19 (before max)."""
        agent = HoneypotAgent(use_llm=False)
        
        state = {
            "turn_count": 19,
            "extraction_confidence": 0.0,
        }
        
        result = agent._should_continue(state)
        
        assert result == "continue"
    
    def test_no_infinite_loops(self):
        """Test that conversation cannot exceed MAX_TURNS (AC-2.2.4)."""
        agent = HoneypotAgent(use_llm=False)
        
        # Simulate a conversation that never extracts anything
        session_state = None
        
        for i in range(25):  # Try more than MAX_TURNS
            session_state = agent.engage(
                f"Scam message {i}",
                session_state=session_state,
            )
            
            # Check we never exceed max turns
            assert session_state["turn_count"] <= MAX_TURNS + 1
            
            # After max turns, should be terminated
            if session_state["turn_count"] >= MAX_TURNS:
                assert session_state.get("terminated", False) or session_state.get("max_turns_reached", False)
                break


class TestEngageMethod:
    """Tests for the engage() method."""
    
    def test_engage_creates_new_session(self):
        """Test engage creates new session if none provided."""
        agent = HoneypotAgent(use_llm=False)
        
        result = agent.engage("You won 10 lakh!")
        
        assert result is not None
        assert "messages" in result
        assert "turn_count" in result
        assert "language" in result
        assert "persona" in result
    
    def test_engage_returns_messages(self):
        """Test engage returns messages list."""
        agent = HoneypotAgent(use_llm=False)
        
        result = agent.engage("You won a prize!")
        
        assert len(result["messages"]) >= 2  # Scammer + agent
        
        # First message should be from scammer
        assert result["messages"][0]["sender"] == "scammer"
    
    def test_engage_increments_turn_count(self):
        """Test engage increments turn count."""
        agent = HoneypotAgent(use_llm=False)
        
        result1 = agent.engage("First message")
        assert result1["turn_count"] == 1
        
        result2 = agent.engage("Second message", session_state=result1)
        assert result2["turn_count"] == 2
    
    def test_engage_with_existing_session(self):
        """Test engage with existing session state."""
        agent = HoneypotAgent(use_llm=False)
        
        # First turn
        session = agent.engage("You won 10 lakh rupees!")
        initial_message_count = len(session["messages"])
        
        # Second turn
        session = agent.engage("Send your OTP to claim", session_state=session)
        
        # Should have more messages
        assert len(session["messages"]) > initial_message_count
        assert session["turn_count"] == 2
    
    def test_engage_with_scam_type(self):
        """Test engage with scam_type parameter."""
        agent = HoneypotAgent(use_llm=False)
        
        result = agent.engage(
            "You won a lottery prize!",
            scam_type="lottery",
        )
        
        # Should select appropriate persona
        assert result["persona"] == "eager"
    
    def test_engage_detects_language(self):
        """Test engage detects language."""
        agent = HoneypotAgent(use_llm=False)
        
        # English message
        result_en = agent.engage("You won 10 lakh rupees!")
        assert result_en["language"] in ["en", "hi", "hinglish"]
        
        # Hindi message
        result_hi = agent.engage("आप जीत गए हैं 10 लाख रुपये!")
        assert result_hi["language"] in ["hi", "hinglish"]
    
    def test_engage_adds_timestamps(self):
        """Test engage adds timestamps to messages."""
        agent = HoneypotAgent(use_llm=False)
        
        result = agent.engage("Test message")
        
        for msg in result["messages"]:
            assert "timestamp" in msg
            # Should be ISO format
            assert "T" in msg["timestamp"]


class TestResponseGeneration:
    """Tests for response generation."""
    
    def test_generate_fallback_response(self):
        """Test fallback response generation."""
        agent = HoneypotAgent(use_llm=False)
        
        response = agent._generate_fallback_response(
            persona="elderly",
            language="en",
            strategy="build_trust",
        )
        
        assert response is not None
        assert len(response) > 0
    
    def test_generate_response_adds_message(self):
        """Test _generate_response adds agent message."""
        agent = HoneypotAgent(use_llm=False)
        
        state = {
            "messages": [
                {"turn": 1, "sender": "scammer", "message": "You won!"}
            ],
            "turn_count": 1,
            "persona": "elderly",
            "language": "en",
            "strategy": "build_trust",
        }
        
        result = agent._generate_response(state)
        
        assert len(result["messages"]) == 2
        assert result["messages"][-1]["sender"] == "agent"
    
    def test_fallback_response_for_different_personas(self):
        """Test fallback responses for different personas."""
        agent = HoneypotAgent(use_llm=False)
        
        personas = ["elderly", "eager", "confused"]
        
        for persona in personas:
            response = agent._generate_fallback_response(
                persona=persona,
                language="en",
                strategy="build_trust",
            )
            
            assert response is not None
            assert len(response) > 0
    
    def test_fallback_response_for_hindi(self):
        """Test fallback response for Hindi language."""
        agent = HoneypotAgent(use_llm=False)
        
        response = agent._generate_fallback_response(
            persona="elderly",
            language="hi",
            strategy="build_trust",
        )
        
        assert response is not None
        assert len(response) > 0


class TestIntelligenceExtraction:
    """Tests for intelligence extraction."""
    
    def test_extract_intelligence_from_messages(self):
        """Test intelligence extraction from conversation."""
        agent = HoneypotAgent(use_llm=False)
        
        state = {
            "messages": [
                {"message": "Send money to scammer@paytm"},
                {"message": "My number is +919876543210"},
            ]
        }
        
        result = agent._extract_intelligence(state)
        
        assert "extracted_intel" in result
        assert "extraction_confidence" in result
    
    def test_extract_upi_ids(self):
        """Test UPI ID extraction."""
        agent = HoneypotAgent(use_llm=False)
        
        state = {
            "messages": [
                {"message": "Pay to scammer@paytm right now"},
            ]
        }
        
        result = agent._extract_intelligence(state)
        
        assert "scammer@paytm" in result["extracted_intel"]["upi_ids"]
    
    def test_extract_phone_numbers(self):
        """Test phone number extraction."""
        agent = HoneypotAgent(use_llm=False)
        
        state = {
            "messages": [
                {"message": "Call me at +919876543210"},
            ]
        }
        
        result = agent._extract_intelligence(state)
        
        # Should extract the phone number
        assert len(result["extracted_intel"]["phone_numbers"]) > 0
    
    def test_extraction_confidence_calculation(self):
        """Test extraction confidence is calculated."""
        agent = HoneypotAgent(use_llm=False)
        
        # Message with multiple entities
        state = {
            "messages": [
                {"message": "Send to scammer@paytm, account 1234567890123, IFSC SBIN0001234"},
            ]
        }
        
        result = agent._extract_intelligence(state)
        
        # Should have some confidence
        assert result["extraction_confidence"] >= 0.0


class TestConversationFlow:
    """Tests for multi-turn conversation flow."""
    
    def test_multi_turn_conversation(self):
        """Test a multi-turn conversation flow."""
        agent = HoneypotAgent(use_llm=False)
        
        # Turn 1
        session = agent.engage("Congratulations! You won 10 lakh!")
        assert session["turn_count"] == 1
        assert session["strategy"] == "build_trust"
        
        # Turn 5
        for i in range(4):
            session = agent.engage(f"Message {i+2}", session_state=session)
        
        assert session["turn_count"] == 5
        
        # Turn 6 - should switch to express_confusion
        session = agent.engage("Send OTP now!", session_state=session)
        assert session["strategy"] == "express_confusion"
        assert session["turn_count"] == 6
    
    def test_conversation_maintains_context(self):
        """Test conversation maintains message history."""
        agent = HoneypotAgent(use_llm=False)
        
        messages_sent = [
            "You won!",
            "Send OTP",
            "Pay to scammer@paytm",
        ]
        
        session = None
        for msg in messages_sent:
            session = agent.engage(msg, session_state=session)
        
        # Should have all scammer messages in history
        scammer_messages = [
            m["message"] for m in session["messages"]
            if m["sender"] == "scammer"
        ]
        
        for sent_msg in messages_sent:
            assert sent_msg in scammer_messages
    
    def test_persona_remains_constant(self):
        """Test persona doesn't change mid-conversation."""
        agent = HoneypotAgent(use_llm=False)
        
        session = agent.engage("You won!", scam_type="lottery")
        initial_persona = session["persona"]
        
        # Continue conversation
        for i in range(5):
            session = agent.engage(f"Message {i}", session_state=session)
        
        # Persona should remain the same
        assert session["persona"] == initial_persona


class TestHelperMethods:
    """Tests for helper methods."""
    
    def test_get_agent_response(self):
        """Test get_agent_response helper."""
        agent = HoneypotAgent(use_llm=False)
        
        session = agent.engage("Test message")
        response = agent.get_agent_response(session)
        
        assert response is not None
        assert len(response) > 0
    
    def test_get_agent_response_empty(self):
        """Test get_agent_response with no agent messages."""
        agent = HoneypotAgent(use_llm=False)
        
        session = {"messages": []}
        response = agent.get_agent_response(session)
        
        assert response is None
    
    def test_get_extracted_intelligence(self):
        """Test get_extracted_intelligence helper."""
        agent = HoneypotAgent(use_llm=False)
        
        session = agent.engage("Send to scammer@paytm")
        intel = agent.get_extracted_intelligence(session)
        
        assert "extraction_confidence" in intel
        assert "upi_ids" in intel


class TestSingletonPattern:
    """Tests for singleton pattern."""
    
    def test_get_honeypot_agent_returns_same_instance(self):
        """Test get_honeypot_agent returns singleton."""
        agent1 = get_honeypot_agent(use_llm=False)
        agent2 = get_honeypot_agent(use_llm=False)
        
        assert agent1 is agent2
    
    def test_reset_honeypot_agent(self):
        """Test reset_honeypot_agent clears singleton."""
        agent1 = get_honeypot_agent(use_llm=False)
        
        reset_honeypot_agent()
        
        agent2 = get_honeypot_agent(use_llm=False)
        
        assert agent1 is not agent2


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_empty_message(self):
        """Test handling empty message."""
        agent = HoneypotAgent(use_llm=False)
        
        result = agent.engage("")
        
        assert result is not None
        assert "messages" in result
    
    def test_very_long_message(self):
        """Test handling very long message."""
        agent = HoneypotAgent(use_llm=False)
        
        long_message = "x" * 5000
        result = agent.engage(long_message)
        
        assert result is not None
    
    def test_special_characters_in_message(self):
        """Test handling special characters."""
        agent = HoneypotAgent(use_llm=False)
        
        result = agent.engage("You won! 🎉 Pay ₹1000 <script>alert('xss')</script>")
        
        assert result is not None
    
    def test_unicode_hindi_message(self):
        """Test handling Unicode Hindi text."""
        agent = HoneypotAgent(use_llm=False)
        
        result = agent.engage("आप जीत गए हैं! ₹10 लाख भेजें।")
        
        assert result is not None
        assert result["language"] in ["hi", "hinglish"]
    
    def test_terminated_session_no_new_messages(self):
        """Test terminated session returns immediately."""
        agent = HoneypotAgent(use_llm=False)
        
        # Create terminated session
        session = {
            "messages": [{"turn": 1, "sender": "scammer", "message": "test"}],
            "turn_count": 20,
            "terminated": True,
            "max_turns_reached": True,
            "extraction_confidence": 0.0,
            "extracted_intel": {},
            "strategy": "probe_details",
            "language": "en",
            "persona": "elderly",
        }
        
        result = agent.engage("New message", session_state=session)
        
        assert result["terminated"] is True


class TestAcceptanceCriteria:
    """
    Tests for Task 5.2 Acceptance Criteria.
    
    AC-2.2.1: Engagement averages >10 turns
    AC-2.2.2: Strategy progression works
    AC-2.2.3: Termination logic correct
    AC-2.2.4: No infinite loops
    """
    
    def test_ac_2_2_1_engagement_length(self):
        """AC-2.2.1: Potential for >10 turns of engagement."""
        agent = HoneypotAgent(use_llm=False)
        
        # Simulate a long conversation with no extraction
        session = None
        for i in range(15):
            session = agent.engage(f"Message {i}", session_state=session)
        
        # Should reach at least 10 turns before any termination
        assert session["turn_count"] >= 10
    
    def test_ac_2_2_2_strategy_progression(self):
        """AC-2.2.2: Strategy progression works correctly."""
        agent = HoneypotAgent(use_llm=False)
        
        # Track strategies across turns
        session = None
        strategies = []
        
        for i in range(20):
            session = agent.engage(f"Message {i}", session_state=session)
            strategies.append(session["strategy"])
            
            if session.get("terminated"):
                break
        
        # Verify progression
        assert strategies[0] == "build_trust"  # Turn 1
        assert strategies[4] == "build_trust"  # Turn 5
        
        if len(strategies) > 5:
            assert strategies[5] == "express_confusion"  # Turn 6
        
        if len(strategies) > 12:
            assert strategies[12] == "probe_details"  # Turn 13
    
    def test_ac_2_2_3_termination_max_turns(self):
        """AC-2.2.3: Termination at max turns."""
        agent = HoneypotAgent(use_llm=False)
        
        state = {"turn_count": 20, "extraction_confidence": 0.0}
        
        assert agent._should_continue(state) == "end"
    
    def test_ac_2_2_3_termination_high_confidence(self):
        """AC-2.2.3: Termination at high confidence."""
        agent = HoneypotAgent(use_llm=False)
        
        state = {"turn_count": 5, "extraction_confidence": 0.9}
        
        assert agent._should_continue(state) == "end"
    
    def test_ac_2_2_4_no_infinite_loops(self):
        """AC-2.2.4: No infinite loops - hard cap at 20 turns."""
        agent = HoneypotAgent(use_llm=False)
        
        session = None
        
        # Try to run 30 turns
        for i in range(30):
            session = agent.engage(f"Message {i}", session_state=session)
            
            # Verify we never exceed max
            assert session["turn_count"] <= MAX_TURNS + 1
            
            # Should terminate at or before max turns
            if session["turn_count"] >= MAX_TURNS:
                break
        
        # Final state should show termination
        assert session["turn_count"] <= MAX_TURNS + 1

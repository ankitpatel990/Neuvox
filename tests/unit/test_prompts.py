"""
Unit Tests for Prompt Templates Module.

Tests prompt generation for the honeypot agent.
"""

import pytest

from app.agent.prompts import (
    SYSTEM_PROMPT_TEMPLATE,
    STRATEGY_PROMPTS,
    STRATEGY_PROMPTS_HI,
    get_system_prompt,
    get_response_prompt,
    get_extraction_prompt,
)


class TestSystemPromptTemplate:
    """Tests for system prompt template."""
    
    def test_template_exists(self):
        """Test system prompt template is defined."""
        assert SYSTEM_PROMPT_TEMPLATE is not None
        assert len(SYSTEM_PROMPT_TEMPLATE) > 0
    
    def test_template_has_placeholders(self):
        """Test template contains required placeholders."""
        assert "{persona}" in SYSTEM_PROMPT_TEMPLATE
        assert "{language}" in SYSTEM_PROMPT_TEMPLATE
        assert "{strategy}" in SYSTEM_PROMPT_TEMPLATE
        assert "{turn_count}" in SYSTEM_PROMPT_TEMPLATE
    
    def test_template_has_critical_rules(self):
        """Test template includes critical rules."""
        assert "CRITICAL RULES" in SYSTEM_PROMPT_TEMPLATE or "Never reveal" in SYSTEM_PROMPT_TEMPLATE


class TestStrategyPrompts:
    """Tests for strategy prompt dictionaries."""
    
    def test_english_strategies_defined(self):
        """Test all English strategy prompts are defined."""
        assert "build_trust" in STRATEGY_PROMPTS
        assert "express_confusion" in STRATEGY_PROMPTS
        assert "probe_details" in STRATEGY_PROMPTS
    
    def test_hindi_strategies_defined(self):
        """Test all Hindi strategy prompts are defined."""
        assert "build_trust" in STRATEGY_PROMPTS_HI
        assert "express_confusion" in STRATEGY_PROMPTS_HI
        assert "probe_details" in STRATEGY_PROMPTS_HI
    
    def test_build_trust_prompt_content(self):
        """Test build_trust prompt has relevant content."""
        prompt = STRATEGY_PROMPTS["build_trust"]
        assert "trust" in prompt.lower() or "interest" in prompt.lower()
    
    def test_express_confusion_prompt_content(self):
        """Test express_confusion prompt has relevant content."""
        prompt = STRATEGY_PROMPTS["express_confusion"]
        assert "confusion" in prompt.lower() or "understand" in prompt.lower()
    
    def test_probe_details_prompt_content(self):
        """Test probe_details prompt has relevant content."""
        prompt = STRATEGY_PROMPTS["probe_details"]
        assert "detail" in prompt.lower() or "payment" in prompt.lower() or "UPI" in prompt


class TestGetSystemPrompt:
    """Tests for get_system_prompt function."""
    
    def test_returns_string(self):
        """Test function returns a string."""
        result = get_system_prompt(
            persona="elderly",
            language="en",
            strategy="build_trust",
            turn_count=1
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_includes_persona(self):
        """Test result includes persona name."""
        result = get_system_prompt(
            persona="eager",
            language="en",
            strategy="build_trust",
            turn_count=5
        )
        
        assert "eager" in result
    
    def test_includes_turn_count(self):
        """Test result includes turn count."""
        result = get_system_prompt(
            persona="confused",
            language="en",
            strategy="express_confusion",
            turn_count=10
        )
        
        assert "10" in result
    
    def test_english_strategy_appended(self):
        """Test English strategy prompt is appended."""
        result = get_system_prompt(
            persona="elderly",
            language="en",
            strategy="probe_details",
            turn_count=15
        )
        
        # Should include content from probe_details strategy
        assert "detail" in result.lower() or "payment" in result.lower() or "UPI" in result
    
    def test_hindi_strategy_appended(self):
        """Test Hindi strategy prompt is appended for hi language."""
        result = get_system_prompt(
            persona="elderly",
            language="hi",
            strategy="build_trust",
            turn_count=1
        )
        
        # Should include Hindi content
        assert "विश्वास" in result or "रुचि" in result or "लक्ष्य" in result
    
    def test_unknown_strategy_handled(self):
        """Test unknown strategy doesn't crash."""
        result = get_system_prompt(
            persona="elderly",
            language="en",
            strategy="unknown_strategy",
            turn_count=1
        )
        
        assert isinstance(result, str)
        assert "elderly" in result


class TestGetResponsePrompt:
    """Tests for get_response_prompt function."""
    
    def test_returns_string(self):
        """Test function returns a string."""
        result = get_response_prompt(
            scammer_message="You won a prize!",
            conversation_history=[],
            language="en"
        )
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_includes_scammer_message(self):
        """Test result includes scammer message."""
        result = get_response_prompt(
            scammer_message="Send money to this account",
            conversation_history=[],
            language="en"
        )
        
        assert "Send money to this account" in result
    
    def test_english_prompt_format(self):
        """Test English prompt format."""
        result = get_response_prompt(
            scammer_message="Test message",
            conversation_history=[],
            language="en"
        )
        
        assert "Scammer's message" in result or "scammer" in result.lower()
        assert "persona" in result.lower()
    
    def test_hindi_prompt_format(self):
        """Test Hindi prompt format."""
        result = get_response_prompt(
            scammer_message="Test message",
            conversation_history=[],
            language="hi"
        )
        
        assert "घोटालेबाज" in result or "संदेश" in result


class TestGetExtractionPrompt:
    """Tests for get_extraction_prompt function."""
    
    def test_returns_string(self):
        """Test function returns a string."""
        result = get_extraction_prompt("Test conversation text")
        
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_includes_conversation_text(self):
        """Test result includes conversation text."""
        result = get_extraction_prompt("Pay to scammer@paytm account 1234567890")
        
        assert "scammer@paytm" in result
        assert "1234567890" in result
    
    def test_mentions_entity_types(self):
        """Test prompt mentions entity types to extract."""
        result = get_extraction_prompt("Sample conversation")
        
        assert "UPI" in result
        assert "bank" in result.lower() or "account" in result.lower()
        assert "IFSC" in result
        assert "phone" in result.lower()
        assert "URL" in result.lower() or "link" in result.lower()
    
    def test_requests_json_output(self):
        """Test prompt requests JSON output."""
        result = get_extraction_prompt("Sample conversation")
        
        assert "JSON" in result or "json" in result


class TestPromptIntegration:
    """Integration tests for prompt components."""
    
    def test_all_personas_work_with_prompts(self):
        """Test all personas work with prompt generation."""
        personas = ["elderly", "eager", "confused"]
        
        for persona in personas:
            result = get_system_prompt(
                persona=persona,
                language="en",
                strategy="build_trust",
                turn_count=1
            )
            assert persona in result
    
    def test_all_strategies_work_with_prompts(self):
        """Test all strategies work with prompt generation."""
        strategies = ["build_trust", "express_confusion", "probe_details"]
        
        for strategy in strategies:
            result = get_system_prompt(
                persona="elderly",
                language="en",
                strategy=strategy,
                turn_count=1
            )
            assert isinstance(result, str)
            assert len(result) > 100  # Should have substantial content
    
    def test_both_languages_work(self):
        """Test both languages work with prompt generation."""
        for lang in ["en", "hi"]:
            result = get_system_prompt(
                persona="elderly",
                language=lang,
                strategy="build_trust",
                turn_count=1
            )
            assert isinstance(result, str)
            assert len(result) > 100

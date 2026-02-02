"""
Unit Tests for Persona Management Module (Task 5.1).

Tests the Persona system for honeypot agent engagement:
- Persona dataclass and attributes
- Persona selection based on scam types
- Persona prompt generation
- Multi-language support

Acceptance Criteria:
- AC-2.1.1: Persona selection aligns with scam type (tested on 50+ scenarios)
- AC-2.1.2: Responses match persona characteristics (human evaluation >80% believability)
- AC-2.1.3: No persona switching mid-conversation
- AC-2.1.4: Responses in correct language (match input language)
"""

import pytest
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


class TestPersonaDataclass:
    """Tests for Persona dataclass."""
    
    def test_persona_has_required_attributes(self):
        """Test Persona dataclass has all required attributes."""
        persona = Persona(
            name="test",
            age_range="20-30",
            tech_literacy="high",
            traits=["trait1", "trait2"],
            response_style="test style",
        )
        
        assert hasattr(persona, "name")
        assert hasattr(persona, "age_range")
        assert hasattr(persona, "tech_literacy")
        assert hasattr(persona, "traits")
        assert hasattr(persona, "response_style")
        assert hasattr(persona, "suitable_scam_types")
    
    def test_persona_attributes_types(self):
        """Test Persona attributes have correct types."""
        persona = Persona(
            name="test",
            age_range="20-30",
            tech_literacy="high",
            traits=["trait1"],
            response_style="style",
        )
        
        assert isinstance(persona.name, str)
        assert isinstance(persona.age_range, str)
        assert isinstance(persona.tech_literacy, str)
        assert isinstance(persona.traits, list)
        assert isinstance(persona.response_style, str)
        assert isinstance(persona.suitable_scam_types, list)
    
    def test_persona_default_suitable_scam_types(self):
        """Test suitable_scam_types defaults to empty list."""
        persona = Persona(
            name="test",
            age_range="20-30",
            tech_literacy="high",
            traits=["trait1"],
            response_style="style",
        )
        
        assert persona.suitable_scam_types == []


class TestPredefinedPersonas:
    """Tests for predefined PERSONAS dictionary."""
    
    def test_personas_dictionary_exists(self):
        """Test PERSONAS dictionary is defined."""
        assert PERSONAS is not None
        assert isinstance(PERSONAS, dict)
    
    def test_three_personas_defined(self):
        """Test exactly three personas are defined."""
        assert len(PERSONAS) == 3
    
    def test_elderly_persona_exists(self):
        """Test elderly persona is defined."""
        assert "elderly" in PERSONAS
        persona = PERSONAS["elderly"]
        
        assert persona.name == "elderly"
        assert persona.age_range == "60-75"
        assert persona.tech_literacy == "low"
        assert "trusting" in persona.traits
        assert "confused by technology" in persona.traits
    
    def test_eager_persona_exists(self):
        """Test eager persona is defined."""
        assert "eager" in PERSONAS
        persona = PERSONAS["eager"]
        
        assert persona.name == "eager"
        assert persona.age_range == "35-50"
        assert persona.tech_literacy == "medium"
        assert "excited" in persona.traits
        assert "compliant" in persona.traits
    
    def test_confused_persona_exists(self):
        """Test confused persona is defined."""
        assert "confused" in PERSONAS
        persona = PERSONAS["confused"]
        
        assert persona.name == "confused"
        assert persona.age_range == "25-40"
        assert persona.tech_literacy == "medium"
        assert "uncertain" in persona.traits
        assert "cautious" in persona.traits
    
    def test_persona_traits_not_empty(self):
        """Test all personas have non-empty traits."""
        for name, persona in PERSONAS.items():
            assert len(persona.traits) > 0, f"{name} has no traits"
    
    def test_persona_response_style_not_empty(self):
        """Test all personas have response style."""
        for name, persona in PERSONAS.items():
            assert persona.response_style, f"{name} has no response style"
    
    def test_persona_suitable_scam_types(self):
        """Test all personas have suitable scam types defined."""
        for name, persona in PERSONAS.items():
            assert len(persona.suitable_scam_types) > 0, f"{name} has no suitable scam types"


class TestSelectPersona:
    """Tests for select_persona function (AC-2.1.1)."""
    
    # Test lottery/prize scams -> eager
    @pytest.mark.parametrize("scam_type", [
        "lottery",
        "prize",
        "winner",
        "jackpot",
        "lucky_draw",
        "contest",
        "gift",
        "reward",
        "lottery_scam",
        "prize_winner",
        "LOTTERY",
        "Prize",
    ])
    def test_lottery_scams_select_eager(self, scam_type):
        """Test lottery/prize scams select eager persona."""
        result = select_persona(scam_type, "en")
        assert result == "eager", f"{scam_type} should select 'eager'"
    
    # Test police/threat scams -> elderly
    @pytest.mark.parametrize("scam_type", [
        "police",
        "police_threat",
        "arrest",
        "court",
        "government",
        "tax",
        "investigation",
        "warrant",
        "legal",
        "cbi",
        "enforcement_directorate",
        "POLICE",
        "Police_Threat",
    ])
    def test_police_scams_select_elderly(self, scam_type):
        """Test police/threat scams select elderly persona."""
        result = select_persona(scam_type, "en")
        assert result == "elderly", f"{scam_type} should select 'elderly'"
    
    # Test bank/phishing scams -> confused
    @pytest.mark.parametrize("scam_type", [
        "bank_fraud",
        "bank",
        "kyc",
        "verification",
        "account",
        "credit_card",
        "loan",
        "insurance",
        "phishing",
        "link",
        "website",
        "password",
        "BANK_FRAUD",
        "Bank",
    ])
    def test_bank_scams_select_confused(self, scam_type):
        """Test bank/phishing scams select confused persona."""
        result = select_persona(scam_type, "en")
        assert result == "confused", f"{scam_type} should select 'confused'"
    
    # Test courier scams -> eager
    @pytest.mark.parametrize("scam_type", [
        "courier",
        "courier_fraud",
        "delivery",
        "parcel",
        "customs",
    ])
    def test_courier_scams_select_eager(self, scam_type):
        """Test courier scams select eager persona."""
        result = select_persona(scam_type, "en")
        assert result == "eager", f"{scam_type} should select 'eager'"
    
    # Test tech support scams -> elderly
    @pytest.mark.parametrize("scam_type", [
        "tech_support",
        "virus",
        "computer",
        "software",
    ])
    def test_tech_support_scams_select_elderly(self, scam_type):
        """Test tech support scams select elderly persona."""
        result = select_persona(scam_type, "en")
        assert result == "elderly", f"{scam_type} should select 'elderly'"
    
    # Test investment scams -> eager
    @pytest.mark.parametrize("scam_type", [
        "investment",
        "crypto",
        "trading",
        "stock",
    ])
    def test_investment_scams_select_eager(self, scam_type):
        """Test investment scams select eager persona."""
        result = select_persona(scam_type, "en")
        assert result == "eager", f"{scam_type} should select 'eager'"
    
    def test_unknown_scam_type_returns_default(self):
        """Test unknown scam types return default persona."""
        result = select_persona("random_unknown_type", "en")
        assert result == DEFAULT_PERSONA
    
    def test_empty_scam_type_returns_default(self):
        """Test empty scam type returns default persona."""
        result = select_persona("", "en")
        assert result == DEFAULT_PERSONA
    
    def test_none_scam_type_handled(self):
        """Test None-like empty scam type returns default."""
        result = select_persona("", "en")
        assert result == DEFAULT_PERSONA
    
    def test_case_insensitive_matching(self):
        """Test scam type matching is case-insensitive."""
        assert select_persona("LOTTERY", "en") == "eager"
        assert select_persona("Lottery", "en") == "eager"
        assert select_persona("lottery", "en") == "eager"
    
    def test_compound_scam_type_matching(self):
        """Test compound scam types are matched correctly."""
        assert select_persona("lottery_prize_scam", "en") == "eager"
        assert select_persona("police_department_fraud", "en") == "elderly"
        assert select_persona("bank_account_phishing", "en") == "confused"
    
    def test_language_parameter_accepted(self):
        """Test select_persona accepts language parameter."""
        result_en = select_persona("lottery", "en")
        result_hi = select_persona("lottery", "hi")
        
        # Both should return same persona
        assert result_en == result_hi == "eager"
    
    def test_hinglish_language(self):
        """Test select_persona works with hinglish language."""
        result = select_persona("lottery", "hinglish")
        assert result == "eager"


class TestGetPersonaPrompt:
    """Tests for get_persona_prompt function (AC-2.1.4)."""
    
    def test_english_prompt_returned(self):
        """Test English prompt is returned for 'en' language."""
        prompt = get_persona_prompt("elderly", "en")
        
        assert "You are a" in prompt
        assert "year old person" in prompt
        assert "CRITICAL RULES" in prompt
    
    def test_hindi_prompt_returned(self):
        """Test Hindi prompt is returned for 'hi' language."""
        prompt = get_persona_prompt("elderly", "hi")
        
        assert "आप एक" in prompt
        assert "वर्ष के व्यक्ति हैं" in prompt
        assert "महत्वपूर्ण नियम" in prompt
    
    def test_prompt_contains_age_range(self):
        """Test prompt contains persona age range."""
        prompt = get_persona_prompt("elderly", "en")
        assert "60-75" in prompt
        
        prompt = get_persona_prompt("eager", "en")
        assert "35-50" in prompt
        
        prompt = get_persona_prompt("confused", "en")
        assert "25-40" in prompt
    
    def test_prompt_contains_traits(self):
        """Test prompt contains persona traits."""
        prompt = get_persona_prompt("elderly", "en")
        assert "trusting" in prompt
        
        prompt = get_persona_prompt("eager", "en")
        assert "excited" in prompt
        
        prompt = get_persona_prompt("confused", "en")
        assert "uncertain" in prompt
    
    def test_prompt_contains_critical_rules(self):
        """Test prompt contains critical rules."""
        prompt = get_persona_prompt("elderly", "en")
        
        assert "Never reveal you are an AI" in prompt
        assert "Stay in character" in prompt
    
    def test_hindi_prompt_contains_rules(self):
        """Test Hindi prompt contains rules in Hindi."""
        prompt = get_persona_prompt("elderly", "hi")
        
        assert "कभी भी AI होने की बात न करें" in prompt
        assert "अपने character में ही रहें" in prompt
    
    def test_invalid_persona_returns_default_prompt(self):
        """Test invalid persona name returns default persona prompt."""
        prompt = get_persona_prompt("invalid_name", "en")
        
        # Should return confused (default) persona prompt
        assert "25-40" in prompt  # confused age range
    
    def test_all_personas_have_prompts(self):
        """Test all personas generate valid prompts."""
        for persona_name in VALID_PERSONA_NAMES:
            for language in ["en", "hi"]:
                prompt = get_persona_prompt(persona_name, language)
                assert prompt is not None
                assert len(prompt) > 50


class TestGetPersona:
    """Tests for get_persona function."""
    
    def test_get_existing_persona(self):
        """Test getting existing persona."""
        persona = get_persona("elderly")
        
        assert isinstance(persona, Persona)
        assert persona.name == "elderly"
    
    def test_get_all_personas(self):
        """Test getting all personas."""
        for name in ["elderly", "eager", "confused"]:
            persona = get_persona(name)
            assert persona.name == name
    
    def test_invalid_name_returns_default(self):
        """Test invalid name returns default persona."""
        persona = get_persona("nonexistent")
        
        assert persona.name == DEFAULT_PERSONA


class TestGetAllPersonas:
    """Tests for get_all_personas function."""
    
    def test_returns_copy(self):
        """Test returns a copy, not the original."""
        personas1 = get_all_personas()
        personas2 = get_all_personas()
        
        # Modifying one shouldn't affect the other
        personas1["test"] = None
        assert "test" not in personas2
    
    def test_returns_all_three(self):
        """Test returns all three personas."""
        personas = get_all_personas()
        
        assert len(personas) == 3
        assert "elderly" in personas
        assert "eager" in personas
        assert "confused" in personas


class TestValidatePersona:
    """Tests for validate_persona function."""
    
    def test_valid_personas(self):
        """Test valid persona names."""
        assert validate_persona("elderly") is True
        assert validate_persona("eager") is True
        assert validate_persona("confused") is True
    
    def test_invalid_personas(self):
        """Test invalid persona names."""
        assert validate_persona("invalid") is False
        assert validate_persona("") is False
        assert validate_persona("ELDERLY") is False  # Case sensitive


class TestGetPersonaForScamTypes:
    """Tests for get_persona_for_scam_types function."""
    
    def test_single_scam_type(self):
        """Test with single scam type."""
        result = get_persona_for_scam_types(["lottery"])
        assert result == "eager"
    
    def test_multiple_same_persona(self):
        """Test multiple scam types mapping to same persona."""
        result = get_persona_for_scam_types(["lottery", "prize", "winner"])
        assert result == "eager"
    
    def test_mixed_scam_types_majority_wins(self):
        """Test mixed types returns majority persona."""
        # 2 eager, 1 elderly -> eager wins
        result = get_persona_for_scam_types(["lottery", "prize", "police"])
        assert result == "eager"
    
    def test_empty_list_returns_default(self):
        """Test empty list returns default persona."""
        result = get_persona_for_scam_types([])
        assert result == DEFAULT_PERSONA


class TestGetPersonaCharacteristics:
    """Tests for get_persona_characteristics function."""
    
    def test_returns_dict(self):
        """Test returns dictionary."""
        result = get_persona_characteristics("elderly")
        assert isinstance(result, dict)
    
    def test_contains_all_fields(self):
        """Test contains all expected fields."""
        result = get_persona_characteristics("elderly")
        
        assert "name" in result
        assert "age_range" in result
        assert "tech_literacy" in result
        assert "traits" in result
        assert "response_style" in result
        assert "suitable_scam_types" in result
    
    def test_traits_is_copy(self):
        """Test traits is a copy, not original."""
        result = get_persona_characteristics("elderly")
        original_persona = PERSONAS["elderly"]
        
        result["traits"].append("new_trait")
        assert "new_trait" not in original_persona.traits


class TestGetSampleResponse:
    """Tests for get_sample_response function."""
    
    def test_english_sample_response(self):
        """Test English sample response."""
        response = get_sample_response("elderly", "en")
        
        assert response is not None
        assert len(response) > 10
        # Should not contain Hindi characters
        assert "अ" not in response
    
    def test_hindi_sample_response(self):
        """Test Hindi sample response."""
        response = get_sample_response("elderly", "hi")
        
        assert response is not None
        assert len(response) > 10
        # Should contain Hindi characters
        assert any(ord(c) > 0x0900 and ord(c) < 0x097F for c in response)
    
    def test_all_personas_have_samples(self):
        """Test all personas have sample responses."""
        for persona in VALID_PERSONA_NAMES:
            for lang in ["en", "hi"]:
                response = get_sample_response(persona, lang)
                assert response is not None
                assert len(response) > 0
    
    def test_invalid_persona_returns_default_sample(self):
        """Test invalid persona returns default persona sample."""
        response = get_sample_response("invalid", "en")
        default_response = get_sample_response(DEFAULT_PERSONA, "en")
        
        assert response == default_response


class TestPersonaConsistency:
    """Tests for persona consistency requirements (AC-2.1.3)."""
    
    def test_persona_selection_deterministic(self):
        """Test persona selection is deterministic for same input."""
        scam_type = "lottery"
        language = "en"
        
        results = [select_persona(scam_type, language) for _ in range(100)]
        
        # All results should be identical
        assert len(set(results)) == 1
    
    def test_scam_persona_mapping_completeness(self):
        """Test SCAM_PERSONA_MAPPING covers common scam types."""
        required_scam_types = [
            "lottery", "prize", "police", "arrest", "bank",
            "kyc", "phishing", "courier", "investment"
        ]
        
        for scam_type in required_scam_types:
            assert scam_type in SCAM_PERSONA_MAPPING, f"{scam_type} missing from mapping"
    
    def test_mapping_values_are_valid_personas(self):
        """Test all mapping values are valid persona names."""
        for scam_type, persona_name in SCAM_PERSONA_MAPPING.items():
            assert persona_name in VALID_PERSONA_NAMES, f"Invalid persona {persona_name} for {scam_type}"


class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_whitespace_scam_type(self):
        """Test whitespace in scam type is handled."""
        result = select_persona("  lottery  ", "en")
        assert result == "eager"
    
    def test_special_characters_in_scam_type(self):
        """Test special characters in scam type."""
        result = select_persona("lottery!", "en")
        assert result == "eager"  # Should still match
    
    def test_very_long_scam_type(self):
        """Test very long scam type."""
        long_type = "a" * 1000
        result = select_persona(long_type, "en")
        assert result == DEFAULT_PERSONA
    
    def test_unicode_in_scam_type(self):
        """Test Unicode characters in scam type."""
        result = select_persona("lottery_लॉटरी", "en")
        assert result == "eager"


class TestVerificationFromTasksSpec:
    """
    Verification tests as specified in TASKS.md.
    
    These are the exact test cases from the task specification.
    """
    
    def test_persona_selection_lottery(self):
        """Test: assert select_persona('lottery', 'en') == 'eager'"""
        assert select_persona("lottery", "en") == "eager"
    
    def test_persona_selection_police_threat(self):
        """Test: assert select_persona('police_threat', 'en') == 'elderly'"""
        assert select_persona("police_threat", "en") == "elderly"
    
    def test_persona_selection_bank_fraud(self):
        """Test: assert select_persona('bank_fraud', 'en') == 'confused'"""
        assert select_persona("bank_fraud", "en") == "confused"
    
    def test_elderly_persona_characteristics(self):
        """Verify elderly persona has correct characteristics."""
        persona = PERSONAS["elderly"]
        
        assert persona.age_range == "60-75"
        assert persona.tech_literacy == "low"
        assert "trusting" in persona.traits
        assert "polite" in persona.traits
        assert "confused by technology" in persona.traits
    
    def test_eager_persona_characteristics(self):
        """Verify eager persona has correct characteristics."""
        persona = PERSONAS["eager"]
        
        assert persona.age_range == "35-50"
        assert persona.tech_literacy == "medium"
        assert "excited" in persona.traits
        assert "compliant" in persona.traits
    
    def test_confused_persona_characteristics(self):
        """Verify confused persona has correct characteristics."""
        persona = PERSONAS["confused"]
        
        assert persona.age_range == "25-40"
        assert persona.tech_literacy == "medium"
        assert "uncertain" in persona.traits
        assert "cautious" in persona.traits


class TestAcceptanceCriteria:
    """
    Tests for Task 5.1 Acceptance Criteria.
    
    AC-2.1.1: Persona selection aligns with scam type
    AC-2.1.2: Responses match persona characteristics
    AC-2.1.3: No persona switching mid-conversation
    """
    
    def test_ac_2_1_1_persona_alignment(self):
        """AC-2.1.1: Persona selection aligns with scam type on 50+ scenarios."""
        test_cases = [
            # Lottery/Prize -> eager (15 cases)
            ("lottery", "eager"),
            ("prize", "eager"),
            ("winner", "eager"),
            ("jackpot", "eager"),
            ("lucky_draw", "eager"),
            ("contest", "eager"),
            ("gift", "eager"),
            ("reward", "eager"),
            ("lottery_scam", "eager"),
            ("prize_winner", "eager"),
            ("big_prize", "eager"),
            ("lucky_winner", "eager"),
            ("free_gift", "eager"),
            ("cash_prize", "eager"),
            ("instant_winner", "eager"),
            
            # Police/Threat -> elderly (15 cases)
            ("police", "elderly"),
            ("police_threat", "elderly"),
            ("arrest", "elderly"),
            ("court", "elderly"),
            ("government", "elderly"),
            ("tax", "elderly"),
            ("investigation", "elderly"),
            ("warrant", "elderly"),
            ("legal", "elderly"),
            ("cbi", "elderly"),
            ("enforcement_directorate", "elderly"),
            ("police_case", "elderly"),
            ("arrest_warrant", "elderly"),
            ("court_order", "elderly"),
            ("tax_investigation", "elderly"),
            
            # Bank/KYC -> confused (15 cases)
            ("bank_fraud", "confused"),
            ("bank", "confused"),
            ("kyc", "confused"),
            ("verification", "confused"),
            ("account", "confused"),
            ("credit_card", "confused"),
            ("loan", "confused"),
            ("insurance", "confused"),
            ("phishing", "confused"),
            ("link", "confused"),
            ("website", "confused"),
            ("password", "confused"),
            ("bank_account", "confused"),
            ("kyc_update", "confused"),
            ("account_blocked", "confused"),
            
            # Courier/Investment -> eager (10 cases)
            ("courier", "eager"),
            ("delivery", "eager"),
            ("parcel", "eager"),
            ("customs", "eager"),
            ("investment", "eager"),
            ("crypto", "eager"),
            ("trading", "eager"),
            ("stock", "eager"),
            ("courier_fraud", "eager"),
            ("parcel_stuck", "eager"),
        ]
        
        assert len(test_cases) >= 50, f"Only {len(test_cases)} test cases, need 50+"
        
        for scam_type, expected_persona in test_cases:
            result = select_persona(scam_type, "en")
            assert result == expected_persona, f"Failed for {scam_type}: expected {expected_persona}, got {result}"
    
    def test_ac_2_1_2_response_characteristics(self):
        """AC-2.1.2: Responses match persona characteristics."""
        # Test that prompts include persona-specific characteristics
        
        # Elderly: should mention confusion, basic questions
        elderly_prompt = get_persona_prompt("elderly", "en")
        assert "confused by technology" in elderly_prompt
        assert "basic questions" in elderly_prompt or "asks basic" in elderly_prompt
        
        # Eager: should mention enthusiasm
        eager_prompt = get_persona_prompt("eager", "en")
        assert "excited" in eager_prompt or "enthusiastic" in eager_prompt
        
        # Confused: should mention skepticism, verification
        confused_prompt = get_persona_prompt("confused", "en")
        assert "uncertain" in confused_prompt or "skeptical" in confused_prompt
    
    def test_ac_2_1_3_no_persona_switching(self):
        """AC-2.1.3: Persona selection is consistent for same input."""
        # Run selection multiple times
        scam_types = ["lottery", "police", "bank_fraud", "courier", "unknown"]
        
        for scam_type in scam_types:
            first_result = select_persona(scam_type, "en")
            
            # Call 50 more times
            for _ in range(50):
                result = select_persona(scam_type, "en")
                assert result == first_result, f"Persona switched for {scam_type}"

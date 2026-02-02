"""
Unit Tests for Engagement Strategies Module.

Tests strategy selection and configuration.
"""

import pytest

from app.agent.strategies import (
    EngagementStrategy,
    STRATEGIES,
    get_strategy,
    get_strategy_details,
    get_example_response,
    should_terminate,
)


class TestEngagementStrategyDataclass:
    """Tests for EngagementStrategy dataclass."""
    
    def test_strategy_creation(self):
        """Test strategy can be created."""
        strategy = EngagementStrategy(
            name="test_strategy",
            turn_range=(1, 10),
            goals=["Goal 1", "Goal 2"],
            techniques=["Technique 1"],
            example_responses=["Response 1"],
        )
        
        assert strategy.name == "test_strategy"
        assert strategy.turn_range == (1, 10)
        assert len(strategy.goals) == 2
    
    def test_strategy_attributes(self):
        """Test strategy has all required attributes."""
        strategy = EngagementStrategy(
            name="test",
            turn_range=(1, 5),
            goals=[],
            techniques=[],
            example_responses=[],
        )
        
        assert hasattr(strategy, "name")
        assert hasattr(strategy, "turn_range")
        assert hasattr(strategy, "goals")
        assert hasattr(strategy, "techniques")
        assert hasattr(strategy, "example_responses")


class TestStrategiesDict:
    """Tests for STRATEGIES dictionary."""
    
    def test_strategies_defined(self):
        """Test strategies dictionary is defined."""
        assert STRATEGIES is not None
        assert isinstance(STRATEGIES, dict)
    
    def test_build_trust_exists(self):
        """Test build_trust strategy exists."""
        assert "build_trust" in STRATEGIES
    
    def test_express_confusion_exists(self):
        """Test express_confusion strategy exists."""
        assert "express_confusion" in STRATEGIES
    
    def test_probe_details_exists(self):
        """Test probe_details strategy exists."""
        assert "probe_details" in STRATEGIES
    
    def test_all_strategies_have_required_fields(self):
        """Test all strategies have required fields."""
        for name, strategy in STRATEGIES.items():
            assert strategy.name == name
            assert isinstance(strategy.turn_range, tuple)
            assert len(strategy.turn_range) == 2
            assert isinstance(strategy.goals, list)
            assert isinstance(strategy.techniques, list)
            assert isinstance(strategy.example_responses, list)
    
    def test_build_trust_turn_range(self):
        """Test build_trust has correct turn range."""
        assert STRATEGIES["build_trust"].turn_range == (1, 5)
    
    def test_express_confusion_turn_range(self):
        """Test express_confusion has correct turn range."""
        assert STRATEGIES["express_confusion"].turn_range == (6, 12)
    
    def test_probe_details_turn_range(self):
        """Test probe_details has correct turn range."""
        assert STRATEGIES["probe_details"].turn_range == (13, 20)


class TestGetStrategy:
    """Tests for get_strategy function."""
    
    def test_returns_string(self):
        """Test function returns a string."""
        result = get_strategy(1)
        
        assert isinstance(result, str)
    
    def test_turn_1_returns_build_trust(self):
        """Test turn 1 returns build_trust."""
        assert get_strategy(1) == "build_trust"
    
    def test_turn_5_returns_build_trust(self):
        """Test turn 5 returns build_trust."""
        assert get_strategy(5) == "build_trust"
    
    def test_turn_6_returns_express_confusion(self):
        """Test turn 6 returns express_confusion."""
        assert get_strategy(6) == "express_confusion"
    
    def test_turn_12_returns_express_confusion(self):
        """Test turn 12 returns express_confusion."""
        assert get_strategy(12) == "express_confusion"
    
    def test_turn_13_returns_probe_details(self):
        """Test turn 13 returns probe_details."""
        assert get_strategy(13) == "probe_details"
    
    def test_turn_20_returns_probe_details(self):
        """Test turn 20 returns probe_details."""
        assert get_strategy(20) == "probe_details"
    
    def test_turn_beyond_20_returns_probe_details(self):
        """Test turns beyond 20 still return probe_details."""
        assert get_strategy(25) == "probe_details"
        assert get_strategy(100) == "probe_details"


class TestGetStrategyDetails:
    """Tests for get_strategy_details function."""
    
    def test_returns_strategy_for_valid_name(self):
        """Test returns strategy for valid name."""
        result = get_strategy_details("build_trust")
        
        assert result is not None
        assert isinstance(result, EngagementStrategy)
    
    def test_returns_none_for_invalid_name(self):
        """Test returns None for invalid name."""
        result = get_strategy_details("invalid_strategy")
        
        assert result is None
    
    def test_returns_correct_strategy(self):
        """Test returns correct strategy object."""
        result = get_strategy_details("probe_details")
        
        assert result.name == "probe_details"
        assert result.turn_range == (13, 20)
    
    def test_all_strategies_retrievable(self):
        """Test all strategies can be retrieved."""
        for name in STRATEGIES.keys():
            result = get_strategy_details(name)
            assert result is not None
            assert result.name == name


class TestGetExampleResponse:
    """Tests for get_example_response function."""
    
    def test_returns_string(self):
        """Test function returns a string."""
        result = get_example_response("build_trust")
        
        assert isinstance(result, str)
    
    def test_returns_non_empty_for_valid_strategy(self):
        """Test returns non-empty string for valid strategy."""
        result = get_example_response("build_trust")
        
        assert len(result) > 0
    
    def test_returns_empty_for_invalid_strategy(self):
        """Test returns empty string for invalid strategy."""
        result = get_example_response("invalid")
        
        assert result == ""
    
    def test_returns_first_example(self):
        """Test returns the first example response."""
        result = get_example_response("build_trust")
        strategy = STRATEGIES["build_trust"]
        
        assert result == strategy.example_responses[0]
    
    def test_all_strategies_have_examples(self):
        """Test all strategies return an example."""
        for name in STRATEGIES.keys():
            result = get_example_response(name)
            assert len(result) > 0


class TestShouldTerminate:
    """Tests for should_terminate function."""
    
    def test_returns_boolean(self):
        """Test function returns a boolean."""
        result = should_terminate(1, 0.0)
        
        assert isinstance(result, bool)
    
    def test_terminates_at_turn_20(self):
        """Test terminates at turn 20."""
        assert should_terminate(20, 0.0) is True
    
    def test_terminates_after_turn_20(self):
        """Test terminates after turn 20."""
        assert should_terminate(21, 0.0) is True
        assert should_terminate(25, 0.0) is True
    
    def test_does_not_terminate_before_turn_20(self):
        """Test does not terminate before turn 20 with low confidence."""
        assert should_terminate(19, 0.0) is False
        assert should_terminate(10, 0.5) is False
    
    def test_terminates_at_high_confidence(self):
        """Test terminates at high extraction confidence."""
        assert should_terminate(5, 0.85) is True
        assert should_terminate(10, 0.9) is True
    
    def test_does_not_terminate_at_moderate_confidence(self):
        """Test does not terminate at moderate confidence."""
        assert should_terminate(5, 0.84) is False
        assert should_terminate(10, 0.80) is False
    
    def test_confidence_threshold_is_085(self):
        """Test confidence threshold is exactly 0.85."""
        assert should_terminate(5, 0.84) is False
        assert should_terminate(5, 0.85) is True
    
    def test_turn_limit_takes_precedence(self):
        """Test turn 20 terminates even with low confidence."""
        assert should_terminate(20, 0.1) is True


class TestStrategyProgression:
    """Integration tests for strategy progression."""
    
    def test_full_conversation_progression(self):
        """Test strategy progression through full conversation."""
        progression = []
        
        for turn in range(1, 21):
            strategy = get_strategy(turn)
            progression.append(strategy)
        
        # Check progression
        assert progression[0:5] == ["build_trust"] * 5
        assert progression[5:12] == ["express_confusion"] * 7
        assert progression[12:20] == ["probe_details"] * 8
    
    def test_strategy_changes_at_correct_turns(self):
        """Test strategy changes at the correct turn boundaries."""
        # Turn 5 -> 6 transition
        assert get_strategy(5) == "build_trust"
        assert get_strategy(6) == "express_confusion"
        
        # Turn 12 -> 13 transition
        assert get_strategy(12) == "express_confusion"
        assert get_strategy(13) == "probe_details"

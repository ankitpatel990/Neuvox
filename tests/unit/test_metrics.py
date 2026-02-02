"""
Unit Tests for Metrics Module.

Tests metric tracking functions for:
- Detection metrics
- Extraction metrics
- Response time tracking
- Error tracking
"""

import pytest
import time

from app.utils.metrics import (
    track_detection,
    track_extraction,
    track_response_time,
    track_error,
    update_active_sessions,
    timed,
    get_metrics_summary,
    reset_metrics,
)


@pytest.fixture(autouse=True)
def reset_metrics_before_each():
    """Reset metrics before each test."""
    reset_metrics()
    yield
    reset_metrics()


class TestTrackDetection:
    """Tests for track_detection function."""
    
    def test_increments_total(self):
        """Test detection total is incremented."""
        track_detection("en", True)
        summary = get_metrics_summary()
        
        assert summary["detection"]["total"] == 1
    
    def test_tracks_by_language(self):
        """Test detection is tracked by language."""
        track_detection("en", True)
        track_detection("hi", True)
        track_detection("en", False)
        
        summary = get_metrics_summary()
        
        assert summary["detection"]["by_language"]["en"] == 2
        assert summary["detection"]["by_language"]["hi"] == 1
    
    def test_tracks_by_result(self):
        """Test detection is tracked by result."""
        track_detection("en", True)
        track_detection("en", True)
        track_detection("en", False)
        
        summary = get_metrics_summary()
        
        assert summary["detection"]["by_result"]["scam"] == 2
        assert summary["detection"]["by_result"]["legitimate"] == 1
    
    def test_handles_hinglish(self):
        """Test handles hinglish language."""
        track_detection("hinglish", True)
        
        summary = get_metrics_summary()
        assert summary["detection"]["by_language"]["hinglish"] == 1


class TestTrackExtraction:
    """Tests for track_extraction function."""
    
    def test_increments_total(self):
        """Test extraction total is incremented."""
        track_extraction("upi_ids", 2)
        
        summary = get_metrics_summary()
        assert summary["extraction"]["total"] == 2
    
    def test_tracks_by_type(self):
        """Test extraction is tracked by type."""
        track_extraction("upi_ids", 3)
        track_extraction("phone_numbers", 2)
        track_extraction("bank_accounts", 1)
        
        summary = get_metrics_summary()
        
        assert summary["extraction"]["by_type"]["upi_ids"] == 3
        assert summary["extraction"]["by_type"]["phone_numbers"] == 2
        assert summary["extraction"]["by_type"]["bank_accounts"] == 1
    
    def test_accumulates_counts(self):
        """Test extraction counts accumulate."""
        track_extraction("upi_ids", 2)
        track_extraction("upi_ids", 3)
        
        summary = get_metrics_summary()
        assert summary["extraction"]["by_type"]["upi_ids"] == 5
    
    def test_default_count_is_one(self):
        """Test default count is 1."""
        track_extraction("ifsc_codes")
        
        summary = get_metrics_summary()
        assert summary["extraction"]["by_type"]["ifsc_codes"] == 1


class TestTrackResponseTime:
    """Tests for track_response_time function."""
    
    def test_records_single_time(self):
        """Test single response time is recorded."""
        track_response_time(0.5)
        
        summary = get_metrics_summary()
        assert summary["response_times"]["count"] == 1
        assert summary["response_times"]["avg_seconds"] == 0.5
    
    def test_calculates_average(self):
        """Test average is calculated correctly."""
        track_response_time(0.5)
        track_response_time(1.0)
        track_response_time(1.5)
        
        summary = get_metrics_summary()
        assert summary["response_times"]["count"] == 3
        assert summary["response_times"]["avg_seconds"] == 1.0
    
    def test_tracks_maximum(self):
        """Test maximum is tracked."""
        track_response_time(0.5)
        track_response_time(2.0)
        track_response_time(1.0)
        
        summary = get_metrics_summary()
        assert summary["response_times"]["max_seconds"] == 2.0


class TestTrackError:
    """Tests for track_error function."""
    
    def test_increments_total(self):
        """Test error total is incremented."""
        track_error("validation")
        
        summary = get_metrics_summary()
        assert summary["errors"]["total"] == 1
    
    def test_tracks_by_type(self):
        """Test errors are tracked by type."""
        track_error("validation")
        track_error("validation")
        track_error("processing")
        
        summary = get_metrics_summary()
        
        assert summary["errors"]["by_type"]["validation"] == 2
        assert summary["errors"]["by_type"]["processing"] == 1


class TestUpdateActiveSessions:
    """Tests for update_active_sessions function."""
    
    def test_increments_sessions(self):
        """Test session count is incremented."""
        update_active_sessions(1)
        
        summary = get_metrics_summary()
        assert summary["active_sessions"] == 1
    
    def test_decrements_sessions(self):
        """Test session count is decremented."""
        update_active_sessions(1)
        update_active_sessions(1)
        update_active_sessions(-1)
        
        summary = get_metrics_summary()
        assert summary["active_sessions"] == 1
    
    def test_handles_multiple_changes(self):
        """Test multiple session changes."""
        update_active_sessions(5)
        update_active_sessions(-2)
        update_active_sessions(3)
        
        summary = get_metrics_summary()
        assert summary["active_sessions"] == 6


class TestTimedDecorator:
    """Tests for timed decorator."""
    
    def test_tracks_function_time(self):
        """Test decorator tracks function execution time."""
        @timed
        def slow_function():
            time.sleep(0.1)
            return "done"
        
        result = slow_function()
        
        assert result == "done"
        summary = get_metrics_summary()
        assert summary["response_times"]["count"] == 1
        assert summary["response_times"]["avg_seconds"] >= 0.1
    
    def test_tracks_on_exception(self):
        """Test time is tracked even on exception."""
        @timed
        def failing_function():
            time.sleep(0.05)
            raise ValueError("test error")
        
        with pytest.raises(ValueError):
            failing_function()
        
        summary = get_metrics_summary()
        assert summary["response_times"]["count"] == 1
    
    def test_preserves_return_value(self):
        """Test decorator preserves return value."""
        @timed
        def add(a, b):
            return a + b
        
        assert add(2, 3) == 5


class TestGetMetricsSummary:
    """Tests for get_metrics_summary function."""
    
    def test_returns_dict(self):
        """Test returns dictionary."""
        summary = get_metrics_summary()
        
        assert isinstance(summary, dict)
    
    def test_contains_all_sections(self):
        """Test contains all metric sections."""
        summary = get_metrics_summary()
        
        assert "detection" in summary
        assert "extraction" in summary
        assert "response_times" in summary
        assert "errors" in summary
        assert "active_sessions" in summary
    
    def test_empty_metrics(self):
        """Test handles empty metrics."""
        summary = get_metrics_summary()
        
        assert summary["detection"]["total"] == 0
        assert summary["extraction"]["total"] == 0
        assert summary["response_times"]["count"] == 0
        assert summary["response_times"]["avg_seconds"] == 0
        assert summary["errors"]["total"] == 0
        assert summary["active_sessions"] == 0


class TestResetMetrics:
    """Tests for reset_metrics function."""
    
    def test_resets_all_metrics(self):
        """Test all metrics are reset."""
        # Add some data
        track_detection("en", True)
        track_extraction("upi_ids", 5)
        track_response_time(1.0)
        track_error("test")
        update_active_sessions(3)
        
        # Reset
        reset_metrics()
        
        # Verify reset
        summary = get_metrics_summary()
        assert summary["detection"]["total"] == 0
        assert summary["extraction"]["total"] == 0
        assert summary["response_times"]["count"] == 0
        assert summary["errors"]["total"] == 0
        assert summary["active_sessions"] == 0

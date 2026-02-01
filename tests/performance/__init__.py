"""
Performance and load tests for ScamShield AI.

This module provides:
- LoadTestResult: Dataclass for storing load test results
- LoadTester: Utility class for running load tests
- print_load_test_report: Function to print formatted test reports

Implements Task 9.2: Performance & Load Testing

Acceptance Criteria:
- QR-1: Response time <2s (p95)
- QR-1: Throughput >100 req/min
- QR-2: Error rate <1%
"""

from tests.performance.test_load import (
    LoadTestResult,
    LoadTester,
    print_load_test_report,
)

__all__ = [
    "LoadTestResult",
    "LoadTester",
    "print_load_test_report",
]

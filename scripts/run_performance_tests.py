#!/usr/bin/env python
"""
Performance Test Runner Script.

Implements Task 9.2: Performance & Load Testing

This script provides a command-line interface for running performance tests
against the ScamShield AI API.

Usage:
    # Run against local TestClient (no server needed)
    python scripts/run_performance_tests.py --mode pytest
    
    # Run against live server
    python scripts/run_performance_tests.py --mode live --url http://localhost:8000
    
    # Run full 5-minute load test
    python scripts/run_performance_tests.py --mode live --url http://localhost:8000 --duration 5

Acceptance Criteria:
- QR-1: Response time <2s (p95)
- QR-1: Throughput >100 req/min
- QR-2: Error rate <1%
"""

import argparse
import sys
import os
import time
from typing import List, Dict, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_pytest_tests(verbose: bool = True) -> int:
    """
    Run performance tests using pytest.
    
    Args:
        verbose: Whether to show verbose output
        
    Returns:
        Exit code (0 for success)
    """
    import subprocess
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/performance/test_load.py",
        "-v" if verbose else "-q",
        "--tb=short",
        "-s",  # Show print statements
    ]
    
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    return result.returncode


def run_live_load_test(
    base_url: str = "http://localhost:8000",
    duration_minutes: float = 1.0,
    requests_per_minute: int = 100,
) -> int:
    """
    Run load test against a live server.
    
    Args:
        base_url: Server URL
        duration_minutes: Test duration in minutes
        requests_per_minute: Target request rate
        
    Returns:
        Exit code (0 if all criteria pass)
    """
    import requests as http_requests
    
    print(f"\n{'='*70}")
    print(f" SCAMSHIELD AI - LIVE PERFORMANCE TEST")
    print(f"{'='*70}")
    print(f"\n[CONFIG] Configuration:")
    print(f"   Target URL:      {base_url}")
    print(f"   Duration:        {duration_minutes} minute(s)")
    print(f"   Target Rate:     {requests_per_minute} req/min")
    
    # First check if server is reachable
    print(f"\n[CHECK] Checking server health...")
    try:
        health_response = http_requests.get(
            f"{base_url}/api/v1/health",
            timeout=10,
        )
        if health_response.status_code == 200:
            health_data = health_response.json()
            print(f"   Server Status: {health_data.get('status', 'unknown')}")
            print(f"   Version: {health_data.get('version', 'unknown')}")
        else:
            print(f"   [WARN] Health check returned: {health_response.status_code}")
    except Exception as e:
        print(f"   [ERROR] Cannot reach server: {e}")
        print(f"\n   Please ensure the server is running at {base_url}")
        return 1
    
    # Test messages with variety
    test_messages = [
        {"message": "You won 10 lakh rupees! Send OTP now!", "language": "auto"},
        {"message": "Your bank account blocked. Call immediately!", "language": "en"},
        {"message": "आप जीत गए हैं 10 लाख! OTP भेजें।", "language": "hi"},
        {"message": "Pay ₹5000 to scammer@paytm immediately!", "language": "auto"},
        {"message": "Hello, how are you today?", "language": "en"},
        {"message": "Police warning: Pay fine or face arrest!", "language": "en"},
        {"message": "Your package stuck. Pay ₹500 clearance.", "language": "auto"},
    ]
    
    # Results tracking
    latencies: List[float] = []
    status_codes: Dict[int, int] = {}
    errors: List[str] = []
    total = 0
    success = 0
    
    # Calculate timing
    duration_seconds = duration_minutes * 60
    interval = 60.0 / requests_per_minute
    
    print(f"\n[START] Starting load test...")
    print(f"   Interval between requests: {interval:.3f}s")
    
    start_time = time.time()
    end_time = start_time + duration_seconds
    last_progress = 0
    
    while time.time() < end_time:
        request_start = time.time()
        
        try:
            msg = test_messages[total % len(test_messages)]
            response = http_requests.post(
                f"{base_url}/api/v1/honeypot/engage",
                json=msg,
                timeout=15,
            )
            
            latency = time.time() - request_start
            latencies.append(latency)
            
            code = response.status_code
            status_codes[code] = status_codes.get(code, 0) + 1
            
            if code == 200:
                success += 1
            else:
                errors.append(f"HTTP {code}: {response.text[:100]}")
                
        except Exception as e:
            errors.append(str(e)[:100])
            status_codes[0] = status_codes.get(0, 0) + 1
        
        total += 1
        
        # Progress update every 10 requests or 10 seconds
        elapsed = time.time() - start_time
        if total - last_progress >= 10 or elapsed - last_progress * 0.1 > 10:
            current_rate = total / elapsed * 60 if elapsed > 0 else 0
            percent = (elapsed / duration_seconds) * 100
            print(f"   [{percent:5.1f}%] Requests: {total:4d} | "
                  f"Rate: {current_rate:6.1f}/min | "
                  f"Success: {success}/{total}")
            last_progress = total
        
        # Wait to maintain rate
        elapsed_request = time.time() - request_start
        if elapsed_request < interval:
            time.sleep(interval - elapsed_request)
    
    actual_duration = time.time() - start_time
    
    # Calculate metrics
    if latencies:
        sorted_latencies = sorted(latencies)
        p50_idx = len(sorted_latencies) // 2
        p95_idx = min(int(len(sorted_latencies) * 0.95), len(sorted_latencies) - 1)
        p99_idx = min(int(len(sorted_latencies) * 0.99), len(sorted_latencies) - 1)
        
        min_lat = min(latencies)
        max_lat = max(latencies)
        avg_lat = sum(latencies) / len(latencies)
        p50 = sorted_latencies[p50_idx]
        p95 = sorted_latencies[p95_idx]
        p99 = sorted_latencies[p99_idx]
    else:
        min_lat = max_lat = avg_lat = p50 = p95 = p99 = 0
    
    failed = total - success
    error_rate = (failed / total * 100) if total > 0 else 0
    throughput = (total / actual_duration * 60) if actual_duration > 0 else 0
    
    # Print results
    print(f"\n{'='*70}")
    print(f" TEST RESULTS")
    print(f"{'='*70}")
    
    print(f"\n[STATS] Request Statistics:")
    print(f"   Total Requests:     {total}")
    print(f"   Successful:         {success}")
    print(f"   Failed:             {failed}")
    print(f"   Success Rate:       {(success/total*100) if total > 0 else 0:.2f}%")
    print(f"   Error Rate:         {error_rate:.2f}%")
    
    print(f"\n[TIME] Latency Metrics (seconds):")
    print(f"   Min:                {min_lat:.3f}s")
    print(f"   Avg:                {avg_lat:.3f}s")
    print(f"   P50 (Median):       {p50:.3f}s")
    print(f"   P95:                {p95:.3f}s")
    print(f"   P99:                {p99:.3f}s")
    print(f"   Max:                {max_lat:.3f}s")
    
    print(f"\n[PERF] Throughput:")
    print(f"   Actual Duration:    {actual_duration:.2f}s")
    print(f"   Requests/minute:    {throughput:.1f}")
    
    print(f"\n[HTTP] Status Code Distribution:")
    for code, count in sorted(status_codes.items()):
        pct = (count / total * 100) if total > 0 else 0
        code_str = str(code) if code > 0 else "Timeout/Error"
        print(f"   {code_str}: {count} ({pct:.1f}%)")
    
    if errors and len(errors) <= 5:
        print(f"\n[ERROR] Sample Errors (first 5):")
        for error in errors[:5]:
            print(f"   - {error}")
    
    # Acceptance criteria check
    print(f"\n{'='*70}")
    print(f" ACCEPTANCE CRITERIA (Task 9.2)")
    print(f"{'='*70}")
    
    p95_pass = p95 < 2.0
    throughput_pass = throughput >= 100
    error_pass = error_rate < 1.0
    
    print(f"\n   QR-1: Response time <2s (p95)")
    print(f"         Result: {p95:.3f}s")
    print(f"         Status: {'[PASS]' if p95_pass else '[FAIL]'}")
    
    print(f"\n   QR-1: Throughput >100 req/min")
    print(f"         Result: {throughput:.1f} req/min")
    print(f"         Status: {'[PASS]' if throughput_pass else '[FAIL]'}")
    
    print(f"\n   QR-2: Error rate <1%")
    print(f"         Result: {error_rate:.2f}%")
    print(f"         Status: {'[PASS]' if error_pass else '[FAIL]'}")
    
    print(f"\n{'='*70}")
    
    all_pass = p95_pass and throughput_pass and error_pass
    if all_pass:
        print(f" [OK] ALL ACCEPTANCE CRITERIA PASSED!")
    else:
        print(f" [WARN] SOME ACCEPTANCE CRITERIA NEED ATTENTION")
        if not p95_pass:
            print(f"    - Response time P95 exceeds 2s target")
        if not throughput_pass:
            print(f"    - Throughput below 100 req/min target")
        if not error_pass:
            print(f"    - Error rate exceeds 1% target")
    
    print(f"{'='*70}\n")
    
    return 0 if all_pass else 1


def main():
    """Main entry point for the performance test runner."""
    parser = argparse.ArgumentParser(
        description="ScamShield AI Performance Test Runner (Task 9.2)"
    )
    parser.add_argument(
        "--mode",
        choices=["pytest", "live"],
        default="pytest",
        help="Test mode: pytest (TestClient) or live (HTTP requests)"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Server URL for live mode (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--duration",
        type=float,
        default=1.0,
        help="Test duration in minutes for live mode (default: 1.0)"
    )
    parser.add_argument(
        "--rate",
        type=int,
        default=100,
        help="Requests per minute for live mode (default: 100)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print(" ScamShield AI Performance Test Runner")
    print(" Task 9.2: Performance & Load Testing")
    print("="*70)
    
    if args.mode == "pytest":
        print("\n[RUN] Running pytest-based performance tests...")
        exit_code = run_pytest_tests(verbose=args.verbose)
    else:
        print("\n[RUN] Running live server load test...")
        exit_code = run_live_load_test(
            base_url=args.url,
            duration_minutes=args.duration,
            requests_per_minute=args.rate,
        )
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()

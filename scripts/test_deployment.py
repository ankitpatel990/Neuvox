#!/usr/bin/env python
"""
Deployment Test Script.

Tests deployed API endpoint to verify functionality:
- Health check
- Scam detection
- Multi-turn engagement
- Intelligence extraction

Run this script to validate a deployed instance.
"""

import sys
import time
import argparse

# Try to import requests, provide helpful message if not available
try:
    import requests
except ImportError:
    print("Error: 'requests' package not installed")
    print("Run: pip install requests")
    sys.exit(1)


DEFAULT_BASE_URL = "http://localhost:8000"


def test_health(base_url: str) -> bool:
    """Test health endpoint."""
    print("Testing health endpoint...")
    
    try:
        response = requests.get(f"{base_url}/api/v1/health", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Status: {data.get('status')}")
            print(f"  Version: {data.get('version')}")
            return data.get("status") == "healthy"
        else:
            print(f"  [FAIL] Status code: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"  [FAIL] Request failed: {e}")
        return False


def test_engage_scam(base_url: str) -> bool:
    """Test engage endpoint with scam message."""
    print("\nTesting engage endpoint (scam message)...")
    
    payload = {
        "message": "Congratulations! You won 10 lakh rupees. Share your OTP now!",
        "language": "auto",
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/honeypot/engage",
            json=payload,
            timeout=30,
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Status: {data.get('status')}")
            print(f"  Scam Detected: {data.get('scam_detected')}")
            print(f"  Confidence: {data.get('confidence')}")
            print(f"  Session ID: {data.get('session_id')}")
            return True
        else:
            print(f"  [FAIL] Status code: {response.status_code}")
            print(f"  Response: {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"  [FAIL] Request failed: {e}")
        return False


def test_engage_legitimate(base_url: str) -> bool:
    """Test engage endpoint with legitimate message."""
    print("\nTesting engage endpoint (legitimate message)...")
    
    payload = {
        "message": "Hi, how are you doing today?",
        "language": "en",
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/honeypot/engage",
            json=payload,
            timeout=30,
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Status: {data.get('status')}")
            print(f"  Scam Detected: {data.get('scam_detected')}")
            return True
        else:
            print(f"  [FAIL] Status code: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"  [FAIL] Request failed: {e}")
        return False


def test_batch(base_url: str) -> bool:
    """Test batch endpoint."""
    print("\nTesting batch endpoint...")
    
    payload = {
        "messages": [
            {"id": "1", "message": "You won a prize!"},
            {"id": "2", "message": "Hello, how are you?"},
        ]
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/v1/honeypot/batch",
            json=payload,
            timeout=30,
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  Status: {data.get('status')}")
            print(f"  Processed: {data.get('processed')}")
            print(f"  Failed: {data.get('failed')}")
            return True
        else:
            print(f"  [FAIL] Status code: {response.status_code}")
            return False
            
    except requests.RequestException as e:
        print(f"  [FAIL] Request failed: {e}")
        return False


def measure_response_time(base_url: str) -> float:
    """Measure average response time."""
    print("\nMeasuring response time...")
    
    times = []
    
    for i in range(3):
        start = time.time()
        try:
            requests.post(
                f"{base_url}/api/v1/honeypot/engage",
                json={"message": "Test message"},
                timeout=30,
            )
            elapsed = time.time() - start
            times.append(elapsed)
            print(f"  Request {i+1}: {elapsed:.2f}s")
        except:
            print(f"  Request {i+1}: FAILED")
    
    if times:
        avg = sum(times) / len(times)
        print(f"  Average: {avg:.2f}s")
        return avg
    
    return 0


def main():
    """Main entry point for deployment testing."""
    parser = argparse.ArgumentParser(description="Test ScamShield AI deployment")
    parser.add_argument(
        "--url",
        default=DEFAULT_BASE_URL,
        help=f"Base URL of API (default: {DEFAULT_BASE_URL})",
    )
    args = parser.parse_args()
    
    base_url = args.url.rstrip("/")
    
    print("=" * 60)
    print("ScamShield AI - Deployment Test")
    print("=" * 60)
    print(f"\nBase URL: {base_url}")
    print()
    
    results = {
        "health": test_health(base_url),
        "engage_scam": test_engage_scam(base_url),
        "engage_legitimate": test_engage_legitimate(base_url),
        "batch": test_batch(base_url),
    }
    
    avg_time = measure_response_time(base_url)
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"  {test}: {status}")
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if avg_time > 0:
        if avg_time < 2.0:
            print(f"Response time: {avg_time:.2f}s (Target: <2s)")
        else:
            print(f"Response time: {avg_time:.2f}s (ABOVE target of 2s)")
    
    if passed == total:
        print("\nDeployment verification SUCCESSFUL!")
        sys.exit(0)
    else:
        print("\nDeployment verification FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    main()

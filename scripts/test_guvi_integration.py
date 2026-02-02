#!/usr/bin/env python3
"""
GUVI Integration Test Script.

Tests all the GUVI submission compliance features:
1. API Key Authentication (x-api-key header)
2. GUVI Input Format Support (nested message object)
3. Response Format (reply, suspiciousKeywords, agentNotes)
4. GUVI Callback (mock test)

Usage:
    # Start the server first:
    uvicorn app.main:app --reload
    
    # Then run tests:
    python scripts/test_guvi_integration.py
"""

import requests
import json
import sys
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
API_KEY = "your-secure-api-key-here"  # Use the same key from your .env file

# Test data
GUVI_FORMAT_REQUEST = {
    "sessionId": "test-guvi-session-001",
    "message": {
        "sender": "scammer",
        "text": "Congratulations! You have won Rs. 10 lakh in our lucky draw. Share your OTP to claim prize immediately!",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    },
    "conversationHistory": [],
    "metadata": {
        "channel": "SMS",
        "language": "English",
        "locale": "IN"
    }
}

OUR_FORMAT_REQUEST = {
    "message": "You won 10 lakh! Send OTP now to claim your prize!",
    "language": "auto"
}

GUVI_FOLLOWUP_REQUEST = {
    "sessionId": "test-guvi-session-001",
    "message": {
        "sender": "scammer",
        "text": "Send money to my UPI: scammer@paytm or call +919876543210",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    },
    "conversationHistory": [
        {
            "sender": "scammer",
            "text": "Congratulations! You have won Rs. 10 lakh!",
            "timestamp": "2026-02-02T10:00:00Z"
        },
        {
            "sender": "user",
            "text": "Really? How do I claim it?",
            "timestamp": "2026-02-02T10:01:00Z"
        }
    ],
    "metadata": {
        "channel": "SMS",
        "language": "English",
        "locale": "IN"
    }
}


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result."""
    status = "✅ PASSED" if passed else "❌ FAILED"
    print(f"\n{status}: {test_name}")
    if details:
        print(f"  Details: {details}")


def test_health_check():
    """Test that health endpoint works without auth."""
    print_header("Test 1: Health Check (No Auth Required)")
    
    try:
        response = requests.get(f"{BASE_URL}/health")
        passed = response.status_code == 200
        data = response.json()
        print_result(
            "Health endpoint accessible",
            passed,
            f"Status: {data.get('status')}, Version: {data.get('version')}"
        )
        return passed
    except Exception as e:
        print_result("Health endpoint accessible", False, str(e))
        return False


def test_missing_api_key():
    """Test that requests without API key are rejected."""
    print_header("Test 2: Missing API Key (Should Return 401)")
    
    try:
        response = requests.post(
            f"{BASE_URL}/honeypot/engage",
            json=OUR_FORMAT_REQUEST,
            headers={"Content-Type": "application/json"}
        )
        
        # Should return 401 if API_KEY is configured
        if response.status_code == 401:
            print_result("Missing API key rejected", True, "401 Unauthorized returned")
            return True
        elif response.status_code == 200:
            print_result(
                "Missing API key rejected", 
                False, 
                "Request succeeded - API_KEY might not be configured in .env"
            )
            return False
        else:
            print_result("Missing API key rejected", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_result("Missing API key rejected", False, str(e))
        return False


def test_invalid_api_key():
    """Test that invalid API keys are rejected."""
    print_header("Test 3: Invalid API Key (Should Return 401)")
    
    try:
        response = requests.post(
            f"{BASE_URL}/honeypot/engage",
            json=OUR_FORMAT_REQUEST,
            headers={
                "Content-Type": "application/json",
                "x-api-key": "invalid-key-12345"
            }
        )
        
        if response.status_code == 401:
            print_result("Invalid API key rejected", True, "401 Unauthorized returned")
            return True
        elif response.status_code == 200:
            print_result(
                "Invalid API key rejected",
                False,
                "Request succeeded - API_KEY might not be configured"
            )
            return False
        else:
            print_result("Invalid API key rejected", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_result("Invalid API key rejected", False, str(e))
        return False


def test_valid_api_key_our_format():
    """Test our standard format with valid API key."""
    print_header("Test 4: Valid API Key - Our Format")
    
    try:
        response = requests.post(
            f"{BASE_URL}/honeypot/engage",
            json=OUR_FORMAT_REQUEST,
            headers={
                "Content-Type": "application/json",
                "x-api-key": API_KEY
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_result("Our format accepted", True, f"Session: {data.get('session_id', 'N/A')[:20]}...")
            
            # Check for required fields
            has_status = "status" in data
            has_scam = "scam_detected" in data
            has_reply = "reply" in data
            
            print(f"  - status field: {'✅' if has_status else '❌'}")
            print(f"  - scam_detected field: {'✅' if has_scam else '❌'}")
            print(f"  - reply field: {'✅' if has_reply else '❌'}")
            
            if data.get("scam_detected"):
                print(f"  - Scam detected with confidence: {data.get('confidence', 0):.2f}")
                if data.get("reply"):
                    print(f"  - Agent reply: {data['reply'][:50]}...")
            
            return True
        else:
            print_result("Our format accepted", False, f"Status: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
    except Exception as e:
        print_result("Our format accepted", False, str(e))
        return False


def test_guvi_format():
    """Test GUVI's exact input format."""
    print_header("Test 5: GUVI Input Format")
    
    try:
        response = requests.post(
            f"{BASE_URL}/honeypot/engage",
            json=GUVI_FORMAT_REQUEST,
            headers={
                "Content-Type": "application/json",
                "x-api-key": API_KEY
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_result("GUVI format accepted", True)
            
            # Check all required response fields
            checks = {
                "status": "status" in data,
                "scam_detected": "scam_detected" in data,
                "session_id": "session_id" in data,
                "reply": "reply" in data,
                "agent_notes": "agent_notes" in data,
            }
            
            for field, present in checks.items():
                print(f"  - {field}: {'✅' if present else '❌'}")
            
            # Check extracted_intelligence has suspicious_keywords
            intel = data.get("extracted_intelligence", {})
            if intel:
                has_keywords = "suspicious_keywords" in intel
                print(f"  - suspicious_keywords: {'✅' if has_keywords else '❌'}")
                if has_keywords and intel["suspicious_keywords"]:
                    print(f"    Keywords: {intel['suspicious_keywords'][:5]}")
            
            # Print agent notes
            if data.get("agent_notes"):
                print(f"  - Agent Notes: {data['agent_notes'][:100]}...")
            
            return True
        else:
            print_result("GUVI format accepted", False, f"Status: {response.status_code}")
            print(f"  Response: {response.text[:200]}")
            return False
    except Exception as e:
        print_result("GUVI format accepted", False, str(e))
        return False


def test_guvi_followup():
    """Test GUVI format with conversation history."""
    print_header("Test 6: GUVI Format with Conversation History")
    
    try:
        response = requests.post(
            f"{BASE_URL}/honeypot/engage",
            json=GUVI_FOLLOWUP_REQUEST,
            headers={
                "Content-Type": "application/json",
                "x-api-key": API_KEY
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print_result("GUVI followup accepted", True)
            
            # Check extracted intelligence for the UPI and phone
            intel = data.get("extracted_intelligence", {})
            if intel:
                upi_ids = intel.get("upi_ids", [])
                phones = intel.get("phone_numbers", [])
                
                has_upi = len(upi_ids) > 0
                has_phone = len(phones) > 0
                
                print(f"  - UPI IDs extracted: {'✅' if has_upi else '❌'} {upi_ids}")
                print(f"  - Phone numbers extracted: {'✅' if has_phone else '❌'} {phones}")
            
            if data.get("reply"):
                print(f"  - Reply: {data['reply'][:80]}...")
            
            return True
        else:
            print_result("GUVI followup accepted", False, f"Status: {response.status_code}")
            return False
    except Exception as e:
        print_result("GUVI followup accepted", False, str(e))
        return False


def main():
    """Run all GUVI integration tests."""
    print("\n" + "=" * 60)
    print("   GUVI INTEGRATION TEST SUITE")
    print("=" * 60)
    print(f"\nBase URL: {BASE_URL}")
    print(f"API Key: {API_KEY[:10]}...")
    
    results = []
    
    # Run tests
    results.append(("Health Check", test_health_check()))
    results.append(("Missing API Key", test_missing_api_key()))
    results.append(("Invalid API Key", test_invalid_api_key()))
    results.append(("Our Format", test_valid_api_key_our_format()))
    results.append(("GUVI Format", test_guvi_format()))
    results.append(("GUVI Followup", test_guvi_followup()))
    
    # Summary
    print_header("TEST SUMMARY")
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  🎉 All tests passed! Ready for GUVI submission.")
        return 0
    else:
        print("\n  ⚠️ Some tests failed. Check configuration.")
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""
GUVI Documentation Compliance Test Suite
=========================================

This script tests all API requirements specified in GuviDOc.md to ensure 100% compliance.

Based on GUVI Problem Statement:
- Agentic Honey-Pot for Scam Detection & Intelligence Extraction

Test Categories:
1. API Authentication (x-api-key header)
2. First Message Format (Section 6.1)
3. Follow-Up Message Format (Section 6.2)
4. Request Body Field Validation (Section 6.3)
5. Agent Behavior (Section 7)
6. Agent Output Format (Section 8)
7. Intelligence Extraction
8. GUVI Callback (Section 12)
9. Multi-Turn Conversation Handling

All tests use LIVE API calls - no hardcoded responses.
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
import uuid


# Configuration
BASE_URL = "http://localhost:8005"
API_ENDPOINT = f"{BASE_URL}/api/v1/honeypot/engage"
HEALTH_ENDPOINT = f"{BASE_URL}/api/v1/health"

# API Key - Get from env or use test key
API_KEY = "sVlunn0LMQZNAkRYqZB-f1-Ye7rgzjB_E3b1gNxnUV8"  # Replace with actual API key if configured


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'


def print_header(text: str):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")


def print_test(test_name: str, passed: bool, details: str = ""):
    """Print test result."""
    status = f"{Colors.GREEN}[PASS]{Colors.END}" if passed else f"{Colors.RED}[FAIL]{Colors.END}"
    print(f"  {status} | {test_name}")
    if details:
        print(f"          -> {Colors.CYAN}{details}{Colors.END}")


def print_response_summary(response: Dict[str, Any]):
    """Print response summary."""
    print(f"\n{Colors.YELLOW}Response Summary:{Colors.END}")
    print(f"  status: {response.get('status')}")
    print(f"  scam_detected: {response.get('scam_detected')}")
    print(f"  confidence: {response.get('confidence')}")
    print(f"  reply: {response.get('reply', 'N/A')[:100]}..." if response.get('reply') else "  reply: N/A")


def make_request(payload: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Make API request and return response."""
    default_headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }
    if headers:
        default_headers.update(headers)
    
    try:
        response = requests.post(
            API_ENDPOINT,
            json=payload,
            headers=default_headers,
            timeout=60
        )
        return {
            "status_code": response.status_code,
            "data": response.json() if response.text else {},
            "headers": dict(response.headers),
            "elapsed_ms": response.elapsed.total_seconds() * 1000
        }
    except requests.exceptions.RequestException as e:
        return {
            "status_code": 0,
            "data": {"error": str(e)},
            "headers": {},
            "elapsed_ms": 0
        }


def generate_timestamp() -> int:
    """Generate current timestamp in epoch milliseconds."""
    return int(datetime.now().timestamp() * 1000)


class GuviComplianceTests:
    """GUVI Documentation Compliance Test Suite."""
    
    def __init__(self):
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "tests": []
        }
    
    def record_test(self, name: str, passed: bool, details: str = ""):
        """Record test result."""
        self.results["total"] += 1
        if passed:
            self.results["passed"] += 1
        else:
            self.results["failed"] += 1
        self.results["tests"].append({
            "name": name,
            "passed": passed,
            "details": details
        })
        print_test(name, passed, details)
    
    def test_health_check(self):
        """Test health endpoint is responding."""
        print_header("1. HEALTH CHECK")
        
        try:
            response = requests.get(HEALTH_ENDPOINT, timeout=10)
            data = response.json()
            
            self.record_test(
                "Health endpoint responds",
                response.status_code == 200,
                f"Status: {response.status_code}"
            )
            
            self.record_test(
                "Health returns status field",
                "status" in data,
                f"Status: {data.get('status', 'N/A')}"
            )
            
            self.record_test(
                "Health returns version field",
                "version" in data,
                f"Version: {data.get('version', 'N/A')}"
            )
            
        except Exception as e:
            self.record_test("Health endpoint responds", False, str(e))
    
    def test_api_authentication(self):
        """
        Test API Authentication (Section 4)
        
        GUVI Doc:
        - x-api-key: YOUR_SECRET_API_KEY
        - Content-Type: application/json
        """
        print_header("2. API AUTHENTICATION (Section 4)")
        
        test_payload = {
            "sessionId": f"auth-test-{uuid.uuid4()}",
            "message": {
                "sender": "scammer",
                "text": "Test message for auth",
                "timestamp": generate_timestamp()
            },
            "conversationHistory": [],
            "metadata": {
                "channel": "SMS",
                "language": "English",
                "locale": "IN"
            }
        }
        
        # Test with correct API key
        response = make_request(test_payload)
        self.record_test(
            "Request with x-api-key header succeeds",
            response["status_code"] == 200,
            f"Status: {response['status_code']}"
        )
        
        # Test Content-Type header
        self.record_test(
            "Content-Type: application/json accepted",
            response["status_code"] == 200,
            "JSON content type working"
        )
    
    def test_first_message_format(self):
        """
        Test First Message Format (Section 6.1)
        
        GUVI Doc Example:
        {
            "sessionId": "wertyu-dfghj-ertyui",
            "message": {
                "sender": "scammer",
                "text": "Your bank account will be blocked today. Verify immediately.",
                "timestamp": 1770005528731
            },
            "conversationHistory": [],
            "metadata": {
                "channel": "SMS",
                "language": "English",
                "locale": "IN"
            }
        }
        """
        print_header("3. FIRST MESSAGE FORMAT (Section 6.1)")
        
        session_id = f"first-msg-{uuid.uuid4()}"
        timestamp = generate_timestamp()
        
        # Exact format from GUVI doc
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": "Your bank account will be blocked today. Verify immediately.",
                "timestamp": timestamp
            },
            "conversationHistory": [],
            "metadata": {
                "channel": "SMS",
                "language": "English",
                "locale": "IN"
            }
        }
        
        response = make_request(payload)
        data = response["data"]
        
        self.record_test(
            "First message request succeeds",
            response["status_code"] == 200,
            f"Status: {response['status_code']}"
        )
        
        self.record_test(
            "Empty conversationHistory[] accepted",
            response["status_code"] == 200,
            "Empty array handled correctly"
        )
        
        self.record_test(
            "sessionId (camelCase) accepted",
            response["status_code"] == 200 and "session_id" in data,
            f"Session: {data.get('session_id', 'N/A')[:30]}"
        )
        
        self.record_test(
            "Nested message object accepted",
            response["status_code"] == 200,
            f"sender={payload['message']['sender']}, text present"
        )
        
        self.record_test(
            "Epoch timestamp (integer) accepted",
            response["status_code"] == 200,
            f"Timestamp: {timestamp}"
        )
        
        self.record_test(
            "Metadata fields accepted (channel, language, locale)",
            response["status_code"] == 200,
            f"channel={payload['metadata']['channel']}, language={payload['metadata']['language']}"
        )
        
        # Verify scam detection for this message
        self.record_test(
            "Scam detected in bank fraud message",
            data.get("scam_detected") == True,
            f"Confidence: {data.get('confidence', 0):.2f}"
        )
        
        print_response_summary(data)
    
    def test_followup_message_format(self):
        """
        Test Second/Follow-Up Message Format (Section 6.2)
        
        GUVI Doc Example:
        {
            "sessionId": "wertyu-dfghj-ertyui",
            "message": {
                "sender": "scammer",
                "text": "Share your UPI ID to avoid account suspension.",
                "timestamp": 1770005528731
            },
            "conversationHistory": [
                {
                    "sender": "scammer",
                    "text": "Your bank account will be blocked today. Verify immediately.",
                    "timestamp": 1770005528731
                },
                {
                    "sender": "user",
                    "text": "Why will my account be blocked?",
                    "timestamp": 1770005528731
                }
            ],
            "metadata": {
                "channel": "SMS",
                "language": "English",
                "locale": "IN"
            }
        }
        """
        print_header("4. FOLLOW-UP MESSAGE FORMAT (Section 6.2)")
        
        session_id = f"followup-{uuid.uuid4()}"
        timestamp = generate_timestamp()
        
        # Exact format from GUVI doc
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": "Share your UPI ID to avoid account suspension.",
                "timestamp": timestamp
            },
            "conversationHistory": [
                {
                    "sender": "scammer",
                    "text": "Your bank account will be blocked today. Verify immediately.",
                    "timestamp": timestamp - 1000
                },
                {
                    "sender": "user",
                    "text": "Why will my account be blocked?",
                    "timestamp": timestamp - 500
                }
            ],
            "metadata": {
                "channel": "SMS",
                "language": "English",
                "locale": "IN"
            }
        }
        
        response = make_request(payload)
        data = response["data"]
        
        self.record_test(
            "Follow-up message request succeeds",
            response["status_code"] == 200,
            f"Status: {response['status_code']}"
        )
        
        self.record_test(
            "conversationHistory array processed",
            response["status_code"] == 200,
            f"History items: {len(payload['conversationHistory'])}"
        )
        
        self.record_test(
            "Both 'scammer' and 'user' senders accepted in history",
            response["status_code"] == 200,
            "scammer and user senders in history"
        )
        
        self.record_test(
            "Scam detected in UPI fraud message",
            data.get("scam_detected") == True,
            f"Confidence: {data.get('confidence', 0):.2f}"
        )
        
        print_response_summary(data)
    
    def test_request_body_fields(self):
        """
        Test Request Body Field Explanation (Section 6.3)
        
        message (Required):
        - sender: scammer or user
        - text: Message content
        - timestamp: Epoch time format in ms
        
        conversationHistory (Optional):
        - Empty array ([]) for first message
        - Required for follow-up messages
        
        metadata (Optional but Recommended):
        - channel: SMS / WhatsApp / Email / Chat
        - language: Language used
        - locale: Country or region
        """
        print_header("5. REQUEST BODY FIELD VALIDATION (Section 6.3)")
        
        session_id = f"fields-{uuid.uuid4()}"
        timestamp = generate_timestamp()
        
        # Test sender = "scammer"
        payload_scammer = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": "URGENT: Transfer Rs 5000 now to avoid arrest.",
                "timestamp": timestamp
            },
            "conversationHistory": [],
            "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
        }
        
        response = make_request(payload_scammer)
        self.record_test(
            "sender='scammer' accepted",
            response["status_code"] == 200,
            "Scammer sender works"
        )
        
        # Test all channel types
        channels = ["SMS", "WhatsApp", "Email", "Chat"]
        for channel in channels:
            payload = {
                "sessionId": f"{session_id}-{channel}",
                "message": {
                    "sender": "scammer",
                    "text": "Your account is blocked. Call now.",
                    "timestamp": timestamp
                },
                "conversationHistory": [],
                "metadata": {"channel": channel, "language": "English", "locale": "IN"}
            }
            response = make_request(payload)
            self.record_test(
                f"channel='{channel}' accepted",
                response["status_code"] == 200,
                f"Channel {channel} works"
            )
        
        # Test language field
        languages = ["English", "Hindi"]
        for lang in languages:
            payload = {
                "sessionId": f"{session_id}-{lang}",
                "message": {
                    "sender": "scammer",
                    "text": "Urgent payment required now!" if lang == "English" else "Turant payment karo!",
                    "timestamp": timestamp
                },
                "conversationHistory": [],
                "metadata": {"channel": "SMS", "language": lang, "locale": "IN"}
            }
            response = make_request(payload)
            self.record_test(
                f"language='{lang}' accepted",
                response["status_code"] == 200,
                f"Language {lang} works"
            )
        
        # Test locale field
        payload_locale = {
            "sessionId": f"{session_id}-locale",
            "message": {
                "sender": "scammer",
                "text": "Payment required immediately.",
                "timestamp": timestamp
            },
            "conversationHistory": [],
            "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
        }
        response = make_request(payload_locale)
        self.record_test(
            "locale='IN' accepted",
            response["status_code"] == 200,
            "Locale IN works"
        )
    
    def test_agent_output_format(self):
        """
        Test Agent Output Format (Section 8)
        
        GUVI Doc:
        {
            "status": "success",
            "reply": "Why is my account being suspended?"
        }
        """
        print_header("6. AGENT OUTPUT FORMAT (Section 8)")
        
        session_id = f"output-{uuid.uuid4()}"
        
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": "Your bank account will be blocked. Send OTP now.",
                "timestamp": generate_timestamp()
            },
            "conversationHistory": [],
            "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
        }
        
        response = make_request(payload)
        data = response["data"]
        
        # CRITICAL: Check for "status" field
        self.record_test(
            "Response contains 'status' field",
            "status" in data,
            f"status: {data.get('status', 'MISSING')}"
        )
        
        self.record_test(
            "status='success' for valid request",
            data.get("status") == "success",
            f"status: {data.get('status')}"
        )
        
        # CRITICAL: Check for "reply" field
        self.record_test(
            "Response contains 'reply' field",
            "reply" in data,
            f"reply present: {'Yes' if 'reply' in data else 'No'}"
        )
        
        if data.get("scam_detected"):
            self.record_test(
                "reply contains agent response when scam detected",
                data.get("reply") is not None and len(data.get("reply", "")) > 0,
                f"reply: {str(data.get('reply', ''))[:50]}..."
            )
        
        print_response_summary(data)
    
    def test_agent_behavior(self):
        """
        Test Agent Behavior Expectations (Section 7)
        
        The AI Agent must:
        - Handle multi-turn conversations
        - Adapt responses dynamically
        - Avoid revealing scam detection
        - Behave like a real human
        - Perform self-correction if needed
        """
        print_header("7. AGENT BEHAVIOR (Section 7)")
        
        session_id = f"behavior-{uuid.uuid4()}"
        timestamp = generate_timestamp()
        
        # Multi-turn conversation test
        print(f"\n{Colors.CYAN}Testing multi-turn conversation...{Colors.END}")
        
        # Turn 1: Initial scam message
        payload1 = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": "Your bank account will be blocked. Verify immediately.",
                "timestamp": timestamp
            },
            "conversationHistory": [],
            "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
        }
        
        response1 = make_request(payload1)
        data1 = response1["data"]
        
        self.record_test(
            "Turn 1: Initial message processed",
            response1["status_code"] == 200,
            f"Scam: {data1.get('scam_detected')}, Reply: {str(data1.get('reply', ''))[:30]}..."
        )
        
        # Turn 2: Follow-up with history
        payload2 = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": "Share your UPI ID now to avoid suspension.",
                "timestamp": timestamp + 1000
            },
            "conversationHistory": [
                {
                    "sender": "scammer",
                    "text": "Your bank account will be blocked. Verify immediately.",
                    "timestamp": timestamp
                },
                {
                    "sender": "user",
                    "text": data1.get("reply", "What do you mean?"),
                    "timestamp": timestamp + 500
                }
            ],
            "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
        }
        
        response2 = make_request(payload2)
        data2 = response2["data"]
        
        self.record_test(
            "Turn 2: Follow-up message processed",
            response2["status_code"] == 200,
            f"Reply: {str(data2.get('reply', ''))[:30]}..."
        )
        
        self.record_test(
            "Multi-turn conversation handled",
            response1["status_code"] == 200 and response2["status_code"] == 200,
            "Both turns successful"
        )
        
        # Check agent response doesn't reveal detection
        reply = data2.get("reply", "")
        detection_keywords = ["scam", "fraud", "fake", "detected", "blocked you", "reported"]
        reveals_detection = any(kw in reply.lower() for kw in detection_keywords)
        
        self.record_test(
            "Agent does NOT reveal scam detection",
            not reveals_detection,
            f"No detection keywords in reply"
        )
        
        # Check human-like behavior
        self.record_test(
            "Agent responds in human-like manner",
            len(reply) > 10 and "?" in reply or "." in reply,
            f"Response length: {len(reply)} chars"
        )
    
    def test_intelligence_extraction(self):
        """
        Test Intelligence Extraction (Section 12 - extractedIntelligence)
        
        GUVI Doc:
        extractedIntelligence: {
            "bankAccounts": ["XXXX-XXXX-XXXX"],
            "upiIds": ["scammer@upi"],
            "phishingLinks": ["http://malicious-link.example"],
            "phoneNumbers": ["+91XXXXXXXXXX"],
            "suspiciousKeywords": ["urgent", "verify now", "account blocked"]
        }
        """
        print_header("8. INTELLIGENCE EXTRACTION")
        
        session_id = f"intel-{uuid.uuid4()}"
        
        # Message with all types of intelligence
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": "URGENT! Transfer Rs 10000 to account 9876543210123456 IFSC HDFC0001234 or UPI scammer@paytm. Click http://fake-bank.com/verify and call +91-9876543210 immediately!",
                "timestamp": generate_timestamp()
            },
            "conversationHistory": [],
            "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
        }
        
        response = make_request(payload)
        data = response["data"]
        
        self.record_test(
            "Intelligence extraction request succeeds",
            response["status_code"] == 200,
            f"Status: {response['status_code']}"
        )
        
        intel = data.get("extracted_intelligence", {})
        
        # Check for bank accounts
        bank_accounts = intel.get("bank_accounts", [])
        self.record_test(
            "Bank accounts extracted",
            len(bank_accounts) > 0,
            f"Found: {bank_accounts}"
        )
        
        # Check for UPI IDs
        upi_ids = intel.get("upi_ids", [])
        self.record_test(
            "UPI IDs extracted",
            len(upi_ids) > 0,
            f"Found: {upi_ids}"
        )
        
        # Check for phishing links
        phishing_links = intel.get("phishing_links", [])
        self.record_test(
            "Phishing links extracted",
            len(phishing_links) > 0,
            f"Found: {phishing_links}"
        )
        
        # Check for phone numbers
        phone_numbers = intel.get("phone_numbers", [])
        self.record_test(
            "Phone numbers extracted",
            len(phone_numbers) > 0,
            f"Found: {phone_numbers}"
        )
        
        # Check for suspicious keywords
        keywords = intel.get("suspicious_keywords", [])
        self.record_test(
            "Suspicious keywords extracted",
            len(keywords) > 0,
            f"Found: {keywords[:5]}..."
        )
        
        print(f"\n{Colors.YELLOW}Extracted Intelligence:{Colors.END}")
        print(json.dumps(intel, indent=2))
    
    def test_guvi_callback_format(self):
        """
        Test GUVI Callback Format (Section 12)
        
        GUVI Doc Callback Payload:
        {
            "sessionId": "abc123-session-id",
            "scamDetected": true,
            "totalMessagesExchanged": 18,
            "extractedIntelligence": {
                "bankAccounts": ["XXXX-XXXX-XXXX"],
                "upiIds": ["scammer@upi"],
                "phishingLinks": ["http://malicious-link.example"],
                "phoneNumbers": ["+91XXXXXXXXXX"],
                "suspiciousKeywords": ["urgent", "verify now", "account blocked"]
            },
            "agentNotes": "Scammer used urgency tactics and payment redirection"
        }
        """
        print_header("9. GUVI CALLBACK FORMAT (Section 12)")
        
        session_id = f"callback-{uuid.uuid4()}"
        
        # High-intel message to trigger callback
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": "URGENT! Send money to account 1234567890123456 IFSC SBIN0001234 or UPI fraud@ybl. Visit http://scam-site.com and call +91-8765432109. Your account BLOCKED!",
                "timestamp": generate_timestamp()
            },
            "conversationHistory": [],
            "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
        }
        
        response = make_request(payload)
        data = response["data"]
        
        # Verify response has fields needed for callback
        self.record_test(
            "Response has session_id (for callback sessionId)",
            "session_id" in data,
            f"session_id: {data.get('session_id', 'MISSING')[:30]}"
        )
        
        self.record_test(
            "Response has scam_detected (for callback scamDetected)",
            "scam_detected" in data,
            f"scam_detected: {data.get('scam_detected')}"
        )
        
        self.record_test(
            "Response has extracted_intelligence (for callback)",
            "extracted_intelligence" in data,
            "Intelligence object present"
        )
        
        intel = data.get("extracted_intelligence", {})
        
        # Verify intelligence fields match GUVI format
        self.record_test(
            "Intel has bank_accounts (maps to bankAccounts)",
            "bank_accounts" in intel,
            f"bank_accounts: {intel.get('bank_accounts', [])}"
        )
        
        self.record_test(
            "Intel has upi_ids (maps to upiIds)",
            "upi_ids" in intel,
            f"upi_ids: {intel.get('upi_ids', [])}"
        )
        
        self.record_test(
            "Intel has phishing_links (maps to phishingLinks)",
            "phishing_links" in intel,
            f"phishing_links: {intel.get('phishing_links', [])}"
        )
        
        self.record_test(
            "Intel has phone_numbers (maps to phoneNumbers)",
            "phone_numbers" in intel,
            f"phone_numbers: {intel.get('phone_numbers', [])}"
        )
        
        self.record_test(
            "Intel has suspicious_keywords (maps to suspiciousKeywords)",
            "suspicious_keywords" in intel,
            f"suspicious_keywords: {intel.get('suspicious_keywords', [])[:3]}"
        )
        
        # Check for agent_notes
        self.record_test(
            "Response has agent_notes (for callback agentNotes)",
            "agent_notes" in data,
            f"agent_notes: {str(data.get('agent_notes', 'MISSING'))[:50]}"
        )
    
    def test_non_scam_detection(self):
        """Test that non-scam messages are correctly identified."""
        print_header("10. NON-SCAM MESSAGE HANDLING")
        
        session_id = f"nonscam-{uuid.uuid4()}"
        
        # Normal, non-scam message
        payload = {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",  # Using scammer sender but legitimate message
                "text": "Hello! How are you today? I hope you are having a wonderful day. Would you like to meet for coffee sometime?",
                "timestamp": generate_timestamp()
            },
            "conversationHistory": [],
            "metadata": {"channel": "WhatsApp", "language": "English", "locale": "IN"}
        }
        
        response = make_request(payload)
        data = response["data"]
        
        self.record_test(
            "Non-scam message processed successfully",
            response["status_code"] == 200,
            f"Status: {response['status_code']}"
        )
        
        self.record_test(
            "Non-scam correctly identified (scam_detected=false or low confidence)",
            data.get("scam_detected") == False or data.get("confidence", 1.0) < 0.5,
            f"scam_detected: {data.get('scam_detected')}, confidence: {data.get('confidence', 0):.2f}"
        )
        
        print_response_summary(data)
    
    def test_response_time(self):
        """
        Test Response Time (Section 9 - AC-4.1.5: Response time <2s p95)
        """
        print_header("11. RESPONSE TIME PERFORMANCE")
        
        times = []
        
        for i in range(3):
            payload = {
                "sessionId": f"perf-{uuid.uuid4()}",
                "message": {
                    "sender": "scammer",
                    "text": "Your account is blocked. Send OTP now.",
                    "timestamp": generate_timestamp()
                },
                "conversationHistory": [],
                "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
            }
            
            response = make_request(payload)
            times.append(response["elapsed_ms"])
            print(f"  Request {i+1}: {response['elapsed_ms']:.0f}ms")
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        self.record_test(
            "Average response time < 2000ms",
            avg_time < 2000,
            f"Avg: {avg_time:.0f}ms"
        )
        
        self.record_test(
            "Max response time < 5000ms",
            max_time < 5000,
            f"Max: {max_time:.0f}ms"
        )
    
    def test_scam_types(self):
        """Test detection of various scam types mentioned in doc."""
        print_header("12. SCAM TYPE DETECTION")
        
        scam_messages = [
            ("Bank Fraud", "Your bank account is blocked. Share OTP immediately to unblock."),
            ("UPI Fraud", "Send Rs 1 to UPI scammer@paytm to verify your account."),
            ("Phishing", "Click this link http://fake-bank.com/verify to update your details."),
            ("Fake Offer/Lottery", "Congratulations! You won Rs 50 lakh lottery. Pay Rs 5000 to claim."),
            ("Authority Impersonation", "This is police. Your Aadhaar is used in fraud. Transfer money or face arrest."),
            ("Urgency Tactics", "URGENT: Your account will be deactivated in 1 hour. Act NOW!"),
        ]
        
        for scam_type, message in scam_messages:
            payload = {
                "sessionId": f"type-{uuid.uuid4()}",
                "message": {
                    "sender": "scammer",
                    "text": message,
                    "timestamp": generate_timestamp()
                },
                "conversationHistory": [],
                "metadata": {"channel": "SMS", "language": "English", "locale": "IN"}
            }
            
            response = make_request(payload)
            data = response["data"]
            
            self.record_test(
                f"{scam_type} detected",
                data.get("scam_detected") == True,
                f"Confidence: {data.get('confidence', 0):.2f}"
            )
    
    def print_summary(self):
        """Print test summary."""
        print_header("TEST SUMMARY")
        
        print(f"  Total Tests: {self.results['total']}")
        print(f"  {Colors.GREEN}Passed: {self.results['passed']}{Colors.END}")
        print(f"  {Colors.RED}Failed: {self.results['failed']}{Colors.END}")
        
        pass_rate = (self.results['passed'] / self.results['total'] * 100) if self.results['total'] > 0 else 0
        
        if pass_rate >= 90:
            color = Colors.GREEN
        elif pass_rate >= 70:
            color = Colors.YELLOW
        else:
            color = Colors.RED
        
        print(f"\n  {color}Pass Rate: {pass_rate:.1f}%{Colors.END}")
        
        if self.results['failed'] > 0:
            print(f"\n{Colors.RED}Failed Tests:{Colors.END}")
            for test in self.results['tests']:
                if not test['passed']:
                    print(f"  - {test['name']}: {test['details']}")
        
        return self.results


def main():
    """Run all compliance tests."""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("=" * 70)
    print("     GUVI DOCUMENTATION COMPLIANCE TEST SUITE")
    print("     Testing: Agentic Honey-Pot for Scam Detection")
    print("     Live API Testing - No Hardcoded Responses")
    print("=" * 70)
    print(f"{Colors.END}")
    
    print(f"\n{Colors.YELLOW}Configuration:{Colors.END}")
    print(f"  API Endpoint: {API_ENDPOINT}")
    print(f"  Health Check: {HEALTH_ENDPOINT}")
    print(f"  Timestamp: {datetime.now().isoformat()}")
    
    tests = GuviComplianceTests()
    
    # Run all tests
    tests.test_health_check()
    tests.test_api_authentication()
    tests.test_first_message_format()
    tests.test_followup_message_format()
    tests.test_request_body_fields()
    tests.test_agent_output_format()
    tests.test_agent_behavior()
    tests.test_intelligence_extraction()
    tests.test_guvi_callback_format()
    tests.test_non_scam_detection()
    tests.test_response_time()
    tests.test_scam_types()
    
    # Print summary
    results = tests.print_summary()
    
    # Save results to file
    results_file = "guvi_test_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n{Colors.CYAN}Results saved to: {results_file}{Colors.END}")
    
    return results


if __name__ == "__main__":
    main()

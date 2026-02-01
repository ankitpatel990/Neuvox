"""
Full Conversation Flow Test for ScamShield AI

This script simulates a complete multi-turn conversation between
a scammer and the honeypot agent to test the full flow.

Run: python scripts/test_full_conversation.py
"""

import sys
import io
import requests
import json
import time
from typing import Optional

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# API Configuration
BASE_URL = "http://127.0.0.1:8080"
API_URL = f"{BASE_URL}/api/v1/honeypot/engage"

# Simulated scammer messages (multi-turn conversation)
SCAMMER_MESSAGES = [
    # Turn 1: Initial scam message
    "Congratulations! You have won 10 lakh rupees in our lucky draw! Reply to claim your prize!",
    
    # Turn 2: Scammer responds to agent's interest
    "Yes sir, you are the lucky winner! Just pay Rs 500 processing fee and the money will be transferred to your account immediately!",
    
    # Turn 3: Scammer provides payment details
    "Please pay to my UPI ID: scammer@paytm. You can also use fraudster@ybl as alternative.",
    
    # Turn 4: Scammer provides more details
    "If you want to pay via bank transfer, use account number 1234567890123, IFSC code SBIN0001234. Call me at +919876543210 for help.",
    
    # Turn 5: Scammer tries to create urgency
    "Hurry up sir! This offer expires in 1 hour. Pay now or you will lose your 10 lakh prize money!",
    
    # Turn 6: Scammer provides phishing link
    "You can also verify your prize at http://fake-lottery-winner.tk/claim?user=12345. Just enter your details there.",
]


def print_header():
    """Print test header"""
    print("=" * 80)
    print("🔒 ScamShield AI - Full Conversation Flow Test")
    print("=" * 80)
    print()


def print_message(turn: int, sender: str, message: str, is_scammer: bool = True):
    """Pretty print a message"""
    emoji = "🦹" if is_scammer else "🤖"
    color_name = "SCAMMER" if is_scammer else "AGENT"
    print(f"\n{'─' * 60}")
    print(f"Turn {turn} | {emoji} {color_name}:")
    print(f"{'─' * 60}")
    print(f"{message}")


def print_intelligence(intel: dict):
    """Print extracted intelligence"""
    print(f"\n{'═' * 60}")
    print("📊 EXTRACTED INTELLIGENCE:")
    print(f"{'═' * 60}")
    
    if intel.get("upi_ids"):
        print(f"  💳 UPI IDs: {', '.join(intel['upi_ids'])}")
    if intel.get("bank_accounts"):
        print(f"  🏦 Bank Accounts: {', '.join(intel['bank_accounts'])}")
    if intel.get("ifsc_codes"):
        print(f"  🔢 IFSC Codes: {', '.join(intel['ifsc_codes'])}")
    if intel.get("phone_numbers"):
        print(f"  📱 Phone Numbers: {', '.join(intel['phone_numbers'])}")
    if intel.get("phishing_links"):
        print(f"  🔗 Phishing Links: {', '.join(intel['phishing_links'])}")
    
    conf = intel.get("extraction_confidence", 0)
    print(f"  📈 Extraction Confidence: {conf:.0%}")


def test_health():
    """Test API health before starting"""
    try:
        response = requests.get(f"{BASE_URL}/api/v1/health", timeout=5)
        data = response.json()
        print(f"✅ API Status: {data['status']}")
        print(f"   Models Loaded: {data['dependencies']['models_loaded']}")
        return True
    except Exception as e:
        print(f"❌ API not available: {e}")
        print(f"   Make sure the server is running: uvicorn app.main:app --port 8080")
        return False


def run_conversation():
    """Run full multi-turn conversation test"""
    print_header()
    
    # Check API health
    print("🔍 Checking API health...")
    if not test_health():
        return
    
    print("\n" + "=" * 80)
    print("🎭 STARTING SIMULATED SCAM CONVERSATION")
    print("=" * 80)
    
    session_id: Optional[str] = None
    all_intelligence = {
        "upi_ids": set(),
        "bank_accounts": set(),
        "ifsc_codes": set(),
        "phone_numbers": set(),
        "phishing_links": set(),
    }
    
    for turn_num, scammer_message in enumerate(SCAMMER_MESSAGES, 1):
        # Print scammer message
        print_message(turn_num, "SCAMMER", scammer_message, is_scammer=True)
        
        # Send to API
        payload = {
            "message": scammer_message,
            "language": "auto",
        }
        if session_id:
            payload["session_id"] = session_id
        
        try:
            response = requests.post(
                API_URL,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=60,
            )
            data = response.json()
            
            # Get session ID for continuation
            if not session_id:
                session_id = data.get("session_id")
                print(f"\n📋 Session ID: {session_id}")
            
            # Print detection result
            scam_detected = data.get("scam_detected", False)
            confidence = data.get("confidence", 0)
            print(f"\n🎯 Scam Detected: {'YES ✓' if scam_detected else 'NO'} (Confidence: {confidence:.0%})")
            
            # Print agent response
            if data.get("engagement"):
                agent_response = data["engagement"].get("agent_response", "")
                strategy = data["engagement"].get("strategy", "")
                persona = data["engagement"].get("persona", "")
                current_turn = data["engagement"].get("turn_count", turn_num)
                
                print_message(current_turn, "AGENT", agent_response, is_scammer=False)
                print(f"\n   📝 Strategy: {strategy} | Persona: {persona}")
            
            # Accumulate intelligence
            if data.get("extracted_intelligence"):
                intel = data["extracted_intelligence"]
                all_intelligence["upi_ids"].update(intel.get("upi_ids", []))
                all_intelligence["bank_accounts"].update(intel.get("bank_accounts", []))
                all_intelligence["ifsc_codes"].update(intel.get("ifsc_codes", []))
                all_intelligence["phone_numbers"].update(intel.get("phone_numbers", []))
                all_intelligence["phishing_links"].update(intel.get("phishing_links", []))
            
            # Small delay between turns
            time.sleep(1)
            
        except requests.exceptions.Timeout:
            print(f"\n⚠️ Request timed out for turn {turn_num}")
        except Exception as e:
            print(f"\n❌ Error on turn {turn_num}: {e}")
    
    # Print final summary
    print("\n" + "=" * 80)
    print("📋 CONVERSATION SUMMARY")
    print("=" * 80)
    print(f"Total Turns: {len(SCAMMER_MESSAGES)}")
    print(f"Session ID: {session_id}")
    
    # Convert sets to lists for printing
    final_intel = {
        "upi_ids": list(all_intelligence["upi_ids"]),
        "bank_accounts": list(all_intelligence["bank_accounts"]),
        "ifsc_codes": list(all_intelligence["ifsc_codes"]),
        "phone_numbers": list(all_intelligence["phone_numbers"]),
        "phishing_links": list(all_intelligence["phishing_links"]),
        "extraction_confidence": 0.9 if any(all_intelligence.values()) else 0.0,
    }
    
    print_intelligence(final_intel)
    
    # Retrieve full session
    if session_id:
        print("\n" + "=" * 80)
        print("📜 RETRIEVING FULL CONVERSATION FROM SESSION")
        print("=" * 80)
        try:
            session_response = requests.get(
                f"{BASE_URL}/api/v1/honeypot/session/{session_id}",
                timeout=10,
            )
            session_data = session_response.json()
            
            print(f"\nSession Details:")
            print(f"  Language: {session_data.get('language')}")
            print(f"  Persona: {session_data.get('persona')}")
            print(f"  Turn Count: {session_data.get('turn_count')}")
            print(f"  Scam Confidence: {session_data.get('scam_confidence', 0):.0%}")
            
            print(f"\nConversation History ({len(session_data.get('conversation_history', []))} messages):")
            for msg in session_data.get("conversation_history", []):
                sender = "🦹 SCAMMER" if msg["sender"] == "scammer" else "🤖 AGENT"
                print(f"  [{msg['turn']}] {sender}: {msg['message'][:80]}...")
                
        except Exception as e:
            print(f"❌ Could not retrieve session: {e}")
    
    print("\n" + "=" * 80)
    print("✅ TEST COMPLETE!")
    print("=" * 80)


def run_hindi_conversation():
    """Run Hindi scam conversation test"""
    print("\n" + "=" * 80)
    print("🎭 HINDI SCAM CONVERSATION TEST")
    print("=" * 80)
    
    hindi_messages = [
        "बधाई हो! आपने 10 लाख रुपये जीते हैं! इनाम पाने के लिए जवाब दें!",
        "हाँ जी, आप विजेता हैं! बस 500 रुपये प्रोसेसिंग फीस भेजें और पैसे आपके खाते में आ जाएंगे!",
        "मेरे UPI पर भेजें: scammer@paytm। फोन करें +919876543210",
    ]
    
    session_id = None
    
    for turn, message in enumerate(hindi_messages, 1):
        print_message(turn, "SCAMMER", message, is_scammer=True)
        
        payload = {"message": message, "language": "hi"}
        if session_id:
            payload["session_id"] = session_id
        
        try:
            response = requests.post(API_URL, json=payload, timeout=60)
            data = response.json()
            
            if not session_id:
                session_id = data.get("session_id")
            
            if data.get("engagement"):
                print_message(turn, "AGENT", data["engagement"]["agent_response"], is_scammer=False)
            
            if data.get("extracted_intelligence"):
                intel = data["extracted_intelligence"]
                if any([intel.get("upi_ids"), intel.get("phone_numbers")]):
                    print_intelligence(intel)
            
            time.sleep(1)
            
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    # Run main English conversation test
    run_conversation()
    
    # Optionally run Hindi test
    print("\n\nWould you like to run Hindi conversation test? (This is automatic)")
    # run_hindi_conversation()

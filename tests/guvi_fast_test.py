"""
GUVI Hackathon Fast Evaluation Test

A streamlined but comprehensive test that simulates GUVI's exact evaluation
process. Tests all 5 scoring categories with realistic scam scenarios.

Run: python tests/guvi_fast_test.py
"""

import requests
import json
import time
import uuid
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000"
API_KEY = "sVlunn0LMQZNAkRYqZB-f1-Ye7rgzjB_E3b1gNxnUV8"
HEADERS = {"Content-Type": "application/json", "x-api-key": API_KEY}


def print_header(text: str):
    print(f"\n{'='*70}")
    print(f" {text}")
    print(f"{'='*70}")


def print_section(text: str):
    print(f"\n{'-'*50}")
    print(f" {text}")
    print(f"{'-'*50}")


def check_health() -> bool:
    """Verify API is running."""
    try:
        r = requests.get(f"{API_URL}/api/v1/health", timeout=5)
        if r.status_code == 200:
            data = r.json()
            print(f"  Status: {data.get('status')}")
            print(f"  Version: {data.get('version')}")
            print(f"  Models: {'Loaded' if data.get('dependencies', {}).get('models_loaded') else 'Not loaded'}")
            return True
    except Exception as e:
        print(f"  Error: {e}")
    return False


def send_guvi_request(session_id: str, message: str, history: List, metadata: Dict) -> Optional[Dict]:
    """Send request in GUVI format."""
    payload = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer",
            "text": message,
            "timestamp": int(time.time() * 1000),
        },
        "conversationHistory": history,
        "metadata": metadata,
    }
    
    try:
        r = requests.post(
            f"{API_URL}/api/v1/honeypot/engage",
            json=payload,
            headers=HEADERS,
            timeout=30,
        )
        if r.status_code == 200:
            return r.json()
        print(f"    HTTP {r.status_code}: {r.text[:100]}")
    except requests.exceptions.Timeout:
        print("    TIMEOUT")
    except Exception as e:
        print(f"    ERROR: {e}")
    return None


def run_multi_turn_scenario(name: str, messages: List[str], fake_data: Dict) -> Dict:
    """Run a complete multi-turn conversation scenario."""
    print_section(f"SCENARIO: {name}")
    
    session_id = str(uuid.uuid4())
    history = []
    responses = []
    metadata = {"channel": "SMS", "language": "English", "locale": "IN"}
    
    start_time = time.time()
    
    for turn, msg in enumerate(messages, 1):
        print(f"\n  Turn {turn}: {msg[:60]}...")
        
        resp = send_guvi_request(session_id, msg, history, metadata)
        
        if resp:
            responses.append(resp)
            reply = resp.get("reply", "")[:60]
            print(f"    Agent: {reply}...")
            
            # Update history
            history.append({"sender": "scammer", "text": msg, "timestamp": int(time.time() * 1000)})
            history.append({"sender": "user", "text": resp.get("reply", ""), "timestamp": int(time.time() * 1000)})
        else:
            print("    [No response]")
        
        time.sleep(0.3)
    
    duration = time.time() - start_time
    
    # Calculate scores
    final = responses[-1] if responses else {}
    scores = calculate_scores(final, responses, history, fake_data, duration)
    
    return {
        "name": name,
        "turns": len(responses),
        "duration": duration,
        "scores": scores,
        "final_response": final,
    }


def calculate_scores(final: Dict, all_responses: List, history: List, fake_data: Dict, duration: float) -> Dict:
    """Calculate all GUVI scoring categories."""
    
    # 1. Scam Detection (20 points)
    scam_detected = final.get("scamDetected", final.get("scam_detected", False))
    scam_score = 20.0 if scam_detected else 0.0
    
    # 2. Intelligence Extraction (30 points)
    intel = final.get("extractedIntelligence", final.get("extracted_intelligence", {}))
    total_fake = sum(len(v) for v in fake_data.values())
    matched = 0
    
    if total_fake > 0:
        intel_str = json.dumps(intel).lower().replace("-", "").replace(" ", "")
        for fake_type, fake_values in fake_data.items():
            for fv in fake_values:
                if fv.lower().replace("-", "").replace(" ", "") in intel_str:
                    matched += 1
        intel_score = min((matched / total_fake) * 30.0, 30.0)
    else:
        intel_score = 30.0
    
    # 3. Conversation Quality (30 points)
    agent_msgs = [h.get("text", "") for h in history if h.get("sender") == "user"]
    turn_count = len(all_responses)
    questions = sum(1 for m in agent_msgs if "?" in m)
    
    # Turn count scoring
    turn_score = 8.0 if turn_count >= 8 else (6.0 if turn_count >= 6 else (3.0 if turn_count >= 4 else 0.0))
    
    # Questions asked
    q_score = 4.0 if questions >= 5 else (2.0 if questions >= 3 else (1.0 if questions >= 1 else 0.0))
    
    # Relevant questions
    investigative = ["upi", "phone", "number", "account", "bank", "ifsc", "name", "verify"]
    relevant = sum(1 for m in agent_msgs if any(k in m.lower() for k in investigative))
    rel_score = 3.0 if relevant >= 3 else (2.0 if relevant >= 2 else (1.0 if relevant >= 1 else 0.0))
    
    # Red flags
    conv_quality = final.get("conversationQuality", {})
    red_flags = conv_quality.get("redFlagsCount", 0)
    if red_flags == 0:
        notes = final.get("agentNotes", "").lower()
        red_flags = notes.count("red flag") + notes.count("urgency") + notes.count("threat")
    rf_score = 8.0 if red_flags >= 5 else (5.0 if red_flags >= 3 else (2.0 if red_flags >= 1 else 0.0))
    
    # Elicitation
    elicit = conv_quality.get("elicitationAttempts", conv_quality.get("questionsAsked", questions))
    el_score = min(elicit * 1.5, 7.0)
    
    conv_score = min(turn_score + q_score + rel_score + rf_score + el_score, 30.0)
    
    # 4. Engagement Quality (10 points)
    metrics = final.get("engagementMetrics", {})
    eng_duration = metrics.get("engagementDurationSeconds", int(duration))
    eng_msgs = metrics.get("totalMessagesExchanged", len(history) // 2)
    
    eng_score = 0.0
    if eng_duration > 0: eng_score += 1.0
    if eng_duration > 60: eng_score += 2.0
    if eng_duration > 180: eng_score += 1.0
    if eng_msgs > 0: eng_score += 2.0
    if eng_msgs >= 5: eng_score += 3.0
    if eng_msgs >= 10: eng_score += 1.0
    eng_score = min(eng_score, 10.0)
    
    # 5. Response Structure (10 points)
    struct_score = 0.0
    required = ["sessionId", "scamDetected", "extractedIntelligence"]
    for f in required:
        snake = re.sub(r'([A-Z])', r'_\1', f).lower().lstrip('_')
        if f in final or snake in final:
            struct_score += 2.0
        else:
            struct_score -= 1.0
    
    optional = ["totalMessagesExchanged", "agentNotes", "scamType", "confidenceLevel"]
    for f in optional:
        snake = re.sub(r'([A-Z])', r'_\1', f).lower().lstrip('_')
        if f in final or snake in final:
            struct_score += 1.0
    
    struct_score = max(struct_score, 0.0)
    
    total = scam_score + intel_score + conv_score + eng_score + struct_score
    
    return {
        "scam_detection": scam_score,
        "intelligence": intel_score,
        "conversation_quality": conv_score,
        "engagement_quality": eng_score,
        "response_structure": struct_score,
        "total": total,
        "details": {
            "turns": turn_count,
            "questions": questions,
            "relevant_questions": relevant,
            "red_flags": red_flags,
            "matched_intel": matched,
            "total_fake": total_fake,
            "duration": eng_duration,
            "messages": eng_msgs,
        }
    }


def main():
    print_header("GUVI HACKATHON EVALUATION TEST")
    print(f"API: {API_URL}")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Health check
    print_section("API Health Check")
    if not check_health():
        print("\nERROR: API not running. Start with:")
        print("  python -m uvicorn app.main:app --port 8000")
        return
    
    # Define test scenarios
    scenarios = [
        {
            "name": "Bank Fraud (SBI Impersonation)",
            "weight": 0.35,
            "messages": [
                "URGENT: Your SBI account will be blocked in 2 hours! Verify immediately.",
                "I am Officer Rajesh from SBI Fraud Department. ID: SBI-FD-7895.",
                "Your account ending 1234 has suspicious activity. Share OTP to verify.",
                "My official number is +91-9876543210. You can call to verify.",
                "Send Rs 500 verification fee to fraud.officer@sbi UPI ID.",
                "Bank account for fee: 12345678901234, IFSC: SBIN0001234",
                "This is final warning. Share OTP or face legal action!",
                "Sir please cooperate. I am trying to help you only.",
            ],
            "fake_data": {
                "phoneNumbers": ["+91-9876543210"],
                "bankAccounts": ["12345678901234"],
                "upiIds": ["fraud.officer@sbi"],
                "ifscCodes": ["SBIN0001234"],
            },
        },
        {
            "name": "UPI Cashback Scam (Paytm)",
            "weight": 0.35,
            "messages": [
                "Congratulations! You won Rs 50,000 Paytm cashback! Claim now!",
                "I am from Paytm Rewards. My number: +91-8765432109",
                "Send Rs 99 to cashback.reward@paytm to process your winning.",
                "Alternate UPI: winner.claim@ybl for faster processing.",
                "Click here to claim: http://paytm-cashback.xyz/claim",
                "Hurry! Only 10 minutes left. Don't miss this chance!",
                "Sir this is genuine. Thousands have already claimed.",
                "Last reminder. Your cashback will expire soon!",
            ],
            "fake_data": {
                "phoneNumbers": ["+91-8765432109"],
                "upiIds": ["cashback.reward@paytm", "winner.claim@ybl"],
                "phishingLinks": ["http://paytm-cashback.xyz/claim"],
            },
        },
        {
            "name": "Amazon Phishing Attack",
            "weight": 0.30,
            "messages": [
                "Amazon Alert: Order #AMZ-789456 worth Rs 45,999 placed. Cancel here: http://amazon-cancel.tk",
                "This is Amazon Support. Call +91-7654321098 to cancel fraudulent order.",
                "Email support@amazon-helpdesk.xyz with your details for refund.",
                "Login here for cancellation: http://secure-amazon.ml/login",
                "Order AMZ-789456 ships in 2 hours if not cancelled!",
                "We need card details to verify and cancel the order.",
                "Sir act fast. Once shipped we cannot help you.",
                "Share OTP to confirm cancellation immediately.",
            ],
            "fake_data": {
                "phoneNumbers": ["+91-7654321098"],
                "emailAddresses": ["support@amazon-helpdesk.xyz"],
                "phishingLinks": ["http://amazon-cancel.tk", "http://secure-amazon.ml/login"],
                "orderNumbers": ["AMZ-789456"],
            },
        },
    ]
    
    # Run scenarios
    results = []
    for scenario in scenarios:
        result = run_multi_turn_scenario(
            scenario["name"],
            scenario["messages"],
            scenario["fake_data"],
        )
        result["weight"] = scenario["weight"]
        results.append(result)
        
        # Print score breakdown
        s = result["scores"]
        print(f"\n  SCORES:")
        print(f"    Scam Detection:       {s['scam_detection']:5.1f}/20")
        print(f"    Intelligence:         {s['intelligence']:5.1f}/30")
        print(f"    Conversation Quality: {s['conversation_quality']:5.1f}/30")
        print(f"    Engagement Quality:   {s['engagement_quality']:5.1f}/10")
        print(f"    Response Structure:   {s['response_structure']:5.1f}/10")
        print(f"    TOTAL:                {s['total']:5.1f}/100")
    
    # Final results
    print_header("FINAL EVALUATION RESULTS")
    
    weighted_score = sum(r["scores"]["total"] * r["weight"] for r in results)
    
    print(f"\n{'Scenario':<35} {'Score':<12} {'Weight':<10} {'Contribution'}")
    print("-"*70)
    for r in results:
        contrib = r["scores"]["total"] * r["weight"]
        print(f"{r['name']:<35} {r['scores']['total']:>5.1f}/100   {r['weight']*100:>4.0f}%      {contrib:>6.2f}")
    print("-"*70)
    print(f"{'Weighted Scenario Score:':<35} {weighted_score:>5.1f}/100")
    
    # Final calculation
    code_quality = 9.0  # Based on README, structure, etc.
    scenario_portion = weighted_score * 0.9
    final_score = scenario_portion + code_quality
    
    print_section("FINAL SCORE (GUVI Formula)")
    print(f"  Scenario Score (100%):   {weighted_score:.1f}")
    print(f"  Scenario Portion (90%):  {scenario_portion:.1f}")
    print(f"  Code Quality (10%):      {code_quality:.1f}")
    print(f"  {'─'*30}")
    print(f"  FINAL SCORE:             {final_score:.1f}/100")
    
    # Assessment
    print_section("COMPETITION ASSESSMENT")
    if final_score >= 95:
        grade = "EXCELLENT"
        msg = "Top-tier performance! Very strong chance of selection from 40K participants."
    elif final_score >= 90:
        grade = "VERY GOOD"
        msg = "Highly competitive score. Strong probability of advancing."
    elif final_score >= 85:
        grade = "GOOD"
        msg = "Above average. Should qualify in most scenarios."
    elif final_score >= 80:
        grade = "FAIR"
        msg = "Average performance. May need improvement."
    else:
        grade = "NEEDS IMPROVEMENT"
        msg = "Below threshold. Focus on weak areas."
    
    print(f"  Grade: {grade}")
    print(f"  {msg}")
    
    # Detailed analysis
    print_section("DETAILED ANALYSIS")
    avg_scores = {
        "scam_detection": sum(r["scores"]["scam_detection"] for r in results) / len(results),
        "intelligence": sum(r["scores"]["intelligence"] for r in results) / len(results),
        "conversation_quality": sum(r["scores"]["conversation_quality"] for r in results) / len(results),
        "engagement_quality": sum(r["scores"]["engagement_quality"] for r in results) / len(results),
        "response_structure": sum(r["scores"]["response_structure"] for r in results) / len(results),
    }
    
    print(f"\n  Average Scores Across Scenarios:")
    print(f"    Scam Detection:       {avg_scores['scam_detection']:5.1f}/20  {'✓' if avg_scores['scam_detection'] >= 18 else '!'}")
    print(f"    Intelligence:         {avg_scores['intelligence']:5.1f}/30  {'✓' if avg_scores['intelligence'] >= 25 else '!'}")
    print(f"    Conversation Quality: {avg_scores['conversation_quality']:5.1f}/30  {'✓' if avg_scores['conversation_quality'] >= 25 else '!'}")
    print(f"    Engagement Quality:   {avg_scores['engagement_quality']:5.1f}/10  {'✓' if avg_scores['engagement_quality'] >= 8 else '!'}")
    print(f"    Response Structure:   {avg_scores['response_structure']:5.1f}/10  {'✓' if avg_scores['response_structure'] >= 8 else '!'}")
    
    # Save results
    with open("tests/guvi_fast_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "scenarios": [
                {
                    "name": r["name"],
                    "weight": r["weight"],
                    "turns": r["turns"],
                    "scores": r["scores"],
                }
                for r in results
            ],
            "weighted_score": weighted_score,
            "code_quality": code_quality,
            "final_score": final_score,
            "grade": grade,
        }, f, indent=2)
    
    print(f"\n  Results saved to: tests/guvi_fast_results.json")
    print_header("TEST COMPLETE")


if __name__ == "__main__":
    main()

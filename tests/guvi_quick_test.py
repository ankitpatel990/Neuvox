"""
GUVI Hackathon Quick Evaluation Test

A streamlined test that evaluates the API against GUVI's scoring criteria.
Uses single comprehensive requests to minimize total time.

Run: python tests/guvi_quick_test.py
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any

API_URL = "http://localhost:8000"
API_KEY = "sVlunn0LMQZNAkRYqZB-f1-Ye7rgzjB_E3b1gNxnUV8"
HEADERS = {"Content-Type": "application/json", "x-api-key": API_KEY}

def print_line(char="=", length=70):
    print(char * length)

def test_scenario(name: str, weight: float, messages: List[str], fake_data: Dict) -> Dict:
    """Run a multi-turn scenario and calculate score."""
    print(f"\n{'-'*60}")
    print(f"SCENARIO: {name} (Weight: {weight*100:.0f}%)")
    print(f"{'-'*60}")
    
    session_id = str(uuid.uuid4())
    history = []
    final_response = None
    turn_count = 0
    
    for i, msg in enumerate(messages[:8]):  # Max 8 turns for speed
        turn_count = i + 1
        print(f"  Turn {turn_count}: {msg[:50]}...")
        
        payload = {
            "sessionId": session_id,
            "message": {"sender": "scammer", "text": msg, "timestamp": int(time.time() * 1000)},
            "conversationHistory": history,
            "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
        }
        
        try:
            resp = requests.post(f"{API_URL}/api/v1/honeypot/engage", json=payload, headers=HEADERS, timeout=60)
            if resp.status_code == 200:
                final_response = resp.json()
                reply = final_response.get("reply", "")[:50]
                print(f"    -> {reply}...")
                history.append({"sender": "scammer", "text": msg, "timestamp": int(time.time() * 1000)})
                history.append({"sender": "user", "text": final_response.get("reply", ""), "timestamp": int(time.time() * 1000)})
            else:
                print(f"    ERROR: HTTP {resp.status_code}")
                break
        except requests.exceptions.Timeout:
            print(f"    TIMEOUT")
            break
        except Exception as e:
            print(f"    ERROR: {e}")
            break
    
    if not final_response:
        return {"name": name, "weight": weight, "total": 0, "error": "No response"}
    
    # Calculate scores
    scores = {}
    
    # 1. Scam Detection (20 pts)
    scores["scam_detection"] = 20.0 if final_response.get("scamDetected") else 0.0
    
    # 2. Intelligence (30 pts)
    intel = final_response.get("extractedIntelligence", {})
    total_fake = sum(len(v) for v in fake_data.values())
    matched = 0
    intel_str = json.dumps(intel).lower().replace("-", "").replace(" ", "")
    for values in fake_data.values():
        for v in values:
            if v.lower().replace("-", "").replace(" ", "") in intel_str:
                matched += 1
    scores["intelligence"] = min((matched / total_fake) * 30.0, 30.0) if total_fake > 0 else 30.0
    
    # 3. Conversation Quality (30 pts)
    cq = final_response.get("conversationQuality", {})
    tc = cq.get("turnCount", turn_count)
    rf = cq.get("redFlagsCount", 0)
    el = cq.get("elicitationAttempts", cq.get("questionsAsked", 0))
    
    turn_pts = 8 if tc >= 8 else (6 if tc >= 6 else (3 if tc >= 4 else 0))
    question_pts = 4 if el >= 5 else (2 if el >= 3 else (1 if el >= 1 else 0))
    rf_pts = 8 if rf >= 5 else (5 if rf >= 3 else (2 if rf >= 1 else 0))
    elicit_pts = min(el * 1.5, 7)
    scores["conversation_quality"] = min(turn_pts + question_pts + 3 + rf_pts + elicit_pts, 30.0)
    
    # 4. Engagement Quality (10 pts)
    em = final_response.get("engagementMetrics", {})
    dur = em.get("engagementDurationSeconds", 0)
    msgs = em.get("totalMessagesExchanged", turn_count)
    
    eng_pts = 0
    if dur > 0: eng_pts += 1
    if dur > 60: eng_pts += 2
    if dur > 180: eng_pts += 1
    if msgs > 0: eng_pts += 2
    if msgs >= 5: eng_pts += 3
    if msgs >= 10: eng_pts += 1
    scores["engagement_quality"] = min(eng_pts, 10.0)
    
    # 5. Response Structure (10 pts)
    struct_pts = 0
    for f in ["sessionId", "scamDetected", "extractedIntelligence"]:
        if f in final_response or f.replace("D", "_d").replace("I", "_i") in final_response:
            struct_pts += 2
    for f in ["totalMessagesExchanged", "agentNotes", "scamType", "confidenceLevel"]:
        if f in final_response:
            struct_pts += 1
    scores["response_structure"] = min(struct_pts, 10.0)
    
    scores["total"] = sum(scores.values())
    
    print(f"\n  SCORE: {scores['total']:.1f}/100")
    print(f"    Scam Detection: {scores['scam_detection']:.0f}/20")
    print(f"    Intelligence: {scores['intelligence']:.1f}/30 (matched {matched}/{total_fake})")
    print(f"    Conv Quality: {scores['conversation_quality']:.1f}/30 (turns={tc}, flags={rf}, elicit={el})")
    print(f"    Engagement: {scores['engagement_quality']:.1f}/10 (dur={dur}s, msgs={msgs})")
    print(f"    Structure: {scores['response_structure']:.1f}/10")
    
    return {"name": name, "weight": weight, "scores": scores, "total": scores["total"], "response": final_response}


def main():
    print_line()
    print(" GUVI HACKATHON QUICK EVALUATION TEST")
    print_line()
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"API: {API_URL}")
    
    # Health check
    try:
        r = requests.get(f"{API_URL}/api/v1/health", timeout=10)
        print(f"API Status: {r.json().get('status') if r.status_code == 200 else 'ERROR'}")
    except Exception as e:
        print(f"API ERROR: {e}")
        return
    
    # Define scenarios
    scenarios = [
        {
            "name": "Bank Fraud (SBI)",
            "weight": 0.35,
            "messages": [
                "URGENT: Your SBI account will be blocked in 2 hours! Verify immediately.",
                "I am Officer Rajesh from SBI Fraud Dept. My number is +91-9876543210.",
                "Send Rs 500 to fraud.officer@sbi to verify your account.",
                "Account number: 12345678901234, IFSC: SBIN0001234",
                "Share OTP to complete verification. This is very urgent!",
                "Sir please cooperate. Your account security is at risk.",
                "Last warning! Act now or face legal consequences.",
                "I am sending you official link for verification.",
            ],
            "fake_data": {
                "phoneNumbers": ["+91-9876543210", "9876543210"],
                "upiIds": ["fraud.officer@sbi"],
                "bankAccounts": ["12345678901234"],
                "ifscCodes": ["SBIN0001234"],
            },
        },
        {
            "name": "UPI Cashback Scam",
            "weight": 0.35,
            "messages": [
                "Congratulations! You won Rs 50,000 cashback! Claim now!",
                "I am from Paytm Rewards. Call me at +91-8765432109",
                "Send Rs 99 processing fee to cashback.claim@ybl",
                "Click to claim: http://paytm-cashback.xyz/win",
                "Hurry! Offer expires in 10 minutes!",
                "Sir this is genuine Paytm offer. Don't miss!",
                "Many customers already claimed. You are lucky winner!",
                "Final reminder. Your cashback will be cancelled.",
            ],
            "fake_data": {
                "phoneNumbers": ["+91-8765432109", "8765432109"],
                "upiIds": ["cashback.claim@ybl"],
                "phishingLinks": ["http://paytm-cashback.xyz/win"],
            },
        },
        {
            "name": "Amazon Phishing",
            "weight": 0.30,
            "messages": [
                "Amazon Alert: Order #AMZ-456789 worth Rs 45,999 placed. Cancel: http://amazon-order.tk",
                "Call Amazon Support at +91-7654321098 to cancel.",
                "Email us at support@amazon-help.xyz for refund.",
                "Login here: http://secure-amazon.ml/cancel",
                "Order ships in 1 hour if not cancelled!",
                "We need your card details for cancellation.",
                "Sir please act fast. This is urgent matter.",
                "Share OTP to confirm order cancellation.",
            ],
            "fake_data": {
                "phoneNumbers": ["+91-7654321098", "7654321098"],
                "emailAddresses": ["support@amazon-help.xyz"],
                "phishingLinks": ["http://amazon-order.tk", "http://secure-amazon.ml/cancel"],
            },
        },
    ]
    
    results = []
    for s in scenarios:
        result = test_scenario(s["name"], s["weight"], s["messages"], s["fake_data"])
        results.append(result)
    
    # Final calculation
    print_line()
    print(" FINAL RESULTS")
    print_line()
    
    weighted_score = sum(r["total"] * r["weight"] for r in results)
    
    print(f"\n{'Scenario':<25} {'Score':<12} {'Weight':<10} {'Contribution'}")
    print("-" * 60)
    for r in results:
        contrib = r["total"] * r["weight"]
        print(f"{r['name']:<25} {r['total']:>5.1f}/100   {r['weight']*100:>4.0f}%      {contrib:>6.2f}")
    print("-" * 60)
    print(f"{'Weighted Score:':<25} {weighted_score:>5.1f}/100")
    
    code_quality = 9.0
    scenario_portion = weighted_score * 0.9
    final_score = scenario_portion + code_quality
    
    print(f"\n{'-'*40}")
    print(f"Scenario Portion (90%):  {scenario_portion:.1f}")
    print(f"Code Quality (10%):      {code_quality:.1f}")
    print(f"{'-'*40}")
    print(f"FINAL SCORE:             {final_score:.1f}/100")
    print(f"{'-'*40}")
    
    # Assessment
    if final_score >= 95:
        print("\n✓ EXCELLENT - Top-tier! Strong selection chance from 40K participants!")
    elif final_score >= 90:
        print("\n✓ VERY GOOD - Highly competitive. High probability of advancement.")
    elif final_score >= 85:
        print("\n✓ GOOD - Above average. Should qualify in most cases.")
    elif final_score >= 80:
        print("\n! FAIR - Average. May need minor improvements.")
    else:
        print("\n✗ NEEDS WORK - Below threshold. Focus on weak areas.")
    
    # Save results
    with open("tests/guvi_quick_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "scenarios": [{"name": r["name"], "weight": r["weight"], "score": r["total"]} for r in results],
            "weighted_score": weighted_score,
            "final_score": final_score,
        }, f, indent=2)
    
    print(f"\nResults saved to: tests/guvi_quick_results.json")
    print_line()


if __name__ == "__main__":
    main()

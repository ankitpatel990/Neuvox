"""
GUVI Hackathon Evaluation Simulation Test Suite

This test file simulates the EXACT evaluation process used by GUVI to score
Honeypot API submissions. It tests all scoring criteria:

1. Scam Detection (20 points)
2. Extracted Intelligence (30 points)
3. Conversation Quality (30 points)
4. Engagement Quality (10 points)
5. Response Structure (10 points)

Total: 100 points per scenario

Run with: python tests/guvi_evaluation_test.py
"""

import requests
import json
import time
import uuid
import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "sVlunn0LMQZNAkRYqZB-f1-Ye7rgzjB_E3b1gNxnUV8"

# GUVI Evaluation Constants
MAX_TURNS = 10
REQUEST_TIMEOUT = 30


@dataclass
class ScenarioResult:
    """Result of a single scenario evaluation."""
    scenario_name: str
    scenario_weight: float
    scam_detection_score: float = 0.0
    intelligence_score: float = 0.0
    conversation_quality_score: float = 0.0
    engagement_quality_score: float = 0.0
    response_structure_score: float = 0.0
    total_score: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)


@dataclass
class TestScenario:
    """Definition of a test scenario."""
    name: str
    scam_type: str
    weight: float
    initial_message: str
    fake_data: Dict[str, List[str]]
    follow_up_messages: List[str]
    metadata: Dict[str, str]


# =============================================================================
# TEST SCENARIOS - Simulating GUVI's diverse scam scenarios
# =============================================================================

SCENARIOS = [
    TestScenario(
        name="Bank Fraud Detection",
        scam_type="bank_fraud",
        weight=0.35,
        initial_message="URGENT: Your SBI account has been compromised and will be blocked within 2 hours. To prevent this, please verify your identity immediately. Share your OTP to unblock your account. This is an official notice from SBI Fraud Department.",
        fake_data={
            "phoneNumbers": ["+91-9876543210"],
            "bankAccounts": ["12345678901234"],
            "upiIds": ["fraud.officer@sbi"],
            "ifscCodes": ["SBIN0001234"],
        },
        follow_up_messages=[
            "I am Senior Fraud Officer Rajesh Kumar from SBI. My employee ID is SBI-FD-78956. You can verify me.",
            "Sir, your account number ending with 1234 has suspicious transactions. Send OTP to verify.",
            "For verification, please note my official contact: +91-9876543210. Call me if needed.",
            "Transfer verification fee of Rs 500 to fraud.officer@sbi to complete the process.",
            "Our bank account for fee deposit: 12345678901234, IFSC: SBIN0001234",
            "Sir, this is very urgent. Your account will be permanently blocked!",
            "I'm sending you the verification link now. Please click immediately.",
            "Last warning! Share OTP now or face legal consequences.",
        ],
        metadata={"channel": "SMS", "language": "English", "locale": "IN"},
    ),
    TestScenario(
        name="UPI Fraud Multi-turn",
        scam_type="upi_fraud",
        weight=0.35,
        initial_message="Congratulations! You have won Rs 50,000 cashback from Paytm! To claim your reward, please verify your UPI details. This offer expires in 30 minutes!",
        fake_data={
            "phoneNumbers": ["+91-8765432109"],
            "upiIds": ["cashback.reward@paytm", "winner.claim@ybl"],
            "phishingLinks": ["http://paytm-cashback.xyz/claim"],
        },
        follow_up_messages=[
            "Dear winner, I am calling from Paytm Rewards Team. My number is +91-8765432109.",
            "To process your Rs 50,000 cashback, please send Rs 99 processing fee to cashback.reward@paytm",
            "Alternatively, you can use winner.claim@ybl for faster processing.",
            "Click this secure link to claim: http://paytm-cashback.xyz/claim",
            "Hurry! Only 15 minutes left. Don't miss this golden opportunity!",
            "Sir, thousands have already claimed. Just small fee and you get 50,000!",
            "This is final reminder. After this, your cashback will be given to someone else.",
            "Please cooperate sir. This is 100% genuine Paytm offer.",
        ],
        metadata={"channel": "WhatsApp", "language": "English", "locale": "IN"},
    ),
    TestScenario(
        name="Phishing Link Detection",
        scam_type="phishing",
        weight=0.30,
        initial_message="Amazon Order Alert: Your order #AMZ-789456123 worth Rs 45,999 has been placed. If you did not place this order, click here to cancel immediately: http://amazon-order-cancel.tk/verify",
        fake_data={
            "phoneNumbers": ["+91-7654321098"],
            "emailAddresses": ["support@amazon-helpdesk.xyz"],
            "phishingLinks": ["http://amazon-order-cancel.tk/verify", "http://secure-amazon.ml/login"],
            "orderNumbers": ["AMZ-789456123"],
        },
        follow_up_messages=[
            "This is Amazon Customer Support. Call +91-7654321098 to cancel this fraudulent order.",
            "Email us at support@amazon-helpdesk.xyz with your bank details for refund.",
            "For immediate cancellation, login here: http://secure-amazon.ml/login",
            "Your order AMZ-789456123 will be shipped in 2 hours if not cancelled!",
            "We need your card details to verify and process the cancellation.",
            "Sir this is genuine Amazon support. Many customers have been scammed recently.",
            "Please act fast. Once shipped, we cannot help you.",
            "Share OTP received on your phone to confirm cancellation.",
        ],
        metadata={"channel": "Email", "language": "English", "locale": "IN"},
    ),
]


class GUVIEvaluator:
    """Simulates GUVI's evaluation system."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
        }
    
    def run_scenario(self, scenario: TestScenario) -> ScenarioResult:
        """Run a complete scenario evaluation."""
        result = ScenarioResult(
            scenario_name=scenario.name,
            scenario_weight=scenario.weight,
        )
        
        print(f"\n{'='*70}")
        print(f"SCENARIO: {scenario.name} (Weight: {scenario.weight*100:.0f}%)")
        print(f"{'='*70}")
        
        session_id = str(uuid.uuid4())
        conversation_history = []
        all_responses = []
        start_time = time.time()
        
        try:
            # Run multi-turn conversation
            messages = [scenario.initial_message] + scenario.follow_up_messages
            
            for turn, scammer_message in enumerate(messages[:MAX_TURNS], 1):
                print(f"\n--- Turn {turn} ---")
                print(f"Scammer: {scammer_message[:80]}...")
                
                # Build GUVI format request
                request_payload = self._build_guvi_request(
                    session_id=session_id,
                    message=scammer_message,
                    conversation_history=conversation_history,
                    metadata=scenario.metadata,
                    turn=turn,
                )
                
                # Send request
                response = self._send_request(request_payload)
                
                if response is None:
                    result.errors.append(f"Turn {turn}: Request failed")
                    continue
                
                all_responses.append(response)
                
                # Extract reply
                reply = response.get("reply") or response.get("message") or response.get("text", "")
                print(f"Agent: {reply[:80]}..." if reply else "Agent: [No reply]")
                
                # Update conversation history
                conversation_history.append({
                    "sender": "scammer",
                    "text": scammer_message,
                    "timestamp": int(time.time() * 1000),
                })
                conversation_history.append({
                    "sender": "user",
                    "text": reply,
                    "timestamp": int(time.time() * 1000),
                })
                
                time.sleep(0.5)  # Small delay between turns
            
            engagement_duration = int(time.time() - start_time)
            
            # Get final response for scoring
            final_response = all_responses[-1] if all_responses else {}
            
            # Calculate scores
            result.scam_detection_score = self._score_scam_detection(final_response)
            result.intelligence_score = self._score_intelligence(final_response, scenario.fake_data)
            result.conversation_quality_score = self._score_conversation_quality(
                all_responses, conversation_history
            )
            result.engagement_quality_score = self._score_engagement_quality(
                final_response, engagement_duration, len(conversation_history)
            )
            result.response_structure_score = self._score_response_structure(final_response)
            
            result.total_score = (
                result.scam_detection_score +
                result.intelligence_score +
                result.conversation_quality_score +
                result.engagement_quality_score +
                result.response_structure_score
            )
            
            result.details = {
                "turns_completed": len(all_responses),
                "engagement_duration_seconds": engagement_duration,
                "total_messages": len(conversation_history),
                "final_response": final_response,
            }
            
        except Exception as e:
            result.errors.append(f"Scenario error: {str(e)}")
            print(f"ERROR: {e}")
        
        return result
    
    def _build_guvi_request(
        self,
        session_id: str,
        message: str,
        conversation_history: List[Dict],
        metadata: Dict[str, str],
        turn: int,
    ) -> Dict:
        """Build request in GUVI's exact format."""
        return {
            "sessionId": session_id,
            "message": {
                "sender": "scammer",
                "text": message,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
            "conversationHistory": conversation_history,
            "metadata": metadata,
        }
    
    def _send_request(self, payload: Dict) -> Optional[Dict]:
        """Send request to API."""
        try:
            response = requests.post(
                f"{self.base_url}/api/v1/honeypot/engage",
                json=payload,
                headers=self.headers,
                timeout=REQUEST_TIMEOUT,
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"  [HTTP {response.status_code}] {response.text[:100]}")
                return None
                
        except requests.exceptions.Timeout:
            print("  [TIMEOUT] Request exceeded 30 seconds")
            return None
        except Exception as e:
            print(f"  [ERROR] {e}")
            return None
    
    def _score_scam_detection(self, response: Dict) -> float:
        """Score scam detection (20 points max)."""
        scam_detected = response.get("scamDetected", response.get("scam_detected", False))
        return 20.0 if scam_detected else 0.0
    
    def _score_intelligence(self, response: Dict, fake_data: Dict) -> float:
        """Score intelligence extraction (30 points max)."""
        intel = response.get("extractedIntelligence", response.get("extracted_intelligence", {}))
        
        if not intel:
            return 0.0
        
        # Count total fake data fields
        total_fake_fields = sum(len(v) for v in fake_data.values())
        if total_fake_fields == 0:
            return 30.0
        
        points_per_item = 30.0 / total_fake_fields
        score = 0.0
        matched_items = []
        
        # Check each fake data type
        field_mapping = {
            "phoneNumbers": ["phoneNumbers", "phone_numbers"],
            "bankAccounts": ["bankAccounts", "bank_accounts"],
            "upiIds": ["upiIds", "upi_ids"],
            "ifscCodes": ["ifscCodes", "ifsc_codes"],
            "phishingLinks": ["phishingLinks", "phishing_links"],
            "emailAddresses": ["emailAddresses", "email_addresses"],
            "orderNumbers": ["orderNumbers", "order_numbers"],
            "caseIds": ["caseIds", "case_ids"],
            "policyNumbers": ["policyNumbers", "policy_numbers"],
        }
        
        for fake_type, fake_values in fake_data.items():
            extracted_values = []
            for key in field_mapping.get(fake_type, [fake_type]):
                extracted_values.extend(intel.get(key, []))
            
            extracted_str = str(extracted_values).lower()
            
            for fake_value in fake_values:
                # Check if fake value is found (substring match)
                fake_clean = fake_value.lower().replace("-", "").replace(" ", "")
                if fake_clean in extracted_str.replace("-", "").replace(" ", ""):
                    score += points_per_item
                    matched_items.append(fake_value)
        
        print(f"  Intelligence matched: {len(matched_items)}/{total_fake_fields}")
        return min(score, 30.0)
    
    def _score_conversation_quality(
        self,
        responses: List[Dict],
        conversation_history: List[Dict],
    ) -> float:
        """Score conversation quality (30 points max)."""
        score = 0.0
        
        # 1. Turn Count (8 points max)
        turn_count = len(responses)
        if turn_count >= 8:
            score += 8.0
        elif turn_count >= 6:
            score += 6.0
        elif turn_count >= 4:
            score += 3.0
        
        # 2. Questions Asked (4 points max)
        agent_messages = [
            h.get("text", "") for h in conversation_history
            if h.get("sender") == "user"
        ]
        questions_asked = sum(1 for m in agent_messages if "?" in m)
        if questions_asked >= 5:
            score += 4.0
        elif questions_asked >= 3:
            score += 2.0
        elif questions_asked >= 1:
            score += 1.0
        
        # 3. Relevant Questions (3 points max)
        investigative_patterns = [
            r"upi", r"phone", r"number", r"account", r"ifsc",
            r"bank", r"name", r"id", r"employee", r"verify",
        ]
        relevant_count = 0
        for msg in agent_messages:
            msg_lower = msg.lower()
            if any(re.search(p, msg_lower) for p in investigative_patterns):
                relevant_count += 1
        
        if relevant_count >= 3:
            score += 3.0
        elif relevant_count >= 2:
            score += 2.0
        elif relevant_count >= 1:
            score += 1.0
        
        # 4. Red Flag Identification (8 points max)
        last_response = responses[-1] if responses else {}
        conv_quality = last_response.get("conversationQuality", {})
        red_flags_count = conv_quality.get("redFlagsCount", 0)
        
        if red_flags_count == 0:
            # Try to count from agentNotes
            agent_notes = last_response.get("agentNotes", "")
            red_flags_count = agent_notes.lower().count("red flag")
        
        if red_flags_count >= 5:
            score += 8.0
        elif red_flags_count >= 3:
            score += 5.0
        elif red_flags_count >= 1:
            score += 2.0
        
        # 5. Information Elicitation (7 points max)
        elicitation_count = conv_quality.get("elicitationAttempts", 0)
        if elicitation_count == 0:
            elicitation_count = conv_quality.get("questionsAsked", 0)
        
        score += min(elicitation_count * 1.5, 7.0)
        
        print(f"  Turns: {turn_count}, Questions: {questions_asked}, Red flags: {red_flags_count}")
        return min(score, 30.0)
    
    def _score_engagement_quality(
        self,
        response: Dict,
        actual_duration: int,
        total_messages: int,
    ) -> float:
        """Score engagement quality (10 points max)."""
        score = 0.0
        
        # Get reported metrics
        metrics = response.get("engagementMetrics", {})
        duration = metrics.get("engagementDurationSeconds", actual_duration)
        messages = metrics.get("totalMessagesExchanged", total_messages // 2)
        
        # Duration scoring
        if duration > 0:
            score += 1.0
        if duration > 60:
            score += 2.0
        if duration > 180:
            score += 1.0
        
        # Messages scoring
        if messages > 0:
            score += 2.0
        if messages >= 5:
            score += 3.0
        if messages >= 10:
            score += 1.0
        
        print(f"  Duration: {duration}s, Messages: {messages}")
        return min(score, 10.0)
    
    def _score_response_structure(self, response: Dict) -> float:
        """Score response structure (10 points max)."""
        score = 0.0
        missing_required = []
        
        # Required fields (2 points each, -1 penalty if missing)
        required_fields = ["sessionId", "scamDetected", "extractedIntelligence"]
        for field in required_fields:
            snake_case = field[0].lower() + field[1:].replace("D", "_d").replace("I", "_i")
            if field in response or snake_case in response:
                score += 2.0
            else:
                missing_required.append(field)
                score -= 1.0
        
        # Optional fields (1 point each)
        optional_fields = [
            ("totalMessagesExchanged", "engagementDurationSeconds"),
            ("agentNotes",),
            ("scamType",),
            ("confidenceLevel",),
        ]
        
        for field_group in optional_fields:
            for field in field_group:
                snake_case = re.sub(r'([A-Z])', r'_\1', field).lower().lstrip('_')
                if field in response or snake_case in response:
                    score += 1.0
                    break
        
        if missing_required:
            print(f"  Missing required: {missing_required}")
        
        return max(score, 0.0)


def run_health_check(base_url: str) -> bool:
    """Check if API is running."""
    try:
        response = requests.get(f"{base_url}/api/v1/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"API Status: {data.get('status', 'unknown')}")
            print(f"Version: {data.get('version', 'unknown')}")
            return True
    except Exception as e:
        print(f"Health check failed: {e}")
    return False


def print_score_breakdown(result: ScenarioResult):
    """Print detailed score breakdown."""
    print(f"\n{'-'*50}")
    print(f"SCORE BREAKDOWN: {result.scenario_name}")
    print(f"{'-'*50}")
    print(f"  Scam Detection:       {result.scam_detection_score:5.1f} / 20.0")
    print(f"  Intelligence:         {result.intelligence_score:5.1f} / 30.0")
    print(f"  Conversation Quality: {result.conversation_quality_score:5.1f} / 30.0")
    print(f"  Engagement Quality:   {result.engagement_quality_score:5.1f} / 10.0")
    print(f"  Response Structure:   {result.response_structure_score:5.1f} / 10.0")
    print(f"  {'-'*40}")
    print(f"  TOTAL:                {result.total_score:5.1f} / 100.0")
    print(f"  Weighted ({result.scenario_weight*100:.0f}%):      {result.total_score * result.scenario_weight:5.1f}")
    
    if result.errors:
        print(f"\n  ERRORS:")
        for error in result.errors:
            print(f"    - {error}")


def main():
    """Run complete GUVI-style evaluation."""
    print("\n" + "="*70)
    print("GUVI HACKATHON EVALUATION SIMULATION")
    print("ScamShield AI - Honeypot API Testing")
    print("="*70)
    print(f"API URL: {API_BASE_URL}")
    print(f"Scenarios: {len(SCENARIOS)}")
    print(f"Max turns per scenario: {MAX_TURNS}")
    
    # Health check
    print("\n--- Health Check ---")
    if not run_health_check(API_BASE_URL):
        print("ERROR: API is not running. Please start the server first.")
        print("Run: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return
    
    # Initialize evaluator
    evaluator = GUVIEvaluator(API_BASE_URL, API_KEY)
    
    # Run all scenarios
    results: List[ScenarioResult] = []
    
    for scenario in SCENARIOS:
        result = evaluator.run_scenario(scenario)
        results.append(result)
        print_score_breakdown(result)
    
    # Calculate final score
    print("\n" + "="*70)
    print("FINAL EVALUATION RESULTS")
    print("="*70)
    
    weighted_scenario_score = sum(r.total_score * r.scenario_weight for r in results)
    
    print(f"\n{'Scenario':<30} {'Score':<10} {'Weight':<10} {'Contribution':<15}")
    print("-"*65)
    
    for result in results:
        contribution = result.total_score * result.scenario_weight
        print(f"{result.scenario_name:<30} {result.total_score:>5.1f}/100  {result.scenario_weight*100:>5.0f}%     {contribution:>10.2f}")
    
    print("-"*65)
    print(f"{'Weighted Scenario Score:':<30} {weighted_scenario_score:>5.1f}/100")
    
    # Estimate code quality (assumed 9/10 based on analysis)
    code_quality_estimate = 9.0
    
    scenario_portion = weighted_scenario_score * 0.9
    final_score = scenario_portion + code_quality_estimate
    
    print(f"\n{'='*50}")
    print("FINAL SCORE CALCULATION (GUVI Formula)")
    print(f"{'='*50}")
    print(f"Scenario Score:        {weighted_scenario_score:.1f}")
    print(f"Scenario Portion (90%): {scenario_portion:.1f}")
    print(f"Code Quality (10%):    {code_quality_estimate:.1f}")
    print(f"{'-'*50}")
    print(f"FINAL SCORE:           {final_score:.1f} / 100")
    print(f"{'='*50}")
    
    # Performance assessment
    print("\n--- COMPETITION ASSESSMENT ---")
    if final_score >= 95:
        print("EXCELLENT: Top tier performance. Strong chance of selection!")
    elif final_score >= 90:
        print("VERY GOOD: Competitive score. High probability of advancement.")
    elif final_score >= 85:
        print("GOOD: Above average. May qualify depending on competition.")
    elif final_score >= 80:
        print("FAIR: Average performance. Needs improvement for selection.")
    else:
        print("NEEDS WORK: Below competitive threshold. Significant improvements needed.")
    
    # Save results
    results_file = "tests/guvi_evaluation_results.json"
    with open(results_file, "w") as f:
        json.dump({
            "timestamp": datetime.utcnow().isoformat(),
            "api_url": API_BASE_URL,
            "scenarios": [
                {
                    "name": r.scenario_name,
                    "weight": r.scenario_weight,
                    "scores": {
                        "scam_detection": r.scam_detection_score,
                        "intelligence": r.intelligence_score,
                        "conversation_quality": r.conversation_quality_score,
                        "engagement_quality": r.engagement_quality_score,
                        "response_structure": r.response_structure_score,
                        "total": r.total_score,
                    },
                    "errors": r.errors,
                }
                for r in results
            ],
            "weighted_scenario_score": weighted_scenario_score,
            "code_quality_estimate": code_quality_estimate,
            "final_score": final_score,
        }, f, indent=2)
    
    print(f"\nResults saved to: {results_file}")


if __name__ == "__main__":
    main()

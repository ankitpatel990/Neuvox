# Evaluation Specification: ScamShield AI
## Metrics, Computation Methods, and Testing Framework

**Version:** 1.0  
**Date:** January 26, 2026  
**Owner:** QA & Evaluation Team  
**Related Documents:** FRD.md, DATA_SPEC.md, API_CONTRACT.md

---

## TABLE OF CONTENTS
1. [Evaluation Overview](#evaluation-overview)
2. [Detection Metrics](#detection-metrics)
3. [Extraction Metrics](#extraction-metrics)
4. [Engagement Metrics](#engagement-metrics)
5. [Performance Metrics](#performance-metrics)
6. [Computation Methods](#computation-methods)
7. [Testing Framework](#testing-framework)
8. [Competition Scoring (Predicted)](#competition-scoring-predicted)

---

## EVALUATION OVERVIEW

### Evaluation Objectives

1. **Functional Correctness:** System meets FRD requirements
2. **Performance:** Response time, throughput within SLAs
3. **Quality:** Detection accuracy, extraction precision/recall
4. **Robustness:** Handles edge cases, adversarial inputs
5. **Competition Readiness:** Meets judging criteria

### Evaluation Phases

| Phase | Timeline | Focus | Pass Criteria |
|-------|----------|-------|---------------|
| **Unit Testing** | Days 3-9 | Individual components | >80% code coverage |
| **Integration Testing** | Day 8 | End-to-end flows | All API endpoints functional |
| **Performance Testing** | Day 9 | Load, latency | <2s p95 latency, 100 req/min |
| **Acceptance Testing** | Day 10 | Requirements validation | All FRD acceptance criteria met |
| **Red Team Testing** | Day 10 | Adversarial scenarios | >80% red team tests passed |
| **Pre-Submission** | Day 11 | Final validation | >90% detection accuracy |

---

## DETECTION METRICS

### Metric 1: Scam Detection Accuracy

**Definition:** Proportion of messages correctly classified as scam or legitimate.

**Formula:**
```
Accuracy = (TP + TN) / (TP + TN + FP + FN)

Where:
- TP (True Positives): Scams correctly identified
- TN (True Negatives): Legitimate messages correctly identified
- FP (False Positives): Legitimate messages incorrectly flagged as scams
- FN (False Negatives): Scams missed
```

**Target:** ≥90%

**Computation:**
```python
def compute_detection_accuracy(predictions: List[dict], ground_truth: List[dict]) -> float:
    """
    Compute scam detection accuracy.
    
    Args:
        predictions: List of {"id": str, "scam_detected": bool}
        ground_truth: List of {"id": str, "label": "scam"|"legitimate"}
    
    Returns:
        Accuracy score (0.0-1.0)
    """
    assert len(predictions) == len(ground_truth), "Mismatched lengths"
    
    # Align by ID
    pred_map = {p['id']: p['scam_detected'] for p in predictions}
    gt_map = {g['id']: (g['label'] == 'scam') for g in ground_truth}
    
    correct = sum(1 for id in pred_map if pred_map[id] == gt_map[id])
    total = len(pred_map)
    
    return correct / total if total > 0 else 0.0

# Example usage
predictions = [
    {"id": "test_001", "scam_detected": True},
    {"id": "test_002", "scam_detected": False},
    {"id": "test_003", "scam_detected": True}
]

ground_truth = [
    {"id": "test_001", "label": "scam"},
    {"id": "test_002", "label": "legitimate"},
    {"id": "test_003", "label": "scam"}
]

accuracy = compute_detection_accuracy(predictions, ground_truth)
print(f"Accuracy: {accuracy:.2%}")  # Expected: 100%
```

---

### Metric 2: Precision

**Definition:** Of all messages flagged as scams, what proportion are actual scams?

**Formula:**
```
Precision = TP / (TP + FP)
```

**Target:** ≥85%

**Significance:** High precision minimizes false alarms (legitimate messages flagged as scams).

**Computation:**
```python
def compute_precision(predictions: List[dict], ground_truth: List[dict]) -> float:
    """Compute precision for scam detection"""
    pred_map = {p['id']: p['scam_detected'] for p in predictions}
    gt_map = {g['id']: (g['label'] == 'scam') for g in ground_truth}
    
    tp = sum(1 for id in pred_map if pred_map[id] and gt_map[id])
    fp = sum(1 for id in pred_map if pred_map[id] and not gt_map[id])
    
    return tp / (tp + fp) if (tp + fp) > 0 else 0.0
```

---

### Metric 3: Recall (Sensitivity)

**Definition:** Of all actual scams, what proportion are detected?

**Formula:**
```
Recall = TP / (TP + FN)
```

**Target:** ≥90%

**Significance:** High recall ensures few scams are missed.

**Computation:**
```python
def compute_recall(predictions: List[dict], ground_truth: List[dict]) -> float:
    """Compute recall for scam detection"""
    pred_map = {p['id']: p['scam_detected'] for p in predictions}
    gt_map = {g['id']: (g['label'] == 'scam') for g in ground_truth}
    
    tp = sum(1 for id in pred_map if pred_map[id] and gt_map[id])
    fn = sum(1 for id in pred_map if not pred_map[id] and gt_map[id])
    
    return tp / (tp + fn) if (tp + fn) > 0 else 0.0
```

---

### Metric 4: F1-Score

**Definition:** Harmonic mean of precision and recall.

**Formula:**
```
F1 = 2 * (Precision * Recall) / (Precision + Recall)
```

**Target:** ≥87%

**Computation:**
```python
def compute_f1_score(precision: float, recall: float) -> float:
    """Compute F1-score from precision and recall"""
    if precision + recall == 0:
        return 0.0
    return 2 * (precision * recall) / (precision + recall)
```

---

### Metric 5: Confidence Calibration

**Definition:** How well do confidence scores correlate with actual accuracy?

**Formula:**
```
Expected Calibration Error (ECE) = Σ (|accuracy_bin - avg_confidence_bin|) × (bin_size / total)

For bins: [0-0.1], [0.1-0.2], ..., [0.9-1.0]
```

**Target:** ECE <0.1 (well-calibrated)

**Computation:**
```python
def compute_ece(predictions: List[dict], ground_truth: List[dict], n_bins: int = 10) -> float:
    """
    Compute Expected Calibration Error.
    
    Predictions must include "confidence" field.
    """
    pred_map = {p['id']: (p['scam_detected'], p['confidence']) for p in predictions}
    gt_map = {g['id']: (g['label'] == 'scam') for g in ground_truth}
    
    bins = [[] for _ in range(n_bins)]
    
    for id in pred_map:
        pred, conf = pred_map[id]
        actual = gt_map[id]
        correct = (pred == actual)
        
        bin_idx = min(int(conf * n_bins), n_bins - 1)
        bins[bin_idx].append((conf, correct))
    
    ece = 0.0
    total = len(pred_map)
    
    for bin_samples in bins:
        if len(bin_samples) == 0:
            continue
        
        avg_conf = sum(conf for conf, _ in bin_samples) / len(bin_samples)
        accuracy = sum(1 for _, correct in bin_samples if correct) / len(bin_samples)
        
        ece += abs(accuracy - avg_conf) * (len(bin_samples) / total)
    
    return ece
```

---

### Metric 6: Language-Specific Accuracy

**Definition:** Detection accuracy broken down by language.

**Target:** 
- English: ≥92%
- Hindi: ≥88%
- Hinglish: ≥85%
- Fairness: <5% difference between languages

**Computation:**
```python
def compute_language_specific_accuracy(predictions: List[dict], ground_truth: List[dict]) -> dict:
    """Compute accuracy per language"""
    from collections import defaultdict
    
    lang_correct = defaultdict(int)
    lang_total = defaultdict(int)
    
    pred_map = {p['id']: p for p in predictions}
    gt_map = {g['id']: g for g in ground_truth}
    
    for id in pred_map:
        lang = gt_map[id]['language']
        pred_scam = pred_map[id]['scam_detected']
        actual_scam = (gt_map[id]['label'] == 'scam')
        
        lang_total[lang] += 1
        if pred_scam == actual_scam:
            lang_correct[lang] += 1
    
    return {
        lang: lang_correct[lang] / lang_total[lang] if lang_total[lang] > 0 else 0.0
        for lang in lang_total
    }

# Check fairness
def check_language_fairness(lang_accuracies: dict, threshold: float = 0.05) -> bool:
    """Ensure accuracy difference between languages is within threshold"""
    accuracies = list(lang_accuracies.values())
    max_diff = max(accuracies) - min(accuracies)
    return max_diff < threshold
```

---

## EXTRACTION METRICS

### Metric 7: Extraction Precision (per entity type)

**Definition:** Of all extracted entities, what proportion are correct?

**Formula:**
```
Precision_entity = |Extracted ∩ Ground_Truth| / |Extracted|

For entity types: upi_ids, bank_accounts, ifsc_codes, phone_numbers, phishing_links
```

**Target:** 
- UPI IDs: ≥90%
- Bank Accounts: ≥85%
- IFSC Codes: ≥95%
- Phone Numbers: ≥90%
- Phishing Links: ≥95%

**Computation:**
```python
def compute_extraction_precision(extracted: dict, ground_truth: dict) -> dict:
    """
    Compute precision for each entity type.
    
    Args:
        extracted: {"upi_ids": [...], "bank_accounts": [...], ...}
        ground_truth: Same structure
    
    Returns:
        {"upi_ids": precision, "bank_accounts": precision, ...}
    """
    precisions = {}
    
    for entity_type in ['upi_ids', 'bank_accounts', 'ifsc_codes', 'phone_numbers', 'phishing_links']:
        extracted_set = set(extracted.get(entity_type, []))
        gt_set = set(ground_truth.get(entity_type, []))
        
        if len(extracted_set) == 0:
            precisions[entity_type] = 1.0 if len(gt_set) == 0 else 0.0
        else:
            correct = len(extracted_set & gt_set)
            precisions[entity_type] = correct / len(extracted_set)
    
    return precisions
```

---

### Metric 8: Extraction Recall (per entity type)

**Definition:** Of all actual entities, what proportion are extracted?

**Formula:**
```
Recall_entity = |Extracted ∩ Ground_Truth| / |Ground_Truth|
```

**Target:** 
- UPI IDs: ≥85%
- Bank Accounts: ≥80%
- IFSC Codes: ≥90%
- Phone Numbers: ≥85%
- Phishing Links: ≥90%

**Computation:**
```python
def compute_extraction_recall(extracted: dict, ground_truth: dict) -> dict:
    """Compute recall for each entity type"""
    recalls = {}
    
    for entity_type in ['upi_ids', 'bank_accounts', 'ifsc_codes', 'phone_numbers', 'phishing_links']:
        extracted_set = set(extracted.get(entity_type, []))
        gt_set = set(ground_truth.get(entity_type, []))
        
        if len(gt_set) == 0:
            recalls[entity_type] = 1.0 if len(extracted_set) == 0 else 0.0
        else:
            correct = len(extracted_set & gt_set)
            recalls[entity_type] = correct / len(gt_set)
    
    return recalls
```

---

### Metric 9: Overall Extraction F1-Score

**Definition:** Weighted average F1-score across all entity types.

**Weights:**
```python
ENTITY_WEIGHTS = {
    'upi_ids': 0.30,
    'bank_accounts': 0.30,
    'ifsc_codes': 0.20,
    'phone_numbers': 0.10,
    'phishing_links': 0.10
}
```

**Target:** ≥85%

**Computation:**
```python
def compute_overall_extraction_f1(precisions: dict, recalls: dict, weights: dict = ENTITY_WEIGHTS) -> float:
    """Compute weighted F1-score across entity types"""
    f1_scores = {}
    
    for entity_type in weights:
        p = precisions.get(entity_type, 0.0)
        r = recalls.get(entity_type, 0.0)
        
        if p + r == 0:
            f1_scores[entity_type] = 0.0
        else:
            f1_scores[entity_type] = 2 * (p * r) / (p + r)
    
    weighted_f1 = sum(f1_scores[entity] * weights[entity] for entity in weights)
    return weighted_f1
```

---

### Metric 10: Extraction Confidence Accuracy

**Definition:** Correlation between extraction_confidence score and actual precision.

**Target:** Pearson correlation >0.7

**Computation:**
```python
from scipy.stats import pearsonr

def evaluate_extraction_confidence(test_results: List[dict]) -> float:
    """
    Evaluate extraction confidence calibration.
    
    test_results: [
        {
            "extraction_confidence": 0.85,
            "actual_precision": 0.90
        },
        ...
    ]
    """
    confidences = [r['extraction_confidence'] for r in test_results]
    precisions = [r['actual_precision'] for r in test_results]
    
    correlation, p_value = pearsonr(confidences, precisions)
    return correlation
```

---

## ENGAGEMENT METRICS

### Metric 11: Average Conversation Length

**Definition:** Mean number of turns per conversation.

**Target:** ≥10 turns (demonstrates sustained engagement)

**Computation:**
```python
def compute_avg_conversation_length(conversations: List[dict]) -> float:
    """
    conversations: [{"session_id": str, "turn_count": int}, ...]
    """
    if len(conversations) == 0:
        return 0.0
    
    total_turns = sum(conv['turn_count'] for conv in conversations)
    return total_turns / len(conversations)
```

---

### Metric 12: Intelligence Extraction Rate

**Definition:** Proportion of conversations that extract at least one intelligence entity.

**Target:** ≥70%

**Computation:**
```python
def compute_extraction_rate(conversations: List[dict]) -> float:
    """
    conversations: [
        {
            "session_id": str,
            "extracted_intelligence": {
                "upi_ids": [...],
                ...
            }
        },
        ...
    ]
    """
    if len(conversations) == 0:
        return 0.0
    
    extracted_count = 0
    for conv in conversations:
        intel = conv['extracted_intelligence']
        has_intel = any(
            len(intel.get(entity_type, [])) > 0
            for entity_type in ['upi_ids', 'bank_accounts', 'ifsc_codes', 'phone_numbers', 'phishing_links']
        )
        if has_intel:
            extracted_count += 1
    
    return extracted_count / len(conversations)
```

---

### Metric 13: Persona Consistency

**Definition:** Proportion of conversations where persona remains consistent across all turns.

**Target:** ≥95%

**Computation:**
```python
def compute_persona_consistency(conversations: List[dict]) -> float:
    """
    conversations: [
        {
            "session_id": str,
            "messages": [
                {"turn": 1, "sender": "agent", "persona": "elderly"},
                {"turn": 2, "sender": "agent", "persona": "elderly"},
                ...
            ]
        },
        ...
    ]
    """
    consistent_count = 0
    
    for conv in conversations:
        agent_messages = [msg for msg in conv['messages'] if msg['sender'] == 'agent']
        if len(agent_messages) == 0:
            continue
        
        personas = [msg.get('persona') for msg in agent_messages]
        if len(set(personas)) == 1:  # All same persona
            consistent_count += 1
    
    return consistent_count / len(conversations) if len(conversations) > 0 else 0.0
```

---

### Metric 14: Engagement Quality Score

**Definition:** Composite score measuring naturalness and effectiveness of engagement.

**Components:**
1. Average turns (weight: 0.4)
2. Extraction rate (weight: 0.4)
3. Persona consistency (weight: 0.2)

**Target:** ≥0.8

**Computation:**
```python
def compute_engagement_quality(avg_turns: float, extraction_rate: float, persona_consistency: float) -> float:
    """
    Normalize and weight engagement metrics.
    
    Args:
        avg_turns: Actual average turns
        extraction_rate: 0.0-1.0
        persona_consistency: 0.0-1.0
    """
    # Normalize avg_turns (max 20)
    normalized_turns = min(avg_turns / 20, 1.0)
    
    quality_score = (
        0.4 * normalized_turns +
        0.4 * extraction_rate +
        0.2 * persona_consistency
    )
    
    return quality_score
```

---

## PERFORMANCE METRICS

### Metric 15: API Response Time

**Definition:** Time from request received to response sent.

**Targets:**
- P50 (Median): <1 second
- P95: <2 seconds
- P99: <3 seconds

**Computation:**
```python
import numpy as np

def compute_response_time_percentiles(response_times: List[float]) -> dict:
    """
    response_times: List of times in seconds
    """
    return {
        'p50': np.percentile(response_times, 50),
        'p95': np.percentile(response_times, 95),
        'p99': np.percentile(response_times, 99),
        'mean': np.mean(response_times),
        'max': np.max(response_times)
    }
```

---

### Metric 16: Throughput

**Definition:** Number of requests processed per minute.

**Target:** ≥100 requests/minute (sustained)

**Computation:**
```python
def compute_throughput(total_requests: int, time_window_seconds: float) -> float:
    """
    Returns requests per minute
    """
    return (total_requests / time_window_seconds) * 60
```

---

### Metric 17: Error Rate

**Definition:** Proportion of requests that result in errors (4xx, 5xx).

**Target:** <1%

**Computation:**
```python
def compute_error_rate(total_requests: int, error_count: int) -> float:
    """Returns error rate as proportion (0.0-1.0)"""
    return error_count / total_requests if total_requests > 0 else 0.0
```

---

### Metric 18: Uptime

**Definition:** Percentage of time service is available and healthy.

**Target:** ≥99% during competition testing window

**Computation:**
```python
def compute_uptime(total_time_seconds: float, downtime_seconds: float) -> float:
    """Returns uptime as percentage"""
    return ((total_time_seconds - downtime_seconds) / total_time_seconds) * 100
```

---

## COMPUTATION METHODS

### Complete Evaluation Pipeline

```python
import json
from typing import List, Dict, Tuple

class ScamShieldEvaluator:
    """Complete evaluation framework for ScamShield AI"""
    
    def __init__(self, api_endpoint: str):
        self.api_endpoint = api_endpoint
        self.results = {
            'detection': {},
            'extraction': {},
            'engagement': {},
            'performance': {}
        }
    
    def evaluate_detection(self, test_file: str) -> dict:
        """
        Evaluate scam detection on test dataset.
        
        Args:
            test_file: Path to JSONL test file
        
        Returns:
            Detection metrics dictionary
        """
        with open(test_file, 'r') as f:
            test_data = [json.loads(line) for line in f]
        
        predictions = []
        ground_truth = []
        response_times = []
        
        for item in test_data:
            import time
            import requests
            
            start_time = time.time()
            
            response = requests.post(
                f"{self.api_endpoint}/honeypot/engage",
                json={"message": item['message'], "language": item['language']}
            )
            
            response_time = time.time() - start_time
            response_times.append(response_time)
            
            result = response.json()
            
            predictions.append({
                'id': item['id'],
                'scam_detected': result['scam_detected'],
                'confidence': result['confidence']
            })
            
            ground_truth.append({
                'id': item['id'],
                'label': item['ground_truth']['label'],
                'language': item['language']
            })
        
        # Compute metrics
        accuracy = compute_detection_accuracy(predictions, ground_truth)
        precision = compute_precision(predictions, ground_truth)
        recall = compute_recall(predictions, ground_truth)
        f1 = compute_f1_score(precision, recall)
        ece = compute_ece(predictions, ground_truth)
        lang_acc = compute_language_specific_accuracy(predictions, ground_truth)
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'ece': ece,
            'language_accuracy': lang_acc,
            'avg_response_time': np.mean(response_times),
            'total_samples': len(test_data)
        }
    
    def evaluate_extraction(self, test_file: str) -> dict:
        """Evaluate intelligence extraction on test dataset"""
        with open(test_file, 'r') as f:
            test_data = [json.loads(line) for line in f]
        
        all_precisions = {entity: [] for entity in ['upi_ids', 'bank_accounts', 'ifsc_codes', 'phone_numbers', 'phishing_links']}
        all_recalls = {entity: [] for entity in ['upi_ids', 'bank_accounts', 'ifsc_codes', 'phone_numbers', 'phishing_links']}
        
        for item in test_data:
            response = requests.post(
                f"{self.api_endpoint}/honeypot/engage",
                json={"message": item['text'], "language": item['language']}
            )
            
            result = response.json()
            extracted = result['extracted_intelligence']
            ground_truth = item['ground_truth']
            
            precisions = compute_extraction_precision(extracted, ground_truth)
            recalls = compute_extraction_recall(extracted, ground_truth)
            
            for entity in all_precisions:
                all_precisions[entity].append(precisions[entity])
                all_recalls[entity].append(recalls[entity])
        
        # Average across all samples
        avg_precisions = {entity: np.mean(all_precisions[entity]) for entity in all_precisions}
        avg_recalls = {entity: np.mean(all_recalls[entity]) for entity in all_recalls}
        
        overall_f1 = compute_overall_extraction_f1(avg_precisions, avg_recalls)
        
        return {
            'precisions': avg_precisions,
            'recalls': avg_recalls,
            'overall_f1': overall_f1,
            'total_samples': len(test_data)
        }
    
    def evaluate_engagement(self, conversation_file: str) -> dict:
        """Evaluate multi-turn engagement quality"""
        with open(conversation_file, 'r') as f:
            conversations = [json.loads(line) for line in f]
        
        completed_conversations = []
        
        for conv in conversations:
            session_id = None
            turn_count = 0
            extracted_intel = {}
            
            for turn in conv['turns']:
                if turn['sender'] == 'scammer':
                    response = requests.post(
                        f"{self.api_endpoint}/honeypot/engage",
                        json={
                            "message": turn['message'],
                            "session_id": session_id,
                            "language": conv['language']
                        }
                    )
                    
                    result = response.json()
                    
                    if session_id is None:
                        session_id = result['session_id']
                    
                    turn_count = result['engagement']['turn_count']
                    extracted_intel = result['extracted_intelligence']
                    
                    # Check termination
                    if result['engagement']['max_turns_reached']:
                        break
            
            completed_conversations.append({
                'session_id': session_id,
                'turn_count': turn_count,
                'extracted_intelligence': extracted_intel
            })
        
        avg_turns = compute_avg_conversation_length(completed_conversations)
        extraction_rate = compute_extraction_rate(completed_conversations)
        
        return {
            'avg_conversation_length': avg_turns,
            'intelligence_extraction_rate': extraction_rate,
            'total_conversations': len(completed_conversations)
        }
    
    def evaluate_performance(self, duration_seconds: int = 60, target_rps: int = 10) -> dict:
        """Load test performance metrics"""
        import concurrent.futures
        import time
        
        test_message = "You won 10 lakh rupees! Send OTP to claim."
        response_times = []
        errors = 0
        
        def make_request():
            try:
                start = time.time()
                response = requests.post(
                    f"{self.api_endpoint}/honeypot/engage",
                    json={"message": test_message},
                    timeout=5
                )
                latency = time.time() - start
                
                if response.status_code != 200:
                    return None, 1
                return latency, 0
            except Exception:
                return None, 1
        
        start_time = time.time()
        total_requests = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            while time.time() - start_time < duration_seconds:
                future = executor.submit(make_request)
                latency, error = future.result()
                
                total_requests += 1
                if latency is not None:
                    response_times.append(latency)
                errors += error
                
                # Rate limiting
                time.sleep(1.0 / target_rps)
        
        elapsed_time = time.time() - start_time
        
        percentiles = compute_response_time_percentiles(response_times)
        throughput = compute_throughput(total_requests, elapsed_time)
        error_rate = compute_error_rate(total_requests, errors)
        
        return {
            'response_time_percentiles': percentiles,
            'throughput_rpm': throughput,
            'error_rate': error_rate,
            'total_requests': total_requests,
            'duration_seconds': elapsed_time
        }
    
    def run_full_evaluation(self) -> dict:
        """Run complete evaluation suite"""
        print("Running detection evaluation...")
        self.results['detection'] = self.evaluate_detection('data/scam_detection_test.jsonl')
        
        print("Running extraction evaluation...")
        self.results['extraction'] = self.evaluate_extraction('data/intelligence_extraction_test.jsonl')
        
        print("Running engagement evaluation...")
        self.results['engagement'] = self.evaluate_engagement('data/conversation_simulation_test.jsonl')
        
        print("Running performance evaluation...")
        self.results['performance'] = self.evaluate_performance(duration_seconds=60, target_rps=10)
        
        return self.results
    
    def generate_report(self, output_file: str = 'evaluation_report.json'):
        """Generate comprehensive evaluation report"""
        report = {
            'timestamp': datetime.utcnow().isoformat(),
            'api_endpoint': self.api_endpoint,
            'results': self.results,
            'pass_criteria': {
                'detection_accuracy': self.results['detection']['accuracy'] >= 0.90,
                'extraction_f1': self.results['extraction']['overall_f1'] >= 0.85,
                'avg_conversation_length': self.results['engagement']['avg_conversation_length'] >= 10,
                'response_time_p95': self.results['performance']['response_time_percentiles']['p95'] < 2.0,
                'error_rate': self.results['performance']['error_rate'] < 0.01
            }
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Evaluation report saved to {output_file}")
        return report
```

---

## TESTING FRAMEWORK

### Test Suite Organization

```
tests/
├── unit/
│   ├── test_detection.py
│   ├── test_extraction.py
│   ├── test_persona.py
│   └── test_utils.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_database.py
│   └── test_llm_integration.py
├── performance/
│   ├── test_load.py
│   └── test_latency.py
├── acceptance/
│   ├── test_requirements.py
│   └── test_red_team.py
└── conftest.py
```

### Sample Unit Test

```python
# tests/unit/test_detection.py
import pytest
from app.models.detector import ScamDetector

@pytest.fixture
def detector():
    return ScamDetector()

def test_english_scam_detection(detector):
    """Test English scam message detection"""
    message = "You won 10 lakh rupees! Send OTP immediately."
    
    result = detector.detect(message)
    
    assert result['scam_detected'] == True
    assert result['confidence'] >= 0.85
    assert result['language'] == 'en'

def test_hindi_scam_detection(detector):
    """Test Hindi scam message detection"""
    message = "आप गिरफ्तार हो जाएंगे। पैसे भेजें।"
    
    result = detector.detect(message)
    
    assert result['scam_detected'] == True
    assert result['confidence'] >= 0.85
    assert result['language'] == 'hi'

def test_legitimate_message(detector):
    """Test legitimate message classification"""
    message = "Hi, how are you? Let's meet for coffee."
    
    result = detector.detect(message)
    
    assert result['scam_detected'] == False
    assert result['confidence'] <= 0.3
```

### Sample Integration Test

```python
# tests/integration/test_api_endpoints.py
import pytest
import requests

@pytest.fixture
def api_url():
    return "http://localhost:8000/api/v1"

def test_engage_endpoint_scam(api_url):
    """Test /honeypot/engage with scam message"""
    response = requests.post(
        f"{api_url}/honeypot/engage",
        json={
            "message": "You won 10 lakh rupees! Send OTP.",
            "language": "auto"
        }
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data['status'] == 'success'
    assert data['scam_detected'] == True
    assert 'agent_response' in data['engagement']
    assert data['engagement']['turn_count'] == 1

def test_engage_endpoint_legitimate(api_url):
    """Test /honeypot/engage with legitimate message"""
    response = requests.post(
        f"{api_url}/honeypot/engage",
        json={
            "message": "Hi, how are you?",
            "language": "auto"
        }
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data['status'] == 'success'
    assert data['scam_detected'] == False
```

---

## COMPETITION SCORING (PREDICTED)

### Predicted Judging Rubric

Based on Challenge 2 requirements, we predict the following scoring:

| Category | Weight | Metrics | Our Target | Competitive Advantage |
|----------|--------|---------|------------|----------------------|
| **Scam Detection** | 25% | Accuracy, Precision, Recall | 92% accuracy | IndicBERT + hybrid approach |
| **Engagement Quality** | 25% | Avg turns, Naturalness | 12 turns avg | Multi-turn agentic AI |
| **Intelligence Extraction** | 30% | Precision, Recall, Coverage | 88% F1 | Hybrid NER + regex |
| **Response Time** | 10% | P95 latency | <1.8s | Optimized inference |
| **System Robustness** | 10% | Uptime, Error rate | 99.5% uptime | Production architecture |

### Expected Score Calculation

```python
def calculate_competition_score(metrics: dict) -> float:
    """
    Calculate predicted competition score.
    
    Args:
        metrics: Dictionary with all evaluation metrics
    
    Returns:
        Estimated score (0-100)
    """
    weights = {
        'detection': 0.25,
        'engagement': 0.25,
        'extraction': 0.30,
        'performance': 0.10,
        'robustness': 0.10
    }
    
    # Normalize each category to 0-1
    detection_score = min(metrics['detection']['accuracy'] / 0.90, 1.0)
    engagement_score = min(metrics['engagement']['avg_conversation_length'] / 10, 1.0)
    extraction_score = min(metrics['extraction']['overall_f1'] / 0.85, 1.0)
    performance_score = 1.0 - min(metrics['performance']['response_time_percentiles']['p95'] / 2.0, 1.0)
    robustness_score = 1.0 - metrics['performance']['error_rate']
    
    total_score = (
        weights['detection'] * detection_score +
        weights['engagement'] * engagement_score +
        weights['extraction'] * extraction_score +
        weights['performance'] * performance_score +
        weights['robustness'] * robustness_score
    ) * 100
    
    return total_score
```

---

## CONTINUOUS MONITORING

### Production Metrics Dashboard

```python
from prometheus_client import Counter, Histogram, Gauge, Summary

# Define metrics
scam_detection_total = Counter(
    'scamshield_scam_detection_total',
    'Total number of scam detections',
    ['language', 'result']
)

intelligence_extracted_total = Counter(
    'scamshield_intelligence_extracted_total',
    'Total pieces of intelligence extracted',
    ['type']
)

api_response_time = Histogram(
    'scamshield_api_response_time_seconds',
    'API response time in seconds',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0]
)

active_sessions = Gauge(
    'scamshield_active_sessions',
    'Number of active honeypot sessions'
)

detection_accuracy = Summary(
    'scamshield_detection_accuracy',
    'Detection accuracy over sliding window'
)
```

---

**Document Status:** Production Ready  
**Next Steps:** Implement evaluation framework, run tests, generate baseline metrics  
**Update Frequency:** Daily during development, hourly during competition testing

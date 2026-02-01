#!/usr/bin/env python
"""
Task 4.1 Verification Script.

Runs the verification code from TASKS.md and validates acceptance criteria:
- 1000+ total samples
- 60% scam, 40% legitimate
- 50% English, 40% Hindi, 10% Hinglish
- All samples validated
"""

import json
import os
import sys

# Set UTF-8 output encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Dataset path
DATASET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "scam_detection_train.jsonl"
)


def main():
    print("=" * 60)
    print("Task 4.1: Dataset Creation - Verification")
    print("=" * 60)
    
    # Check if file exists
    if not os.path.exists(DATASET_PATH):
        print(f"\n[ERROR] Dataset file not found: {DATASET_PATH}")
        print("Run 'python scripts/generate_dataset.py' first.")
        return 1
    
    # Load dataset (as per TASKS.md verification code)
    print(f"\nLoading: {DATASET_PATH}")
    with open(DATASET_PATH, encoding="utf-8") as f:
        data = [json.loads(line) for line in f]
    
    # Print statistics (as per TASKS.md)
    print(f"\nTotal samples: {len(data)}")
    scam_ratio = sum(1 for d in data if d['label'] == 'scam') / len(data)
    print(f"Scam ratio: {scam_ratio:.2%}")
    
    # Extended statistics
    print("\n--- Detailed Statistics ---")
    
    # Label distribution
    scam_count = sum(1 for d in data if d['label'] == 'scam')
    legit_count = sum(1 for d in data if d['label'] == 'legitimate')
    print(f"Scam: {scam_count} ({scam_count/len(data):.1%})")
    print(f"Legitimate: {legit_count} ({legit_count/len(data):.1%})")
    
    # Language distribution
    en_count = sum(1 for d in data if d['language'] == 'en')
    hi_count = sum(1 for d in data if d['language'] == 'hi')
    hinglish_count = sum(1 for d in data if d['language'] == 'hinglish')
    print(f"\nEnglish: {en_count} ({en_count/len(data):.1%})")
    print(f"Hindi: {hi_count} ({hi_count/len(data):.1%})")
    print(f"Hinglish: {hinglish_count} ({hinglish_count/len(data):.1%})")
    
    # Acceptance Criteria Validation
    print("\n" + "=" * 60)
    print("Acceptance Criteria")
    print("=" * 60)
    
    criteria_results = []
    
    # AC-1: 1000+ total samples
    ac1_pass = len(data) >= 1000
    criteria_results.append(ac1_pass)
    print(f"\nAC-1: 1000+ total samples")
    print(f"  Value: {len(data)}")
    print(f"  Status: {'PASS' if ac1_pass else 'FAIL'}")
    
    # AC-2: 60% scam, 40% legitimate
    ac2_pass = 0.55 <= scam_ratio <= 0.65
    criteria_results.append(ac2_pass)
    print(f"\nAC-2: 60% scam, 40% legitimate")
    print(f"  Scam: {scam_ratio:.1%} (expected: 55-65%)")
    print(f"  Legitimate: {1-scam_ratio:.1%} (expected: 35-45%)")
    print(f"  Status: {'PASS' if ac2_pass else 'FAIL'}")
    
    # AC-3: 50% English, 40% Hindi, 10% Hinglish
    en_ratio = en_count / len(data)
    hi_ratio = hi_count / len(data)
    hinglish_ratio = hinglish_count / len(data)
    ac3_en = 0.45 <= en_ratio <= 0.55
    ac3_hi = 0.35 <= hi_ratio <= 0.45
    ac3_hinglish = 0.05 <= hinglish_ratio <= 0.15
    ac3_pass = ac3_en and ac3_hi and ac3_hinglish
    criteria_results.append(ac3_pass)
    print(f"\nAC-3: 50% English, 40% Hindi, 10% Hinglish")
    print(f"  English: {en_ratio:.1%} (expected: 45-55%) - {'PASS' if ac3_en else 'FAIL'}")
    print(f"  Hindi: {hi_ratio:.1%} (expected: 35-45%) - {'PASS' if ac3_hi else 'FAIL'}")
    print(f"  Hinglish: {hinglish_ratio:.1%} (expected: 5-15%) - {'PASS' if ac3_hinglish else 'FAIL'}")
    print(f"  Status: {'PASS' if ac3_pass else 'FAIL'}")
    
    # AC-4: All samples validated (check schema)
    validation_errors = 0
    required_fields = ["id", "message", "language", "label", "confidence", "scam_type", "indicators", "metadata"]
    for sample in data:
        for field in required_fields:
            if field not in sample:
                validation_errors += 1
                break
        if "metadata" in sample:
            meta = sample["metadata"]
            if not all(k in meta for k in ["source", "annotator", "annotation_date", "difficulty"]):
                validation_errors += 1
    
    ac4_pass = validation_errors == 0
    criteria_results.append(ac4_pass)
    print(f"\nAC-4: All samples validated")
    print(f"  Validation errors: {validation_errors}")
    print(f"  Status: {'PASS' if ac4_pass else 'FAIL'}")
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    all_pass = all(criteria_results)
    print(f"\nAC-1 (1000+ samples): {'PASS' if criteria_results[0] else 'FAIL'}")
    print(f"AC-2 (60% scam ratio): {'PASS' if criteria_results[1] else 'FAIL'}")
    print(f"AC-3 (Language distribution): {'PASS' if criteria_results[2] else 'FAIL'}")
    print(f"AC-4 (All validated): {'PASS' if criteria_results[3] else 'FAIL'}")
    
    if all_pass:
        print("\n[SUCCESS] ALL ACCEPTANCE CRITERIA PASSED")
        return 0
    else:
        print("\n[FAILURE] SOME ACCEPTANCE CRITERIA FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())

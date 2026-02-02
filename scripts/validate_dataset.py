#!/usr/bin/env python
"""
Dataset Validation Script for ScamShield AI.

Validates the scam detection training dataset against:
- DATA_SPEC.md schema requirements
- Task 4.1 acceptance criteria:
  - 1000+ total samples
  - 60% scam, 40% legitimate
  - 50% English, 40% Hindi, 10% Hinglish
  - All samples validated

Output: Validation report with pass/fail status.
"""

import json
import os
import sys
from collections import Counter
from typing import Dict, List, Tuple

# Ensure we can import from app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Required schema fields
REQUIRED_FIELDS = ["id", "message", "language", "label", "confidence", "scam_type", "indicators", "metadata"]
REQUIRED_METADATA_FIELDS = ["source", "annotator", "annotation_date", "difficulty"]

# Valid values
VALID_LANGUAGES = {"en", "hi", "hinglish"}
VALID_LABELS = {"scam", "legitimate"}
VALID_SOURCES = {"synthetic", "real", "curated"}
VALID_ANNOTATORS = {"human", "ai"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}
VALID_SCAM_TYPES = {
    "lottery", "bank_fraud", "police_threat", "phishing",
    "courier_fraud", "government_impersonation", "upi_fraud", None
}


def load_dataset(filepath: str) -> List[Dict]:
    """Load dataset from JSONL file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Dataset not found: {filepath}")
    
    samples = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                sample = json.loads(line)
                samples.append(sample)
            except json.JSONDecodeError as e:
                print(f"  [ERROR] Line {line_num}: Invalid JSON - {e}")
    
    return samples


def validate_sample_schema(sample: Dict, sample_idx: int) -> List[str]:
    """Validate a single sample against the schema."""
    errors = []
    sample_id = sample.get("id", f"sample_{sample_idx}")
    
    # Check required fields
    for field in REQUIRED_FIELDS:
        if field not in sample:
            errors.append(f"{sample_id}: Missing required field '{field}'")
    
    # Check metadata fields
    if "metadata" in sample and isinstance(sample["metadata"], dict):
        for field in REQUIRED_METADATA_FIELDS:
            if field not in sample["metadata"]:
                errors.append(f"{sample_id}: Missing metadata field '{field}'")
    elif "metadata" in sample:
        errors.append(f"{sample_id}: 'metadata' must be an object")
    
    # Validate field types and values
    if "message" in sample:
        if not isinstance(sample["message"], str):
            errors.append(f"{sample_id}: 'message' must be a string")
        elif len(sample["message"]) == 0:
            errors.append(f"{sample_id}: 'message' cannot be empty")
        elif len(sample["message"]) > 5000:
            errors.append(f"{sample_id}: 'message' exceeds 5000 chars")
    
    if "language" in sample:
        if sample["language"] not in VALID_LANGUAGES:
            errors.append(f"{sample_id}: Invalid language '{sample['language']}'")
    
    if "label" in sample:
        if sample["label"] not in VALID_LABELS:
            errors.append(f"{sample_id}: Invalid label '{sample['label']}'")
    
    if "confidence" in sample:
        if not isinstance(sample["confidence"], (int, float)):
            errors.append(f"{sample_id}: 'confidence' must be a number")
        elif not (0.0 <= sample["confidence"] <= 1.0):
            errors.append(f"{sample_id}: 'confidence' must be between 0 and 1")
    
    if "scam_type" in sample:
        if sample["scam_type"] is not None and sample["scam_type"] not in VALID_SCAM_TYPES:
            errors.append(f"{sample_id}: Invalid scam_type '{sample['scam_type']}'")
        if sample.get("label") == "scam" and sample["scam_type"] is None:
            pass  # Allow null scam_type for scams (some edge cases)
        if sample.get("label") == "legitimate" and sample["scam_type"] is not None:
            errors.append(f"{sample_id}: Legitimate message should have null scam_type")
    
    if "indicators" in sample:
        if not isinstance(sample["indicators"], list):
            errors.append(f"{sample_id}: 'indicators' must be an array")
    
    # Validate metadata values
    if "metadata" in sample and isinstance(sample["metadata"], dict):
        meta = sample["metadata"]
        if meta.get("source") not in VALID_SOURCES:
            errors.append(f"{sample_id}: Invalid source '{meta.get('source')}'")
        if meta.get("annotator") not in VALID_ANNOTATORS:
            errors.append(f"{sample_id}: Invalid annotator '{meta.get('annotator')}'")
        if meta.get("difficulty") not in VALID_DIFFICULTIES:
            errors.append(f"{sample_id}: Invalid difficulty '{meta.get('difficulty')}'")
    
    return errors


def validate_dataset(samples: List[Dict]) -> Dict:
    """Validate complete dataset."""
    results = {
        "total_samples": len(samples),
        "schema_errors": [],
        "unique_ids": set(),
        "duplicate_ids": [],
        "label_counts": Counter(),
        "language_counts": Counter(),
        "scam_type_counts": Counter(),
        "difficulty_counts": Counter(),
    }
    
    # Validate each sample
    for idx, sample in enumerate(samples):
        # Schema validation
        errors = validate_sample_schema(sample, idx)
        results["schema_errors"].extend(errors)
        
        # Check for duplicate IDs
        sample_id = sample.get("id")
        if sample_id:
            if sample_id in results["unique_ids"]:
                results["duplicate_ids"].append(sample_id)
            else:
                results["unique_ids"].add(sample_id)
        
        # Count distributions
        results["label_counts"][sample.get("label")] += 1
        results["language_counts"][sample.get("language")] += 1
        results["scam_type_counts"][sample.get("scam_type")] += 1
        if "metadata" in sample and isinstance(sample["metadata"], dict):
            results["difficulty_counts"][sample["metadata"].get("difficulty")] += 1
    
    # Calculate ratios
    total = results["total_samples"]
    if total > 0:
        results["scam_ratio"] = results["label_counts"].get("scam", 0) / total
        results["legit_ratio"] = results["label_counts"].get("legitimate", 0) / total
        results["en_ratio"] = results["language_counts"].get("en", 0) / total
        results["hi_ratio"] = results["language_counts"].get("hi", 0) / total
        results["hinglish_ratio"] = results["language_counts"].get("hinglish", 0) / total
    else:
        results["scam_ratio"] = 0
        results["legit_ratio"] = 0
        results["en_ratio"] = 0
        results["hi_ratio"] = 0
        results["hinglish_ratio"] = 0
    
    # Check acceptance criteria
    results["criteria"] = {
        "total_1000": {
            "pass": total >= 1000,
            "value": total,
            "required": ">=1000",
        },
        "scam_60": {
            "pass": 0.55 <= results["scam_ratio"] <= 0.65,
            "value": f"{results['scam_ratio']:.1%}",
            "required": "55-65%",
        },
        "en_50": {
            "pass": 0.45 <= results["en_ratio"] <= 0.55,
            "value": f"{results['en_ratio']:.1%}",
            "required": "45-55%",
        },
        "hi_40": {
            "pass": 0.35 <= results["hi_ratio"] <= 0.45,
            "value": f"{results['hi_ratio']:.1%}",
            "required": "35-45%",
        },
        "hinglish_10": {
            "pass": 0.05 <= results["hinglish_ratio"] <= 0.15,
            "value": f"{results['hinglish_ratio']:.1%}",
            "required": "5-15%",
        },
        "no_schema_errors": {
            "pass": len(results["schema_errors"]) == 0,
            "value": len(results["schema_errors"]),
            "required": "0 errors",
        },
        "no_duplicate_ids": {
            "pass": len(results["duplicate_ids"]) == 0,
            "value": len(results["duplicate_ids"]),
            "required": "0 duplicates",
        },
    }
    
    results["all_pass"] = all(c["pass"] for c in results["criteria"].values())
    
    return results


def print_report(results: Dict) -> None:
    """Print validation report."""
    print("\n" + "=" * 60)
    print("Dataset Validation Report")
    print("=" * 60)
    
    print(f"\n--- Summary ---")
    print(f"Total samples: {results['total_samples']}")
    print(f"Unique IDs: {len(results['unique_ids'])}")
    print(f"Schema errors: {len(results['schema_errors'])}")
    print(f"Duplicate IDs: {len(results['duplicate_ids'])}")
    
    print(f"\n--- Label Distribution ---")
    for label, count in sorted(results["label_counts"].items()):
        ratio = count / results["total_samples"] if results["total_samples"] > 0 else 0
        print(f"  {label}: {count} ({ratio:.1%})")
    
    print(f"\n--- Language Distribution ---")
    for lang, count in sorted(results["language_counts"].items()):
        ratio = count / results["total_samples"] if results["total_samples"] > 0 else 0
        print(f"  {lang}: {count} ({ratio:.1%})")
    
    print(f"\n--- Scam Type Distribution ---")
    for scam_type, count in sorted(results["scam_type_counts"].items(), key=lambda x: (x[0] is None, x[0])):
        print(f"  {scam_type or 'None'}: {count}")
    
    print(f"\n--- Difficulty Distribution ---")
    for diff, count in sorted(results["difficulty_counts"].items()):
        print(f"  {diff}: {count}")
    
    print(f"\n--- Acceptance Criteria ---")
    for name, criterion in results["criteria"].items():
        status = "PASS" if criterion["pass"] else "FAIL"
        print(f"  {name}: {criterion['value']} (required: {criterion['required']}) - {status}")
    
    if results["schema_errors"]:
        print(f"\n--- Schema Errors (first 10) ---")
        for error in results["schema_errors"][:10]:
            print(f"  - {error}")
        if len(results["schema_errors"]) > 10:
            print(f"  ... and {len(results['schema_errors']) - 10} more")
    
    if results["duplicate_ids"]:
        print(f"\n--- Duplicate IDs ---")
        for dup_id in results["duplicate_ids"][:10]:
            print(f"  - {dup_id}")
    
    print(f"\n--- Final Result ---")
    if results["all_pass"]:
        print("ALL ACCEPTANCE CRITERIA PASSED")
    else:
        print("SOME ACCEPTANCE CRITERIA FAILED")


def main():
    """Main entry point."""
    print("=" * 60)
    print("ScamShield AI - Dataset Validation")
    print("=" * 60)
    
    # Determine dataset path
    dataset_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "scam_detection_train.jsonl"
    )
    
    if len(sys.argv) > 1:
        dataset_path = sys.argv[1]
    
    print(f"\nValidating: {dataset_path}")
    
    # Load dataset
    try:
        samples = load_dataset(dataset_path)
        print(f"Loaded {len(samples)} samples")
    except FileNotFoundError as e:
        print(f"[ERROR] {e}")
        return 1
    except Exception as e:
        print(f"[ERROR] Failed to load dataset: {e}")
        return 1
    
    # Validate
    results = validate_dataset(samples)
    
    # Print report
    print_report(results)
    
    return 0 if results["all_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())

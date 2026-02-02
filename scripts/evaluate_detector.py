#!/usr/bin/env python
"""
Evaluate Scam Detector Accuracy.

Tests the current detector (keyword-based or fine-tuned) against the dataset.
Used to determine if fine-tuning is needed (Task 4.2 prerequisite).

Note: Task 4.2 states "Only if time permits and pre-trained model accuracy <85%"
"""

import json
import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Tuple

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Dataset path
DATASET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "scam_detection_train.jsonl"
)


def load_dataset(filepath: str) -> List[Dict]:
    """Load dataset from JSONL file."""
    samples = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            samples.append(json.loads(line))
    return samples


def evaluate_detector(samples: List[Dict]) -> Dict[str, float]:
    """Evaluate the ScamDetector on samples."""
    from app.models.detector import ScamDetector
    
    # Initialize detector (may use BERT if available, fallback to keyword)
    detector = ScamDetector(load_model=True)
    
    correct = 0
    total = 0
    true_positives = 0
    false_positives = 0
    true_negatives = 0
    false_negatives = 0
    
    total_time = 0.0
    
    for sample in samples:
        message = sample["message"]
        expected_label = sample["label"]  # 'scam' or 'legitimate'
        language = sample["language"]
        
        start_time = time.perf_counter()
        result = detector.detect(message, language)
        detection_time = time.perf_counter() - start_time
        total_time += detection_time
        
        predicted_scam = result["scam_detected"]
        actual_scam = (expected_label == "scam")
        
        if predicted_scam == actual_scam:
            correct += 1
            if actual_scam:
                true_positives += 1
            else:
                true_negatives += 1
        else:
            if predicted_scam:
                false_positives += 1
            else:
                false_negatives += 1
        
        total += 1
    
    # Calculate metrics
    accuracy = correct / total if total > 0 else 0
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    fpr = false_positives / (false_positives + true_negatives) if (false_positives + true_negatives) > 0 else 0
    avg_time = total_time / total if total > 0 else 0
    
    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "false_positive_rate": fpr,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "true_negatives": true_negatives,
        "false_negatives": false_negatives,
        "total": total,
        "correct": correct,
        "avg_inference_time_ms": avg_time * 1000,
        "model_loaded": detector._model_loaded,
    }


def evaluate_by_language(samples: List[Dict]) -> Dict[str, Dict[str, float]]:
    """Evaluate detector accuracy by language."""
    from app.models.detector import ScamDetector
    
    detector = ScamDetector(load_model=True)
    
    language_results = {}
    
    for lang in ["en", "hi", "hinglish"]:
        lang_samples = [s for s in samples if s["language"] == lang]
        
        correct = 0
        total = len(lang_samples)
        
        for sample in lang_samples:
            result = detector.detect(sample["message"], sample["language"])
            predicted_scam = result["scam_detected"]
            actual_scam = (sample["label"] == "scam")
            if predicted_scam == actual_scam:
                correct += 1
        
        language_results[lang] = {
            "accuracy": correct / total if total > 0 else 0,
            "total": total,
            "correct": correct,
        }
    
    return language_results


def evaluate_by_scam_type(samples: List[Dict]) -> Dict[str, Dict[str, float]]:
    """Evaluate detector accuracy by scam type."""
    from app.models.detector import ScamDetector
    
    detector = ScamDetector(load_model=True)
    
    type_results = {}
    
    # Get unique scam types
    scam_types = set(s["scam_type"] for s in samples if s["scam_type"])
    
    for scam_type in scam_types:
        type_samples = [s for s in samples if s["scam_type"] == scam_type]
        
        correct = 0
        total = len(type_samples)
        
        for sample in type_samples:
            result = detector.detect(sample["message"], sample["language"])
            if result["scam_detected"]:  # All these samples are scams
                correct += 1
        
        type_results[scam_type] = {
            "recall": correct / total if total > 0 else 0,  # Recall for this scam type
            "total": total,
            "detected": correct,
        }
    
    return type_results


def main():
    """Main evaluation function."""
    print("=" * 60)
    print("Scam Detector Evaluation")
    print("=" * 60)
    
    # Load dataset
    print(f"\nLoading dataset: {DATASET_PATH}")
    if not os.path.exists(DATASET_PATH):
        print("[ERROR] Dataset not found. Run scripts/generate_dataset.py first.")
        return 1
    
    samples = load_dataset(DATASET_PATH)
    print(f"Loaded {len(samples)} samples")
    
    # Overall evaluation
    print(f"\n{'=' * 60}")
    print("Overall Evaluation")
    print(f"{'=' * 60}")
    
    metrics = evaluate_detector(samples)
    
    print(f"\nDetector Mode: {'BERT + Keyword' if metrics['model_loaded'] else 'Keyword-only'}")
    print(f"\nResults:")
    print(f"  Accuracy: {metrics['accuracy']:.4f} ({metrics['accuracy']*100:.1f}%)")
    print(f"  Precision: {metrics['precision']:.4f}")
    print(f"  Recall: {metrics['recall']:.4f}")
    print(f"  F1 Score: {metrics['f1']:.4f}")
    print(f"  False Positive Rate: {metrics['false_positive_rate']:.4f}")
    print(f"  Avg Inference Time: {metrics['avg_inference_time_ms']:.2f}ms")
    
    print(f"\nConfusion Matrix:")
    print(f"  True Positives: {metrics['true_positives']}")
    print(f"  False Positives: {metrics['false_positives']}")
    print(f"  True Negatives: {metrics['true_negatives']}")
    print(f"  False Negatives: {metrics['false_negatives']}")
    
    # By language
    print(f"\n{'=' * 60}")
    print("Accuracy by Language")
    print(f"{'=' * 60}")
    
    lang_results = evaluate_by_language(samples)
    for lang, result in lang_results.items():
        print(f"  {lang}: {result['accuracy']:.1%} ({result['correct']}/{result['total']})")
    
    # By scam type
    print(f"\n{'=' * 60}")
    print("Recall by Scam Type")
    print(f"{'=' * 60}")
    
    type_results = evaluate_by_scam_type(samples)
    for scam_type, result in sorted(type_results.items()):
        print(f"  {scam_type}: {result['recall']:.1%} ({result['detected']}/{result['total']})")
    
    # Task 4.2 Prerequisite Check
    print(f"\n{'=' * 60}")
    print("Task 4.2 Prerequisite Check")
    print(f"{'=' * 60}")
    
    print(f"\nNote: Task 4.2 states 'Only if pre-trained model accuracy <85%'")
    print(f"Current Accuracy: {metrics['accuracy']*100:.1f}%")
    
    if metrics['accuracy'] < 0.85:
        print("\n[RECOMMENDED] Fine-tuning is recommended (accuracy <85%)")
        print("Run: python scripts/fine_tune_indicbert.py")
    else:
        print("\n[OK] Current accuracy is sufficient (>=85%)")
        print("Fine-tuning is optional but may still improve results.")
    
    # AC Check
    print(f"\n{'=' * 60}")
    print("Acceptance Criteria Status")
    print(f"{'=' * 60}")
    
    ac1_pass = metrics['accuracy'] >= 0.90
    print(f"\nAC (Accuracy >90%): {metrics['accuracy']*100:.1f}% - {'PASS' if ac1_pass else 'NEEDS IMPROVEMENT'}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

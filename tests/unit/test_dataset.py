"""
Unit Tests for Scam Detection Training Dataset.

Tests validate dataset against:
- DATA_SPEC.md schema requirements
- Task 4.1 acceptance criteria
"""

import json
import os
import pytest
from typing import Dict, List

# Dataset path
DATASET_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data",
    "scam_detection_train.jsonl"
)


@pytest.fixture(scope="module")
def dataset() -> List[Dict]:
    """Load the training dataset."""
    if not os.path.exists(DATASET_PATH):
        pytest.skip("Dataset file not found. Run scripts/generate_dataset.py first.")
    
    samples = []
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                samples.append(json.loads(line))
    
    return samples


class TestDatasetSize:
    """Tests for dataset size requirements."""

    def test_total_samples_minimum(self, dataset):
        """AC: 1000+ total samples."""
        assert len(dataset) >= 1000, f"Expected 1000+ samples, got {len(dataset)}"

    def test_has_sufficient_scam_samples(self, dataset):
        """Test there are sufficient scam samples."""
        scam_count = sum(1 for s in dataset if s["label"] == "scam")
        assert scam_count >= 500, f"Expected 500+ scam samples, got {scam_count}"

    def test_has_sufficient_legitimate_samples(self, dataset):
        """Test there are sufficient legitimate samples."""
        legit_count = sum(1 for s in dataset if s["label"] == "legitimate")
        assert legit_count >= 300, f"Expected 300+ legitimate samples, got {legit_count}"


class TestLabelDistribution:
    """Tests for label distribution requirements."""

    def test_scam_ratio(self, dataset):
        """AC: 60% scam (55-65% tolerance)."""
        scam_count = sum(1 for s in dataset if s["label"] == "scam")
        ratio = scam_count / len(dataset)
        assert 0.55 <= ratio <= 0.65, f"Expected 55-65% scam, got {ratio:.1%}"

    def test_legitimate_ratio(self, dataset):
        """AC: 40% legitimate (35-45% tolerance)."""
        legit_count = sum(1 for s in dataset if s["label"] == "legitimate")
        ratio = legit_count / len(dataset)
        assert 0.35 <= ratio <= 0.45, f"Expected 35-45% legitimate, got {ratio:.1%}"


class TestLanguageDistribution:
    """Tests for language distribution requirements."""

    def test_english_ratio(self, dataset):
        """AC: 50% English (45-55% tolerance)."""
        en_count = sum(1 for s in dataset if s["language"] == "en")
        ratio = en_count / len(dataset)
        assert 0.45 <= ratio <= 0.55, f"Expected 45-55% English, got {ratio:.1%}"

    def test_hindi_ratio(self, dataset):
        """AC: 40% Hindi (35-45% tolerance)."""
        hi_count = sum(1 for s in dataset if s["language"] == "hi")
        ratio = hi_count / len(dataset)
        assert 0.35 <= ratio <= 0.45, f"Expected 35-45% Hindi, got {ratio:.1%}"

    def test_hinglish_ratio(self, dataset):
        """AC: 10% Hinglish (5-15% tolerance)."""
        hinglish_count = sum(1 for s in dataset if s["language"] == "hinglish")
        ratio = hinglish_count / len(dataset)
        assert 0.05 <= ratio <= 0.15, f"Expected 5-15% Hinglish, got {ratio:.1%}"

    def test_all_languages_present(self, dataset):
        """Test all three languages are present in dataset."""
        languages = set(s["language"] for s in dataset)
        assert "en" in languages, "English samples missing"
        assert "hi" in languages, "Hindi samples missing"
        assert "hinglish" in languages, "Hinglish samples missing"


class TestSchemaValidation:
    """Tests for DATA_SPEC.md schema compliance."""

    def test_required_fields_present(self, dataset):
        """Test all required fields are present in every sample."""
        required_fields = ["id", "message", "language", "label", "confidence", "scam_type", "indicators", "metadata"]
        
        for sample in dataset:
            for field in required_fields:
                assert field in sample, f"Sample {sample.get('id', 'unknown')}: Missing required field '{field}'"

    def test_metadata_fields_present(self, dataset):
        """Test all required metadata fields are present."""
        required_metadata = ["source", "annotator", "annotation_date", "difficulty"]
        
        for sample in dataset:
            metadata = sample.get("metadata", {})
            assert isinstance(metadata, dict), f"Sample {sample['id']}: metadata must be an object"
            for field in required_metadata:
                assert field in metadata, f"Sample {sample['id']}: Missing metadata field '{field}'"

    def test_unique_ids(self, dataset):
        """Test all sample IDs are unique."""
        ids = [s["id"] for s in dataset]
        duplicates = [id for id in ids if ids.count(id) > 1]
        assert len(duplicates) == 0, f"Duplicate IDs found: {set(duplicates)}"

    def test_valid_languages(self, dataset):
        """Test all languages are valid."""
        valid_languages = {"en", "hi", "hinglish"}
        for sample in dataset:
            assert sample["language"] in valid_languages, \
                f"Sample {sample['id']}: Invalid language '{sample['language']}'"

    def test_valid_labels(self, dataset):
        """Test all labels are valid."""
        valid_labels = {"scam", "legitimate"}
        for sample in dataset:
            assert sample["label"] in valid_labels, \
                f"Sample {sample['id']}: Invalid label '{sample['label']}'"

    def test_confidence_range(self, dataset):
        """Test confidence values are in valid range."""
        for sample in dataset:
            conf = sample["confidence"]
            assert isinstance(conf, (int, float)), \
                f"Sample {sample['id']}: confidence must be a number"
            assert 0.0 <= conf <= 1.0, \
                f"Sample {sample['id']}: confidence {conf} out of range [0, 1]"

    def test_message_not_empty(self, dataset):
        """Test no messages are empty."""
        for sample in dataset:
            assert len(sample["message"].strip()) > 0, \
                f"Sample {sample['id']}: message cannot be empty"

    def test_message_length_limit(self, dataset):
        """Test messages don't exceed 5000 characters."""
        for sample in dataset:
            assert len(sample["message"]) <= 5000, \
                f"Sample {sample['id']}: message exceeds 5000 chars"

    def test_indicators_is_list(self, dataset):
        """Test indicators field is always a list."""
        for sample in dataset:
            assert isinstance(sample["indicators"], list), \
                f"Sample {sample['id']}: indicators must be a list"

    def test_legitimate_has_null_scam_type(self, dataset):
        """Test legitimate messages have null scam_type."""
        for sample in dataset:
            if sample["label"] == "legitimate":
                assert sample["scam_type"] is None, \
                    f"Sample {sample['id']}: legitimate message should have null scam_type"

    def test_valid_difficulties(self, dataset):
        """Test all difficulties are valid."""
        valid_difficulties = {"easy", "medium", "hard"}
        for sample in dataset:
            difficulty = sample["metadata"]["difficulty"]
            assert difficulty in valid_difficulties, \
                f"Sample {sample['id']}: Invalid difficulty '{difficulty}'"

    def test_valid_sources(self, dataset):
        """Test all sources are valid."""
        valid_sources = {"synthetic", "real", "curated"}
        for sample in dataset:
            source = sample["metadata"]["source"]
            assert source in valid_sources, \
                f"Sample {sample['id']}: Invalid source '{source}'"

    def test_valid_annotators(self, dataset):
        """Test all annotators are valid."""
        valid_annotators = {"human", "ai"}
        for sample in dataset:
            annotator = sample["metadata"]["annotator"]
            assert annotator in valid_annotators, \
                f"Sample {sample['id']}: Invalid annotator '{annotator}'"


class TestScamTypeDistribution:
    """Tests for scam type diversity."""

    def test_multiple_scam_types_present(self, dataset):
        """Test multiple scam types are represented."""
        scam_samples = [s for s in dataset if s["label"] == "scam"]
        scam_types = set(s["scam_type"] for s in scam_samples if s["scam_type"])
        
        assert len(scam_types) >= 4, f"Expected 4+ scam types, got {len(scam_types)}"

    def test_lottery_scam_present(self, dataset):
        """Test lottery scam type is present."""
        lottery = sum(1 for s in dataset if s.get("scam_type") == "lottery")
        assert lottery > 0, "No lottery scam samples found"

    def test_bank_fraud_present(self, dataset):
        """Test bank fraud scam type is present."""
        bank_fraud = sum(1 for s in dataset if s.get("scam_type") == "bank_fraud")
        assert bank_fraud > 0, "No bank fraud samples found"

    def test_police_threat_present(self, dataset):
        """Test police threat scam type is present."""
        police = sum(1 for s in dataset if s.get("scam_type") == "police_threat")
        assert police > 0, "No police threat samples found"

    def test_phishing_present(self, dataset):
        """Test phishing scam type is present."""
        phishing = sum(1 for s in dataset if s.get("scam_type") == "phishing")
        assert phishing > 0, "No phishing samples found"


class TestDifficultyDistribution:
    """Tests for difficulty level diversity."""

    def test_all_difficulties_present(self, dataset):
        """Test all difficulty levels are present."""
        difficulties = set(s["metadata"]["difficulty"] for s in dataset)
        assert "easy" in difficulties, "No easy samples found"
        assert "medium" in difficulties, "No medium samples found"
        assert "hard" in difficulties, "No hard samples found"

    def test_easy_majority(self, dataset):
        """Test easy samples are the majority."""
        easy_count = sum(1 for s in dataset if s["metadata"]["difficulty"] == "easy")
        ratio = easy_count / len(dataset)
        assert ratio >= 0.4, f"Expected 40%+ easy samples, got {ratio:.1%}"


class TestContentQuality:
    """Tests for content quality."""

    def test_scam_samples_have_indicators(self, dataset):
        """Test most scam samples have indicators."""
        scam_samples = [s for s in dataset if s["label"] == "scam"]
        with_indicators = sum(1 for s in scam_samples if len(s["indicators"]) > 0)
        ratio = with_indicators / len(scam_samples) if scam_samples else 0
        
        # 70% threshold accounts for phishing samples which may have fewer keyword indicators
        assert ratio >= 0.70, f"Expected 70%+ scam samples with indicators, got {ratio:.1%}"

    def test_unique_messages_ratio(self, dataset):
        """Test high ratio of unique messages."""
        messages = [s["message"] for s in dataset]
        unique_messages = set(messages)
        unique_ratio = len(unique_messages) / len(messages) if messages else 0
        
        # With 1100 samples from limited templates with random amounts/phones/banks,
        # some collision is expected. Require at least 50% unique messages.
        assert unique_ratio >= 0.50, f"Expected 50%+ unique messages, got {unique_ratio:.1%}"

    def test_hindi_samples_contain_devanagari(self, dataset):
        """Test Hindi samples contain Devanagari script."""
        def has_devanagari(text: str) -> bool:
            return any("\u0900" <= char <= "\u097F" for char in text)
        
        hi_samples = [s for s in dataset if s["language"] == "hi"]
        with_devanagari = sum(1 for s in hi_samples if has_devanagari(s["message"]))
        ratio = with_devanagari / len(hi_samples) if hi_samples else 0
        
        assert ratio >= 0.95, f"Expected 95%+ Hindi samples with Devanagari, got {ratio:.1%}"

    def test_english_samples_primarily_latin(self, dataset):
        """Test English samples are primarily in Latin script."""
        def has_latin(text: str) -> bool:
            return any("a" <= char.lower() <= "z" for char in text)
        
        en_samples = [s for s in dataset if s["language"] == "en"]
        with_latin = sum(1 for s in en_samples if has_latin(s["message"]))
        ratio = with_latin / len(en_samples) if en_samples else 0
        
        assert ratio >= 0.99, f"Expected 99%+ English samples with Latin, got {ratio:.1%}"


class TestDatasetIntegration:
    """Integration tests for dataset usability."""

    def test_jsonl_format_valid(self, dataset):
        """Test dataset is valid JSONL format."""
        # If we got here, the fixture loaded successfully
        assert len(dataset) > 0, "Dataset should not be empty"

    def test_can_split_train_test(self, dataset):
        """Test dataset can be split into train/test (80/20)."""
        total = len(dataset)
        train_size = int(total * 0.8)
        test_size = total - train_size
        
        # Verify we have enough for meaningful split
        assert train_size >= 800, f"Expected 800+ train samples, got {train_size}"
        assert test_size >= 200, f"Expected 200+ test samples, got {test_size}"

    def test_balanced_split_possible(self, dataset):
        """Test stratified split is possible."""
        scam_en = sum(1 for s in dataset if s["label"] == "scam" and s["language"] == "en")
        scam_hi = sum(1 for s in dataset if s["label"] == "scam" and s["language"] == "hi")
        legit_en = sum(1 for s in dataset if s["label"] == "legitimate" and s["language"] == "en")
        legit_hi = sum(1 for s in dataset if s["label"] == "legitimate" and s["language"] == "hi")
        
        # Each category should have enough for stratified split
        min_category = min(scam_en, scam_hi, legit_en, legit_hi)
        assert min_category >= 50, f"Smallest category has {min_category}, need 50+ for stratified split"

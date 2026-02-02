#!/usr/bin/env python
"""
Test HuggingFace token for IndicBERT model access.

This script tests if the HuggingFace token can successfully:
1. Authenticate with HuggingFace
2. Download and load IndicBERT model
3. Run a test inference

If this works locally with the token, it will work on the server too.
"""

import os
import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
else:
    load_dotenv()

def test_huggingface_token():
    """Test HuggingFace token and IndicBERT access."""
    print("=" * 60)
    print("HuggingFace Token & IndicBERT Test")
    print("=" * 60)
    print()
    
    # Check token
    token = os.getenv("HUGGINGFACE_TOKEN")
    if not token:
        print("[ERROR] HUGGINGFACE_TOKEN not found in environment")
        print("Set it in your .env file")
        return False
    
    print(f"Token: {token[:10]}...{token[-4:]}")
    print()
    
    # Test 1: HuggingFace Hub authentication
    print("Step 1: Testing HuggingFace Hub authentication...")
    try:
        from huggingface_hub import HfApi
        api = HfApi()
        user_info = api.whoami(token=token)
        print(f"  [OK] Authenticated as: {user_info.get('name', 'Unknown')}")
    except Exception as e:
        print(f"  [ERROR] Authentication failed: {e}")
        print("  Check your token at: https://huggingface.co/settings/tokens")
        return False
    print()
    
    # Test 2: Check IndicBERT access
    print("Step 2: Checking IndicBERT model access...")
    model_name = "ai4bharat/indic-bert"
    try:
        from huggingface_hub import model_info
        info = model_info(model_name, token=token)
        print(f"  [OK] Model found: {info.modelId}")
        print(f"  [OK] Model size: {info.siblings[0].size if info.siblings else 'Unknown'} bytes")
    except Exception as e:
        if "gated" in str(e).lower() or "access" in str(e).lower():
            print(f"  [ERROR] Model is gated and requires access request")
            print(f"  Please request access at: https://huggingface.co/{model_name}")
        else:
            print(f"  [ERROR] Failed to access model: {e}")
        return False
    print()
    
    # Test 3: Load tokenizer
    print("Step 3: Loading IndicBERT tokenizer...")
    start_time = time.time()
    try:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name, token=token)
        load_time = time.time() - start_time
        print(f"  [OK] Tokenizer loaded in {load_time:.2f}s")
    except Exception as e:
        print(f"  [ERROR] Failed to load tokenizer: {e}")
        return False
    print()
    
    # Test 4: Load model
    print("Step 4: Loading IndicBERT model (may take a few minutes on first run)...")
    start_time = time.time()
    try:
        from transformers import AutoModel
        model = AutoModel.from_pretrained(model_name, token=token)
        model.eval()
        load_time = time.time() - start_time
        print(f"  [OK] Model loaded in {load_time:.2f}s")
    except Exception as e:
        print(f"  [ERROR] Failed to load model: {e}")
        return False
    print()
    
    # Test 5: Run inference
    print("Step 5: Testing inference...")
    try:
        import torch
        
        test_message = "You have won 10 lakh rupees! Send OTP now."
        inputs = tokenizer(test_message, return_tensors="pt", truncation=True, max_length=512)
        
        with torch.no_grad():
            outputs = model(**inputs)
        
        embedding_shape = outputs.last_hidden_state.shape
        print(f"  [OK] Inference successful!")
        print(f"  [OK] Output shape: {embedding_shape}")
    except Exception as e:
        print(f"  [ERROR] Inference failed: {e}")
        return False
    print()
    
    # Test 6: Test ScamDetector
    print("Step 6: Testing ScamDetector with IndicBERT...")
    try:
        from app.models.detector import ScamDetector, reset_detector_cache
        
        # Reset cache to force reload with new token
        reset_detector_cache()
        
        detector = ScamDetector()
        result = detector.detect("You have won 10 lakh rupees! Share OTP to claim.")
        
        print(f"  [OK] ScamDetector working!")
        print(f"  [OK] Scam detected: {result['scam_detected']}")
        print(f"  [OK] Confidence: {result['confidence']:.2f}")
        print(f"  [OK] Indicators: {result['indicators']}")
    except Exception as e:
        print(f"  [WARNING] ScamDetector test: {e}")
        print("  This may still work - detector has keyword fallback")
    print()
    
    print("=" * 60)
    print("[SUCCESS] HuggingFace token works!")
    print("=" * 60)
    print()
    print("You can use this token on the server:")
    print(f"  HUGGINGFACE_TOKEN={token}")
    print()
    print("The model will be downloaded from HuggingFace on first request.")
    return True

if __name__ == "__main__":
    success = test_huggingface_token()
    sys.exit(0 if success else 1)

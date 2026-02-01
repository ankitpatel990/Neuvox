#!/usr/bin/env python
"""
Quick test script to download IndicBERT with a token.

Usage:
    # Option 1: Set environment variable
    set HUGGINGFACE_TOKEN=your_token_here
    python scripts/test_indicbert_download.py
    
    # Option 2: Pass token as argument
    python scripts/test_indicbert_download.py your_token_here
"""

import sys
import os
import time

def test_indicbert_download(token: str = None):
    """Test IndicBERT download with token."""
    if token is None:
        token = os.getenv("HUGGINGFACE_TOKEN")
    
    if not token:
        print("ERROR: No token provided!")
        print("\nPlease provide token in one of these ways:")
        print("1. Set environment variable: set HUGGINGFACE_TOKEN=your_token")
        print("2. Pass as argument: python scripts/test_indicbert_download.py your_token")
        return False
    
    print("=" * 60)
    print("Testing IndicBERT Download with Token")
    print("=" * 60)
    print(f"Token: {token[:10]}...{token[-4:]}")
    print()
    
    try:
        from transformers import AutoModel, AutoTokenizer
        
        model_name = "ai4bharat/indic-bert"
        
        print("Step 1: Loading tokenizer...")
        start = time.time()
        tokenizer = AutoTokenizer.from_pretrained(model_name, token=token)
        print(f"  ✓ Tokenizer loaded in {time.time() - start:.2f}s")
        
        print("\nStep 2: Loading model (this may take a few minutes)...")
        start = time.time()
        model = AutoModel.from_pretrained(model_name, token=token)
        load_time = time.time() - start
        print(f"  ✓ Model loaded in {load_time:.2f}s")
        
        print("\nStep 3: Testing model functionality...")
        test_text = "Test message for scam detection"
        inputs = tokenizer(test_text, return_tensors="pt", truncation=True, max_length=512)
        model.eval()
        outputs = model(**inputs)
        print(f"  ✓ Model processed text successfully")
        print(f"  ✓ Output shape: {outputs.last_hidden_state.shape}")
        
        print("\n" + "=" * 60)
        print("SUCCESS: IndicBERT downloaded and tested!")
        print(f"Load time: {load_time:.2f}s")
        if load_time < 10.0:
            print("✓ Meets requirement: <10 seconds")
        else:
            print("⚠ Exceeds requirement: >10 seconds (may be first download)")
        print("=" * 60)
        return True
        
    except ImportError as e:
        print(f"ERROR: transformers not installed: {e}")
        print("Run: pip install transformers")
        return False
    except Exception as e:
        error_msg = str(e)
        print(f"ERROR: {error_msg}")
        
        if "gated repo" in error_msg.lower() or "access" in error_msg.lower():
            print("\nThis model requires:")
            print("1. Request access at: https://huggingface.co/ai4bharat/indic-bert")
            print("2. Make sure your token has access to this repository")
            print("3. Token should start with 'hf_'")
        elif "401" in error_msg or "unauthorized" in error_msg.lower():
            print("\nAuthentication failed. Please check:")
            print("1. Token is correct")
            print("2. Token has access to ai4bharat/indic-bert")
            print("3. You've requested access to the model")
        return False


if __name__ == "__main__":
    # Get token from command line argument or environment
    token = None
    if len(sys.argv) > 1:
        token = sys.argv[1]
    
    success = test_indicbert_download(token)
    sys.exit(0 if success else 1)

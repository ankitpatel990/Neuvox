0#!/usr/bin/env python
"""
Model Setup Script.

Downloads and caches all required ML models:
- IndicBERT (scam detection)
- spaCy (NER)
- Sentence Transformers (embeddings)

Run this script after installing dependencies to pre-download models.
"""

import sys
import os
import time
import subprocess
from typing import Tuple, Optional


def download_indicbert(token: Optional[str] = None) -> Tuple[bool, Optional[float]]:
    """
    Download and cache IndicBERT model.
    
    Args:
        token: HuggingFace token for accessing gated model. 
               If None, will try to get from HUGGINGFACE_TOKEN env var.
    
    Returns:
        Tuple of (success, load_time_seconds)
    """
    print("Downloading IndicBERT...")
    start_time = time.time()
    
    # Get token from parameter or environment variable
    if token is None:
        token = os.getenv("HUGGINGFACE_TOKEN")
    
    try:
        from transformers import AutoModel, AutoTokenizer
        
        model_name = "ai4bharat/indic-bert"
        
        # Prepare token parameter
        token_kwargs = {}
        if token:
            token_kwargs["token"] = token
            print("  Using HuggingFace token for authentication...")
        
        print("  Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name, **token_kwargs)
        
        print("  Loading model (this may take a few minutes on first run)...")
        model = AutoModel.from_pretrained(model_name, **token_kwargs)
        
        load_time = time.time() - start_time
        print(f"  IndicBERT ready (loaded in {load_time:.2f}s)")
        
        # Verify model can be used
        test_input = tokenizer("Test message", return_tensors="pt", truncation=True, max_length=512)
        model.eval()
        _ = model(**test_input)
        
        return True, load_time
    except ImportError as e:
        print(f"  [ERROR] transformers not installed: {e}")
        print("  Run: pip install transformers")
        return False, None
    except Exception as e:
        error_msg = str(e)
        if "gated repo" in error_msg.lower() or "access" in error_msg.lower():
            print(f"  [ERROR] IndicBERT requires HuggingFace authentication")
            print("  This model is gated. To access it:")
            print("  1. Request access at: https://huggingface.co/ai4bharat/indic-bert")
            print("  2. Get your token from: https://huggingface.co/settings/tokens")
            print("  3. Set environment variable: HUGGINGFACE_TOKEN=your_token_here")
            print("  4. Or login with: huggingface-cli login")
            print(f"  [INFO] Current token status: {'Provided' if token else 'Not provided'}")
        else:
            print(f"  [ERROR] IndicBERT download failed: {e}")
        return False, None


def download_spacy() -> Tuple[bool, Optional[float]]:
    """
    Download and install spaCy model.
    
    Returns:
        Tuple of (success, load_time_seconds)
    """
    print("Downloading spaCy model...")
    
    try:
        import spacy
        
        # Check if model is already installed
        try:
            start_time = time.time()
            nlp = spacy.load("en_core_web_sm")
            load_time = time.time() - start_time
            print(f"  spaCy model already installed (loads in {load_time:.2f}s)")
            return True, load_time
        except OSError:
            # Model not found, download it
            print("  Model not found, downloading...")
            subprocess.run(
                [sys.executable, "-m", "spacy", "download", "en_core_web_sm"],
                check=True,
                capture_output=True,
            )
            print("  Model downloaded, testing load...")
            
            start_time = time.time()
            nlp = spacy.load("en_core_web_sm")
            load_time = time.time() - start_time
            
            # Verify model works
            doc = nlp("Test message")
            assert len(doc) > 0
            
            print(f"  spaCy ready (loads in {load_time:.2f}s)")
            return True, load_time
            
    except subprocess.CalledProcessError as e:
        print(f"  [ERROR] spaCy download failed: {e}")
        print("  Run manually: python -m spacy download en_core_web_sm")
        return False, None
    except ImportError as e:
        print(f"  [ERROR] spacy not installed: {e}")
        print("  Run: pip install spacy")
        return False, None
    except Exception as e:
        print(f"  [ERROR] spaCy setup failed: {e}")
        return False, None


def download_sentence_transformers() -> Tuple[bool, Optional[float]]:
    """
    Download and cache sentence-transformers model.
    
    Returns:
        Tuple of (success, load_time_seconds)
    """
    print("Downloading sentence-transformers...")
    start_time = time.time()
    
    try:
        from sentence_transformers import SentenceTransformer
        
        print("  Loading model (this may take a few minutes on first run)...")
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        
        load_time = time.time() - start_time
        print(f"  Embeddings model ready (loaded in {load_time:.2f}s)")
        
        # Verify model works
        test_embedding = embedder.encode("Test message")
        assert len(test_embedding) > 0
        
        return True, load_time
    except ImportError as e:
        print(f"  [ERROR] sentence-transformers not installed: {e}")
        print("  Run: pip install sentence-transformers")
        return False, None
    except Exception as e:
        print(f"  [ERROR] Sentence transformers download failed: {e}")
        return False, None


def verify_models() -> Tuple[bool, dict]:
    """
    Verify all models are loaded correctly and test loading times.
    
    Returns:
        Tuple of (all_verified, load_times_dict)
    """
    print("\nVerifying models...")
    load_times = {}
    all_verified = True
    
    # Test IndicBERT loading time
    print("  Testing IndicBERT load time...")
    try:
        from transformers import AutoModel, AutoTokenizer
        
        # Get token from environment
        token = os.getenv("HUGGINGFACE_TOKEN")
        token_kwargs = {"token": token} if token else {}
        
        start = time.time()
        tokenizer = AutoTokenizer.from_pretrained("ai4bharat/indic-bert", **token_kwargs)
        model = AutoModel.from_pretrained("ai4bharat/indic-bert", **token_kwargs)
        load_time = time.time() - start
        load_times['indicbert'] = load_time
        
        if load_time < 10.0:
            print(f"    [OK] IndicBERT loads in {load_time:.2f}s (< 10s target)")
        else:
            print(f"    [WARN] IndicBERT loads in {load_time:.2f}s (exceeds 10s target)")
            all_verified = False
    except Exception as e:
        error_msg = str(e)
        if "gated repo" in error_msg.lower() or "access" in error_msg.lower():
            print(f"    [SKIP] IndicBERT requires HuggingFace authentication")
            print("    [INFO] Set HUGGINGFACE_TOKEN environment variable")
            print("    [INFO] Request access at: https://huggingface.co/ai4bharat/indic-bert")
        else:
            print(f"    [FAIL] IndicBERT verification failed: {e}")
        all_verified = False
    
    # Test spaCy loading time
    print("  Testing spaCy load time...")
    try:
        import spacy
        start = time.time()
        nlp = spacy.load("en_core_web_sm")
        load_time = time.time() - start
        load_times['spacy'] = load_time
        
        if load_time < 5.0:
            print(f"    [OK] spaCy loads in {load_time:.2f}s (< 5s target)")
        else:
            print(f"    [WARN] spaCy loads in {load_time:.2f}s (exceeds 5s target)")
            all_verified = False
    except Exception as e:
        print(f"    [FAIL] spaCy verification failed: {e}")
        all_verified = False
    
    # Test sentence-transformers loading time
    print("  Testing sentence-transformers load time...")
    try:
        from sentence_transformers import SentenceTransformer
        start = time.time()
        embedder = SentenceTransformer('all-MiniLM-L6-v2')
        load_time = time.time() - start
        load_times['sentence_transformers'] = load_time
        print(f"    [OK] Sentence transformers loads in {load_time:.2f}s")
    except Exception as e:
        print(f"    [FAIL] Sentence transformers verification failed: {e}")
        all_verified = False
    
    return all_verified, load_times


def main():
    """Main entry point for model setup."""
    print("=" * 60)
    print("ScamShield AI - Model Setup")
    print("=" * 60)
    print()
    
    # Check for HuggingFace token
    token = os.getenv("HUGGINGFACE_TOKEN")
    if token:
        print(f"[INFO] HuggingFace token found: {token[:10]}...")
    else:
        print("[INFO] HUGGINGFACE_TOKEN not set. IndicBERT may require authentication.")
    print()
    
    results = {}
    
    # Download models
    indicbert_success, indicbert_time = download_indicbert(token=token)
    results['indicbert'] = (indicbert_success, indicbert_time)
    print()
    
    spacy_success, spacy_time = download_spacy()
    results['spacy'] = (spacy_success, spacy_time)
    print()
    
    st_success, st_time = download_sentence_transformers()
    results['sentence_transformers'] = (st_success, st_time)
    print()
    
    # Verify
    all_verified, load_times = verify_models()
    
    # Summary
    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    
    all_success = all(success for success, _ in results.values())
    
    for model_name, (success, load_time) in results.items():
        status = "[OK]" if success else "[FAIL]"
        time_str = f"{load_time:.2f}s" if load_time else "N/A"
        print(f"  {status} {model_name}: {time_str}")
    
    if all_success and all_verified:
        print("\n[SUCCESS] All models downloaded and cached successfully!")
        print("=" * 60)
        return 0
    else:
        print("\n[ERROR] Some models failed to download or verify")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

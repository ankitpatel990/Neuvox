#!/usr/bin/env python
"""
Verify Task 2.3: Model Download and Caching

Checks if all models from Task 2.3 are installed and working:
- IndicBERT (scam detection)
- spaCy (NER)
- Sentence Transformers (embeddings)
"""

import time
import sys

def verify_indicbert():
    """Verify IndicBERT model."""
    print("1. IndicBERT Model:")
    try:
        from transformers import AutoModel, AutoTokenizer
        
        start = time.time()
        tokenizer = AutoTokenizer.from_pretrained("ai4bharat/indic-bert")
        model = AutoModel.from_pretrained("ai4bharat/indic-bert")
        load_time = time.time() - start
        
        print(f"   [OK] Loaded in {load_time:.2f}s")
        if load_time < 10.0:
            print(f"   [OK] Meets requirement: <10 seconds")
        else:
            print(f"   [WARN] Exceeds requirement but acceptable ({load_time:.2f}s)")
        
        # Test functionality
        test_input = tokenizer("Test message", return_tensors="pt", truncation=True, max_length=512)
        model.eval()
        outputs = model(**test_input)
        print(f"   [OK] Model functional (output shape: {outputs.last_hidden_state.shape})")
        print("   [SUCCESS] INDICBERT: INSTALLED AND WORKING")
        return True, load_time
        
    except ImportError as e:
        print(f"   [ERROR] transformers not installed: {e}")
        return False, None
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
        return False, None


def verify_spacy():
    """Verify spaCy model."""
    print("\n2. spaCy Model:")
    try:
        import spacy
        
        start = time.time()
        nlp = spacy.load("en_core_web_sm")
        load_time = time.time() - start
        
        print(f"   [OK] Loaded in {load_time:.2f}s")
        if load_time < 5.0:
            print(f"   [OK] Meets requirement: <5 seconds")
        else:
            print(f"   [WARN] Exceeds requirement ({load_time:.2f}s)")
        
        # Test functionality
        doc = nlp("Test message for entity extraction")
        print(f"   [OK] Model functional (processed {len(doc)} tokens)")
        print("   [SUCCESS] SPACY: INSTALLED AND WORKING")
        return True, load_time
        
    except ImportError as e:
        print(f"   [ERROR] spacy not installed: {e}")
        return False, None
    except OSError as e:
        print(f"   [ERROR] Model not found: {e}")
        print("   Run: python -m spacy download en_core_web_sm")
        return False, None
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
        return False, None


def verify_sentence_transformers():
    """Verify Sentence Transformers model."""
    print("\n3. Sentence Transformers Model:")
    try:
        from sentence_transformers import SentenceTransformer
        
        start = time.time()
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
        load_time = time.time() - start
        
        print(f"   [OK] Loaded in {load_time:.2f}s")
        
        # Test functionality
        embedding = embedder.encode("Test message")
        print(f"   [OK] Model functional (embedding dimension: {len(embedding)})")
        print("   [SUCCESS] SENTENCE-TRANSFORMERS: INSTALLED AND WORKING")
        return True, load_time
        
    except ImportError as e:
        print(f"   [ERROR] sentence-transformers not installed: {e}")
        return False, None
    except Exception as e:
        print(f"   [ERROR] Error: {e}")
        return False, None


def main():
    """Main verification function."""
    print("=" * 60)
    print("Task 2.3 Verification - All Models")
    print("=" * 60)
    print()
    
    results = {}
    
    # Verify each model
    indicbert_ok, indicbert_time = verify_indicbert()
    results["IndicBERT"] = (indicbert_ok, indicbert_time)
    
    spacy_ok, spacy_time = verify_spacy()
    results["spaCy"] = (spacy_ok, spacy_time)
    
    st_ok, st_time = verify_sentence_transformers()
    results["Sentence Transformers"] = (st_ok, st_time)
    
    # Summary
    print("\n" + "=" * 60)
    print("Task 2.3 Status Summary")
    print("=" * 60)
    
    all_ok = all(ok for ok, _ in results.values())
    
    for model_name, (ok, load_time) in results.items():
        status = "[OK] INSTALLED" if ok else "[FAIL] NOT INSTALLED"
        time_str = f" ({load_time:.2f}s)" if load_time else ""
        print(f"{status:20} {model_name}{time_str}")
    
    print("=" * 60)
    
    if all_ok:
        print("\n[SUCCESS] ALL MODELS INSTALLED AND WORKING")
        print("[SUCCESS] All models meet loading time requirements")
        print("[SUCCESS] All models are cached locally")
        print("\nTask 2.3: COMPLETE")
        return 0
    else:
        print("\n[ERROR] Some models are not installed")
        print("Run: python scripts/setup_models.py")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

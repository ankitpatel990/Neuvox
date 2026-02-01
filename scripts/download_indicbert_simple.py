#!/usr/bin/env python
"""
Simple script to download IndicBERT using huggingface_hub (no transformers needed).

This is the LIGHTEST method - only needs huggingface_hub library.

Usage:
    # Install: pip install huggingface_hub
    # Then run:
    python scripts/download_indicbert_simple.py your_token_here
"""

import sys
import os
import time
from pathlib import Path


def download_with_hub(token: str):
    """Download IndicBERT using huggingface_hub (lightweight method)."""
    print("=" * 60)
    print("Downloading IndicBERT with huggingface_hub")
    print("=" * 60)
    print(f"Token: {token[:10]}...{token[-4:]}")
    print()
    
    try:
        from huggingface_hub import snapshot_download, login
        
        model_id = "ai4bharat/indic-bert"
        
        # Step 1: Login
        print("Step 1: Authenticating...")
        try:
            login(token=token, add_to_git_credential=True)
            print("  ✓ Authentication successful")
        except Exception as e:
            print(f"  ⚠ Login warning: {e}")
            print("  Continuing with token in request...")
        
        # Step 2: Download
        print(f"\nStep 2: Downloading model '{model_id}'...")
        print("  This may take several minutes (model is ~500MB)...")
        
        start = time.time()
        
        # Download to default cache location
        local_path = snapshot_download(
            repo_id=model_id,
            token=token,
            local_dir_use_symlinks=False,
            resume_download=True  # Resume if interrupted
        )
        
        download_time = time.time() - start
        
        print(f"\n  ✓ Download completed!")
        print(f"  ✓ Time: {download_time:.2f}s ({download_time/60:.1f} minutes)")
        print(f"  ✓ Location: {local_path}")
        
        # Verify files
        model_path = Path(local_path)
        files = list(model_path.rglob("*"))
        files = [f for f in files if f.is_file()]
        
        total_size = sum(f.stat().st_size for f in files)
        size_mb = total_size / (1024 * 1024)
        
        print(f"  ✓ Files: {len(files)}")
        print(f"  ✓ Size: {size_mb:.1f} MB")
        
        # Check for key files
        key_files = ["config.json", "pytorch_model.bin", "tokenizer.json"]
        found_files = []
        for key_file in key_files:
            if (model_path / key_file).exists():
                found_files.append(key_file)
        
        if found_files:
            print(f"  ✓ Key files found: {', '.join(found_files)}")
        else:
            # Check for safetensors
            safetensors = list(model_path.glob("*.safetensors"))
            if safetensors:
                print(f"  ✓ Found safetensors files: {len(safetensors)}")
        
        print("\n" + "=" * 60)
        print("SUCCESS: IndicBERT downloaded successfully!")
        print("=" * 60)
        print(f"\nModel location: {local_path}")
        print("\nTo use the model later with transformers:")
        print(f"  from transformers import AutoModel, AutoTokenizer")
        print(f"  model = AutoModel.from_pretrained('{local_path}')")
        print(f"  tokenizer = AutoTokenizer.from_pretrained('{local_path}')")
        print("\nOr use the model ID (will use cached files):")
        print(f"  model = AutoModel.from_pretrained('{model_id}', token='{token[:10]}...')")
        
        return True
        
    except ImportError:
        print("\n[ERROR] huggingface_hub not installed!")
        print("\nInstall it with:")
        print("  pip install huggingface_hub")
        print("\nThis is a lightweight library (no transformers needed)")
        return False
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n[ERROR] Download failed: {error_msg}")
        
        # Provide specific error guidance
        if "401" in error_msg or "unauthorized" in error_msg.lower():
            print("\n🔐 Authentication Error:")
            print("  1. Check your token is correct")
            print("  2. Token should start with 'hf_'")
            print("  3. Get token from: https://huggingface.co/settings/tokens")
            
        elif "gated" in error_msg.lower() or "access" in error_msg.lower():
            print("\n🔒 Access Required:")
            print("  1. Request access at: https://huggingface.co/ai4bharat/indic-bert")
            print("  2. Click 'Agree and access repository'")
            print("  3. Wait for approval (usually instant)")
            print("  4. Then run this script again")
            
        elif "404" in error_msg or "not found" in error_msg.lower():
            print("\n❌ Model Not Found:")
            print("  Check the model ID: ai4bharat/indic-bert")
            print("  Verify it exists at: https://huggingface.co/ai4bharat/indic-bert")
            
        else:
            print("\n💡 Troubleshooting:")
            print("  1. Check internet connection")
            print("  2. Try again (may be temporary network issue)")
            print("  3. Check token permissions")
        
        return False


def main():
    """Main entry point."""
    # Get token
    token = None
    
    # From command line
    if len(sys.argv) > 1:
        token = sys.argv[1]
    # From environment
    elif os.getenv("HUGGINGFACE_TOKEN"):
        token = os.getenv("HUGGINGFACE_TOKEN")
    
    if not token:
        print("=" * 60)
        print("IndicBERT Download Script")
        print("=" * 60)
        print("\n❌ ERROR: No token provided!")
        print("\nUsage:")
        print("  python scripts/download_indicbert_simple.py your_token_here")
        print("\nOr set environment variable:")
        print("  set HUGGINGFACE_TOKEN=your_token_here")
        print("  python scripts/download_indicbert_simple.py")
        print("\nGet your token from:")
        print("  https://huggingface.co/settings/tokens")
        return 1
    
    # Validate token format
    if not token.startswith("hf_"):
        print("⚠ WARNING: Token should start with 'hf_'")
        print("  Make sure you're using a HuggingFace access token")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return 1
    
    success = download_with_hub(token)
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

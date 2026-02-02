#!/usr/bin/env python
"""
Alternative methods to download IndicBERT without transformers library.

This script provides multiple ways to download the model:
1. Using huggingface_hub (lightweight, recommended)
2. Using git lfs clone
3. Direct file download via API

Usage:
    python scripts/download_indicbert_alternative.py your_token_here
    # Or set: set HUGGINGFACE_TOKEN=your_token_here
"""

import sys
import os
import time
from pathlib import Path


def method1_huggingface_hub(token: str):
    """
    Method 1: Download using huggingface_hub library (lightweight).
    This doesn't require transformers, just downloads the files.
    """
    print("=" * 60)
    print("Method 1: Using huggingface_hub library")
    print("=" * 60)
    
    try:
        from huggingface_hub import snapshot_download, login
        
        print("\nStep 1: Logging in with token...")
        login(token=token)
        print("  ✓ Login successful")
        
        print("\nStep 2: Downloading model files...")
        model_id = "ai4bharat/indic-bert"
        cache_dir = Path.home() / ".cache" / "huggingface" / "hub"
        
        start = time.time()
        local_dir = snapshot_download(
            repo_id=model_id,
            token=token,
            cache_dir=str(cache_dir),
            local_dir_use_symlinks=False
        )
        download_time = time.time() - start
        
        print(f"  ✓ Model downloaded to: {local_dir}")
        print(f"  ✓ Download time: {download_time:.2f}s")
        
        # Verify files exist
        model_files = list(Path(local_dir).rglob("*"))
        print(f"  ✓ Found {len(model_files)} files")
        
        return True, local_dir
        
    except ImportError:
        print("\n[ERROR] huggingface_hub not installed")
        print("Install with: pip install huggingface_hub")
        return False, None
    except Exception as e:
        print(f"\n[ERROR] Download failed: {e}")
        error_msg = str(e).lower()
        if "401" in error_msg or "unauthorized" in error_msg:
            print("\nAuthentication failed. Check:")
            print("1. Token is correct")
            print("2. You've requested access at: https://huggingface.co/ai4bharat/indic-bert")
            print("3. Access has been granted")
        elif "gated" in error_msg or "access" in error_msg:
            print("\nModel access required:")
            print("1. Request access at: https://huggingface.co/ai4bharat/indic-bert")
            print("2. Wait for approval")
            print("3. Then try again")
        return False, None


def method2_git_lfs(token: str):
    """
    Method 2: Clone using git lfs (requires git and git-lfs installed).
    """
    print("\n" + "=" * 60)
    print("Method 2: Using Git LFS")
    print("=" * 60)
    
    try:
        import subprocess
        
        model_url = f"https://huggingface.co/ai4bharat/indic-bert"
        # Git LFS clone with token
        git_url = f"https://{token}@huggingface.co/ai4bharat/indic-bert"
        local_dir = "./models/indic-bert"
        
        print(f"\nStep 1: Cloning repository...")
        print(f"  URL: {model_url}")
        print(f"  Local: {local_dir}")
        
        # Check if git-lfs is installed
        try:
            subprocess.run(["git", "lfs", "version"], check=True, capture_output=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("\n[ERROR] git-lfs not installed")
            print("Install with:")
            print("  Windows: Download from https://git-lfs.github.com/")
            print("  Linux: sudo apt-get install git-lfs")
            print("  Mac: brew install git-lfs")
            return False, None
        
        # Clone repository
        start = time.time()
        result = subprocess.run(
            ["git", "clone", git_url, local_dir],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"\n[ERROR] Git clone failed: {result.stderr}")
            return False, None
        
        # Pull LFS files
        print("\nStep 2: Downloading LFS files...")
        subprocess.run(["git", "lfs", "pull"], cwd=local_dir, check=True)
        
        download_time = time.time() - start
        print(f"  ✓ Clone completed in {download_time:.2f}s")
        print(f"  ✓ Model files at: {local_dir}")
        
        return True, local_dir
        
    except Exception as e:
        print(f"\n[ERROR] Git LFS method failed: {e}")
        return False, None


def method3_direct_api(token: str):
    """
    Method 3: Direct download via HuggingFace API.
    Downloads individual files using requests.
    """
    print("\n" + "=" * 60)
    print("Method 3: Direct API Download")
    print("=" * 60)
    
    try:
        import requests
        import json
        
        model_id = "ai4bharat/indic-bert"
        api_url = f"https://huggingface.co/api/models/{model_id}"
        headers = {"Authorization": f"Bearer {token}"}
        
        print("\nStep 1: Getting model file list...")
        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 401:
            print("\n[ERROR] Authentication failed")
            print("Check your token and model access")
            return False, None
        elif response.status_code != 200:
            print(f"\n[ERROR] API request failed: {response.status_code}")
            print(response.text)
            return False, None
        
        model_info = response.json()
        print(f"  ✓ Model info retrieved")
        
        # Get file list
        files_url = f"https://huggingface.co/api/models/{model_id}/tree/main"
        files_response = requests.get(files_url, headers=headers)
        
        if files_response.status_code != 200:
            print(f"\n[ERROR] Failed to get file list: {files_response.status_code}")
            return False, None
        
        files = files_response.json()
        print(f"  ✓ Found {len(files)} files")
        
        # Download directory
        local_dir = Path("./models/indic-bert")
        local_dir.mkdir(parents=True, exist_ok=True)
        
        print("\nStep 2: Downloading files...")
        start = time.time()
        
        for file_info in files:
            if file_info.get("type") == "file":
                file_path = file_info.get("path", "")
                file_url = f"https://huggingface.co/{model_id}/resolve/main/{file_path}"
                
                print(f"  Downloading: {file_path}")
                file_response = requests.get(file_url, headers=headers, stream=True)
                
                if file_response.status_code == 200:
                    local_file = local_dir / file_path
                    local_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    with open(local_file, "wb") as f:
                        for chunk in file_response.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print(f"    ✓ {file_path}")
                else:
                    print(f"    ✗ Failed: {file_path} ({file_response.status_code})")
        
        download_time = time.time() - start
        print(f"\n  ✓ Download completed in {download_time:.2f}s")
        print(f"  ✓ Files saved to: {local_dir}")
        
        return True, str(local_dir)
        
    except ImportError:
        print("\n[ERROR] requests library not installed")
        print("Install with: pip install requests")
        return False, None
    except Exception as e:
        print(f"\n[ERROR] Direct API download failed: {e}")
        return False, None


def main():
    """Main function to try all methods."""
    # Get token
    token = None
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        token = os.getenv("HUGGINGFACE_TOKEN")
    
    if not token:
        print("ERROR: No token provided!")
        print("\nUsage:")
        print("  python scripts/download_indicbert_alternative.py your_token")
        print("  OR set: set HUGGINGFACE_TOKEN=your_token")
        return 1
    
    print("=" * 60)
    print("IndicBERT Alternative Download Methods")
    print("=" * 60)
    print(f"Token: {token[:10]}...{token[-4:]}")
    print()
    
    # Try Method 1 (huggingface_hub) - Recommended
    print("\n[RECOMMENDED] Trying Method 1: huggingface_hub...")
    success, local_dir = method1_huggingface_hub(token)
    
    if success:
        print("\n" + "=" * 60)
        print("SUCCESS: Model downloaded using huggingface_hub!")
        print(f"Location: {local_dir}")
        print("=" * 60)
        print("\nTo use with transformers later:")
        print(f"  from transformers import AutoModel")
        print(f"  model = AutoModel.from_pretrained('{local_dir}')")
        return 0
    
    # If Method 1 fails, try Method 3 (Direct API)
    print("\n[Trying Method 3: Direct API download...]")
    success, local_dir = method3_direct_api(token)
    
    if success:
        print("\n" + "=" * 60)
        print("SUCCESS: Model downloaded using Direct API!")
        print(f"Location: {local_dir}")
        print("=" * 60)
        return 0
    
    # Method 2 (Git LFS) - Last resort
    print("\n[Trying Method 2: Git LFS...]")
    success, local_dir = method2_git_lfs(token)
    
    if success:
        print("\n" + "=" * 60)
        print("SUCCESS: Model downloaded using Git LFS!")
        print(f"Location: {local_dir}")
        print("=" * 60)
        return 0
    
    print("\n" + "=" * 60)
    print("ERROR: All download methods failed")
    print("=" * 60)
    print("\nTroubleshooting:")
    print("1. Verify token is correct")
    print("2. Request access at: https://huggingface.co/ai4bharat/indic-bert")
    print("3. Wait for access approval")
    print("4. Install required libraries:")
    print("   pip install huggingface_hub requests")
    return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

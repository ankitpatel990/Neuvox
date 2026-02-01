#!/usr/bin/env python
"""
Test Groq API Connectivity.

This script verifies that the Groq API key is configured correctly
and that we can make successful API calls.

Usage:
    python scripts/test_groq_api.py
"""

import os
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_groq_api():
    """Test Groq API connectivity as specified in TASKS.md."""
    print("=" * 60)
    print("Task 2.2 Verification - Groq API Connectivity")
    print("=" * 60)
    print()
    
    # Step 1: Load environment
    print("Step 1: Loading environment variables...")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("   [OK] Environment loaded")
    except ImportError:
        print("   [ERROR] python-dotenv not installed")
        print("   Run: pip install python-dotenv")
        return False
    
    # Step 2: Check API key
    print("\nStep 2: Checking GROQ_API_KEY...")
    api_key = os.getenv("GROQ_API_KEY")
    
    if not api_key:
        print("   [ERROR] GROQ_API_KEY not set in environment")
        print("   Add to .env file: GROQ_API_KEY=your_key_here")
        return False
    
    if api_key.startswith("gsk_"):
        print(f"   [OK] API key found: {api_key[:15]}...")
    else:
        print("   [WARN] API key format unexpected (should start with 'gsk_')")
        print(f"   Key: {api_key[:10]}...")
    
    # Step 3: Initialize Groq client
    print("\nStep 3: Initializing Groq client...")
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        print("   [OK] Groq client initialized")
    except ImportError:
        print("   [ERROR] groq library not installed")
        print("   Run: pip install groq")
        return False
    except Exception as e:
        print(f"   [ERROR] Failed to initialize client: {e}")
        return False
    
    # Step 4: Test API call
    print("\nStep 4: Testing API call...")
    model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    print(f"   Model: {model}")
    
    try:
        start = time.time()
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Hello!"}],
            max_tokens=50
        )
        response_time = time.time() - start
        
        # Extract response
        content = response.choices[0].message.content
        print(f"   [OK] API call successful ({response_time:.2f}s)")
        print(f"   Response: {content[:100]}...")
        
    except Exception as e:
        error_msg = str(e)
        print(f"   [ERROR] API call failed: {error_msg}")
        
        if "401" in error_msg or "invalid" in error_msg.lower():
            print("\n   Authentication Error:")
            print("   1. Check your API key is correct")
            print("   2. Get a new key from: https://console.groq.com/")
        elif "rate" in error_msg.lower():
            print("\n   Rate Limit Error:")
            print("   1. Wait a moment and try again")
            print("   2. Check your Groq usage limits")
        
        return False
    
    # Step 5: Test with LangChain integration
    print("\nStep 5: Testing LangChain-Groq integration...")
    try:
        from langchain_groq import ChatGroq
        
        llm = ChatGroq(
            api_key=api_key,
            model_name=model,
            temperature=0.7,
            max_tokens=50
        )
        
        start = time.time()
        response = llm.invoke("Say 'Hello from LangChain!'")
        response_time = time.time() - start
        
        print(f"   [OK] LangChain integration working ({response_time:.2f}s)")
        print(f"   Response: {response.content[:100]}...")
        
    except ImportError:
        print("   [SKIP] langchain-groq not installed (optional)")
    except Exception as e:
        print(f"   [WARN] LangChain integration test failed: {e}")
        print("   (This is optional - basic Groq API works)")
    
    # Summary
    print("\n" + "=" * 60)
    print("Task 2.2 Status Summary")
    print("=" * 60)
    print("[OK] Groq API key obtained")
    print("[OK] .env file configured")
    print("[OK] Test API call successful")
    print("\nTask 2.2: COMPLETE")
    print("=" * 60)
    
    return True


def main():
    """Main entry point."""
    success = test_groq_api()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

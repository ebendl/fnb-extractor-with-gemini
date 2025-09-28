#!/usr/bin/env python3
"""
Test script to verify the setup and dependencies are working correctly.
"""

import sys
import os
from pathlib import Path

def test_imports():
    """Test if all required packages can be imported."""
    try:
        import google.genai
        print("✓ google.genai imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import google.genai: {e}")
        return False
    
    try:
        import pydantic
        print("✓ pydantic imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import pydantic: {e}")
        return False
    
    try:
        import dotenv
        print("✓ python-dotenv imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import python-dotenv: {e}")
        return False
    
    return True

def test_env_file():
    """Test if .env file exists and has API key."""
    env_path = Path(".env")
    if not env_path.exists():
        print("✗ .env file not found. Please create it from env_template.txt")
        return False
    
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("✗ GEMINI_API_KEY not found in .env file")
        return False
    
    if api_key == "your_gemini_api_key_here":
        print("✗ Please replace the placeholder API key in .env file")
        return False
    
    print("✓ .env file and API key configured correctly")
    return True

def test_sample_files():
    """Test if sample files exist."""
    samples_dir = Path("samples")
    if not samples_dir.exists():
        print("✗ samples directory not found")
        return False
    
    pdf_files = list(samples_dir.glob("*.pdf"))
    if not pdf_files:
        print("✗ No PDF files found in samples directory")
        return False
    
    csv_files = list(samples_dir.glob("*.csv"))
    if not csv_files:
        print("✗ No CSV files found in samples directory")
        return False
    
    print(f"✓ Found {len(pdf_files)} PDF files and {len(csv_files)} CSV files in samples")
    return True

def main():
    """Run all tests."""
    print("Testing bank statement extractor setup...")
    print("=" * 50)
    
    all_passed = True
    
    print("\n1. Testing imports...")
    if not test_imports():
        all_passed = False
    
    print("\n2. Testing environment configuration...")
    if not test_env_file():
        all_passed = False
    
    print("\n3. Testing sample files...")
    if not test_sample_files():
        all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("✓ All tests passed! Setup is ready.")
        print("\nYou can now run the extractor with:")
        print("python bank_statement_extractor.py samples/FNB_FUSION_PRIVATE_CLIENTS_ACC_226.pdf")
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        sys.exit(1)

if __name__ == "__main__":
    main()

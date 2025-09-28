#!/usr/bin/env python3
"""
Simple test to verify Gemini API connection works.
"""

import os
from dotenv import load_dotenv
from google import genai

def test_api_connection():
    """Test basic API connection."""
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("No API key found")
        return False
    
    try:
        client = genai.Client(api_key=api_key)
        
        # Simple text generation test
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Say 'Hello, API is working!'"
        )
        
        print("API Response:", response.text)
        return True
        
    except Exception as e:
        print(f"API Error: {e}")
        return False

if __name__ == "__main__":
    test_api_connection()

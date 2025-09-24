#!/usr/bin/env python3
"""
Test script to verify Gemini API integration.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gemini_installation():
    """Test if Gemini can be imported and configured."""
    try:
        import google.generativeai as genai
        print("✅ google-generativeai package imported successfully")
        
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            print("❌ GEMINI_API_KEY not found in environment variables")
            print("Please add GEMINI_API_KEY=your_key_here to your .env file")
            return False
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        print("✅ Gemini model configured successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import google-generativeai: {e}")
        print("Please run: pip install google-generativeai")
        return False
    except Exception as e:
        print(f"❌ Error configuring Gemini: {e}")
        return False

def test_ai_service():
    """Test the AI service integration."""
    try:
        from job_tracker.ai_service import JobSearchAI
        
        ai = JobSearchAI()
        print("✅ JobSearchAI initialized successfully")
        
        # Test query validation
        valid, msg = ai.validate_query("How many applications do I have?")
        if valid:
            print("✅ Query validation working")
        else:
            print(f"❌ Query validation failed: {msg}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing AI service: {e}")
        return False

if __name__ == "__main__":
    print("Testing Gemini API integration...\n")
    
    if test_gemini_installation():
        print()
        if test_ai_service():
            print("\n🎉 All tests passed! The /search command should work.")
        else:
            print("\n❌ AI service test failed.")
    else:
        print("\n❌ Gemini installation test failed.")

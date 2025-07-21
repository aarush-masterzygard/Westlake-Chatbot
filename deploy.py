#!/usr/bin/env python3
"""
Deployment script for Beachside Chatbot
Run this to start the Streamlit app locally
"""

import subprocess
import sys
import os

def check_requirements():
    """Check if all required packages are installed"""
    try:
        import streamlit
        import langchain
        import openai
        import faiss
        print("✅ All required packages are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing package: {e}")
        print("Run: pip install -r requirements.txt")
        return False

def check_api_key():
    """Check if API key is configured"""
    from dotenv import load_dotenv
    load_dotenv(dotenv_path="Environment/API-Key.env")
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "your-openai-api-key-here":
        print("❌ OpenAI API key not configured")
        print("Please add your API key to Environment/API-Key.env")
        return False
    
    print("✅ API key configured")
    return True

def check_vector_db():
    """Check if vector database exists"""
    if os.path.exists("index.faiss/index.faiss"):
        print("✅ Vector database found")
        return True
    else:
        print("❌ Vector database not found")
        print("Run Source/6_LoadWebsiteData.py first to create the vector database")
        return False

def main():
    print("🌊 Beachside Chatbot Deployment Check")
    print("=" * 40)
    
    # Run all checks
    checks_passed = all([
        check_requirements(),
        check_api_key(),
        check_vector_db()
    ])
    
    if checks_passed:
        print("\n✅ All checks passed! Starting Streamlit app...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", "Source/7_Chatbot.py"])
    else:
        print("\n❌ Some checks failed. Please fix the issues above before deploying.")

if __name__ == "__main__":
    main()
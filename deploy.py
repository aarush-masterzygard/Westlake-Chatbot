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
    """Check if API key is configured - prioritize Streamlit secrets"""
    from dotenv import load_dotenv
    import streamlit as st
    
    # Load environment variables as fallback
    load_dotenv(dotenv_path="Environment/API-Key.env")
    
    api_key = None
    source = ""
    
    # First try Streamlit secrets (check both possible locations)
    try:
        secrets_paths = [
            "Source/.streamlit/secrets.toml",  # App-level (where Streamlit looks when running Source/7_Chatbot.py)
            ".streamlit/secrets.toml"          # Root-level (backup)
        ]
        
        for secrets_path in secrets_paths:
            if os.path.exists(secrets_path):
                with open(secrets_path, "r") as f:
                    content = f.read()
                    if "OPENAI_API_KEY" in content and "sk-" in content:
                        api_key = "found_in_secrets"
                        source = f"Streamlit secrets ({secrets_path})"
                        break
    except Exception:
        pass
    
    # Fallback to environment variable
    if not api_key:
        api_key = os.getenv("OPENAI_API_KEY")
        source = "environment variable"
    
    if not api_key or api_key == "your-openai-api-key-here":
        print("❌ OpenAI API key not configured")
        print("Please add your API key to:")
        print("  - Source/.streamlit/secrets.toml (for deployment)")
        print("  - Environment/API-Key.env (for local development)")
        return False
    
    print(f"✅ API key configured from {source}")
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
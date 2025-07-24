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
            ".streamlit/secrets.toml",         # Root-level (where Streamlit looks)
            "Source/.streamlit/secrets.toml"   # App-level (backup)
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
    """Check if vector database exists in the correct location"""
    # Check both possible locations
    db_paths = [
        "Source/index.faiss/index.faiss",  # New location
        "index.faiss/index.faiss"          # Old location (fallback)
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            # Also check for the pickle file
            pkl_path = os.path.join(os.path.dirname(db_path), "index.pkl")
            if os.path.exists(pkl_path):
                print(f"✅ Vector database found at {db_path}")
                
                # Get file sizes for verification
                faiss_size = os.path.getsize(db_path)
                pkl_size = os.path.getsize(pkl_path)
                print(f"   📊 FAISS index: {faiss_size:,} bytes")
                print(f"   📊 Metadata: {pkl_size:,} bytes")
                
                # Try to get vector count (basic validation)
                try:
                    import faiss
                    index = faiss.read_index(db_path)
                    print(f"   📊 Vector count: {index.ntotal:,} vectors")
                except Exception as e:
                    print(f"   ⚠️ Could not read vector count: {e}")
                
                return True
            else:
                print(f"⚠️ Found FAISS index but missing metadata file: {pkl_path}")
    
    print("❌ Vector database not found")
    print("Expected locations:")
    for path in db_paths:
        print(f"  - {path}")
    print("Run 'python Source/6_LoadWebsiteData.py' to create the vector database")
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
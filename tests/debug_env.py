#!/usr/bin/env python3
"""
Debug script to check environment variables
"""
import os
from pathlib import Path

def debug_environment():
    """Debug environment variables."""
    print("🔍 Environment Variable Debug")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path(".env")
    print(f"📁 .env file exists: {env_file.exists()}")
    
    if env_file.exists():
        print(f"📄 .env file size: {env_file.stat().st_size} bytes")
        print("\n📋 .env file contents:")
        print("-" * 30)
        try:
            with open(env_file, 'r') as f:
                content = f.read()
                print(content[:500] + "..." if len(content) > 500 else content)
        except Exception as e:
            print(f"❌ Error reading .env file: {e}")
    
    # Check environment variables
    print(f"\n🔧 Environment Variables:")
    print("-" * 30)
    
    # Check CORS origins specifically
    cors_origins = os.getenv("BACKEND_CORS_ORIGINS")
    print(f"BACKEND_CORS_ORIGINS: {repr(cors_origins)}")
    
    # Check other key variables
    key_vars = [
        "SECRET_KEY",
        "DATABASE_URL", 
        "POSTGRES_HOST",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "ALPHA_VANTAGE_API_KEY"
    ]
    
    for var in key_vars:
        value = os.getenv(var)
        if value:
            # Hide sensitive data
            if "KEY" in var or "PASSWORD" in var:
                display_value = f"{value[:10]}..." if len(value) > 10 else "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: Not set")
    
    # Try to load the dotenv file manually
    print(f"\n🔄 Manual .env loading test:")
    print("-" * 30)
    try:
        from dotenv import load_dotenv
        load_dotenv()
        cors_after_load = os.getenv("BACKEND_CORS_ORIGINS")
        print(f"BACKEND_CORS_ORIGINS after load_dotenv(): {repr(cors_after_load)}")
        
        if cors_after_load:
            print(f"Type: {type(cors_after_load)}")
            print(f"Length: {len(cors_after_load)}")
            print(f"Starts with '[': {cors_after_load.startswith('[') if cors_after_load else 'N/A'}")
        
    except ImportError:
        print("❌ python-dotenv not installed")
    except Exception as e:
        print(f"❌ Error loading .env: {e}")

if __name__ == "__main__":
    debug_environment()
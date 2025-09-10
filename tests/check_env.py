#!/usr/bin/env python3
"""
Environment variables checker to debug configuration issues.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

def check_env_file():
    """Check if .env file exists and what variables it contains."""
    env_path = Path(".env")
    
    print("🔍 Environment File Check")
    print("=" * 40)
    
    if not env_path.exists():
        print("❌ .env file not found")
        print("💡 Create .env file from .env.example")
        return False
    
    print("✅ .env file found")
    
    # Load .env file
    load_dotenv()
    
    # Expected variables
    expected_vars = [
        "SECRET_KEY",
        "ALPHA_VANTAGE_API_KEY", 
        "POSTGRES_HOST",
        "POSTGRES_PORT",
        "POSTGRES_DB", 
        "POSTGRES_USER",
        "POSTGRES_PASSWORD"
    ]
    
    print("\n📋 Expected Variables:")
    for var in expected_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "SECRET" in var or "PASSWORD" in var or "KEY" in var:
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"  ✅ {var} = {display_value}")
        else:
            print(f"  ❌ {var} = NOT SET")
    
    # Check for unexpected postgres variables
    print("\n🔍 All POSTGRES Variables:")
    postgres_vars = {k: v for k, v in os.environ.items() if k.startswith("POSTGRES")}
    
    for var, value in postgres_vars.items():
        if "PASSWORD" in var:
            display_value = "***"
        else:
            display_value = value
        print(f"  {var} = {display_value}")
    
    # Check for problematic variables
    problematic = ["POSTGRES_NAME", "POSTGRES_DATABASE", "DATABASE_NAME"]
    found_problematic = []
    
    for var in problematic:
        if os.getenv(var):
            found_problematic.append(var)
            print(f"  ⚠️  {var} = {os.getenv(var)} (UNEXPECTED)")
    
    if found_problematic:
        print(f"\n❌ Found unexpected variables: {found_problematic}")
        print("💡 These might be causing the validation error")
        print("   Remove them from your .env file or environment")
        return False
    
    return True

def check_environment():
    """Check current environment variables."""
    print("\n🌍 Current Environment Variables")
    print("=" * 40)
    
    # Show all environment variables starting with common prefixes
    prefixes = ["POSTGRES", "ALPHA", "SECRET", "DEBUG", "APP_"]
    
    for prefix in prefixes:
        matching_vars = {k: v for k, v in os.environ.items() if k.startswith(prefix)}
        
        if matching_vars:
            print(f"\n{prefix}* variables:")
            for var, value in matching_vars.items():
                if any(sensitive in var for sensitive in ["SECRET", "PASSWORD", "KEY"]):
                    display_value = "***"
                else:
                    display_value = value
                print(f"  {var} = {display_value}")

def test_config_import():
    """Test importing the configuration."""
    print("\n⚙️  Configuration Import Test")
    print("=" * 40)
    
    try:
        from app.core.config import settings
        print("✅ Configuration imported successfully")
        
        print(f"\n📊 Loaded Configuration:")
        print(f"  APP_NAME: {settings.APP_NAME}")
        print(f"  ENVIRONMENT: {settings.ENVIRONMENT}")
        print(f"  DEBUG: {settings.DEBUG}")
        print(f"  DATABASE_URL: {settings.DATABASE_URL[:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration import failed: {e}")
        print(f"   Error type: {type(e).__name__}")
        
        if "extra_forbidden" in str(e):
            print("\n💡 This is likely caused by extra environment variables")
            print("   Check your .env file for variables not defined in Settings class")
        
        return False

def main():
    """Main diagnostic function."""
    print("🔧 ZSPRD Backend Environment Diagnostic")
    print("=" * 50)
    
    # Check .env file
    env_ok = check_env_file()
    
    # Check environment
    check_environment()
    
    # Test config import
    config_ok = test_config_import()
    
    print("\n" + "=" * 50)
    if env_ok and config_ok:
        print("🎉 Environment configuration looks good!")
        print("   Try running the server: python run_server.py")
    else:
        print("⚠️  Environment issues found")
        print("\n🔧 Suggested fixes:")
        print("1. Check your .env file for typos")
        print("2. Remove any unexpected POSTGRES_* variables")
        print("3. Ensure all required variables are set")
        print("4. Use the provided .env.example as a template")

if __name__ == "__main__":
    main()
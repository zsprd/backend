#!/usr/bin/env python3
"""
ZSPRD Backend Configuration Test
Run this to verify your configuration is working properly.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_config():
    """Test if the configuration loads properly."""
    print("🔧 Testing ZSPRD Backend Configuration...")
    print("=" * 50)
    
    try:
        # Test importing the config
        from app.core.config import settings
        print("✅ Configuration loaded successfully!")
        print(f"   • App Name: {settings.APP_NAME}")
        print(f"   • Environment: {settings.ENVIRONMENT}")
        print(f"   • Debug Mode: {settings.DEBUG}")
        print(f"   • CORS Origins: {settings.BACKEND_CORS_ORIGINS}")
        print(f"   • Database: {settings.POSTGRES_DB}@{settings.POSTGRES_HOST}")
        
        # Test database URL
        if settings.DATABASE_URL:
            print(f"   • Database URL: {settings.DATABASE_URL[:50]}...")
        
        print("\n🎉 Configuration test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        print("\n💡 Tips to fix this:")
        print("   1. Make sure you have a .env file in the backend directory")
        print("   2. Check that BACKEND_CORS_ORIGINS is properly formatted")
        print("   3. Verify all required environment variables are set")
        return False

def test_database_connection():
    """Test database connection."""
    print("\n🔗 Testing Database Connection...")
    print("-" * 30)
    
    try:
        import psycopg2
        from app.core.config import settings
        
        # Test connection
        conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            database=settings.POSTGRES_DB,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD
        )
        conn.close()
        print("✅ Database connection successful!")
        return True
        
    except ImportError:
        print("⚠️  psycopg2 not installed. Run: pip install psycopg2-binary")
        return False
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("\n💡 Make sure PostgreSQL is running and credentials are correct")
        return False

def main():
    """Run all configuration tests."""
    print("🚀 ZSPRD Backend Health Check")
    print("=" * 50)
    
    # Test config
    config_ok = test_config()
    
    # Test database (only if config is OK)
    db_ok = test_database_connection() if config_ok else False
    
    # Summary
    print("\n📋 Summary:")
    print(f"   • Configuration: {'✅ OK' if config_ok else '❌ FAILED'}")
    print(f"   • Database: {'✅ OK' if db_ok else '❌ FAILED'}")
    
    if config_ok and db_ok:
        print("\n🎉 All tests passed! Your backend is ready to run.")
        print("   Run: python run_server.py")
    else:
        print("\n⚠️  Please fix the issues above before starting the server.")
    
    return config_ok and db_ok

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
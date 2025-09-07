#!/usr/bin/env python3
"""
Debug script to identify which imports are causing Pydantic errors.
Run this to find the specific problematic schema.
"""

import sys
import traceback

def test_import(module_name, description):
    """Test importing a specific module and report results."""
    try:
        print(f"Testing {description}...")
        exec(f"import {module_name}")
        print(f"✅ {description} - OK")
        return True
    except Exception as e:
        print(f"❌ {description} - ERROR: {e}")
        if "--verbose" in sys.argv:
            traceback.print_exc()
        return False

def main():
    """Run import tests for all components."""
    print("🔍 ZSPRD Backend Import Debug")
    print("=" * 50)
    
    success_count = 0
    total_count = 0
    
    # Test core imports first
    tests = [
        ("app.core.config", "Core Configuration"),
        ("app.core.database", "Database Setup"),
        ("app.core.auth", "Authentication"),
        ("app.models.enums", "Database Enums"),
        ("app.models.base", "Base Model"),
        ("app.models.user", "User Model"),
        ("app.models.account", "Account Models"),
        ("app.models.security", "Security Model"),
        ("app.models.holding", "Holding Models"),
        ("app.models.transaction", "Transaction Models"),
        ("app.models.market_data", "Market Data Models"),
        ("app.schemas.user", "User Schemas"),
        ("app.schemas.account", "Account Schemas"),
        ("app.schemas.security", "Security Schemas"),
        ("app.schemas.holding", "Holding Schemas"),
        ("app.schemas.transaction", "Transaction Schemas"),
        ("app.schemas.market_data", "Market Data Schemas"),
        ("app.schemas.analytics", "Analytics Schemas"),
        ("app.crud.base", "Base CRUD"),
        ("app.crud.user", "User CRUD"),
        ("app.crud.account", "Account CRUD"),
        ("app.crud.security", "Security CRUD"),
        ("app.crud.holding", "Holding CRUD"),
        ("app.crud.transaction", "Transaction CRUD"),
        ("app.crud.market_data", "Market Data CRUD"),
        ("app.services.analytics_service", "Analytics Service"),
        ("app.utils.calculations", "Financial Calculations"),
        ("app.utils.alpha_vantage", "Alpha Vantage Client"),
        ("app.utils.rate_limiter", "Rate Limiter"),
        ("app.api.deps", "API Dependencies"),
        ("app.api.v1.auth", "Auth Endpoints"),
        ("app.api.v1.users", "User Endpoints"),
        ("app.api.v1.accounts", "Account Endpoints"),
        ("app.api.v1.holdings", "Holdings Endpoints"),
        ("app.api.v1.transactions", "Transaction Endpoints"),
        ("app.api.v1.analytics", "Analytics Endpoints"),
        ("app.api.v1.market_data", "Market Data Endpoints"),
        ("app.api.v1.router", "API Router"),
    ]
    
    for module, description in tests:
        total_count += 1
        if test_import(module, description):
            success_count += 1
        print()
    
    # Test main app import
    print("Testing Main FastAPI App...")
    total_count += 1
    try:
        import main
        print("✅ Main FastAPI App - OK")
        success_count += 1
    except Exception as e:
        print(f"❌ Main FastAPI App - ERROR: {e}")
        if "--verbose" in sys.argv:
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {success_count}/{total_count} imports successful")
    
    if success_count == total_count:
        print("🎉 All imports working! Your backend should start successfully.")
    else:
        print("⚠️  Some imports failed. Fix the errors above before starting the server.")
        print("\n💡 Tips:")
        print("- Check for typos in field names")
        print("- Ensure all __init__.py files exist")
        print("- Verify Pydantic schema syntax")
        print("- Run with --verbose for detailed error messages")
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Diagnostic script to identify router import issues.
"""

import sys
import traceback

def test_individual_endpoints():
    """Test importing each endpoint module individually."""
    print("🔍 Testing Individual Endpoint Imports")
    print("=" * 50)
    
    endpoints = [
        ("app.api.v1.auth", "Authentication endpoints"),
        ("app.api.v1.users", "User endpoints"),
        ("app.api.v1.accounts", "Account endpoints"),
        ("app.api.v1.holdings", "Holdings endpoints"),
        ("app.api.v1.transactions", "Transaction endpoints"),
        ("app.api.v1.analytics", "Analytics endpoints"),
        ("app.api.v1.market_data", "Market data endpoints"),
    ]
    
    failed_imports = []
    
    for module, description in endpoints:
        try:
            print(f"Testing {description}...")
            __import__(module)
            print(f"✅ {description} - OK")
        except Exception as e:
            print(f"❌ {description} - FAILED: {e}")
            failed_imports.append((module, str(e)))
            if "--verbose" in sys.argv:
                traceback.print_exc()
        print()
    
    return failed_imports

def test_router_import():
    """Test importing the main router."""
    print("🔗 Testing Main Router Import")
    print("=" * 30)
    
    try:
        print("Importing API router...")
        from app.api.v1.router import api_router
        print("✅ Router imported successfully")
        print(f"   Router type: {type(api_router)}")
        
        # Check if router has routes
        if hasattr(api_router, 'routes'):
            print(f"   Number of routes: {len(api_router.routes)}")
            for route in api_router.routes[:5]:  # Show first 5 routes
                if hasattr(route, 'path'):
                    print(f"   Route: {route.path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Router import failed: {e}")
        if "--verbose" in sys.argv:
            traceback.print_exc()
        return False

def test_dependencies():
    """Test importing dependencies."""
    print("📦 Testing Dependencies")
    print("=" * 25)
    
    deps = [
        ("app.api.deps", "API dependencies"),
        ("app.crud.user", "User CRUD"),
        ("app.crud.account", "Account CRUD"),
        ("app.services.analytics_service", "Analytics service"),
    ]
    
    for module, description in deps:
        try:
            print(f"Testing {description}...")
            __import__(module)
            print(f"✅ {description} - OK")
        except Exception as e:
            print(f"❌ {description} - FAILED: {e}")
            if "--verbose" in sys.argv:
                traceback.print_exc()
        print()

def test_main_app():
    """Test the main FastAPI app."""
    print("🚀 Testing Main FastAPI App")
    print("=" * 30)
    
    try:
        print("Importing main app...")
        from main import app
        print("✅ Main app imported")
        
        # Check if app has routes
        print(f"   App type: {type(app)}")
        if hasattr(app, 'routes'):
            print(f"   Total routes: {len(app.routes)}")
            
            print("\n📋 Available routes:")
            for route in app.routes:
                if hasattr(route, 'path'):
                    print(f"   {route.path}")
                elif hasattr(route, 'path_regex'):
                    print(f"   {route.path_regex.pattern}")
        
        return True
        
    except Exception as e:
        print(f"❌ Main app import failed: {e}")
        if "--verbose" in sys.argv:
            traceback.print_exc()
        return False

def create_minimal_router():
    """Create a minimal working router for testing."""
    print("\n🔧 Creating Minimal Test Router")
    print("=" * 35)
    
    try:
        from fastapi import APIRouter
        
        # Create minimal test router
        test_router = APIRouter()
        
        @test_router.get("/test")
        async def test_endpoint():
            return {"message": "Test endpoint working"}
        
        @test_router.get("/accounts")
        async def test_accounts():
            return {"message": "Test accounts endpoint"}
        
        # Save to a test file
        router_code = '''
from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def test_endpoint():
    return {"message": "Test endpoint working"}

@router.get("/accounts")
async def test_accounts():
    return {"accounts": [], "message": "Minimal accounts endpoint"}

@router.get("/analytics/performance")
async def test_performance():
    return {"total_return": 0.0, "message": "Minimal performance endpoint"}
'''
        
        with open("test_router.py", "w") as f:
            f.write(router_code)
        
        print("✅ Created test_router.py")
        print("💡 You can use this for testing if the main router fails")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create test router: {e}")
        return False

def main():
    """Main diagnostic function."""
    print("🔍 ZSPRD API Router Diagnostic")
    print("=" * 50)
    
    # Test dependencies first
    test_dependencies()
    
    # Test individual endpoints
    failed_endpoints = test_individual_endpoints()
    
    # Test main router
    router_ok = test_router_import()
    
    # Test main app
    app_ok = test_main_app()
    
    # Create minimal router as fallback
    create_minimal_router()
    
    print("\n" + "=" * 50)
    print("📊 Diagnostic Summary")
    print("=" * 50)
    
    if failed_endpoints:
        print("❌ Failed endpoint imports:")
        for module, error in failed_endpoints:
            print(f"   {module}: {error}")
    
    if not router_ok:
        print("❌ Router import failed")
        print("💡 Try fixing the endpoint imports above")
    
    if not app_ok:
        print("❌ Main app issues")
    
    if router_ok and app_ok and not failed_endpoints:
        print("✅ All imports working!")
        print("🤔 The 404 issue might be elsewhere:")
        print("   1. Check if routes are properly registered")
        print("   2. Verify the API prefix is correct")
        print("   3. Restart the server")
    else:
        print("\n🔧 Suggested fixes:")
        print("1. Fix the failed imports shown above")
        print("2. Use the minimal test_router.py as a starting point")
        print("3. Add imports back one by one to identify the problem")
        print("4. Run with --verbose for detailed error traces")

if __name__ == "__main__":
    main()
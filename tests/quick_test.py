#!/usr/bin/env python3
"""
Quick diagnostic test to identify the exact Pydantic issue.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

def test_pydantic_basic():
    """Test basic Pydantic functionality."""
    try:
        from pydantic import BaseModel, Field
        from typing import Optional
        
        class TestModel(BaseModel):
            name: str
            value: Optional[int] = None
            
        test = TestModel(name="test")
        print("✅ Basic Pydantic working")
        return True
    except Exception as e:
        print(f"❌ Basic Pydantic failed: {e}")
        return False

def test_enums():
    """Test enum imports."""
    try:
        from app.models.enums import AccountCategory, SecurityCategory
        print("✅ Enums working")
        return True
    except Exception as e:
        print(f"❌ Enums failed: {e}")
        return False

def test_config():
    """Test config import."""
    try:
        from app.core.config import settings
        print("✅ Config working")
        return True
    except Exception as e:
        print(f"❌ Config failed: {e}")
        return False

def test_individual_schemas():
    """Test each schema individually."""
    schemas = [
        ("app.schemas.user", "User schemas"),
        ("app.schemas.account", "Account schemas"),
        ("app.schemas.security", "Security schemas"),
        ("app.schemas.market_data", "Market data schemas"),
        ("app.schemas.holding", "Holding schemas"),
        ("app.schemas.transaction", "Transaction schemas"),
        ("app.schemas.analytics", "Analytics schemas"),
    ]
    
    success = True
    for module, name in schemas:
        try:
            __import__(module)
            print(f"✅ {name} working")
        except Exception as e:
            print(f"❌ {name} failed: {e}")
            success = False
    
    return success

def main():
    print("🔍 Quick Diagnostic Test")
    print("=" * 30)
    
    tests = [
        test_pydantic_basic,
        test_enums,
        test_config,
        test_individual_schemas,
    ]
    
    all_passed = True
    for test in tests:
        try:
            result = test()
            all_passed = all_passed and result
        except Exception as e:
            print(f"❌ Test failed: {e}")
            all_passed = False
        print()
    
    if all_passed:
        print("🎉 All tests passed! Try starting the server again.")
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        print("\n💡 Try these fixes:")
        print("1. Update requirements: pip install -r requirements.txt")
        print("2. Check Python version: python --version (need 3.11+)")
        print("3. Verify all files are in the correct locations")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
#!/usr/bin/env python3
"""
Minimal FastAPI app to test basic functionality.
Use this to isolate Pydantic issues.
"""

from fastapi import FastAPI
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create minimal FastAPI app
app = FastAPI(
    title="ZSPRD Backend - Minimal Test",
    version="1.0.0",
    description="Minimal app to test basic functionality"
)

@app.get("/")
async def root():
    return {"message": "Minimal FastAPI app is working!"}

@app.get("/health")
async def health():
    return {"status": "healthy", "message": "Basic app working"}

# Try to import components one by one
try:
    from app.core.config import settings
    logger.info("✅ Config imported successfully")
    
    @app.get("/config-test")
    async def config_test():
        return {
            "app_name": settings.APP_NAME,
            "environment": settings.ENVIRONMENT,
            "database_configured": bool(settings.DATABASE_URL)
        }
except Exception as e:
    logger.error(f"❌ Config import failed: {e}")

try:
    from app.models.enums import AccountType, SecurityType
    logger.info("✅ Enums imported successfully")
    
    @app.get("/enums-test")
    async def enums_test():
        return {
            "account_types": [t.value for t in AccountType],
            "security_types": [t.value for t in SecurityType]
        }
except Exception as e:
    logger.error(f"❌ Enums import failed: {e}")

try:
    from app.schemas.user import User, UserCreate
    logger.info("✅ User schemas imported successfully")
    
    @app.get("/user-schema-test")
    async def user_schema_test():
        return {"message": "User schemas working"}
except Exception as e:
    logger.error(f"❌ User schemas import failed: {e}")

try:
    from app.schemas.account import Account, AccountCreate
    logger.info("✅ Account schemas imported successfully")
    
    @app.get("/account-schema-test")
    async def account_schema_test():
        return {"message": "Account schemas working"}
except Exception as e:
    logger.error(f"❌ Account schemas import failed: {e}")

if __name__ == "__main__":
    import uvicorn
    
    print("🧪 Starting minimal FastAPI test app...")
    print("If this works, the issue is in the full app imports.")
    print("Visit http://localhost:8001 to test")
    
    uvicorn.run(
        "minimal_main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
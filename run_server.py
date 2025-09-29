"""
run_server.py: Development server startup script

- Performs environment checks, DB connectivity tests, and model imports
- Ensures all models are registered before starting the FastAPI app
- For production, use main:app as the entry point for Uvicorn/Gunicorn
- For development, run this script directly (python run_server.py)
"""

import asyncio
import importlib
import logging
import pkgutil
import sys
from pathlib import Path

import uvicorn
from sqlalchemy import text

import app as app_pkg

# Import after path setup
from app.core.config import settings
from app.core.database import async_engine, async_session_maker
from app.core.redis import redis_client

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def check_environment():
    """Check if all required environment variables are set."""
    required_vars = ["SECRET_KEY", "DATABASE_URL"]

    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var)

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file")
        return False

    return True


async def test_database_connection():
    """Test database connectivity."""
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.error("Please ensure PostgreSQL is running and credentials are correct")
        return False


async def test_redis_connection():
    """Test Redis connectivity."""
    try:
        if redis_client.is_available():
            logger.info("✅ Redis connection successful")
            logger.info("   - Token blacklist: Redis backend")
            logger.info("   - Rate limiting: Redis backend")
            logger.info("   - Caching: Redis backend")
            return True
        else:
            logger.warning("⚠️  Redis unavailable - using in-memory fallback")
            logger.warning("   - Token blacklist: In-memory (NOT production ready)")
            logger.warning("   - Rate limiting: In-memory (NOT distributed)")
            logger.warning("   - Caching: In-memory (NOT distributed)")
            return True  # Don't fail startup, just warn
    except Exception as e:
        logger.error(f"⚠️  Redis connection check failed: {e}")
        logger.warning("   - Continuing with in-memory fallback")
        return True  # Don't fail startup


async def create_tables() -> bool:
    """Create database tables if they don't exist."""
    try:
        # Import all models to ensure they're registered
        from app.core.model import Base
        from app.user.accounts.model import UserAccount  # ensures user model is registered

        for finder, name, ispkg in pkgutil.walk_packages(app_pkg.__path__, app_pkg.__name__ + "."):
            if name.endswith(".model"):
                importlib.import_module(name)

        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("✅ Database tables created/verified")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to create tables: {e}")
        return False


def print_startup_info():
    """Print startup information."""
    print("\n" + "=" * 60)
    print("🚀 ZSPRD Portfolio Analytics Backend")
    print("=" * 60)
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Debug Mode: {settings.DEBUG}")
    print(f"Database: {settings.POSTGRES_DB}@{settings.POSTGRES_HOST}")
    if redis_client.is_available():
        print(f"Redis: ✅ Connected")
    else:
        print(f"Redis: ⚠️ Unavailable (using in-memory fallback)")
    print(f"API Version: {settings.API_PREFIX}")
    print(f"CORS Origins: {settings.CORS_ORIGINS}")
    print("=" * 60)
    print("\n📋 Available Endpoints:")
    print("  • Health Check: http://localhost:8000/health")
    print("  • API Docs: http://localhost:8000/api/v1/docs")
    print("  • ReDoc: http://localhost:8000/api/v1/redoc")
    print("  • OpenAPI JSON: http://localhost:8000/api/v1/openapi.json")
    print("\n🔑 API Endpoints:")
    print("  • Authentication: /api/v1/auth/*")
    print("  • Users: /api/v1/users/*")
    print("  • Accounts: /api/v1/accounts/*")
    print("  • Holdings: /api/v1/holdings/*")
    print("  • Transactions: /api/v1/transactions/*")
    print("  • Analytics: /api/v1/analytics/*")
    print("  • Market Data: /api/v1/market-data/*")
    print("\n💡 Tips:")
    print("  • Use the interactive API docs to test endpoints")
    print("  • Check logs for any issues during startup")
    print("  • Ensure your frontend is configured to use these endpoints")
    print("=" * 60 + "\n")


async def main() -> None:
    """Main startup function."""
    print("🔧 Starting ZSPRD Portfolio Analytics Backend...")

    # Check environment
    if not check_environment():
        sys.exit(1)

    # Test database
    if not await test_database_connection():
        sys.exit(1)

    # Test Redis (don't fail if unavailable)
    await test_redis_connection()

    # Create tables
    if not await create_tables():
        sys.exit(1)

    # Print startup info
    print_startup_info()

    # Start server
    config = uvicorn.Config(
        app="main:app",
        host="127.0.0.1",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        reload_dirs=[str(current_dir)] if settings.DEBUG else None,
    )

    server = uvicorn.Server(config)

    try:
        logger.info("🚀 Starting FastAPI server...")
        await server.serve()
    except KeyboardInterrupt:
        logger.info("👋 Server shutdown requested")
    except Exception as e:
        logger.error(f"❌ Server error: {e}")
        sys.exit(1)
    finally:
        # Always dispose DB connections on shutdown
        logger.info("🧹 Disposing database engine...")
        await async_engine.dispose()
        logger.info("✅ Database engine disposed")

        # Add Redis cleanup
        redis_client.close()
        logger.info("✅ Redis connection closed")


def run_development_server():
    """Run the development server with all checks."""
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print(
            "❌ Error: main.py not found. Please run this script from the project root directory."
        )
        sys.exit(1)

    # Check if .env file exists
    if not Path(".env").exists():
        print("⚠️  Warning: .env file not found. Please create one based on .env.example")
        if input("Continue anyway? (y/N): ").lower() != "y":
            sys.exit(1)

    run_development_server()

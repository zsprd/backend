"""
ZSPRD Portfolio Analytics Backend - Development Server
This script starts the FastAPI development server with proper configuration.
"""

import asyncio
import logging
import sys
from pathlib import Path

import uvicorn
from sqlalchemy import text

# Import after path setup
from app.core.config import settings
from app.core.database import SessionLocal, engine
from app.core.model import Base

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
    required_vars = ["SECRET_KEY", "ALPHA_VANTAGE_API_KEY", "DATABASE_URL"]

    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var)

    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.error("Please check your .env file")
        return False

    return True


def test_database_connection():
    """Test database connectivity."""
    try:
        # Test connection
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        logger.info("✅ Database connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        logger.error("Please ensure PostgreSQL is running and credentials are correct")
        return False


def create_tables():
    """Create database tables if they don't exist."""
    try:
        # Import all models to ensure they're registered
        from app.portfolio.accounts import model
        from app.portfolio.holdings import model
        from app.portfolio.transactions import model
        from app.provider.connections import model
        from app.provider.institutions import model
        from app.provider.mappings import model
        from app.security.master import model
        from app.security.prices import model
        from app.user.accounts import model
        from app.user.sessions import model

        # Create tables
        Base.metadata.create_all(bind=engine)
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
    print(f"API Version: {settings.API_VERSION}")
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


async def main():
    """Main startup function."""
    print("🔧 Starting ZSPRD Portfolio Analytics Backend...")

    # Check environment
    if not check_environment():
        sys.exit(1)

    # Test database
    if not test_database_connection():
        sys.exit(1)

    # Create tables
    if not create_tables():
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


# Additional utility functions for development
def create_test_user():
    """Create a test users for development."""
    from app.user.accounts.crud import CRUDUserAccount as user_crud

    db = SessionLocal()
    try:
        # Check if test users exists
        existing_user = user_crud.get_by_email(db, email="test@zsprd.com")
        if existing_user:
            logger.info("Test users already exists")
            return

        # Create test users
        user_data = {
            "email": "test@zsprd.com",
            "full_name": "Test UserProfile",
            "is_active": True,
            "is_verified": True,
            "base_currency": "USD",
        }

        user = user_crud.create_from_dict(db, obj_in=user_data)
        logger.info(f"Created test users: {user.email} (ID: {user.id})")

    except Exception as e:
        logger.error(f"Failed to create test users: {e}")
    finally:
        db.close()


def create_sample_data():
    """Create sample data for development and testing."""
    logger.info("Creating sample data...")

    # This would create sample accounts, securities, holdings, etc.
    # For now, just create a test users
    create_test_user()


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="ZSPRD Backend Development Server")
    parser.add_argument(
        "--create-sample-data",
        action="store_true",
        help="Create sample data for testing",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only check environment and database, don't start server",
    )

    args = parser.parse_args()

    if args.create_sample_data:
        create_sample_data()
        sys.exit(0)

    if args.check_only:
        if check_environment() and test_database_connection():
            print("✅ All checks passed!")
            sys.exit(0)
        else:
            print("❌ Some checks failed")
            sys.exit(1)

    run_development_server()

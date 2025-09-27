import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from main import app

from app.auth import schema
from app.auth.service import AuthService
from app.core.config import Settings
from app.core.database import Base, get_async_db
from app.core.dependencies import get_auth_service


class TestSettings(Settings):
    """Test-specific settings that load from .env.test file."""

    # Add any test-specific fields that might be in your .env.test
    SLOWAPI_ENABLED: bool = False  # Rate limiting for tests

    class Config:
        env_file = ".env.test"
        extra = "ignore"  # Ignore extra fields that aren't defined


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings():
    """Provide test-specific settings from .env.test."""
    return TestSettings()


@pytest_asyncio.fixture(scope="session")
async def test_engine(test_settings):
    """Create async engine for testing using test settings."""

    if not test_settings.DATABASE_URL:
        pytest.skip("TEST DATABASE_URL is not set in .env.test")

    # Create test engine with the same pattern as main database.py
    engine = create_async_engine(
        test_settings.DATABASE_URL,
        echo=test_settings.DEBUG,
        # PostgreSQL-specific pooling configuration for tests
        pool_pre_ping=True,
        pool_recycle=300,
        pool_timeout=30,
        pool_size=5,
        max_overflow=10,
    )

    # Test the connection
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception as e:
        await engine.dispose()
        pytest.skip(f"Test database connection failed: {e}")

    # Create all tables
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception as e:
        await engine.dispose()
        pytest.skip(f"Could not create test database tables: {e}")

    yield engine

    # Cleanup
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    except Exception:
        pass
    finally:
        await engine.dispose()


@pytest.fixture(scope="session")
def test_session_maker(test_engine):
    """Create session maker for test database."""
    return async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def test_db_session(test_session_maker) -> AsyncGenerator[AsyncSession, None]:
    """Provide isolated database session for each test with transaction rollback."""

    async with test_session_maker() as session:
        # Start a transaction
        async with session.begin():
            yield session
            # Transaction will be rolled back automatically when exiting context


@pytest.fixture
def override_get_db(test_db_session):
    """Override the database dependency for testing."""

    def _override_get_db():
        yield test_db_session

    app.dependency_overrides[get_async_db] = _override_get_db
    yield
    app.dependency_overrides.clear()


# Mock Authentication Service
@pytest.fixture
def mock_auth_service():
    """Mock auth service for unit tests without database."""
    service = AsyncMock(spec=AuthService)

    # Configure realistic return values
    async def _register(registration_data, background_tasks=None):
        return schema.RegistrationResponse(
            message="User registered successfully. Please verify your email.",
            user_id=uuid.uuid4(),
            email_verification_required=True,
            user=schema.UserAccountRead(
                id=uuid.uuid4(),
                email=getattr(registration_data, "email", "test@example.com"),
                full_name=getattr(registration_data, "full_name", "Test User"),
                language="en",
                country="US",
                currency="USD",
                is_active=True,
                is_verified=False,
                last_login_at=None,
                is_locked=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
        )

    async def _login(signin_data, request=None):
        email = getattr(signin_data, "email", "test@example.com")
        return schema.AuthResponse(
            access_token="test-access-token",
            refresh_token="test-refresh-token",
            token_type="bearer",
            expires_in=300,
            user=schema.UserAccountRead(
                id=uuid.uuid4(),
                email=email,
                full_name="Test User",
                language="en",
                country="US",
                currency="USD",
                is_active=True,
                is_verified=True,
                last_login_at=datetime.now(timezone.utc),
                is_locked=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            ),
        )

    service.register.side_effect = _register
    service.login.side_effect = _login
    service.logout.return_value = schema.LogoutResponse(message="Logout successful.")
    service.verify_email.return_value = schema.EmailVerificationResponse(
        message="Email verified successfully.",
        user=schema.UserAccountRead(
            id=uuid.uuid4(),
            email="test@example.com",
            full_name="Test User",
            language="en",
            country="US",
            currency="USD",
            is_active=True,
            is_verified=True,
            last_login_at=None,
            is_locked=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
    )
    service.refresh.return_value = schema.TokenResponse(
        access_token="new-access-token",
        refresh_token="new-refresh-token",
        token_type="bearer",
        expires_in=300,
    )
    service.forgot_password.return_value = schema.ForgotPasswordResponse(
        message="If an account with this email exists, a password reset link has been sent."
    )
    service.reset_password.return_value = schema.PasswordResetResponse(
        message="Password reset successful."
    )

    return service


@pytest.fixture
def mock_current_user():
    """Mock current user for authenticated endpoints."""
    mock_user = MagicMock()
    mock_user.id = uuid.uuid4()
    mock_user.email = "authenticated@example.com"
    mock_user.full_name = "Authenticated User"
    mock_user.is_active = True
    mock_user.is_verified = True
    mock_user.language = "en"
    mock_user.country = "US"
    mock_user.currency = "USD"
    mock_user.is_locked = False
    mock_user.last_login_at = datetime.now(timezone.utc)
    mock_user.created_at = datetime.now(timezone.utc)
    mock_user.updated_at = datetime.now(timezone.utc)
    return mock_user


@pytest.fixture
def mock_dependencies(mock_auth_service):
    """Override dependencies with mocks for unit tests."""
    app.dependency_overrides[get_auth_service] = lambda: mock_auth_service
    yield {"auth_service": mock_auth_service}
    app.dependency_overrides.clear()


# Test Clients
@pytest.fixture
def client(mock_dependencies) -> Generator[TestClient, None, None]:
    """Test client with mocked dependencies for unit tests."""
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def async_client(mock_dependencies) -> AsyncGenerator[AsyncClient, None]:
    """Async test client with mocked dependencies for unit tests."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# Integration Test Fixtures
@pytest_asyncio.fixture
async def real_auth_service(test_db_session):
    """Real auth service with test database for integration tests."""
    from app.user.accounts.crud import CRUDUserAccount
    from app.user.sessions.crud import CRUDUserSession

    user_crud = CRUDUserAccount(test_db_session)
    session_crud = CRUDUserSession(test_db_session)
    return AuthService(user_crud, session_crud)


@pytest.fixture
async def integration_auth_headers(ensure_test_user):
    """Valid authorization headers for integration tests with real database."""
    from app.auth.tokens import create_access_token

    # Use the test user ID from ensure_test_user fixture
    test_user_id = str(ensure_test_user.id)
    token = create_access_token(test_user_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def integration_dependencies(test_db_session, real_auth_service):
    """Real dependencies for integration tests."""

    # Override database dependency to use test database
    def override_get_db():
        yield test_db_session

    # Override auth service dependency to use real auth service
    def override_get_auth_service():
        return real_auth_service

    app.dependency_overrides[get_async_db] = override_get_db
    app.dependency_overrides[get_auth_service] = override_get_auth_service

    yield {"db": test_db_session, "auth_service": real_auth_service}

    app.dependency_overrides.clear()


# Add the missing fixtures that tests expect
@pytest.fixture
def real_dependencies(integration_dependencies):
    """Alias for integration_dependencies to match test expectations."""
    return integration_dependencies


@pytest_asyncio.fixture
async def ensure_test_user(test_db_session):
    """Ensure a test user exists for JWT token validation."""
    try:
        import uuid
        from datetime import datetime, timezone

        from passlib.context import CryptContext

        from app.user.accounts.model import UserAccount

        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

        test_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

        # Always create fresh user for each test to avoid session issues
        user = UserAccount(
            id=test_user_id,
            email="testuser@example.com",
            full_name="Test User",
            hashed_password=pwd_context.hash("TestPassword123!"),  # Properly hashed password
            is_active=True,
            is_verified=True,
            language="en",
            country="US",
            currency="USD",
            failed_login_attempts=0,
            locked_until=None,
            last_login_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        # Use merge to handle potential conflicts
        user = await test_db_session.merge(user)
        await test_db_session.commit()
        await test_db_session.refresh(user)

        yield user

    except Exception as e:
        # If database setup fails, create a mock user but log the issue
        print(f"Failed to create test user: {e}")
        import uuid
        from unittest.mock import MagicMock

        mock_user = MagicMock()
        mock_user.id = uuid.UUID("00000000-0000-0000-0000-000000000001")
        mock_user.email = "testuser@example.com"
        mock_user.full_name = "Test User"
        mock_user.is_active = True
        mock_user.is_verified = True

        yield mock_user


@pytest.fixture
def integration_client(integration_dependencies) -> Generator[TestClient, None, None]:
    """Test client with real dependencies for integration tests."""
    with TestClient(app) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def integration_async_client(integration_dependencies) -> AsyncGenerator[AsyncClient, None]:
    """Async test client with real dependencies for integration tests."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# Test Data Fixtures
@pytest.fixture
def valid_registration_data():
    """Valid user registration data for testing."""
    return {
        "full_name": "John Doe",
        "email": "john.doe@example.com",
        "password": "StrongP@ssw0rd123!",
    }


@pytest.fixture
def valid_login_data():
    """Valid login data for testing."""
    return {"email": "john.doe@example.com", "password": "StrongP@ssw0rd123!"}


@pytest.fixture
def invalid_registration_data():
    """Invalid registration data for testing validation."""
    return [
        {"email": "test@example.com"},  # Missing required fields
        {
            "full_name": "Test User",
            "email": "invalid-email",
            "password": "StrongP@ss1!",
        },  # Invalid email
        {
            "full_name": "Test User",
            "email": "test@example.com",
            "password": "weak",
        },  # Weak password
        {"full_name": "", "email": "test@example.com", "password": "StrongP@ss1!"},  # Empty name
        {"full_name": "A", "email": "test@example.com", "password": "StrongP@ss1!"},  # Short name
    ]


@pytest.fixture
def auth_headers():
    """Valid authorization headers for authenticated requests."""
    from app.auth.tokens import create_access_token

    test_user_id = str(uuid.uuid4())
    token = create_access_token(test_user_id)
    return {"Authorization": f"Bearer {token}"}


# Mock External Services
@pytest.fixture
def mock_background_tasks():
    """Mock FastAPI background tasks."""
    return MagicMock()


@pytest.fixture
def mock_email_service():
    """Mock email service for testing email functionality."""
    from unittest.mock import patch

    with patch("app.core.email.send_verification_email") as mock_send:
        mock_send.return_value = True
        yield mock_send


# Pytest Configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as a unit test (fast, mocked)")
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test (slower, real dependencies)"
    )
    config.addinivalue_line("markers", "auth: mark test as authentication-related")
    config.addinivalue_line("markers", "rate_limit: mark test as rate limiting related")
    config.addinivalue_line("markers", "database: mark test as requiring database")


def pytest_collection_modifyitems(config, items):
    """Add markers to tests based on their names and fixtures."""
    for item in items:
        # Mark auth tests
        if "auth" in item.nodeid:
            item.add_marker(pytest.mark.auth)

        # Mark integration tests
        if (
            "integration" in item.name.lower()
            or any("real_" in fixture for fixture in item.fixturenames)
            or "test_db_session" in item.fixturenames
            or "integration_" in item.name.lower()
        ):
            item.add_marker(pytest.mark.integration)
            item.add_marker(pytest.mark.database)
        else:
            item.add_marker(pytest.mark.unit)

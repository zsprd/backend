import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

import types
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from main import app

from app.core.dependencies import get_current_user
from app.user.accounts.model import UserAccount
from app.user.accounts.schema import UserAccountRead


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def auth_headers():
    """Return valid JWT auth headers for test user."""
    # Replace with actual JWT generation logic if available
    return {"Authorization": "Bearer test_valid_jwt_token"}


@pytest.fixture
def test_user_data():
    """Sample user data matching UserAccountRead schema."""
    return {
        "id": str(uuid4()),
        "email": "user@example.com",
        "full_name": "Test User",
        "timezone": "UTC",
        "base_currency": "USD",
        "is_active": True,
        "is_verified": True,
        "last_login_at": datetime.now(timezone.utc).isoformat(),
        "user_sessions": [],
        "user_subscriptions": [],
        "portfolio_accounts": [],
    }


@pytest.fixture
def mock_user_account(test_user_data):
    """Create a mock SQLAlchemy UserAccount model instance."""
    user = UserAccount()
    for k, v in test_user_data.items():
        if hasattr(user, k):
            setattr(user, k, v)
    user.is_active = True
    user.is_verified = True
    user.updated_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def override_get_current_user_authenticated(test_user_data):
    """Override get_current_user dependency with Pydantic schema for authenticated tests only."""
    app.dependency_overrides[get_current_user] = lambda: UserAccountRead(**test_user_data)
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def override_update_user_profile():
    """Patch UserAccountService.update_user_profile to work with Pydantic schema in tests."""
    from app.user.accounts.service import UserAccountService

    def _mock_update_user_profile(self, db, user, profile_update):
        # Update fields in memory, return updated user
        update_data = profile_update.model_dump(exclude_unset=True)
        for k, v in update_data.items():
            setattr(user, k, v)
        return user

    UserAccountService.update_user_profile = types.MethodType(
        _mock_update_user_profile, UserAccountService
    )
    yield
    # Optionally restore original method if needed


def test_get_current_user_profile(client, auth_headers, override_get_current_user_authenticated):
    """Authenticated: should return current user's profile."""
    response = client.get("/api/v1/user/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert "id" in data
    assert data["is_active"] is True
    assert data["is_verified"] in [True, False]
    assert data["base_currency"] in ["USD", "EUR", "GBP"]


def test_get_current_user_profile_unauthenticated(client):
    """Unauthenticated: should return 403 error (FastAPI HTTPBearer default)."""
    response = client.get("/api/v1/user/me")
    assert response.status_code == 403


def test_update_current_user_profile(
    client, auth_headers, override_get_current_user_authenticated, override_update_user_profile
):
    """Authenticated: should update and return user profile."""
    update_payload = {
        "full_name": "Updated Name",
        "timezone": "America/New_York",
        "base_currency": "EUR",
    }
    response = client.put("/api/v1/user/me", json=update_payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["timezone"] == "America/New_York"
    assert data["base_currency"] == "EUR"


def test_update_current_user_profile_unauthenticated(client):
    """Unauthenticated: should return 403 error (FastAPI HTTPBearer default)."""
    update_payload = {
        "full_name": "Updated Name",
        "timezone": "America/New_York",
        "base_currency": "EUR",
    }
    response = client.put("/api/v1/user/me", json=update_payload)
    assert response.status_code == 403


def test_update_current_user_profile_invalid_currency(
    client, auth_headers, override_get_current_user_authenticated, override_update_user_profile
):
    """Invalid currency: should return 422 validation error."""
    update_payload = {"base_currency": "INVALID"}
    response = client.put("/api/v1/user/me", json=update_payload, headers=auth_headers)
    assert response.status_code == 422
    assert "detail" in response.json()

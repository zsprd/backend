import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))

from datetime import datetime, timezone
from unittest.mock import Mock, patch
from uuid import uuid4

import main
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.service import AuthError, AuthService
from app.core.config import settings
from app.core.dependencies import (
    get_async_db,
    get_auth_service,
    get_current_active_user,
)
from app.user.accounts.model import UserAccount


# Fixtures
@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def mock_auth_service():
    """Mock auth service."""
    return Mock(spec=AuthService)


@pytest.fixture
def mock_user():
    """Mock user account with actual values instead of Mock objects."""
    user = Mock(spec=UserAccount)
    # Use actual values, not Mock objects
    user.id = uuid4()
    user.email = "test@example.com"
    user.full_name = "Test User"
    user.is_active = True
    user.is_verified = True
    user.created_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    user.timezone = "UTC"
    user.base_currency = "USD"
    user.last_login_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def valid_registration_data():
    """Valid registration data."""
    return {"full_name": "John Doe", "email": "john@example.com", "password": "StrongPass123!"}


@pytest.fixture
def valid_login_data():
    """Valid login data."""
    return {"email": "john@example.com", "password": "StrongPass123!"}


@pytest.fixture
def mock_tokens():
    """Mock JWT tokens."""
    return {"access_token": "mock_access_token", "refresh_token": "mock_refresh_token"}


@pytest.fixture
def client_with_mocks(mock_db, mock_auth_service):
    """Test client with mocked dependencies."""
    main.app.dependency_overrides[get_async_db] = lambda: mock_db
    main.app.dependency_overrides[get_auth_service] = lambda: mock_auth_service

    with TestClient(main.app) as client:
        yield client

    main.app.dependency_overrides.clear()


class TestRegisterEndpoint:
    """Tests for /register endpoint."""

    def test_register_success(
        self, client_with_mocks, mock_auth_service, mock_user, valid_registration_data
    ):
        """Test successful user registration."""
        mock_auth_service.register_user.return_value = mock_user

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/register", json=valid_registration_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert (
            data["message"]
            == "User registered successfully. Please check your email for verification."
        )
        assert data["user_id"] == str(mock_user.id)
        assert data["email_verification_required"] is True
        assert "user" in data

        mock_auth_service.register_user.assert_called_once()

    def test_register_duplicate_email(
        self, client_with_mocks, mock_auth_service, valid_registration_data
    ):
        """Test registration with duplicate email."""
        mock_auth_service.register_user.side_effect = AuthError(
            "User with this email already exists"
        )

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/register", json=valid_registration_data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "User with this email already exists" in response.json()["detail"]

    def test_register_invalid_email(self, client_with_mocks, valid_registration_data):
        """Test registration with invalid email format."""
        valid_registration_data["email"] = "invalid-email"

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/register", json=valid_registration_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_register_weak_password(self, client_with_mocks, valid_registration_data):
        """Test registration with weak password."""
        valid_registration_data["password"] = "weak"

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/register", json=valid_registration_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_register_missing_fields(self, client_with_mocks):
        """Test registration with missing required fields."""
        incomplete_data = {"email": "test@example.com"}

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/register", json=incomplete_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_register_empty_full_name(self, client_with_mocks, valid_registration_data):
        """Test registration with empty full name."""
        valid_registration_data["full_name"] = ""

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/register", json=valid_registration_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_register_name_too_long(self, client_with_mocks, valid_registration_data):
        """Test registration with name exceeding max length."""
        valid_registration_data["full_name"] = "x" * 256  # Assuming 255 is max

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/register", json=valid_registration_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestLoginEndpoint:
    """Tests for /login endpoint."""

    def test_login_success(
        self, client_with_mocks, mock_auth_service, mock_user, mock_tokens, valid_login_data
    ):
        """Test successful user login."""
        # Configure mock to return a tuple
        mock_auth_service.authenticate_user.return_value = (
            mock_user,
            mock_tokens["access_token"],
            mock_tokens["refresh_token"],
        )

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/login", json=valid_login_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["access_token"] == mock_tokens["access_token"]
        assert data["refresh_token"] == mock_tokens["refresh_token"]
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert "user" in data

    def test_login_invalid_credentials(
        self, client_with_mocks, mock_auth_service, valid_login_data
    ):
        """Test login with invalid credentials."""
        mock_auth_service.authenticate_user.side_effect = AuthError("Invalid credentials")

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/login", json=valid_login_data
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Invalid credentials"

    def test_login_invalid_email_format(self, client_with_mocks, valid_login_data):
        """Test login with invalid email format."""
        valid_login_data["email"] = "invalid-email"

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/login", json=valid_login_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_login_missing_password(self, client_with_mocks):
        """Test login with missing password."""
        login_data = {"email": "test@example.com"}

        response = client_with_mocks.post(f"/api/{settings.API_PREFIX}/auth/login", json=login_data)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_login_empty_password(self, client_with_mocks, valid_login_data):
        """Test login with empty password."""
        valid_login_data["password"] = ""

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/login", json=valid_login_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestVerifyEmailEndpoint:
    """Tests for /verify-email endpoint."""

    def test_verify_email_success(self, client_with_mocks, mock_auth_service, mock_user):
        """Test successful email verification."""
        verification_data = {"token": "valid_token"}
        mock_auth_service.confirm_email.return_value = mock_user

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/verify-email", json=verification_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Email verified successfully"
        assert "user" in data

    def test_verify_email_invalid_token(self, client_with_mocks, mock_auth_service):
        """Test email verification with invalid token."""
        verification_data = {"token": "invalid_token"}
        mock_auth_service.confirm_email.side_effect = AuthError(
            "Invalid or expired confirmation token"
        )

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/verify-email", json=verification_data
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "Invalid or expired confirmation token" in response.json()["detail"]

    def test_verify_email_missing_token(self, client_with_mocks):
        """Test email verification with missing token."""
        response = client_with_mocks.post(f"/api/{settings.API_PREFIX}/auth/verify-email", json={})
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_verify_email_empty_token(self, client_with_mocks):
        """Test email verification with empty token."""
        verification_data = {"token": ""}
        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/verify-email", json=verification_data
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestRefreshTokensEndpoint:
    """Tests for /refresh endpoint."""

    def test_refresh_tokens_success(self, client_with_mocks, mock_auth_service, mock_tokens):
        """Test successful token refresh."""
        refresh_data = {"refresh_token": "valid_refresh_token"}
        # Configure mock to return a tuple
        mock_auth_service.refresh_tokens.return_value = (
            mock_tokens["access_token"],
            mock_tokens["refresh_token"],
        )

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/refresh", json=refresh_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["access_token"] == mock_tokens["access_token"]
        assert data["refresh_token"] == mock_tokens["refresh_token"]
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    def test_refresh_tokens_invalid_token(self, client_with_mocks, mock_auth_service):
        """Test token refresh with invalid refresh token."""
        refresh_data = {"refresh_token": "invalid_refresh_token"}
        mock_auth_service.refresh_tokens.side_effect = AuthError("Invalid or expired refresh token")

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/refresh", json=refresh_data
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid or expired refresh token" in response.json()["detail"]

    def test_refresh_tokens_missing_token(self, client_with_mocks):
        """Test token refresh with missing refresh token."""
        response = client_with_mocks.post(f"/api/{settings.API_PREFIX}/auth/refresh", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_refresh_tokens_empty_token(self, client_with_mocks):
        """Test token refresh with empty refresh token."""
        refresh_data = {"refresh_token": ""}
        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/refresh", json=refresh_data
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestForgotPasswordEndpoint:
    """Tests for /forgot-password endpoint."""

    def test_forgot_password_success(self, client_with_mocks, mock_auth_service):
        """Test successful password reset initiation."""
        reset_request = {"email": "test@example.com"}
        mock_auth_service.initiate_password_reset.return_value = True

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/forgot-password", json=reset_request
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "password reset instructions have been sent" in data["message"]

    def test_forgot_password_invalid_email(self, client_with_mocks):
        """Test forgot password with invalid email format."""
        reset_request = {"email": "invalid-email"}

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/forgot-password", json=reset_request
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_forgot_password_missing_email(self, client_with_mocks):
        """Test forgot password with missing email."""
        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/forgot-password", json={}
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_forgot_password_service_error(self, client_with_mocks, mock_auth_service):
        """Test forgot password with service error."""
        reset_request = {"email": "test@example.com"}
        mock_auth_service.initiate_password_reset.side_effect = AuthError("Service error")

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/forgot-password", json=reset_request
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestResetPasswordEndpoint:
    """Tests for /reset-password endpoint."""

    def test_reset_password_success(self, client_with_mocks, mock_auth_service, mock_user):
        """Test successful password reset."""
        reset_data = {"token": "valid_reset_token", "new_password": "NewStrongPass123!"}
        mock_auth_service.reset_password.return_value = mock_user

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/reset-password", json=reset_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Password reset successfully"

    def test_reset_password_invalid_token(self, client_with_mocks, mock_auth_service):
        """Test password reset with invalid token."""
        reset_data = {"token": "invalid_token", "new_password": "NewStrongPass123!"}
        mock_auth_service.reset_password.side_effect = AuthError("Invalid or expired reset token")

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/reset-password", json=reset_data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid or expired reset token" in response.json()["detail"]

    def test_reset_password_weak_password(self, client_with_mocks):
        """Test password reset with weak password."""
        reset_data = {"token": "valid_reset_token", "new_password": "weak"}

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/reset-password", json=reset_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_reset_password_missing_fields(self, client_with_mocks):
        """Test password reset with missing fields."""
        reset_data = {"token": "valid_token"}  # Missing new_password

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/reset-password", json=reset_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_reset_password_short_password(self, client_with_mocks):
        """Test password reset with too short password."""
        reset_data = {
            "token": "valid_reset_token",
            "new_password": "Short1!",  # Less than 8 characters
        }

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/reset-password", json=reset_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


class TestLogoutEndpoint:
    """Tests for /logout endpoint."""

    def test_logout_success_with_refresh_token(
        self, client_with_mocks, mock_auth_service, mock_user
    ):
        """Test successful logout with refresh token."""
        refresh_data = {"refresh_token": "valid_refresh_token"}
        mock_auth_service.sign_out.return_value = True

        # Mock authentication dependency
        main.app.dependency_overrides[get_current_active_user] = lambda: mock_user

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/logout", json=refresh_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Successfully logged out."

    def test_logout_success_without_refresh_token(
        self, client_with_mocks, mock_auth_service, mock_user
    ):
        """Test successful logout without refresh token."""
        mock_auth_service.sign_out.return_value = True

        # Mock authentication dependency
        main.app.dependency_overrides[get_current_active_user] = lambda: mock_user

        response = client_with_mocks.post(f"/api/{settings.API_PREFIX}/auth/logout")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["message"] == "Successfully logged out."

    def test_logout_unauthenticated(self, client_with_mocks):
        """Test logout without authentication."""

        def mock_auth_dependency():
            raise HTTPException(status_code=401, detail="Not authenticated")

        main.app.dependency_overrides[get_current_active_user] = mock_auth_dependency

        response = client_with_mocks.post(f"/api/{settings.API_PREFIX}/auth/logout")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_service_error(self, client_with_mocks, mock_auth_service, mock_user):
        """Test logout with service error."""
        refresh_data = {"refresh_token": "invalid_token"}
        mock_auth_service.sign_out.side_effect = AuthError("Invalid refresh token")

        main.app.dependency_overrides[get_current_active_user] = lambda: mock_user

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/logout", json=refresh_data
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestRateLimiting:
    """Tests for rate limiting functionality."""

    @patch("app.core.dependencies.rate_limiter")
    def test_register_rate_limited(
        self, mock_rate_limiter, client_with_mocks, valid_registration_data
    ):
        """Test that registration endpoint is rate limited."""
        # Configure rate limiter to raise an exception
        from fastapi import HTTPException

        mock_rate_limiter.side_effect = HTTPException(429, "Rate limit exceeded")

        # Override the dependency back to use the mock

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/register", json=valid_registration_data
        )

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    @patch("app.core.dependencies.rate_limiter")
    def test_login_rate_limited(self, mock_rate_limiter, client_with_mocks, valid_login_data):
        """Test that login endpoint is rate limited."""
        from fastapi import HTTPException

        mock_rate_limiter.side_effect = HTTPException(429, "Rate limit exceeded")

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/login", json=valid_login_data
        )

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_malformed_json(self, client_with_mocks):
        """Test endpoints with malformed JSON."""
        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/register",
            data="{invalid json}",
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT

    def test_extremely_long_email(self, client_with_mocks, valid_registration_data):
        """Test registration with extremely long email."""
        valid_registration_data["email"] = "a" * 250 + "@example.com"

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/register", json=valid_registration_data
        )

        # This might pass validation but fail at database level
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            status.HTTP_400_BAD_REQUEST,
        ]

    def test_sql_injection_attempt(self, client_with_mocks):
        """Test endpoints with potential SQL injection payloads."""
        malicious_data = {
            "email": "test'; DROP TABLE users; --@example.com",
            "password": "password123",
        }

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/login", json=malicious_data
        )

        # Should either fail validation or return auth error, not cause server error
        assert response.status_code in [
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            status.HTTP_401_UNAUTHORIZED,
        ]

    def test_unicode_characters(
        self, client_with_mocks, mock_auth_service, mock_user, valid_registration_data
    ):
        """Test endpoints with unicode characters."""
        valid_registration_data["full_name"] = "João José María 中文 🚀"
        mock_auth_service.register_user.return_value = mock_user

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/register", json=valid_registration_data
        )

        # Should handle unicode characters properly
        assert response.status_code == status.HTTP_200_OK


class TestSecurityHeaders:
    """Tests for security-related aspects."""

    def test_no_sensitive_data_in_error_responses(self, client_with_mocks, mock_auth_service):
        """Ensure error responses don't leak sensitive data."""
        mock_auth_service.authenticate_user.side_effect = AuthError("Database connection failed")

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/login",
            json={"email": "test@example.com", "password": "password"},
        )

        # Should return generic error message, not internal error details
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Invalid credentials"
        assert "Database" not in response.json()["detail"]

    def test_password_not_in_response(
        self, client_with_mocks, mock_auth_service, mock_user, valid_login_data
    ):
        """Ensure passwords are never returned in responses."""
        mock_auth_service.authenticate_user.return_value = (
            mock_user,
            "access_token",
            "refresh_token",
        )

        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/login", json=valid_login_data
        )

        assert response.status_code == status.HTTP_200_OK
        response_text = response.text
        assert "password" not in response_text.lower()
        assert "StrongPass123!" not in response_text


# Integration-style tests (if you want to test actual dependencies)
class TestWithRealDependencies:
    """Integration tests that use real dependencies (optional)."""

    @pytest.mark.integration
    def test_full_registration_flow(self):
        """Test complete registration flow with real dependencies."""
        # This would require actual database setup
        # and should be run separately from unit tests
        pass

    @pytest.mark.integration
    def test_full_login_flow(self):
        """Test complete login flow with real dependencies."""
        pass


# Test configuration and cleanup
@pytest.fixture(autouse=True)
def cleanup_mocks():
    """Clean up any global state after each test."""
    yield
    # Clean up dependency overrides after each test
    main.app.dependency_overrides.clear()


class TestChangePasswordEndpoint:
    def test_change_password_success(
        self, client_with_mocks, mock_auth_service, mock_user, mock_tokens
    ):
        """Test successful password change."""
        main.app.dependency_overrides[get_current_active_user] = lambda: mock_user
        mock_auth_service.change_password.return_value = None
        headers = {"Authorization": f"Bearer {mock_tokens['access_token']}"}
        payload = {"current_password": "OldPass123!", "new_password": "NewStrongPass456!"}
        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/change-password", json=payload, headers=headers
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully."
        mock_auth_service.change_password.assert_called_once()

    def test_change_password_incorrect_old(
        self, client_with_mocks, mock_auth_service, mock_user, mock_tokens
    ):
        """Test password change with incorrect current password."""
        main.app.dependency_overrides[get_current_active_user] = lambda: mock_user
        mock_auth_service.change_password.side_effect = AuthError("Incorrect current password")
        headers = {"Authorization": f"Bearer {mock_tokens['access_token']}"}
        payload = {"current_password": "WrongPass!", "new_password": "NewStrongPass456!"}
        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/change-password", json=payload, headers=headers
        )
        assert response.status_code == 400
        assert "Incorrect current password" in response.json()["detail"]

    def test_change_password_weak_new(
        self, client_with_mocks, mock_auth_service, mock_user, mock_tokens
    ):
        """Test password change with weak new password."""
        main.app.dependency_overrides[get_current_active_user] = lambda: mock_user
        headers = {"Authorization": f"Bearer {mock_tokens['access_token']}"}
        payload = {"current_password": "OldPass123!", "new_password": "weak"}
        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/change-password", json=payload, headers=headers
        )
        assert response.status_code == 422
        assert "password" in response.text.lower()

    def test_change_password_missing_fields(
        self, client_with_mocks, mock_auth_service, mock_user, mock_tokens
    ):
        """Test password change with missing fields."""
        main.app.dependency_overrides[get_current_active_user] = lambda: mock_user
        headers = {"Authorization": f"Bearer {mock_tokens['access_token']}"}
        payload = {"current_password": "OldPass123!"}  # missing new_password
        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/change-password", json=payload, headers=headers
        )
        assert response.status_code == 422
        assert "new_password" in response.text

    def test_change_password_unauthenticated(self, client_with_mocks):
        """Test password change without authentication."""
        payload = {"current_password": "OldPass123!", "new_password": "NewStrongPass456!"}
        response = client_with_mocks.post(
            f"/api/{settings.API_PREFIX}/auth/change-password", json=payload
        )
        assert response.status_code in (401, 403)
        assert (
            "not authenticated" in response.text.lower() or "credentials" in response.text.lower()
        )

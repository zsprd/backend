import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.user.accounts.model import UserAccount


class TestUserProfile:
    """Test user profile management endpoints."""

    @pytest.mark.user
    def test_get_user_profile_success(self, client: TestClient, auth_headers, verified_user):
        """Test successful user profile retrieval."""
        response = client.get("/user/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(verified_user.id)
        assert data["email"] == verified_user.email
        assert data["full_name"] == verified_user.full_name
        assert data["language"] == verified_user.language
        assert data["country"] == verified_user.country
        assert data["currency"] == verified_user.currency
        assert data["is_active"] is True
        assert data["is_verified"] is True
        assert "created_at" in data
        assert "updated_at" in data

        # Ensure sensitive data is not exposed
        assert "hashed_password" not in data
        assert "email_verification_token" not in data
        assert "password_reset_token" not in data

    @pytest.mark.user
    def test_get_user_profile_unauthorized(self, client: TestClient):
        """Test profile retrieval without authentication."""
        response = client.get("/user/me")

        assert response.status_code == 401

    @pytest.mark.user
    def test_get_user_profile_invalid_token(self, client: TestClient):
        """Test profile retrieval with invalid token."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.get("/user/me", headers=headers)

        assert response.status_code == 401

    @pytest.mark.user
    def test_update_user_profile_success(self, client: TestClient, auth_headers):
        """Test successful user profile update."""
        update_data = {
            "full_name": "Updated Name",
            "language": "fr",
            "country": "FR",
            "currency": "EUR",
        }

        response = client.patch("/user/me", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["full_name"] == "Updated Name"
        assert data["language"] == "fr"
        assert data["country"] == "FR"
        assert data["currency"] == "EUR"

    @pytest.mark.user
    def test_update_user_profile_partial(self, client: TestClient, auth_headers):
        """Test partial user profile update."""
        update_data = {
            "full_name": "Partially Updated Name",
        }

        response = client.patch("/user/me", json=update_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["full_name"] == "Partially Updated Name"
        # Other fields should remain unchanged

    @pytest.mark.user
    def test_update_user_profile_invalid_data(self, client: TestClient, auth_headers):
        """Test profile update with invalid data."""
        invalid_updates = [
            {"language": "invalid-lang"},  # Invalid language code
            {"country": "INVALID"},  # Invalid country code
            {"currency": "INVALID"},  # Invalid currency code
            {"full_name": "A"},  # Too short name
            {"full_name": ""},  # Empty name
        ]

        for invalid_data in invalid_updates:
            response = client.patch("/user/me", json=invalid_data, headers=auth_headers)
            assert response.status_code == 422

    @pytest.mark.user
    def test_update_user_profile_unauthorized(self, client: TestClient):
        """Test profile update without authentication."""
        update_data = {"full_name": "New Name"}

        response = client.patch("/user/me", json=update_data)

        assert response.status_code == 401


class TestUserPasswordChange:
    """Test user password change endpoint."""

    @pytest.mark.user
    def test_change_password_success(self, client: TestClient, auth_headers):
        """Test successful password change via user endpoint."""
        password_data = {
            "current_password": "password123",
            "new_password": "NewStrongPass123!",
        }

        response = client.post("/user/me/change-password", json=password_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "changed successfully" in data["message"]

    @pytest.mark.user
    def test_change_password_wrong_current(self, client: TestClient, auth_headers):
        """Test password change with wrong current password."""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "NewStrongPass123!",
        }

        response = client.post("/user/me/change-password", json=password_data, headers=auth_headers)

        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()

    @pytest.mark.user
    def test_change_password_weak_new_password(
        self, client: TestClient, auth_headers, invalid_passwords
    ):
        """Test password change with weak new password."""
        for weak_password in invalid_passwords:
            password_data = {
                "current_password": "password123",
                "new_password": weak_password,
            }

            response = client.post(
                "/user/me/change-password", json=password_data, headers=auth_headers
            )

            assert response.status_code == 422

    @pytest.mark.user
    def test_change_password_unauthorized(self, client: TestClient):
        """Test password change without authentication."""
        password_data = {
            "current_password": "password123",
            "new_password": "NewStrongPass123!",
        }

        response = client.post("/user/me/change-password", json=password_data)

        assert response.status_code == 401


class TestAccountManagement:
    """Test account management operations."""

    @pytest.mark.user
    def test_deactivate_account_success(self, client: TestClient, auth_headers):
        """Test successful account deactivation."""
        response = client.post("/user/me/deactivate", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert "deactivated successfully" in data["message"]

    @pytest.mark.user
    def test_deactivate_account_unauthorized(self, client: TestClient):
        """Test account deactivation without authentication."""
        response = client.post("/user/me/deactivate")

        assert response.status_code == 401

    @pytest.mark.user
    def test_delete_account_success(self, client: TestClient, auth_headers):
        """Test successful account deletion."""
        response = client.delete("/user/me", headers=auth_headers)

        assert response.status_code == 204

    @pytest.mark.user
    def test_delete_account_unauthorized(self, client: TestClient):
        """Test account deletion without authentication."""
        response = client.delete("/user/me")

        assert response.status_code == 401


class TestUserUtilities:
    """Test user utility endpoints."""

    @pytest.mark.user
    def test_check_email_availability_available(self, client: TestClient):
        """Test email availability check for available email."""
        response = client.get("/users/check-email?email=available@example.com")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is True

    @pytest.mark.user
    def test_check_email_availability_taken(self, client: TestClient, verified_user):
        """Test email availability check for taken email."""
        response = client.get(f"/users/check-email?email={verified_user.email}")

        assert response.status_code == 200
        data = response.json()
        assert data["available"] is False

    @pytest.mark.user
    def test_check_email_availability_invalid_email(self, client: TestClient, invalid_emails):
        """Test email availability check with invalid emails."""
        for invalid_email in invalid_emails:
            response = client.get(f"/users/check-email?email={invalid_email}")
            assert response.status_code == 400

    @pytest.mark.user
    def test_get_user_security_info(self, client: TestClient, auth_headers, verified_user):
        """Test getting user security information."""
        response = client.get("/user/me/security", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == str(verified_user.id)
        assert data["email"] == verified_user.email
        assert "failed_login_attempts" in data
        assert "is_locked" in data
        assert "is_active" in data
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.user
    def test_get_security_info_unauthorized(self, client: TestClient):
        """Test getting security info without authentication."""
        response = client.get("/user/me/security")

        assert response.status_code == 401

    @pytest.mark.user
    def test_user_health_check(self, client: TestClient):
        """Test user service health check."""
        response = client.get("/users/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "user"


class TestUserSecurity:
    """Test security aspects of user management."""

    @pytest.mark.security
    def test_unverified_user_access(self, client: TestClient, unverified_user):
        """Test that unverified users cannot access protected endpoints."""
        # Create token for unverified user
        from app.auth import tokens

        access_token = tokens.create_access_token(str(unverified_user.id))
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.get("/user/me", headers=headers)

        assert response.status_code == 403
        assert "verified" in response.json()["detail"].lower()

    @pytest.mark.security
    def test_locked_user_access(self, client: TestClient, locked_user):
        """Test that locked users cannot access protected endpoints."""
        # Create token for locked user
        from app.auth import tokens

        access_token = tokens.create_access_token(str(locked_user.id))
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.get("/user/me", headers=headers)

        assert response.status_code == 423
        assert "locked" in response.json()["detail"].lower()

    @pytest.mark.security
    async def test_inactive_user_access(self, client: TestClient, async_db: AsyncSession):
        """Test that inactive users cannot access protected endpoints."""
        # Create inactive user
        inactive_user = UserAccount(
            email="inactive@example.com",
            full_name="Inactive User",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj1fhpKOKkFm",
            is_verified=True,
            is_active=False,  # Inactive
        )

        async_db.add(inactive_user)
        await async_db.commit()
        await async_db.refresh(inactive_user)

        # Create token for inactive user
        from app.auth import tokens

        access_token = tokens.create_access_token(str(inactive_user.id))
        headers = {"Authorization": f"Bearer {access_token}"}

        response = client.get("/user/me", headers=headers)

        assert response.status_code == 403
        assert "not active" in response.json()["detail"].lower()

    @pytest.mark.security
    def test_sensitive_data_not_exposed(self, client: TestClient, auth_headers):
        """Test that sensitive data is not exposed in API responses."""
        response = client.get("/user/me", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()

        # Ensure sensitive fields are not present
        sensitive_fields = [
            "hashed_password",
            "password_reset_token",
            "email_verification_token",
            "failed_login_attempts",
            "locked_until",
        ]

        for field in sensitive_fields:
            assert field not in data

    @pytest.mark.security
    async def test_user_isolation(self, client: TestClient, async_db: AsyncSession, verified_user):
        """Test that users can only access their own data."""
        # Create second user
        other_user = UserAccount(
            email="other@example.com",
            full_name="Other User",
            hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj1fhpKOKkFm",
            is_verified=True,
            is_active=True,
        )

        async_db.add(other_user)
        await async_db.commit()
        await async_db.refresh(other_user)

        # Create token for first user
        from app.auth import tokens

        access_token = tokens.create_access_token(str(verified_user.id))
        headers = {"Authorization": f"Bearer {access_token}"}

        # Access should return first user's data, not other user's
        response = client.get("/user/me", headers=headers)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(verified_user.id)
        assert data["email"] == verified_user.email


class TestUserDataValidation:
    """Test data validation for user endpoints."""

    @pytest.mark.user
    def test_profile_update_sql_injection(self, client: TestClient, auth_headers):
        """Test profile update resistance to SQL injection."""
        malicious_data = {
            "full_name": "'; DROP TABLE user_accounts; --",
        }

        response = client.patch("/user/me", json=malicious_data, headers=auth_headers)

        # Should either update safely or reject, but not cause server error
        assert response.status_code in [200, 400, 422]

        # Verify user data is still intact
        profile_response = client.get("/user/me", headers=auth_headers)
        assert profile_response.status_code == 200

    @pytest.mark.user
    def test_profile_update_xss_prevention(self, client: TestClient, auth_headers):
        """Test profile update XSS prevention."""
        xss_data = {
            "full_name": "<script>alert('xss')</script>",
        }

        response = client.patch("/user/me", json=xss_data, headers=auth_headers)

        if response.status_code == 200:
            # If update succeeds, verify script tags are sanitized
            data = response.json()
            assert "<script>" not in data["full_name"]
        else:
            # Or update should be rejected
            assert response.status_code in [400, 422]

    @pytest.mark.user
    def test_extremely_long_input(self, client: TestClient, auth_headers):
        """Test handling of extremely long input."""
        long_name = "A" * 10000  # Very long name

        update_data = {"full_name": long_name}

        response = client.patch("/user/me", json=update_data, headers=auth_headers)

        # Should reject overly long input
        assert response.status_code == 422

    @pytest.mark.user
    def test_unicode_handling(self, client: TestClient, auth_headers):
        """Test proper Unicode handling in user data."""
        unicode_data = {
            "full_name": "José María François 日本語 العربية",
        }

        response = client.patch("/user/me", json=unicode_data, headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == unicode_data["full_name"]

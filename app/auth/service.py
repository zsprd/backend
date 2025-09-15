from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from fastapi import HTTPException, Request, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import schema, utils
from app.auth.crud import auth_crud
from app.core.config import settings
from app.users.profile.model import UserProfile
from app.users.profile.service import user_profile_service
from app.users.session.crud import user_session_crud


class AuthService:
    """Service layer for authentication operations."""

    def __init__(self):
        self.auth_crud = auth_crud
        self.user_service = user_profile_service
        self.session_crud = user_session_crud

    # ----------------------
    # User Registration
    # ----------------------
    def register_user(
        self, db: Session, registration_data: schema.UserRegistrationData
    ) -> UserProfile:
        """Register a new user with email and password."""
        # Check if email already exists
        if not self.user_service.is_email_available(db, str(registration_data.email)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

        try:
            # Hash password
            password_hash = utils.hash_password(registration_data.password)

            # Create profile data (excluding password)
            profile_data = {
                "email": registration_data.email,
                "full_name": registration_data.full_name,
                "timezone": registration_data.timezone,
                "base_currency": registration_data.base_currency,
                "language": registration_data.language,
                "theme_preference": registration_data.theme_preference,
            }

            # Create user with password
            user = self.auth_crud.create_user_with_password(
                db, user_data=profile_data, password_hash=password_hash
            )

            # TODO: Send verification email in background task
            return user

        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

    def register_oauth_user(self, db: Session, oauth_data: schema.OAuthUserData) -> UserProfile:
        """Register a new user via OAuth provider."""
        # Check if email already exists
        if not self.user_service.is_email_available(db, str(oauth_data.email)):
            existing_user = self.user_service.get_user_by_email(db, str(oauth_data.email))
            if existing_user and not existing_user.password_hash:
                # User exists as OAuth user, return existing
                return existing_user
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="User with this email already exists with different authentication method",
                )

        try:
            # Create OAuth user data
            user_data = oauth_data.model_dump()
            return self.auth_crud.create_oauth_user(db, user_data=user_data)

        except IntegrityError:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists",
            )

    def confirm_email(
        self, db: Session, confirmation_data: schema.EmailConfirmRequest
    ) -> UserProfile:
        """Confirm user email with verification token."""
        # Verify token and extract email
        email = utils.verify_email_token(confirmation_data.token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired confirmation token",
            )

        # Get user by email
        user = self.user_service.get_user_by_email(db, email)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )

        # Check if already verified
        if user.is_verified:
            return user

        # Mark as verified
        return self.user_service.mark_email_verified(db, user)

    # ----------------------
    # Authentication
    # ----------------------
    def authenticate_user(
        self, db: Session, signin_data: schema.SignInRequest, request: Optional[Request] = None
    ) -> Tuple[UserProfile, str, str]:
        """Authenticate user and create session."""
        # Authenticate credentials
        user = self.auth_crud.authenticate_user(
            db, email=str(signin_data.email), password=signin_data.password
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not user.is_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Please verify your email before signing in",
            )

        # Create token pair
        access_token, refresh_token = self._create_token_pair(str(user.id))

        if request and hasattr(self, "session_crud"):
            self._create_user_session(db, user, refresh_token, request)

        return user, access_token, refresh_token

    def refresh_tokens(
        self, db: Session, refresh_data: schema.RefreshTokenRequest
    ) -> Tuple[str, str]:
        """Refresh access and refresh tokens."""
        # Verify refresh token
        token_data = utils.verify_token(refresh_data.refresh_token, utils.TOKEN_TYPE_REFRESH)
        if not token_data or not token_data.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
            )

        # Get user
        user_id = token_data["sub"]
        user = self.auth_crud.get_user_for_token_validation(db, user_id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account not found or inactive",
            )

        if hasattr(self, "session_crud"):
            self._validate_refresh_token_session(db, refresh_data.refresh_token)

        # Create new token pair
        access_token, refresh_token = self._create_token_pair(str(user.id))

        if hasattr(self, "session_crud"):
            self._update_user_session(db, refresh_data.refresh_token, refresh_token)

        return access_token, refresh_token

    def sign_out(
        self,
        db: Session,
        refresh_token: Optional[str] = None,
        current_user: Optional[UserProfile] = None,
    ) -> bool:
        """Sign out user by revoking tokens/sessions."""

        if hasattr(self, "session_crud"):
            if refresh_token:
                self.session_crud.revoke_session_by_token(db, refresh_token=refresh_token)
            elif current_user:
                self.session_crud.revoke_all_user_sessions(db, user_id=str(current_user.id))
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Either refresh token or user authentication required",
                )

        # For JWT-only implementation, tokens are stateless
        # Just return success - tokens will expire naturally
        return True

    # ----------------------
    # Password Management
    # ----------------------
    def initiate_password_reset(
        self, db: Session, reset_request: schema.ForgotPasswordRequest
    ) -> bool:
        """Initiate password reset process."""
        user = self.user_service.get_user_by_email(db, str(reset_request.email))

        # Always return success to prevent email enumeration
        if user and user.is_active and user.password_hash:
            # Create reset token and send email
            reset_token = utils.create_password_reset_token(str(user.email))
            # TODO: Send reset email in background task

        return True

    def reset_password(self, db: Session, reset_data: schema.ResetPasswordRequest) -> UserProfile:
        """Reset user password with reset token."""
        # Verify reset token
        email = utils.verify_password_reset_token(reset_data.token)
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired reset token"
            )

        # Get user
        user = self.user_service.get_user_by_email(db, email)
        if not user or not user.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        # Update password
        password_hash = utils.hash_password(reset_data.new_password)
        user = self.auth_crud.update_password(db, user=user, new_password_hash=password_hash)

        if hasattr(self, "session_crud"):
            self.session_crud.revoke_all_user_sessions(db, user_id=str(user.id))

        return user

    def change_password(
        self, db: Session, password_change: schema.ChangePasswordRequest, current_user: UserProfile
    ) -> UserProfile:
        """Change user password (authenticated operation)."""
        # Verify current password
        authenticated_user = self.auth_crud.authenticate_user(
            db, email=str(current_user.email), password=password_change.current_password
        )

        if not authenticated_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect"
            )

        # Update password
        password_hash = utils.hash_password(password_change.new_password)
        user = self.auth_crud.update_password(
            db, user=current_user, new_password_hash=password_hash
        )

        if hasattr(self, "session_crud"):
            self.session_crud.revoke_all_user_sessions(db, user_id=str(user.id))

        return user

    # ----------------------
    # Account Management
    # ----------------------
    def deactivate_account(self, db: Session, user: UserProfile) -> UserProfile:
        """Deactivate user account."""
        deactivated_user = self.user_service.deactivate_user_account(db, user)

        if hasattr(self, "session_crud"):
            self.session_crud.revoke_all_user_sessions(db, user_id=str(user.id))

        return deactivated_user

    def delete_account(self, db: Session, user: UserProfile, hard_delete: bool = False) -> bool:
        """Delete user account (soft delete by default)."""
        self.auth_crud.delete_user_account(db, user_id=user.id, hard_delete=hard_delete)

        if hasattr(self, "session_crud"):
            self.session_crud.revoke_all_user_sessions(db, user_id=str(user.id))

        return True

    # ----------------------
    # OAuth Operations
    # ----------------------
    def link_oauth_account(self, db: Session, user: UserProfile, oauth_data: dict) -> UserProfile:
        """Link OAuth account to existing user."""
        # This would typically involve storing OAuth provider info
        pass

    def unlink_password_auth(self, db: Session, user: UserProfile) -> UserProfile:
        """Remove password authentication (convert to OAuth-only)."""
        if not user.password_hash:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has no password authentication",
            )

        return self.auth_crud.remove_password(db, user=user)

    # ----------------------
    # Private Helper Methods
    # ----------------------
    def _create_token_pair(self, user_id: str) -> Tuple[str, str]:
        """Create access and refresh token pair."""
        access_token = utils.create_access_token(data={"sub": user_id})
        refresh_token = utils.create_refresh_token(user_id)
        return access_token, refresh_token

    # Optional session management helpers (uncomment if you have session support)
    def _create_user_session(
        self, db: Session, user: UserProfile, refresh_token: str, request: Request
    ):
        """Create user session."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        self.session_crud.create_session(
            db,
            user_id=str(user.id),
            refresh_token=refresh_token,
            expires_at=expires_at,
            ip_address=utils.get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            device_type="web",
        )

    def _validate_refresh_token_session(self, db: Session, refresh_token: str):
        """Validate refresh token has active session."""
        session = self.session_crud.get_active_session_by_token(db, refresh_token=refresh_token)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Session not found or expired"
            )

    def _update_user_session(self, db: Session, old_token: str, new_token: str):
        """Update session with new refresh token."""
        session = self.session_crud.get_active_session_by_token(db, refresh_token=old_token)
        if session:
            session.refresh_token = new_token
            session.last_used_at = datetime.now(timezone.utc)
            session.expires_at = datetime.now(timezone.utc) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
            db.add(session)
            db.commit()


# Singleton instance
auth_service = AuthService()

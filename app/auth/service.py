import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from fastapi import BackgroundTasks, Request
from pydantic import EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import schema, utils
from app.auth.crud import auth_crud
from app.core.config import settings
from app.core.email import send_email
from app.user.accounts.model import UserAccount
from app.user.accounts.service import user_account_service
from app.user.sessions.crud import user_session_crud

logger = logging.getLogger(__name__)

# Constants for account lockout
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


class AuthError(Exception):
    """Base exception for authentication and business logic errors."""

    pass


class AuthService:
    """Service layer for authentication operations."""

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db
        self.auth_crud = auth_crud
        self.user_service = user_account_service
        self.session_crud = user_session_crud

    # ----------------------
    # User Registration
    # ----------------------
    async def register(
        self,
        db: AsyncSession,
        registration_data: schema.UserRegistrationData,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> UserAccount:
        """Register a new user with email and password."""
        logger.info(f"Attempting to register user with email: {registration_data.email}")

        # Check if email is available
        if not await self.user_service.is_email_available(db, str(registration_data.email)):
            logger.warning(f"Registration failed: Email {registration_data.email} already exists")
            raise AuthError("User with this email already exists")

        try:
            # Hash the password
            hashed_password = utils.hash_password(registration_data.password)

            # Create user data without the password
            profile_data = {
                "email": registration_data.email,
                "full_name": registration_data.full_name,
            }

            # Create the user
            user = await self.auth_crud.create_user_with_password(
                db, user_data=profile_data, hashed_password=hashed_password
            )

            logger.info(f"User created successfully with ID: {user.id}")

            # Send verification email in background
            if background_tasks:
                verification_token = utils.create_email_verification_token(str(user.email))
                background_tasks.add_task(
                    self._send_verification_email, user.email, verification_token
                )
                logger.info(f"Verification email scheduled for user: {user.id}")

            return user

        except IntegrityError:
            await db.rollback()
            logger.error(
                f"Database integrity error during registration for {registration_data.email}"
            )
            raise AuthError("User with this email already exists")
        except Exception as e:
            await db.rollback()
            logger.error(f"Unexpected error during registration: {str(e)}")
            raise AuthError(f"Registration failed: {str(e)}")

    async def register_oauth(
        self, db: AsyncSession, oauth_data: schema.OAuthUserData
    ) -> UserAccount:
        """Register a new user via OAuth provider."""
        logger.info(f"Attempting OAuth registration for email: {oauth_data.email}")

        if not await self.user_service.is_email_available(db, str(oauth_data.email)):
            existing_user = await self.user_service.get_user_by_email(db, str(oauth_data.email))
            if existing_user and not existing_user.hashed_password:
                # User exists as OAuth user, return existing
                logger.info(f"Returning existing OAuth user: {existing_user.id}")
                return existing_user
            else:
                logger.warning(
                    f"OAuth registration failed: Email {oauth_data.email} exists with password auth"
                )
                raise AuthError(
                    "User with this email already exists with different authentication method"
                )

        try:
            user_data = oauth_data.model_dump()
            user = await self.auth_crud.create_oauth_user(db, user_data=user_data)
            logger.info(f"OAuth user created successfully with ID: {user.id}")
            return user
        except IntegrityError:
            await db.rollback()
            logger.error(
                f"Database integrity error during OAuth registration for {oauth_data.email}"
            )
            raise AuthError("User with this email already exists")

    async def verify_email(
        self, db: AsyncSession, confirmation_data: schema.EmailConfirmRequest
    ) -> UserAccount:
        """Confirm user email with verification token."""
        logger.info("Processing email verification request")

        email = utils.verify_email_token(confirmation_data.token)
        if not email:
            logger.warning("Email verification failed: Invalid or expired token")
            raise AuthError("Invalid or expired token")

        user = await self.user_service.get_user_by_email(db, email)
        if not user:
            logger.warning(f"Email verification failed: User not found for email {email}")
            raise AuthError("User not found")

        if user.is_verified:
            logger.info(f"Email already verified for user: {user.id}")
            return user

        verified_user = await self.user_service.mark_email_verified(db, user)
        logger.info(f"Email verified successfully for user: {user.id}")

        # Send welcome email
        if verified_user.email:
            await send_email(
                to_email=verified_user.email,
                subject="Welcome to ZSPRD Portfolio Analytics! 🎉",
                template="emails/welcome.html",
                context={"name": verified_user.full_name or verified_user.email},
            )

        return verified_user

    # ----------------------
    # Authentication
    # ----------------------
    async def login(
        self, db: AsyncSession, signin_data: schema.SignInRequest, request: Optional[Request] = None
    ) -> Tuple[UserAccount, str, str]:
        """Authenticate user and create session."""
        email = str(signin_data.email)
        logger.info(f"Login attempt for email: {email}")

        # Get user first to check account status
        user = await self.user_service.get_user_by_email(db, email)

        if user:
            # Check if account is locked
            await self._check_account_lockout(db, user)

            # Attempt authentication
            authenticated_user = await self.auth_crud.authenticate_user(
                db, email=email, password=signin_data.password
            )

            if not authenticated_user:
                # Increment failed attempts
                await self._handle_failed_login(db, user)
                logger.warning(f"Login failed for {email}: Invalid password")
                raise AuthError("Invalid credentials")

            # Reset failed attempts on successful login
            if user.failed_login_attempts > 0:
                await self._reset_failed_attempts(db, user)

            if not user.is_verified:
                logger.warning(f"Login failed for {email}: Email not verified")
                raise AuthError(
                    "Email address not verified. Please verify your email before logging in"
                )

            # Create tokens
            access_token, refresh_token = self._create_token_pair(str(user.id))

            # Create session
            if request:
                await self._create_user_session(db, user, refresh_token, request)

            logger.info(f"Login successful for user: {user.id}")
            return user, access_token, refresh_token
        else:
            logger.warning(f"Login failed for {email}: User not found")
            raise AuthError("Invalid credentials")

    async def refresh(
        self, db: AsyncSession, refresh_data: schema.RefreshTokenRequest
    ) -> Tuple[str, str]:
        """Refresh access and refresh tokens."""
        logger.info("Processing token refresh request")

        token_data = utils.verify_token(refresh_data.refresh_token, utils.TOKEN_TYPE_REFRESH)
        if not token_data or not token_data.get("sub"):
            logger.warning("Token refresh failed: Invalid or expired token")
            raise AuthError("Invalid or expired token")

        user_id = token_data["sub"]
        user = await self.auth_crud.get_user_for_token_validation(db, user_id=user_id)
        if not user:
            logger.warning(f"Token refresh failed: User {user_id} not found or inactive")
            raise AuthError("User account not found or inactive")

        # Validate refresh token session
        await self._validate_refresh_token_session(db, refresh_data.refresh_token)

        # Create new token pair
        access_token, refresh_token = self._create_token_pair(str(user.id))

        # Update session with new refresh token
        await self._update_user_session(db, refresh_data.refresh_token, refresh_token)

        logger.info(f"Token refresh successful for user: {user_id}")
        return access_token, refresh_token

    async def logout(
        self,
        db: AsyncSession,
        refresh_token: Optional[str] = None,
        current_user: Optional[UserAccount] = None,
    ) -> bool:
        """Sign out user by revoking tokens/sessions."""
        if refresh_token:
            await self.session_crud.revoke_session_by_token(db, refresh_token=refresh_token)
            logger.info(f"Revoked session for refresh token")
        elif current_user:
            await self.session_crud.revoke_all_user_sessions(db, user_id=str(current_user.id))
            logger.info(f"Revoked all sessions for user: {current_user.id}")
        else:
            raise AuthError("Either refresh token or user authentication required")

        return True

    # ----------------------
    # Password Management
    # ----------------------
    async def forgot_password(
        self,
        db: AsyncSession,
        reset_request: schema.ForgotPasswordRequest,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> bool:
        """Initiate password reset process."""
        email = reset_request.email
        logger.info(f"Password reset requested for email: {str(email)}")

        user = await self.user_service.get_user_by_email(db, email)

        # Always return success to prevent email enumeration
        if user and user.is_active and user.hashed_password:
            # Create reset token and send email
            reset_token = utils.create_password_reset_token(str(email))

            if background_tasks:
                background_tasks.add_task(self._send_password_reset_email, email, reset_token)
                logger.info(f"Password reset email scheduled for user: {user.id}")
        else:
            logger.info(f"Password reset requested for non-existent or inactive email: {email}")

        return True

    async def reset_password(
        self, db: AsyncSession, reset_data: schema.ResetPasswordRequest
    ) -> UserAccount:
        """Reset user password with reset token."""
        logger.info("Processing password reset")

        # Verify reset token
        email = utils.verify_password_reset_token(reset_data.token)
        if not email:
            logger.warning("Password reset failed: Invalid or expired token")
            raise AuthError("Invalid or expired token")

        # Get user
        user = await self.user_service.get_user_by_email(db, email)
        if not user or not user.is_active:
            logger.warning(f"Password reset failed: User not found for email {email}")
            raise AuthError("User not found")

        # Update password
        hashed_password = utils.hash_password(reset_data.new_password)
        user = await self.auth_crud.update_password(
            db, user=user, new_hashed_password=hashed_password
        )

        # Revoke all sessions
        await self.session_crud.revoke_all_user_sessions(db, user_id=str(user.id))

        logger.info(f"Password reset successful for user: {user.id}")

        if user.email:
            await send_email(
                to_email=user.email,
                subject="Your password has been changed",
                template="emails/password_changed.html",
                context={"name": user.full_name or user.email},
            )

        return user

    async def change_password(
        self,
        db: AsyncSession,
        password_change: schema.ChangePasswordRequest,
        current_user: UserAccount,
    ) -> UserAccount:
        """Change user password (authenticated operation)."""
        logger.info(f"Password change requested for user: {current_user.id}")

        # Verify current password
        authenticated_user = await self.auth_crud.authenticate_user(
            db, email=str(current_user.email), password=password_change.current_password
        )
        if not authenticated_user:
            logger.warning(
                f"Password change failed for user {current_user.id}: Current password incorrect"
            )
            raise AuthError("Current password is incorrect")

        # Update password
        hashed_password = utils.hash_password(password_change.new_password)
        user = await self.auth_crud.update_password(
            db, user=current_user, new_hashed_password=hashed_password
        )

        # Revoke all sessions
        await self.session_crud.revoke_all_user_sessions(db, user_id=str(user.id))

        logger.info(f"Password changed successfully for user: {user.id}")

        if user.email:
            await send_email(
                to_email=user.email,
                subject="Your password has been changed",
                template="emails/password_changed.html",
                context={"name": user.full_name or user.email},
            )

        return user

    # ----------------------
    # Account Management
    # ----------------------
    async def deactivate_account(self, db: AsyncSession, user: UserAccount) -> UserAccount:
        """Deactivate user account."""
        logger.info(f"Deactivating account for user: {user.id}")

        deactivated_user = await self.user_service.deactivate_user_account(db, user)
        await self.session_crud.revoke_all_user_sessions(db, user_id=str(user.id))

        logger.info(f"Account deactivated for user: {user.id}")
        return deactivated_user

    async def delete_account(
        self, db: AsyncSession, user: UserAccount, hard_delete: bool = False
    ) -> bool:
        """Delete user account (soft delete by default)."""
        logger.info(f"Deleting account for user: {user.id} (hard_delete={hard_delete})")

        await self.auth_crud.delete_user_account(db, user_id=user.id, hard_delete=hard_delete)
        await self.session_crud.revoke_all_user_sessions(db, user_id=str(user.id))

        logger.info(f"Account deleted for user: {user.id}")
        return True

    # ----------------------
    # Private Helper Methods
    # ----------------------
    def _create_token_pair(self, user_id: str) -> Tuple[str, str]:
        """Create access and refresh token pair."""
        access_token = utils.create_access_token(user_id, data={"sub": user_id})
        refresh_token = utils.create_refresh_token(user_id)
        return access_token, refresh_token

    async def _create_user_session(
        self, db: AsyncSession, user: UserAccount, refresh_token: str, request: Request
    ):
        """Create user session."""
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        await self.session_crud.create_session(
            db,
            user_id=str(user.id),
            refresh_token=refresh_token,
            expires_at=expires_at,
            ip_address=utils.get_client_ip(request),
            user_agent=utils.sanitize_user_agent(request.headers.get("User-Agent")),
        )

    async def _validate_refresh_token_session(self, db: AsyncSession, refresh_token: str):
        """Validate refresh token has active session."""
        session = await self.session_crud.get_active_session_by_token(
            db, refresh_token=refresh_token
        )
        if not session:
            raise AuthError("Session not found or expired")

    async def _update_user_session(self, db: AsyncSession, old_token: str, new_token: str):
        """Update session with new refresh token."""
        session = await self.session_crud.get_active_session_by_token(db, refresh_token=old_token)
        if session:
            session.refresh_token = new_token
            session.last_used_at = datetime.now(timezone.utc)
            session.expires_at = datetime.now(timezone.utc) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
            db.add(session)
            await db.commit()

    async def _check_account_lockout(self, db: AsyncSession, user: UserAccount):
        """Check if account is locked due to failed attempts."""
        if hasattr(user, "locked_until") and user.locked_until:
            if user.locked_until > datetime.now(timezone.utc):
                remaining_minutes = int(
                    (user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60
                )
                logger.warning(f"Account locked for user {user.id}")
                raise AuthError(
                    f"Account temporarily locked. Try again in {remaining_minutes} minutes"
                )
            else:
                # Unlock the account
                user.locked_until = None
                user.failed_login_attempts = 0
                db.add(user)
                await db.commit()

    async def _handle_failed_login(self, db: AsyncSession, user: UserAccount):
        """Handle failed login attempt."""
        if not hasattr(user, "failed_login_attempts"):
            # If the field doesn't exist on the model yet, just log
            logger.warning(
                f"Failed login for user {user.id}, but failed_login_attempts field not available"
            )
            return

        user.failed_login_attempts = getattr(user, "failed_login_attempts", 0) + 1

        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.now(timezone.utc) + timedelta(
                minutes=LOCKOUT_DURATION_MINUTES
            )
            logger.warning(
                f"Account locked for user {user.id} after {MAX_FAILED_ATTEMPTS} failed attempts"
            )

        db.add(user)
        await db.commit()

    async def _reset_failed_attempts(self, db: AsyncSession, user: UserAccount):
        """Reset failed login attempts after successful login."""
        if hasattr(user, "failed_login_attempts"):
            user.failed_login_attempts = 0
            if hasattr(user, "locked_until"):
                user.locked_until = None
            db.add(user)
            await db.commit()

    async def _send_verification_email(self, email: EmailStr, token: str):
        """Send email verification email."""
        try:
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
            await send_email(
                to_email=email,
                subject="Verify your email address",
                template="email_verification.html",
                context={
                    "verification_url": verification_url,
                    "expires_in_hours": settings.EMAIL_VERIFICATION_EXPIRE_HOURS,
                },
            )
            logger.info(f"Verification email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send verification email to {email}: {str(e)}")

    async def _send_password_reset_email(self, email: EmailStr, token: str):
        """Send password reset email."""
        try:
            reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
            await send_email(
                to_email=email,
                subject="Reset your password",
                template="password_reset.html",
                context={
                    "reset_url": reset_url,
                    "expires_in_minutes": settings.PASSWORD_RESET_EXPIRE_MINUTES,
                },
            )
            logger.info(f"Password reset email sent to {email}")
        except Exception as e:
            logger.error(f"Failed to send password reset email to {email}: {str(e)}")


# Singleton instance
auth_service = AuthService()

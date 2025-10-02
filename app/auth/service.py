import logging
from dataclasses import dataclass
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import email, schema, tokens
from app.core.config import settings
from app.user.accounts.model import UserAccount
from app.user.accounts.repository import UserAccountRepository
from app.user.sessions.repository import UserSessionRepository

logger = logging.getLogger(__name__)


class AuthError(Exception):
    """Custom exception for authentication-related errors."""

    pass


@dataclass
class SessionContext:
    """Context information for session creation."""

    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuthService:
    """Pure authentication business logic service."""

    def __init__(self, db: AsyncSession):
        self.user_crud = UserAccountRepository(db)
        self.session_crud = UserSessionRepository(db)

    async def register(
        self,
        registration_data: schema.UserRegistrationData,
    ) -> schema.RegistrationResponse:
        """Register a new user account."""
        logger.info(f"Processing user registration for email: {registration_data.email}")

        try:
            # Check if user already exists
            existing_user = await self.user_crud.get_user_by_email(registration_data.email)
            if existing_user:
                logger.warning(
                    f"Registration failed: Email already exists - {registration_data.email}"
                )
                raise AuthError("An account with this email already exists.")

            # Create user account
            user = await self.user_crud.create_user_with_password(
                registration_data.email,
                registration_data.full_name,
                registration_data.password,
            )

            if not user:
                logger.error("Failed to create user account")
                raise AuthError("Failed to create user account")

            logger.info(f"User created successfully: {user.id}")

            # Generate email verification token
            verification_token = tokens.create_verification_token(str(user.id))
            verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"

            # Send verification email
            try:
                await email.send_verification_email(
                    user.email,
                    verification_url,
                    user.full_name,
                )
                logger.info(f"Verification email sent to user: {user.id}")
            except Exception as e:
                logger.warning(f"Failed to send verification email: {type(e).__name__}: {str(e)}")
                # Don't fail registration if email fails

            return schema.RegistrationResponse(
                message="User registered successfully. Please verify your email.",
                user_id=user.id,
                email_verification_required=True,
                user=schema.UserAccountRead.model_validate(user),
            )

        except AuthError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during registration: {type(e).__name__}: {str(e)}")
            raise AuthError("Registration failed due to unexpected error")

    async def login(
        self, signin_data: schema.SignInRequest, session_context: Optional[SessionContext] = None
    ) -> schema.AuthResponse:
        """Authenticate user and create session."""
        logger.info(f"Processing login request for email: {signin_data.email}")

        try:
            # Get user by email
            user = await self.user_crud.get_user_by_email(signin_data.email)
            if not user:
                logger.warning(f"Login failed: User not found - {signin_data.email}")
                raise AuthError("Invalid credentials.")

            # Check account lockout
            if user.is_locked:
                lockout_minutes = user.lockout_time_remaining or 0
                logger.warning(f"Login attempt on locked account: {user.id}")
                raise AuthError(
                    f"Account is temporarily locked. Try again in {lockout_minutes} minutes."
                )

            # Authenticate with password
            authenticated = await self.user_crud.authenticate_user(user, signin_data.password)

            if not authenticated:
                logger.warning(f"Login failed: Invalid credentials for {signin_data.email}")
                raise AuthError("Invalid credentials.")

            # Check email verification
            if not user.is_verified:
                logger.warning(f"Login failed: Email not verified for {signin_data.email}")
                raise AuthError(
                    "Email address not verified. Please verify your email before logging in."
                )

            # Update last login timestamp
            await self.user_crud.update_last_login(user)

            # Generate tokens
            access_token = tokens.create_access_token(str(user.id))
            refresh_token = tokens.create_refresh_token(str(user.id))

            # Create user session with provided context
            ip_address = session_context.ip_address if session_context else None
            user_agent = session_context.user_agent if session_context else None

            session = await self.session_crud.create_user_session(
                user, refresh_token, ip_address, user_agent
            )

            if not session:
                logger.error("Failed to create session")
                raise AuthError("Failed to create session")

            logger.info(f"Login successful for user: {user.id}")

            return schema.AuthResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
                user=schema.UserAccountRead.model_validate(user),
            )

        except AuthError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during login: {type(e).__name__}: {str(e)}")
            raise AuthError("Login failed due to unexpected error")

    async def logout(self, user: UserAccount) -> schema.LogoutResponse:
        """Logout user and revoke all sessions."""
        logger.info(f"Processing logout for user: {user.id}")

        try:
            # Revoke all user sessions
            revoked_count = await self.session_crud.revoke_all_user_sessions(user.id)
            logger.info(f"Logout successful: {revoked_count} sessions revoked for user {user.id}")

            return schema.LogoutResponse(message="Logout successful.")

        except Exception as e:
            logger.error(f"Error during logout for user {user.id}: {type(e).__name__}: {str(e)}")
            raise AuthError("Logout failed due to unexpected error")

    async def refresh(self, refresh_data: schema.RefreshTokenRequest) -> schema.TokenResponse:
        """Refresh access token using valid refresh token."""
        logger.info("Processing token refresh")

        try:
            # Verify refresh token
            token_data = tokens.verify_token(refresh_data.refresh_token, tokens.TOKEN_TYPE_REFRESH)
            if not token_data or not token_data.get("sub"):
                logger.warning("Token refresh failed: Invalid token")
                raise AuthError("Invalid or expired token")

            user_id = token_data["sub"]

            # Get user
            user = await self.user_crud.get_user_by_id(user_id)
            if not user or not user.is_active:
                logger.warning(f"Token refresh failed: User not found or inactive - {user_id}")
                raise AuthError("User account not found or inactive")

            # Validate refresh token session
            session = await self.session_crud.get_user_session_by_token(refresh_data.refresh_token)
            if not session or not session.is_active:
                logger.warning(f"Token refresh failed: Invalid session for user {user_id}")
                raise AuthError("Invalid or expired session")

            # Generate new tokens
            access_token = tokens.create_access_token(str(user.id))
            new_refresh_token = tokens.create_refresh_token(str(user.id))

            # Update session with new refresh token
            updated_session = await self.session_crud.update_user_session(
                refresh_data.refresh_token, new_refresh_token
            )

            if not updated_session:
                logger.error(f"Failed to update session for user {user_id}")
                raise AuthError("Failed to update session")

            logger.info(f"Token refresh successful for user: {user_id}")

            return schema.TokenResponse(
                access_token=access_token,
                refresh_token=new_refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            )

        except AuthError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {type(e).__name__}: {str(e)}")
            raise AuthError("Token refresh failed due to unexpected error")

    async def verify_email(
        self, confirmation_data: schema.EmailConfirmRequest
    ) -> schema.EmailVerificationResponse:
        """Verify user email address using verification token."""
        logger.info("Processing email verification")

        try:
            # Verify token and get user ID
            token_data = tokens.verify_token(
                confirmation_data.token, tokens.TOKEN_TYPE_VERIFICATION
            )
            if not token_data or not token_data.get("sub"):
                logger.warning("Email verification failed: Invalid token")
                raise AuthError("Invalid or expired token")

            user_id = token_data["sub"]

            # Get user
            user = await self.user_crud.get_user_by_id(user_id)
            if not user:
                logger.warning(f"Email verification failed: User not found - {user_id}")
                raise AuthError("User not found")

            # Check if already verified
            if user.is_verified:
                logger.info(f"Email already verified for user: {user_id}")
                return schema.EmailVerificationResponse(
                    message="Email address is already verified.",
                    user=schema.UserAccountRead.model_validate(user),
                )

            # Mark as verified
            verified_user = await self.user_crud.mark_email_verified(user)
            if not verified_user:
                logger.error(f"Failed to mark email as verified for user: {user_id}")
                raise AuthError("Failed to verify email")

            logger.info(f"Email verified successfully for user: {user_id}")

            # Send welcome email
            if verified_user.email:
                try:
                    await email.send_welcome_email(verified_user.email, verified_user.full_name)
                    logger.info(f"Welcome email sent to user: {user_id}")
                except Exception as e:
                    logger.warning(f"Failed to send welcome email: {type(e).__name__}: {str(e)}")

            return schema.EmailVerificationResponse(
                message="Email verified successfully. Welcome!",
                user=schema.UserAccountRead.model_validate(verified_user),
            )

        except AuthError:
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error during email verification: {type(e).__name__}: {str(e)}"
            )
            raise AuthError("Email verification failed due to unexpected error")

    async def forgot_password(
        self,
        reset_request: schema.ForgotPasswordRequest,
    ) -> schema.ForgotPasswordResponse:
        """Send password reset email if user exists."""
        logger.info(f"Processing password reset request for email: {reset_request.email}")

        try:
            # Get user (but don't reveal if they exist)
            user = await self.user_crud.get_user_by_email(reset_request.email)

            if user and user.is_active and user.hashed_password:
                # Generate reset token using user ID (not email)
                reset_token = tokens.create_reset_token(str(user.id))
                reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

                # Send password reset email
                try:
                    await email.send_password_reset_email(user.email, reset_url, user.full_name)
                    logger.info(f"Password reset email sent to user: {user.id}")
                except Exception as e:
                    logger.warning(
                        f"Failed to send password reset email: {type(e).__name__}: {str(e)}"
                    )
            else:
                logger.info(f"Password reset requested for non-existent/inactive user: {email}")

            # Always return the same response for security
            return schema.ForgotPasswordResponse(
                message="If an account with this email exists, a password reset link has been sent."
            )

        except Exception as e:
            logger.error(f"Error during password reset request: {type(e).__name__}: {str(e)}")
            # Still return success message for security
            return schema.ForgotPasswordResponse(
                message="If an account with this email exists, a password reset link has been sent."
            )

    async def reset_password(
        self, reset_data: schema.ResetPasswordRequest
    ) -> schema.PasswordResetResponse:
        """Reset user password using reset token."""
        logger.info("Processing password reset")

        try:
            # Verify reset token and get user ID
            token_data = tokens.verify_token(reset_data.token, tokens.TOKEN_TYPE_RESET)
            if not token_data or not token_data.get("sub"):
                logger.warning("Password reset failed: Invalid token")
                raise AuthError("Invalid or expired token")

            user_id = token_data["sub"]

            # Get user
            user = await self.user_crud.get_user_by_id(user_id)
            if not user or not user.is_active:
                logger.warning(f"Password reset failed: User not found or inactive - {user_id}")
                raise AuthError("User not found or inactive")

            # Update password
            updated_user = await self.user_crud.reset_password(user, reset_data.new_password)
            if not updated_user:
                logger.error(f"Failed to reset password for user: {user_id}")
                raise AuthError("Failed to reset password")

            # Revoke all sessions for security
            await self.session_crud.revoke_all_user_sessions(user.id)

            logger.info(f"Password reset successful for user: {user_id}")

            # Send confirmation email
            if user.email:
                try:
                    await email.send_password_changed_email(user.email, user.full_name)
                    logger.info(f"Password change confirmation email sent to user: {user_id}")
                except Exception as e:
                    logger.warning(
                        f"Failed to send password change confirmation: {type(e).__name__}: {str(e)}"
                    )

            return schema.PasswordResetResponse(
                message="Password has been reset successfully. Please log in with your new password."
            )

        except AuthError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during password reset: {type(e).__name__}: {str(e)}")
            raise AuthError("Password reset failed due to unexpected error")

    def _verify_access_token(self, token: str) -> dict:
        """Verify access token and return payload, raise AuthError if invalid."""
        token_data = tokens.verify_token(token, tokens.TOKEN_TYPE_ACCESS)
        if not token_data or "sub" not in token_data:
            raise AuthError("Invalid or expired token")
        return token_data

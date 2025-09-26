import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth import schema
from app.auth.service import AuthError, AuthService
from app.core.config import settings
from app.core.dependencies import get_auth_service, get_current_user
from app.user.accounts.model import UserAccount

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

router = APIRouter()


@router.post(
    "/register",
    response_model=schema.RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email verification required.",
)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
async def register(
    registration_data: schema.UserRegistrationData,
    background_tasks: BackgroundTasks,
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> schema.RegistrationResponse:
    """Register a new user account with email verification required."""
    client_ip = get_remote_address(request)
    logger.info(
        "Registration attempt",
        extra={"client_ip": client_ip, "email": registration_data.email, "action": "register"},
    )

    try:
        result = await auth_service.register(registration_data, background_tasks)
        logger.info(
            "Registration successful",
            extra={"email": registration_data.email, "action": "register"},
        )
        return result

    except AuthError as e:
        logger.error(f"Registration failed: {str(e)}")
        if "already exists" in str(e).lower():
            raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e))
        else:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/login",
    response_model=schema.AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="User authentication",
    description="Authenticate user credentials and return JWT tokens.",
)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(
    signin_data: schema.SignInRequest,
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> schema.AuthResponse:
    """Authenticate user credentials and return JWT tokens."""
    client_ip = get_remote_address(request)
    logger.info(
        "Login attempt",
        extra={"client_ip": client_ip, "email": signin_data.email, "action": "login"},
    )

    try:
        result = await auth_service.login(signin_data, request)
        logger.info("Login successful", extra={"email": signin_data.email, "action": "login"})
        return result

    except AuthError as e:
        logger.error(f"Login failed: {str(e)}")
        if "temporarily locked" in str(e).lower():
            raise HTTPException(status.HTTP_423_LOCKED, detail=str(e))
        elif "not verified" in str(e).lower():
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(e))
        elif "invalid credentials" in str(e).lower():
            # Don't reveal whether email exists or which part of credentials is wrong
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(e))
        else:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/logout",
    response_model=schema.LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="User logout",
    description="Invalidate all user sessions (logout from all devices).",
)
async def logout(
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> schema.LogoutResponse:
    """Invalidate all user sessions for the current user (logout everywhere)."""
    try:
        result = await auth_service.logout(current_user)
        logger.info(
            "Logout successful",
            extra={"user_id": getattr(current_user, "id", "unknown"), "action": "logout"},
        )
        return result

    except AuthError as e:
        logger.error(f"Logout failed: {str(e)}")
        if "authentication required" in str(e).lower():
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail=str(e))
        else:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/verify-email",
    response_model=schema.EmailVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify email address",
    description="Verify user email address using verification token.",
)
async def verify_email(
    verification_data: schema.EmailConfirmRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> schema.EmailVerificationResponse:
    """Verify user email address using verification token."""
    logger.info(
        "Email verification attempt",
        extra={"token": verification_data.token[:10] + "...", "action": "verify_email"},
    )

    try:
        result = await auth_service.verify_email(verification_data)
        logger.info("Email verification successful", extra={"action": "verify_email"})
        return result

    except AuthError as e:
        logger.error(f"Email verification failed: {str(e)}")
        if "expired token" in str(e).lower():
            raise HTTPException(status.HTTP_410_GONE, detail=str(e))
        elif "not found" in str(e).lower():
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/refresh",
    response_model=schema.TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Generate new access token using valid refresh token.",
)
async def refresh(
    refresh_data: schema.RefreshTokenRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> schema.TokenResponse:
    """Generate new access token using valid refresh token."""
    logger.info("Token refresh attempt", extra={"action": "refresh_token"})

    try:
        result = await auth_service.refresh(refresh_data)
        logger.info("Token refresh successful", extra={"action": "refresh_token"})
        return result

    except AuthError as e:
        logger.error(f"Token refresh failed: {str(e)}")
        if "expired token" in str(e).lower():
            raise HTTPException(status.HTTP_410_GONE, detail=str(e))
        elif "not found" in str(e).lower():
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/forgot-password",
    response_model=schema.ForgotPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Send password reset email if account exists.",
)
@limiter.limit(settings.RATE_LIMIT_PASSWORD)
async def forgot_password(
    reset_request: schema.ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> schema.ForgotPasswordResponse:
    """Send password reset email if account exists."""
    client_ip = get_remote_address(request)
    logger.info(
        "Password reset request",
        extra={"client_ip": client_ip, "email": reset_request.email, "action": "forgot_password"},
    )
    try:
        result = await auth_service.forgot_password(reset_request, background_tasks)
        logger.info(
            "Password reset request processed",
            extra={"email": reset_request.email, "action": "forgot_password"},
        )
        return result
    except AuthError as e:
        logger.error(f"Password reset request error: {str(e)}")
        # Always return the same response for security and type consistency
        return schema.ForgotPasswordResponse(
            message="If an account with this email exists, a password reset link has been sent."
        )


@router.post(
    "/reset-password",
    response_model=schema.PasswordResetResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset password",
    description="Reset password using valid reset token.",
)
async def reset_password(
    reset_data: schema.ResetPasswordRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> schema.PasswordResetResponse:
    """Reset password using valid reset token."""
    logger.info("Password reset attempt", extra={"action": "reset_password"})

    try:
        result = await auth_service.reset_password(reset_data)
        logger.info("Password reset successful", extra={"action": "reset_password"})
        return result

    except AuthError as e:
        logger.error(f"Password reset failed: {str(e)}")
        if "expired token" in str(e).lower():
            raise HTTPException(status.HTTP_410_GONE, detail=str(e))
        elif "not found" in str(e).lower():
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Auth system health check",
    description="Check if authentication system is operational.",
    include_in_schema=False,  # Don't include in public API docs
)
async def auth_health_check() -> dict:
    """Simple health check for auth system."""
    return {"status": "healthy", "service": "auth"}

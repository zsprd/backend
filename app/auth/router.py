import logging
from typing import Annotated, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import schema
from app.auth.service import AuthError, AuthService
from app.core.config import settings
from app.core.database import get_async_db
from app.core.dependencies import get_current_active_user
from app.user.accounts.model import UserAccount

logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


async def get_auth_service(db: Annotated[AsyncSession, Depends(get_async_db)]) -> AuthService:
    """Return an instance of AuthService with injected DB session."""
    return AuthService(db=db)


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
    db: Annotated[AsyncSession, Depends(get_async_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> schema.RegistrationResponse:
    """Register a new user account with email verification required."""
    client_ip = get_remote_address(request)
    logger.info(f"Registration attempt from IP: {client_ip}, email: {registration_data.email}")

    try:
        user = await auth_service.register(
            db=db, registration_data=registration_data, background_tasks=background_tasks
        )
        logger.info(f"Registration successful for user: {user.id}")

        return schema.RegistrationResponse(
            message="Registration successful. Please check your email for verification instructions.",
            user_id=user.id,
            email_verification_required=True,
            user=user,
        )
    except AuthError as e:
        logger.warning(f"Registration failed: {str(e)}")
        if "already exists" in str(e).lower():
            raise HTTPException(status.HTTP_409_CONFLICT, detail=str(e))
        else:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during registration: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Registration failed")


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
    db: Annotated[AsyncSession, Depends(get_async_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> schema.AuthResponse:
    """Authenticate user credentials and return JWT tokens."""
    client_ip = get_remote_address(request)
    logger.info(f"Login attempt from IP: {client_ip}, email: {signin_data.email}")

    try:
        user, access_token, refresh_token = await auth_service.login(
            db=db, signin_data=signin_data, request=request
        )
        logger.info(f"Login successful for user: {user.id}")

        return schema.AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
            user=user,
        )
    except AuthError as e:
        logger.warning(f"Login failed for {signin_data.email}: {str(e)}")
        if "locked" in str(e).lower():
            raise HTTPException(status.HTTP_423_LOCKED, detail=str(e))
        elif "not found" in str(e).lower() or "incorrect" in str(e).lower():
            # Don't reveal whether email exists
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
        elif "not verified" in str(e).lower():
            raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(e))
        else:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error during login: {str(e)}")
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Login failed")


@router.post(
    "/logout",
    response_model=schema.LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="User logout",
    description="Invalidate user session and optionally revoke refresh token.",
)
async def logout(
    request: Request,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    current_user: Annotated[UserAccount, Depends(get_current_active_user)],
    refresh_data: Optional[schema.RefreshTokenRequest] = None,
) -> schema.LogoutResponse:
    """Invalidate user session and optionally revoke refresh token."""
    logger.info(f"Logout request for user: {current_user.id}")

    try:
        refresh_token = getattr(refresh_data, "refresh_token", None) if refresh_data else None
        await auth_service.logout(db=db, refresh_token=refresh_token, current_user=current_user)
        logger.info(f"Logout successful for user: {current_user.id}")

        return schema.LogoutResponse(message="Logout successful")
    except AuthError as e:
        logger.warning(f"Logout failed: {str(e)}")
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
    request: Request,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> schema.EmailVerificationResponse:
    """Verify user email address using verification token."""
    logger.info("Email verification attempt")

    try:
        user = await auth_service.verify_email(db=db, confirmation_data=verification_data)
        logger.info(f"Email verified successfully for user: {user.id}")

        return schema.EmailVerificationResponse(
            message="Email address verified successfully",
            user=user,
        )
    except AuthError as e:
        logger.warning(f"Email verification failed: {str(e)}")
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
    request: Request,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> schema.TokenResponse:
    """Generate new access token using valid refresh token."""
    logger.info("Token refresh attempt")

    try:
        access_token, new_refresh_token = await auth_service.refresh(
            db=db, refresh_data=refresh_data
        )
        logger.info("Token refresh successful")

        return schema.TokenResponse(
            access_token=access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        )
    except AuthError as e:
        logger.warning(f"Token refresh failed: {str(e)}")
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
    db: Annotated[AsyncSession, Depends(get_async_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> schema.ForgotPasswordResponse:
    """Send password reset email if account exists."""
    client_ip = get_remote_address(request)
    logger.info(f"Password reset request from IP: {client_ip}, email: {reset_request.email}")

    try:
        await auth_service.forgot_password(
            db=db, reset_request=reset_request, background_tasks=background_tasks
        )
    except AuthError as e:
        logger.warning(f"Password reset request failed: {str(e)}")
        # Don't reveal if email exists
        pass

    return schema.ForgotPasswordResponse(
        message="If an account with this email exists, password reset instructions have been sent."
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
    request: Request,
    db: Annotated[AsyncSession, Depends(get_async_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> schema.PasswordResetResponse:
    """Reset password using valid reset token."""
    logger.info("Password reset attempt")

    try:
        await auth_service.reset_password(db=db, reset_data=reset_data)
        logger.info("Password reset successful")

        return schema.PasswordResetResponse(
            message="Password has been reset successfully. Please log in with your new password."
        )
    except AuthError as e:
        logger.warning(f"Password reset failed: {str(e)}")
        if "expired token" in str(e).lower():
            raise HTTPException(status.HTTP_410_GONE, detail=str(e))
        elif "not found" in str(e).lower():
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))
        else:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


# Health check endpoint for the auth system
@router.get(
    "/health",
    summary="Auth system health check",
    description="Check if authentication system is operational.",
    include_in_schema=False,  # Don't include in public API docs
)
async def auth_health_check():
    """Simple health check for auth system."""
    return {"status": "healthy", "service": "auth"}

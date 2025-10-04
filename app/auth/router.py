import logging
from ipaddress import ip_address
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.dependencies import get_auth_service, get_current_user
from app.auth.rate_limiter import rate_limit
from app.auth.schemas import (
    RegistrationResponse,
    UserRegistrationData,
    AuthResponse,
    SignInRequest,
    EmailConfirmRequest,
    EmailVerificationResponse,
    TokenResponse,
    RefreshTokenRequest,
    ResetPasswordRequest,
    PasswordResetResponse,
    ForgotPasswordResponse,
    ForgotPasswordRequest,
    LogoutResponse,
)
from app.auth.service import AuthError, AuthService
from app.core.config import settings
from app.user.accounts.model import UserAccount

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/register",
    response_model=RegistrationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account with email verification required.",
)
@rate_limit(settings.RATE_LIMIT_REGISTER)
async def register(
    payload: UserRegistrationData,
    service: AuthService = Depends(get_auth_service),
) -> RegistrationResponse:
    """Register a new user account with email verification required."""
    logger.info("Registration attempt", extra={"email": payload.email, "action": "register"})

    try:
        result = await service.register(payload)

        logger.info("Registration successful", extra={"email": payload.email, "action": "register"})
        return result

    except AuthError as e:
        logger.error(f"Registration failed: {str(e)}")
        raise handle_auth_error(e)


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="User authentication",
    description="Authenticate user credentials and return JWT tokens.",
)
@rate_limit(settings.RATE_LIMIT_LOGIN)
async def login(
    payload: SignInRequest,
    request: Request,
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """Authenticate user credentials and return JWT tokens."""
    logger.info("Login attempt", extra={"email": payload.email, "action": "login"})

    try:
        user_ip = _extract_ip_address(request)
        user_agent = _extract_user_agent(request)

        result = await service.login(payload, user_ip, user_agent)
        logger.info("Login successful", extra={"email": payload.email, "action": "login"})
        return result

    except AuthError as e:
        logger.error(f"Login failed: {str(e)}")
        raise handle_auth_error(e)


@router.post(
    "/logout",
    response_model=LogoutResponse,
    status_code=status.HTTP_200_OK,
    summary="User logout",
    description="Invalidate all user sessions (logout from all devices).",
)
async def logout(
    user: UserAccount = Depends(get_current_user),
    service: AuthService = Depends(get_auth_service),
) -> LogoutResponse:
    """Invalidate all user sessions for the current user (logout everywhere)."""
    try:
        result = await service.logout(user)
        logger.info("Logout successful", extra={"user_id": str(user.id), "action": "logout"})
        return result

    except AuthError as e:
        logger.error(f"Logout failed: {str(e)}")
        raise handle_auth_error(e)


@router.post(
    "/verify-email",
    response_model=EmailVerificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify email address",
    description="Verify user email address using verification token.",
)
@rate_limit(settings.RATE_LIMIT_VERIFY)
async def verify_email(
    payload: EmailConfirmRequest,
    service: AuthService = Depends(get_auth_service),
) -> EmailVerificationResponse:
    """Verify user email address using verification token."""
    logger.info("Email verification attempt", extra={"action": "verify_email"})

    try:
        result = await service.verify_email(payload)
        logger.info("Email verification successful", extra={"action": "verify_email"})
        return result

    except AuthError as e:
        logger.error(f"Email verification failed: {str(e)}")
        raise handle_auth_error(e)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Generate new access token using valid refresh token.",
)
@rate_limit(settings.RATE_LIMIT_REFRESH)
async def refresh(
    payload: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Generate new access token using valid refresh token."""
    logger.info("Token refresh attempt", extra={"action": "refresh_token"})

    try:
        result = await service.refresh(payload)
        logger.info("Token refresh successful", extra={"action": "refresh_token"})
        return result

    except AuthError as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise handle_auth_error(e)


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Send password reset email if account exists.",
)
@rate_limit(settings.RATE_LIMIT_PASSWORD)
async def forgot_password(
    payload: ForgotPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> ForgotPasswordResponse:
    """Send password reset email if account exists."""
    logger.info(
        "Password reset request", extra={"email": payload.email, "action": "forgot_password"}
    )

    try:
        result = await service.forgot_password(payload)

        logger.info(
            "Password reset email sent", extra={"email": payload.email, "action": "forgot_password"}
        )
        return result

    except AuthError as e:
        logger.error(f"Password reset request error: {str(e)}")
        raise handle_auth_error(e)


@router.post(
    "/reset-password",
    response_model=PasswordResetResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset password",
    description="Reset password using valid reset token.",
)
@rate_limit(settings.RATE_LIMIT_PASSWORD)
async def reset_password(
    payload: ResetPasswordRequest,
    service: AuthService = Depends(get_auth_service),
) -> PasswordResetResponse:
    """Reset password using valid reset token."""
    logger.info("Password reset attempt", extra={"action": "reset_password"})

    try:
        result = await service.reset_password(payload)
        logger.info("Password reset successful", extra={"action": "reset_password"})
        return result

    except AuthError as e:
        logger.error(f"Password reset failed: {str(e)}")
        raise handle_auth_error(e)


def _extract_ip_address(request: Optional[Request]) -> Optional[str]:
    """Extract IP address from request with proxy support."""
    if not request:
        return None

    # Check proxy headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take first IP from comma-separated list
        ip = forwarded_for.split(",")[0].strip()
        try:
            ip_address(ip)  # Validate
            return ip
        except ValueError:
            pass  # Invalid IP

    # Check other proxy headers
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        try:
            ip_address(real_ip)
            return real_ip
        except ValueError:
            pass

    # Fall back to direct connection
    if hasattr(request, "client") and request.client:
        return request.client.host

    return None


def _extract_user_agent(request: Optional[Request]) -> Optional[str]:
    """Extract and sanitize user agent from request."""
    if not request:
        return None

    user_agent = request.headers.get("User-Agent", "")
    if not user_agent:
        return None

    # Truncate and sanitize
    sanitized = user_agent[:500].strip()

    # Remove potential XSS
    if "<" in sanitized or ">" in sanitized:
        sanitized = "".join(c for c in sanitized if c not in "<>")

    return sanitized or None


def handle_auth_error(e: AuthError) -> HTTPException:
    """Convert AuthError to appropriate HTTP status code."""
    error_msg = str(e).lower()

    if "expired" in error_msg:  # Expired token/session errors -> 410 Gone
        return HTTPException(status_code=status.HTTP_410_GONE, detail=str(e))
    elif "not found" in error_msg:  # Not found errors -> 404 Not Found
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    elif "invalid credentials" in error_msg:  # Invalid credentials -> 401 Unauthorized
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    elif "not verified" in error_msg:  # Email not verified -> 403 Forbidden
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    elif "temporarily locked" in error_msg:  # Account locked -> 423 Locked
        return HTTPException(status_code=status.HTTP_423_LOCKED, detail=str(e))
    elif "already exists" in error_msg:  # Already exists -> 409 Conflict
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    elif "unexpected error" in error_msg:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    else:  # Default to 400 Bad Request
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

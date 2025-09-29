import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.auth import schema
from app.auth.dependencies import get_auth_service, get_current_user
from app.auth.service import AuthError, AuthService, SessionContext
from app.core.config import settings
from app.user.accounts.model import UserAccount

logger = logging.getLogger(__name__)
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
        result = await auth_service.register(registration_data)

        logger.info(
            "Registration successful",
            extra={"email": registration_data.email, "action": "register"},
        )
        return result

    except AuthError as e:
        logger.error(f"Registration failed: {str(e)}")
        raise handle_auth_error(e)


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
        # Extract session context from request
        session_context = SessionContext(
            ip_address=_extract_ip_address(request), user_agent=_extract_user_agent(request)
        )

        result = await auth_service.login(signin_data, session_context)
        logger.info("Login successful", extra={"email": signin_data.email, "action": "login"})
        return result

    except AuthError as e:
        logger.error(f"Login failed: {str(e)}")
        raise handle_auth_error(e)


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
        raise handle_auth_error(e)


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
        raise handle_auth_error(e)


@router.post(
    "/refresh",
    response_model=schema.TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Generate new access token using valid refresh token.",
)
@limiter.limit(settings.RATE_LIMIT_REFRESH)
async def refresh(
    request: Request,
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
        raise handle_auth_error(e)


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
        result = await auth_service.forgot_password(reset_request)

        logger.info(
            "Password reset request processed",
            extra={"email": reset_request.email, "action": "forgot_password"},
        )
        return result

    except AuthError as e:
        logger.error(f"Password reset request error: {str(e)}")
        raise handle_auth_error(e)


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
        raise handle_auth_error(e)


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="Auth system health check",
    description="Check if authentication system is operational.",
    include_in_schema=False,  # Don't include in public API docs
)
async def auth_health_check() -> dict:
    """Simple health check for auth system."""
    from datetime import datetime, timezone

    return {"status": "ok", "service": "auth", "timestamp": datetime.now(timezone.utc).isoformat()}


def _extract_ip_address(request: Optional[Request]) -> Optional[str]:
    """Extract IP address from request with proxy support."""
    if not request:
        return None

    # Check proxy headers
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take first IP from comma-separated list
        ip = forwarded_for.split(",")[0].strip()
        if _is_valid_ip(ip):
            return ip

    # Check other proxy headers
    real_ip = request.headers.get("X-Real-IP")
    if real_ip and _is_valid_ip(real_ip):
        return real_ip

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


def _is_valid_ip(ip: str) -> bool:
    """Basic IP address validation."""
    if not ip or ip == "unknown":
        return False

    # Basic IPv4 validation
    parts = ip.split(".")
    if len(parts) == 4:
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            pass

    # Basic IPv6 validation (simplified)
    if ":" in ip and len(ip) <= 45:
        return True

    return False


def handle_auth_error(e: AuthError) -> HTTPException:
    """Convert AuthError to appropriate HTTP status code."""
    error_msg = str(e).lower()

    # Expired token/session errors -> 410 Gone
    if any(phrase in error_msg for phrase in ["expired token", "expired session", "has expired"]):
        return HTTPException(status_code=status.HTTP_410_GONE, detail=str(e))

    # Not found errors -> 404 Not Found
    if "not found" in error_msg:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    # Invalid credentials -> 401 Unauthorized
    if "invalid credentials" in error_msg:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    # Email not verified -> 403 Forbidden
    if "not verified" in error_msg:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    # Account locked -> 423 Locked
    if "temporarily locked" in error_msg:
        return HTTPException(status_code=status.HTTP_423_LOCKED, detail=str(e))

    # Already exists -> 409 Conflict
    if "already exists" in error_msg:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    if "unexpected error" in error_msg:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # Default to 400 Bad Request
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

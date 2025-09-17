from typing import Annotated, Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.auth import schema
from app.auth.service import AuthError, AuthService
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import get_auth_service, get_current_active_user, rate_limiter

router = APIRouter()


@router.post(
    "/register", response_model=schema.RegistrationResponse, status_code=status.HTTP_200_OK
)
def register_user(
    registration_data: schema.UserRegistrationData,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    rate_limiter: Annotated[Any, Depends(rate_limiter)],
) -> schema.RegistrationResponse:
    """Register a new user. No authentication required. Rate limited."""
    try:
        # Password requirements enforced in service layer
        user = auth_service.register_user(db, registration_data)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return schema.RegistrationResponse(
        message="User registered successfully. Please check your email for verification.",
        user_id=user.id,
        email_verification_required=True,
        user=schema.UserAccountBase.model_validate(user),
    )


@router.post("/login", response_model=schema.AuthResponse, status_code=status.HTTP_200_OK)
def login_user(
    signin_data: schema.SignInRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    rate_limiter: Annotated[Any, Depends(rate_limiter)],
) -> schema.AuthResponse:
    """Authenticate user and return tokens. No authentication required. Rate limited."""
    try:
        user, access_token, refresh_token = auth_service.authenticate_user(db, signin_data, request)
    except AuthError:
        # Generic error message for security
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return schema.AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES,  # 30 minutes
        user=schema.UserAccountBase.model_validate(user),
    )


@router.post(
    "/verify-email", response_model=schema.EmailVerificationResponse, status_code=status.HTTP_200_OK
)
def verify_email(
    verification_data: schema.EmailConfirmRequest,
    request: Request,  # <-- Added
    db: Annotated[Session, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    rate_limiter: Annotated[Any, Depends(rate_limiter)],  # Added rate limiting
) -> schema.EmailVerificationResponse:
    """Verify user email. No authentication required. Rate limited."""
    try:
        user = auth_service.confirm_email(db, verification_data)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    return schema.EmailVerificationResponse(
        message="Email verified successfully",
        user=schema.UserAccountBase.model_validate(user),
    )


@router.post("/refresh", response_model=schema.TokenResponse, status_code=status.HTTP_200_OK)
def refresh_tokens(
    refresh_data: schema.RefreshTokenRequest,
    db: Annotated[Session, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> schema.TokenResponse:
    """Refresh access token."""
    try:
        access_token, refresh_token = auth_service.refresh_tokens(db, refresh_data)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return schema.TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )


@router.post(
    "/forgot-password", response_model=schema.ForgotPasswordResponse, status_code=status.HTTP_200_OK
)
def forgot_password(
    reset_request: schema.ForgotPasswordRequest,
    request: Request,  # <-- Added
    db: Annotated[Session, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    rate_limiter: Annotated[Any, Depends(rate_limiter)],
) -> schema.ForgotPasswordResponse:
    """Initiate password reset."""
    try:
        auth_service.initiate_password_reset(db, reset_request)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return schema.ForgotPasswordResponse(
        message="If an account with that email exists, password reset instructions have been sent."
    )


@router.post(
    "/reset-password", response_model=schema.PasswordResetResponse, status_code=status.HTTP_200_OK
)
def reset_password(
    reset_data: schema.ResetPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> schema.PasswordResetResponse:
    """Reset password with token."""
    try:
        auth_service.reset_password(db, reset_data)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return schema.PasswordResetResponse(message="Password reset successfully")


@router.post("/logout", response_model=schema.LogoutResponse, status_code=status.HTTP_200_OK)
def logout_user(
    db: Annotated[Session, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    current_user: Annotated[Any, Depends(get_current_active_user)],
    refresh_data: Optional[schema.RefreshTokenRequest] = None,
) -> schema.LogoutResponse:
    """Logout user by revoking session(s). Requires authentication."""
    try:
        refresh_token = refresh_data.refresh_token if refresh_data else None
        auth_service.sign_out(db, refresh_token=refresh_token, current_user=current_user)
    except AuthError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return schema.LogoutResponse(message="Successfully logged out.")

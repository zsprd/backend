from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.auth import schema
from app.auth.service import AuthService
from app.core.database import get_db
from app.core.dependencies import get_auth_service

router = APIRouter()


@router.post("/register", response_model=schema.RegistrationResponse)
def register_user(
    registration_data: schema.UserRegistrationData,
    db: Annotated[Session, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Register a new user."""
    user = auth_service.register_user(db, registration_data)

    return schema.RegistrationResponse(
        message="User registered successfully. Please check your email for verification.",
        user_id=user.id,
        email_verification_required=True,
        user=user,
    )


@router.post("/login", response_model=schema.AuthResponse)
def login_user(
    signin_data: schema.SignInRequest,
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Authenticate user and return tokens."""
    user, access_token, refresh_token = auth_service.authenticate_user(db, signin_data, request)

    return schema.AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=1800,  # 30 minutes
        user=user,
    )


@router.post("/verify-email", response_model=schema.EmailVerificationResponse)
def verify_email(
    verification_data: schema.EmailConfirmRequest,
    db: Annotated[Session, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Verify user email."""
    user = auth_service.confirm_email(db, verification_data)

    return schema.EmailVerificationResponse(
        message="Email verified successfully",
        user=user,
    )


@router.post("/refresh", response_model=schema.TokenResponse)
def refresh_tokens(
    refresh_data: schema.RefreshTokenRequest,
    db: Annotated[Session, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Refresh access token."""
    access_token, refresh_token = auth_service.refresh_tokens(db, refresh_data)

    return schema.TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=1800,
    )


@router.post("/forgot-password")
def forgot_password(
    reset_request: schema.ForgotPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Initiate password reset."""
    auth_service.initiate_password_reset(db, reset_request)
    return {
        "message": "If an account with that email exists, password reset instructions have been sent."
    }


@router.post("/reset-password", response_model=schema.PasswordResetResponse)
def reset_password(
    reset_data: schema.ResetPasswordRequest,
    db: Annotated[Session, Depends(get_db)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
):
    """Reset password with token."""
    auth_service.reset_password(db, reset_data)
    return schema.PasswordResetResponse(message="Password reset successfully")

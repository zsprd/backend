from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
import secrets
import uuid

from app.core.database import get_db
from app.core.auth import (
    get_current_user_id, 
    create_access_token, 
    verify_token,
    create_email_verification_token,
    verify_email_token,
    create_password_reset_token,
    verify_password_reset_token,
    verify_password_hash
)
from app.crud.user import user_crud
from app.crud.user_session import user_session_crud
from app.core.email import send_verification_email, send_password_reset_email

router = APIRouter()


# Request/Response Models
class SignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., description="Frontend-hashed password")
    name: str = Field(..., min_length=1, max_length=255)


class SignUpResponse(BaseModel):
    message: str
    user_id: str
    email_verification_required: bool = True


class EmailConfirmRequest(BaseModel):
    token: str


class SignInRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., description="Frontend-hashed password")


class SignInResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., description="Frontend-hashed new password")


class SignOutRequest(BaseModel):
    refresh_token: Optional[str] = None


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    base_currency: str
    theme_preference: str
    is_verified: bool
    is_premium: bool
    is_active: bool
    created_at: str
    last_login_at: Optional[str]


@router.post("/signup", response_model=SignUpResponse)
async def sign_up(
    *,
    db: Session = Depends(get_db),
    request: SignUpRequest,
    background_tasks: BackgroundTasks
):
    """
    User registration with email verification.
    Password should be hashed on the frontend before sending.
    """
    # Check if user already exists
    existing_user = user_crud.get_by_email(db, email=request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create user (active but unverified)
    user = user_crud.create_user(
        db,
        email=request.email,
        password_hash=request.password,  # Frontend already hashed this
        full_name=request.name,
        is_active=True,
        is_verified=False
    )
    
    # Generate email verification token
    verification_token = create_email_verification_token(user.email)
    
    # Send verification email in background
    background_tasks.add_task(
        send_verification_email,
        email=user.email,
        name=request.name,
        token=verification_token
    )
    
    return SignUpResponse(
        message="Account created successfully. Please check your email to verify your account.",
        user_id=str(user.id),
        email_verification_required=True
    )


@router.post("/confirm")
async def confirm_email(
    *,
    db: Session = Depends(get_db),
    request: EmailConfirmRequest
):
    """
    Confirm user email address using verification token.
    """
    # Verify the token
    email = verify_email_token(request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired confirmation token"
        )
    
    # Get user by email
    user = user_crud.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # Verify the user
    user_crud.verify_email(db, user_id=str(user.id))
    
    return {
        "message": "Email verified successfully",
        "verified_at": datetime.utcnow().isoformat()
    }


@router.post("/signin", response_model=SignInResponse)
async def sign_in(
    *,
    db: Session = Depends(get_db),
    request: SignInRequest
):
    """
    User sign in with email and password.
    Returns access token, refresh token, and user data.
    """
    # Get user by email
    user = user_crud.get_by_email(db, email=request.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled"
        )
    
    # Verify password (compare frontend hash with stored hash)
    if not verify_password_hash(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # Create refresh token and session
    refresh_token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    session = user_session_crud.create_session(
        db,
        user_id=str(user.id),
        refresh_token=refresh_token,
        expires_at=expires_at
    )
    
    # Update last login
    user_crud.update_last_login(db, user=user)
    
    return SignInResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=15 * 60,  # 15 minutes
        user={
            "id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "base_currency": user.base_currency,
            "theme_preference": user.theme_preference,
            "is_verified": user.is_verified,
            "is_premium": user.is_premium,
            "is_active": user.is_active
        }
    )


@router.post("/signout")
async def sign_out(
    *,
    db: Session = Depends(get_db),
    request: SignOutRequest = None,
    current_user_id: Optional[str] = Depends(get_current_user_id)
):
    """
    Sign out user and revoke refresh token.
    Can be called with or without authentication.
    """
    if request and request.refresh_token:
        # Revoke specific refresh token
        user_session_crud.revoke_session_by_token(db, refresh_token=request.refresh_token)
    elif current_user_id:
        # Revoke all sessions for current user
        user_session_crud.revoke_all_user_sessions(db, user_id=current_user_id)
    
    return {
        "message": "Successfully signed out",
        "signed_out_at": datetime.utcnow().isoformat()
    }


@router.post("/forgot-password")
async def forgot_password(
    *,
    db: Session = Depends(get_db),
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks
):
    """
    Request password reset email.
    Always returns success to prevent email enumeration.
    """
    # Always return success, but only send email if user exists
    user = user_crud.get_by_email(db, email=request.email)
    
    if user and user.is_active:
        # Generate password reset token
        reset_token = create_password_reset_token(user.email)
        
        # Send reset email in background
        background_tasks.add_task(
            send_password_reset_email,
            email=user.email,
            name=user.full_name or user.email,
            token=reset_token
        )
    
    return {
        "message": "If an account exists with this email, you will receive password reset instructions.",
        "requested_at": datetime.utcnow().isoformat()
    }


@router.post("/reset-password")
async def reset_password(
    *,
    db: Session = Depends(get_db),
    request: ResetPasswordRequest
):
    """
    Reset user password using reset token.
    New password should be hashed on the frontend.
    """
    # Verify the reset token
    email = verify_password_reset_token(request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Get user by email
    user = user_crud.get_by_email(db, email=email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is disabled"
        )
    
    # Update password
    user_crud.update_password(db, user=user, new_password_hash=request.new_password)
    
    # Revoke all existing sessions for security
    user_session_crud.revoke_all_user_sessions(db, user_id=str(user.id))
    
    return {
        "message": "Password updated successfully",
        "updated_at": datetime.utcnow().isoformat()
    }


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    *,
    db: Session = Depends(get_db),
    request: RefreshTokenRequest
):
    """
    Get new access token using refresh token.
    """
    # Verify refresh token
    session = user_session_crud.get_active_session_by_token(db, refresh_token=request.refresh_token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Get user
    user = user_crud.get(db, id=session.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new access token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    # Create new refresh token and update session
    new_refresh_token = secrets.token_urlsafe(32)
    new_expires_at = datetime.utcnow() + timedelta(days=7)
    
    user_session_crud.update_session(
        db,
        session=session,
        refresh_token=new_refresh_token,
        expires_at=new_expires_at
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=15 * 60  # 15 minutes
    )


@router.get("/me", response_model=UserProfileResponse)
async def get_current_user(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get current user profile information.
    """
    user = user_crud.get(db, id=current_user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserProfileResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        first_name=user.first_name,
        last_name=user.last_name,
        base_currency=user.base_currency,
        theme_preference=user.theme_preference,
        is_verified=user.is_verified,
        is_premium=user.is_premium,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None
    )
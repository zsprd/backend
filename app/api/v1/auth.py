from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from app.core.database import get_db
from app.core.auth import (
    get_current_user_id, 
    get_current_user,
    create_access_token, 
    create_refresh_token,
    verify_token,
    create_email_verification_token,
    verify_email_token,
    create_password_reset_token,
    verify_password_reset_token,
    get_client_ip,
    TOKEN_TYPE_REFRESH,
    FINTECH_SECURITY_SETTINGS
)
from app.core.password import check_password_strength  # Import from password module
from app.models.user import User  # Import User model
from app.crud.user import user_crud
from app.crud.user_session import user_session_crud
# from app.core.email import send_verification_email, send_password_reset_email

router = APIRouter()


# Request/Response Models
class SignUpRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Plain password (will be hashed)")
    full_name: str = Field(..., min_length=1, max_length=255, description="User's full name")
    base_currency: Optional[str] = Field("USD", pattern="^[A-Z]{3}$", description="ISO currency code")
    timezone: Optional[str] = Field("UTC", description="User timezone")


class SignUpResponse(BaseModel):
    message: str
    user_id: str
    email_verification_required: bool = True
    user: dict


class EmailConfirmRequest(BaseModel):
    token: str = Field(..., description="Email verification token")


class SignInRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="Plain password")


class SignInResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Current refresh token")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str  # New refresh token (rotation)
    token_type: str = "bearer"
    expires_in: int


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New plain password")


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


class SignOutRequest(BaseModel):
    refresh_token: Optional[str] = Field(None, description="Refresh token to revoke")
    revoke_all_sessions: bool = Field(False, description="Revoke all user sessions")


class PasswordStrengthRequest(BaseModel):
    password: str = Field(..., description="Password to check")


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    base_currency: str
    theme_preference: str
    timezone: str
    language: str
    is_verified: bool
    is_premium: bool
    is_active: bool
    created_at: str
    last_login_at: Optional[str]


@router.post("/signup", response_model=SignUpResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(
    *,
    db: Session = Depends(get_db),
    request: SignUpRequest,
    background_tasks: BackgroundTasks
):
    """
    User registration with secure password hashing and email verification.
    Passwords are hashed using bcrypt with salt on the backend.
    """
    # Check if user already exists
    existing_user = user_crud.get_by_email(db, email=request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Validate password strength
    password_check = check_password_strength(request.password)
    if not password_check["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet security requirements",
            headers={"X-Password-Strength": str(password_check)}
        )
    
    # Create user (password will be hashed in user_crud.create_user)
    user = user_crud.create_user(
        db,
        email=request.email,
        password=request.password,  # Plain password - will be hashed
        full_name=request.full_name,
        base_currency=request.base_currency,
        timezone=request.timezone,
        is_active=True,
        is_verified=False  # Requires email verification
    )
    
    # Generate email verification token
    verification_token = create_email_verification_token(user.email)
    
    # Send verification email in background
    # background_tasks.add_task(
    #     send_verification_email,
    #     email=user.email,
    #     name=request.full_name,
    #     token=verification_token
    # )
    
    return SignUpResponse(
        message="Account created successfully. Please check your email to verify your account.",
        user_id=str(user.id),
        email_verification_required=True,
        user=user.to_dict()
    )


@router.post("/confirm", status_code=status.HTTP_200_OK)
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
        return {
            "message": "Email already verified",
            "verified_at": user.updated_at.isoformat()
        }
    
    # Verify the user
    user_crud.verify_email(db, user_id=str(user.id))
    
    return {
        "message": "Email verified successfully",
        "verified_at": datetime.utcnow().isoformat()
    }


@router.post("/signin", response_model=SignInResponse, status_code=status.HTTP_200_OK)
async def sign_in(
    *,
    db: Session = Depends(get_db),
    request: SignInRequest,
    client_request: Request
):
    """
    User sign in with email and password.
    Returns access token, refresh token, and user data.
    Implements proper password verification with bcrypt.
    """
    # Authenticate user with bcrypt password verification
    user = user_crud.authenticate_user(db, email=request.email, password=request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(str(user.id))
    
    # Create session with refresh token
    expires_at = datetime.utcnow() + timedelta(days=FINTECH_SECURITY_SETTINGS["refresh_token_expire_days"])
    
    session = user_session_crud.create_session(
        db,
        user_id=str(user.id),
        refresh_token=refresh_token,
        expires_at=expires_at,
        ip_address=get_client_ip(client_request),
        user_agent=client_request.headers.get("User-Agent")
    )
    
    # Update last login
    user_crud.update_last_login(db, user=user)
    
    return SignInResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=FINTECH_SECURITY_SETTINGS["access_token_expire_minutes"] * 60,
        user=user.to_dict()
    )


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    *,
    db: Session = Depends(get_db),
    request: RefreshTokenRequest,
    client_request: Request
):
    """
    Get new access and refresh tokens using current refresh token.
    Implements token rotation for enhanced security.
    """
    # Verify refresh token format
    payload = verify_token(request.refresh_token, TOKEN_TYPE_REFRESH)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token payload"
        )
    
    # Check if session exists and is valid
    session = user_session_crud.get_active_session_by_token(
        db, refresh_token=request.refresh_token
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token not found or expired"
        )
    
    # Verify user still exists and is active
    user = user_crud.get(db, id=user_id)
    if not user or not user.is_active:
        # Revoke the session
        user_session_crud.revoke_session(db, session_id=str(session.id))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled or not found"
        )
    
    # Create new tokens
    new_access_token = create_access_token(data={"sub": str(user.id)})
    new_refresh_token = create_refresh_token(str(user.id))
    
    # Update session with new refresh token (token rotation)
    new_expires_at = datetime.utcnow() + timedelta(days=FINTECH_SECURITY_SETTINGS["refresh_token_expire_days"])
    
    user_session_crud.update_session_token(
        db,
        session=session,
        new_refresh_token=new_refresh_token,
        new_expires_at=new_expires_at,
        ip_address=get_client_ip(client_request),
        user_agent=client_request.headers.get("User-Agent")
    )
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=FINTECH_SECURITY_SETTINGS["access_token_expire_minutes"] * 60
    )


@router.post("/signout", status_code=status.HTTP_200_OK)
async def sign_out(
    *,
    db: Session = Depends(get_db),
    request: Optional[SignOutRequest] = None,
    current_user_id: Optional[str] = Depends(get_current_user_id)
):
    """
    Sign out user and revoke refresh tokens.
    Can revoke specific token or all user sessions.
    """
    if request and request.refresh_token:
        # Revoke specific refresh token
        user_session_crud.revoke_session_by_token(db, refresh_token=request.refresh_token)
        message = "Session revoked successfully"
    elif request and request.revoke_all_sessions and current_user_id:
        # Revoke all sessions for current user
        count = user_session_crud.revoke_all_user_sessions(db, user_id=current_user_id)
        message = f"All {count} sessions revoked successfully"
    elif current_user_id:
        # Default: revoke all sessions for current user
        count = user_session_crud.revoke_all_user_sessions(db, user_id=current_user_id)
        message = f"All {count} sessions revoked successfully"
    else:
        message = "No active session to revoke"
    
    return {
        "message": message,
        "signed_out_at": datetime.utcnow().isoformat()
    }


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
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
        # background_tasks.add_task(
        #     send_password_reset_email,
        #     email=user.email,
        #     name=user.display_name,
        #     token=reset_token
        # )
    
    return {
        "message": "If an account exists with this email, you will receive password reset instructions.",
        "requested_at": datetime.utcnow().isoformat()
    }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    *,
    db: Session = Depends(get_db),
    request: ResetPasswordRequest
):
    """
    Reset user password using reset token.
    New password is hashed using bcrypt.
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
    
    # Validate password strength
    password_check = check_password_strength(request.new_password)
    if not password_check["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet security requirements"
        )
    
    # Update password (will be hashed in user_crud.update_password)
    user_crud.update_password(db, user=user, new_password=request.new_password)
    
    # Revoke all existing sessions for security
    user_session_crud.revoke_all_user_sessions(db, user_id=str(user.id))
    
    return {
        "message": "Password updated successfully. Please sign in with your new password.",
        "updated_at": datetime.utcnow().isoformat()
    }


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    *,
    db: Session = Depends(get_db),
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Change password for authenticated user.
    Requires current password verification.
    """
    # Verify current password
    user = user_crud.authenticate_user(
        db, email=current_user.email, password=request.current_password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password strength
    password_check = check_password_strength(request.new_password)
    if not password_check["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet security requirements"
        )
    
    # Update password
    user_crud.update_password(db, user=current_user, new_password=request.new_password)
    
    # Revoke all other sessions (keep current session active)
    user_session_crud.revoke_all_user_sessions(
        db, user_id=str(current_user.id), except_current=True
    )
    
    return {
        "message": "Password changed successfully",
        "updated_at": datetime.utcnow().isoformat()
    }


@router.post("/check-password-strength", status_code=status.HTTP_200_OK)
async def check_password_strength_endpoint(
    *,
    request: PasswordStrengthRequest
):
    """
    Check password strength and return detailed analysis.
    Useful for frontend password strength indicators.
    """
    return check_password_strength(request.password)


@router.get("/me", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
async def get_current_user_profile(
    *,
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user's profile information.
    """
    return UserProfileResponse(**current_user.to_dict())


@router.get("/sessions", status_code=status.HTTP_200_OK)
async def get_user_sessions(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get user's active sessions for session management.
    """
    sessions = user_session_crud.get_user_sessions(
        db, user_id=current_user_id, active_only=True
    )
    
    return {
        "sessions": [
            {
                "id": str(session.id),
                "created_at": session.created_at.isoformat(),
                "last_accessed_at": session.last_accessed_at.isoformat(),
                "expires_at": session.expires_at.isoformat(),
                "ip_address": str(session.ip_address) if session.ip_address else None,
                "user_agent": session.user_agent,
                "is_current": False  # TODO: Detect current session
            }
            for session in sessions
        ],
        "total_active_sessions": len(sessions)
    }


@router.delete("/sessions/{session_id}", status_code=status.HTTP_200_OK)
async def revoke_session(
    *,
    db: Session = Depends(get_db),
    session_id: str,
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Revoke a specific user session.
    """
    # Verify session belongs to current user
    session = user_session_crud.get(db, id=session_id)
    if not session or str(session.user_id) != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    user_session_crud.revoke_session(db, session_id=session_id)
    
    return {
        "message": "Session revoked successfully",
        "revoked_at": datetime.utcnow().isoformat()
    }

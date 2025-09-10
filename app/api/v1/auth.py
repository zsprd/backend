from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.schemas.user import EmailConfirmRequest, ChangePasswordRequest, ResetPasswordRequest, ForgotPasswordRequest, RefreshTokenRequest, SignUpResponse, SignInResponse, SignUpRequest, SignInRequest, TokenResponse

from app.core.database import get_db
from app.core.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    create_email_verification_token,
    verify_email_token,
    create_password_reset_token,
    verify_password_reset_token,
    get_client_ip,
    check_password_strength,
    TOKEN_TYPE_REFRESH
)
from app.core.oauth import oauth_manager
from app.core.config import settings
from app.core.user import get_current_user, get_optional_current_user_id

from app.models.user import User
from app.crud.user import user_crud
from app.crud.user_session import user_session_crud


router = APIRouter()



# ===================================================================
# Auth Endpoints
# ===================================================================

@router.post("/signup", response_model=SignUpResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(
    *,
    db: Session = Depends(get_db),
    request: SignUpRequest,
    background_tasks: BackgroundTasks,
    client_request: Request
):
    """User registration with secure password hashing."""
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
    
    # Create user
    user = user_crud.create_user(
        db,
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        base_currency="USD",
        timezone="UTC",
        is_verified=False
    )
    
    # Generate email verification token
    verification_token = create_email_verification_token(user.email)
    
    # TODO: Send verification email in background
    # background_tasks.add_task(send_verification_email, user.email, verification_token)
    
    return SignUpResponse(
        message="Account created successfully. Please check your email to verify your account.",
        user_id=str(user.id),
        email_verification_required=True,
        user=user.to_dict()
    )


@router.post("/confirm-email", status_code=status.HTTP_200_OK)
async def confirm_email(
    *,
    db: Session = Depends(get_db),
    request: EmailConfirmRequest
):
    """Confirm user email address."""
    email = verify_email_token(request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired confirmation token"
        )
    
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
    
    user_crud.verify_email(db, user_id=str(user.id))
    
    return {
        "message": "Email verified successfully",
        "verified_at": datetime.now(timezone.utc).isoformat()
    }


@router.post("/signin", response_model=SignInResponse, status_code=status.HTTP_200_OK)
async def sign_in(
    *,
    db: Session = Depends(get_db),
    request: SignInRequest,
    client_request: Request
):
    """User sign in with email and password."""
    user = user_crud.authenticate_user(db, email=request.email, password=request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(str(user.id))
    
    # Create session
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    user_session_crud.create_session(
        db,
        user_id=str(user.id),
        refresh_token=refresh_token,
        expires_at=expires_at,
        ip_address=get_client_ip(client_request),
        user_agent=client_request.headers.get("User-Agent"),
        device_type="web"
    )
    
    # Update last login
    user_crud.update_last_login(db, user=user)
    
    return SignInResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user.to_dict()
    )


@router.get("/oauth/{provider}")
async def oauth_login(provider: str, request: Request):
    """Initiate OAuth login with provider."""
    if provider not in ['google', 'apple']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported OAuth provider"
        )
    
    oauth_client = getattr(oauth_manager.oauth, provider)
    if not oauth_client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{provider.title()} OAuth not configured"
        )
    
    redirect_uri = f"{settings.FRONTEND_URL}/auth/callback/{provider}"
    return await oauth_client.authorize_redirect(request, redirect_uri)


@router.get("/oauth/{provider}/callback")
async def oauth_callback(
    provider: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle OAuth callback."""
    if provider not in ['google', 'apple']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported OAuth provider"
        )
    
    oauth_client = getattr(oauth_manager.oauth, provider)
    
    try:
        # Get token from OAuth provider
        token = await oauth_client.authorize_access_token(request)
        
        # Get user info
        if provider == 'google':
            user_info = await oauth_manager.get_user_info(provider, token['access_token'])
        else:  # Apple
            user_info = await oauth_manager.get_user_info(provider, token['id_token'])
        
        if not user_info or not user_info.get('email'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user information from OAuth provider"
            )
        
        # Check if user exists
        if provider == 'google':
            user = user_crud.get_by_google_id(db, google_id=user_info['id'])
        else:  # Apple
            user = user_crud.get_by_apple_id(db, apple_id=user_info['id'])
        
        if not user:
            # Check if user exists with same email
            user = user_crud.get_by_email(db, email=user_info['email'])
            
            if user:
                # Link OAuth account to existing user
                if provider == 'google':
                    user.google_id = user_info['id']
                else:  # Apple
                    user.apple_id = user_info['id']
                db.add(user)
                db.commit()
            else:
                # Create new user
                oauth_data = {
                    'email': user_info['email'],
                    'full_name': user_info.get('name', ''),
                    'is_verified': user_info.get('email_verified', True)
                }
                
                if provider == 'google':
                    oauth_data['google_id'] = user_info['id']
                else:  # Apple
                    oauth_data['apple_id'] = user_info['id']
                
                user = user_crud.create_user(db, **oauth_data)
        
        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(str(user.id))
        
        # Create session
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        user_session_crud.create_session(
            db,
            user_id=str(user.id),
            refresh_token=refresh_token,
            expires_at=expires_at,
            ip_address=get_client_ip(request),
            user_agent=request.headers.get("User-Agent"),
            device_type="web"
        )
        
        # Update last login
        user_crud.update_last_login(db, user=user)
        
        # Redirect to frontend with tokens
        redirect_url = f"{settings.FRONTEND_URL}/auth/success?access_token={access_token}&refresh_token={refresh_token}"
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        error_url = f"{settings.FRONTEND_URL}/auth/error?error=oauth_failed"
        return RedirectResponse(url=error_url)


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    *,
    db: Session = Depends(get_db),
    request: RefreshTokenRequest,
    client_request: Request
):
    """Refresh access token using refresh token."""
    # Verify refresh token
    payload = verify_token(request.refresh_token, TOKEN_TYPE_REFRESH)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Get session from database
    session = user_session_crud.get_active_session_by_token(
        db, refresh_token=request.refresh_token
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or expired"
        )
    
    user_id = payload.get("sub")
    
    # Create new tokens (token rotation)
    new_access_token = create_access_token(data={"sub": user_id})
    new_refresh_token = create_refresh_token(user_id)
    
    # Update session with new refresh token
    session.refresh_token = new_refresh_token
    session.last_used_at = datetime.now(timezone.utc)
    session.expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    db.add(session)
    db.commit()
    
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/signout", status_code=status.HTTP_200_OK)
async def sign_out(
    *,
    db: Session = Depends(get_db),
    refresh_token: Optional[str] = None,
    current_user_id: Optional[str] = Depends(get_optional_current_user_id)
):
    """Sign out user by revoking refresh token."""
    if refresh_token:
        user_session_crud.revoke_session_by_token(db, refresh_token=refresh_token)
        message = "Session revoked successfully"
    elif current_user_id:
        count = user_session_crud.revoke_all_user_sessions(db, user_id=current_user_id)
        message = f"All {count} sessions revoked successfully"
    else:
        message = "No active session to revoke"
    
    return {
        "message": message,
        "signed_out_at": datetime.now(timezone.utc).isoformat()
    }


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    *,
    db: Session = Depends(get_db),
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks
):
    """Request password reset email."""
    user = user_crud.get_by_email(db, email=request.email)
    
    if user and user.is_active and not user.is_oauth_user:
        reset_token = create_password_reset_token(user.email)
        
        # TODO: Send reset email in background
        # background_tasks.add_task(send_password_reset_email, user.email, reset_token)
    
    # Always return success to prevent email enumeration
    return {
        "message": "If an account exists with this email, you will receive password reset instructions.",
        "requested_at": datetime.now(timezone.utc).isoformat()
    }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    *,
    db: Session = Depends(get_db),
    request: ResetPasswordRequest
):
    """Reset password using reset token."""
    email = verify_password_reset_token(request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    user = user_crud.get_by_email(db, email=email)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Validate password strength
    password_check = check_password_strength(request.new_password)
    if not password_check["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet security requirements"
        )
    
    # Update password
    user_crud.update_password(db, user=user, new_password=request.new_password)
    
    # Revoke all sessions for security
    user_session_crud.revoke_all_user_sessions(db, user_id=str(user.id))
    
    return {
        "message": "Password updated successfully. Please sign in with your new password.",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    *,
    db: Session = Depends(get_db),
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user)
):
    """Change password for authenticated user."""
    if current_user.is_oauth_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change password for OAuth users"
        )
    
    # Verify current password
    if not user_crud.authenticate_user(
        db, email=current_user.email, password=request.current_password
    ):
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
    
    # Revoke all other sessions for security
    user_session_crud.revoke_all_user_sessions(db, user_id=str(current_user.id))
    
    return {
        "message": "Password changed successfully. Please sign in again.",
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
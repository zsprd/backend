from datetime import datetime, timedelta, timezone

from fastapi import BackgroundTasks, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.auth import (
    TOKEN_TYPE_REFRESH,
    check_password_strength,
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    get_client_ip,
    verify_email_token,
    verify_password_reset_token,
    verify_token,
)
from app.core.config import settings
from app.crud.user import user_crud
from app.crud.user_session import user_session_crud
from app.models.users.user import User
from app.schemas.users import (
    ChangePasswordRequest,
    EmailConfirmRequest,
    ForgotPasswordRequest,
    RefreshTokenRequest,
    ResetPasswordRequest,
    SignInRequest,
    SignUpRequest,
)

# --- Service Functions ---


def sign_up_service(
    db: Session, request: SignUpRequest, background_tasks: BackgroundTasks, client_request: Request
):
    existing_user = user_crud.get_by_email(db, email=request.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists",
        )
    password_check = check_password_strength(request.password)
    if not password_check["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet securities requirements",
            headers={"X-Password-Strength": str(password_check)},
        )
    user = user_crud.create_user(
        db,
        email=request.email,
        password=request.password,
        full_name=request.full_name,
        base_currency="USD",
        timezone="UTC",
        is_verified=False,
    )
    # TODO: Send verification email in background
    return user


def confirm_email_service(db: Session, request: EmailConfirmRequest):
    email = verify_email_token(request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired confirmation token",
        )
    user = user_crud.get_by_email(db, email=email)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.is_verified:
        return user, True
    user_crud.verify_email(db, user_id=str(user.id))
    return user, False


def sign_in_service(db: Session, request: SignInRequest, client_request: Request):
    user = user_crud.authenticate_user(db, email=request.email, password=request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password"
        )
    access_token = create_access_token(data={"sub": str(user.id)})
    refresh_token = create_refresh_token(str(user.id))
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    user_session_crud.create_session(
        db,
        user_id=str(user.id),
        refresh_token=refresh_token,
        expires_at=expires_at,
        ip_address=get_client_ip(client_request),
        user_agent=client_request.headers.get("User-Agent"),
        device_type="web",
    )
    user_crud.update_last_login(db, user=user)
    return user, access_token, refresh_token


def refresh_token_service(db: Session, request: RefreshTokenRequest, client_request: Request):
    payload = verify_token(request.refresh_token, TOKEN_TYPE_REFRESH)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    session = user_session_crud.get_active_session_by_token(db, refresh_token=request.refresh_token)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session not found or expired",
        )
    user_id = payload.get("sub")
    new_access_token = create_access_token(data={"sub": user_id})
    new_refresh_token = create_refresh_token(user_id)
    session.refresh_token = new_refresh_token
    session.last_used_at = datetime.now(timezone.utc)
    session.expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    db.add(session)
    db.commit()
    return new_access_token, new_refresh_token


def sign_out_service(db: Session, refresh_token: str = None, current_user_id: str = None):
    if refresh_token:
        user_session_crud.revoke_session_by_token(db, refresh_token=refresh_token)
        return "Session revoked successfully"
    elif current_user_id:
        count = user_session_crud.revoke_all_user_sessions(db, user_id=current_user_id)
        return f"All {count} sessions revoked successfully"
    else:
        return "No active session to revoke"


def forgot_password_service(
    db: Session, request: ForgotPasswordRequest, background_tasks: BackgroundTasks
):
    user = user_crud.get_by_email(db, email=request.email)
    if user and user.is_active and not user.is_oauth_user:
        create_password_reset_token(user.email)
        # TODO: Send reset email in background
    # Always return success
    return True


def reset_password_service(db: Session, request: ResetPasswordRequest):
    email = verify_password_reset_token(request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    user = user_crud.get_by_email(db, email=email)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    password_check = check_password_strength(request.new_password)
    if not password_check["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet securities requirements",
        )
    user_crud.update_password(db, user=user, new_password=request.new_password)
    user_session_crud.revoke_all_user_sessions(db, user_id=str(user.id))
    return user


def change_password_service(db: Session, request: ChangePasswordRequest, current_user: User):
    if current_user.is_oauth_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change password for OAuth users",
        )
    if not user_crud.authenticate_user(
        db, email=current_user.email, password=request.current_password
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    password_check = check_password_strength(request.new_password)
    if not password_check["is_valid"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password does not meet securities requirements",
        )
    user_crud.update_password(db, user=current_user, new_password=request.new_password)
    user_session_crud.revoke_all_user_sessions(db, user_id=str(current_user.id))
    return current_user

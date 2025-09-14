from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.auth import (
    create_access_token,
    create_refresh_token,
    get_client_ip,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.oauth import oauth_manager
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
    SignInResponse,
    SignUpRequest,
    SignUpResponse,
    TokenResponse,
)
from app.services import auth_service

router = APIRouter()


@router.post("/signup", response_model=SignUpResponse, status_code=status.HTTP_201_CREATED)
async def sign_up(
    *,
    db: Session = Depends(get_db),
    request: SignUpRequest,
    background_tasks: BackgroundTasks,
    client_request: Request,
):
    user = auth_service.sign_up_service(db, request, background_tasks, client_request)
    return SignUpResponse(
        message="PortfolioAccount created successfully. Please check your email to verify your account.",
        user_id=user.id,
        email_verification_required=True,
        user=user.to_dict(),
    )


@router.post("/confirm-email", status_code=status.HTTP_200_OK)
async def confirm_email(*, db: Session = Depends(get_db), request: EmailConfirmRequest):
    user, already_verified = auth_service.confirm_email_service(db, request)
    if already_verified:
        return {
            "message": "Email already verified",
            "verified_at": user.updated_at.isoformat(),
        }
    return {
        "message": "Email verified successfully",
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/signin", response_model=SignInResponse, status_code=status.HTTP_200_OK)
async def sign_in(
    *, db: Session = Depends(get_db), request: SignInRequest, client_request: Request
):
    user, access_token, refresh_token = auth_service.sign_in_service(db, request, client_request)
    return SignInResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user.to_dict(),
    )


@router.get("/oauth/{provider}")
async def oauth_login(provider: str, request: Request):
    """Initiate OAuth login with provider."""
    if provider not in ["google", "apple"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported OAuth provider"
        )

    oauth_client = getattr(oauth_manager.oauth, provider)
    if not oauth_client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{provider.title()} OAuth not configured",
        )

    redirect_uri = f"{settings.FRONTEND_URL}/auth/callback/{provider}"
    return await oauth_client.authorize_redirect(request, redirect_uri)


@router.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, request: Request, db: Session = Depends(get_db)):
    """Handle OAuth callback."""
    if provider not in ["google", "apple"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported OAuth provider"
        )

    oauth_client = getattr(oauth_manager.oauth, provider)

    try:
        # Get token from OAuth provider
        token = await oauth_client.authorize_access_token(request)

        # Get users info
        if provider == "google":
            user_info = await oauth_manager.get_user_info(provider, token["access_token"])
        else:  # Apple
            user_info = await oauth_manager.get_user_info(provider, token["id_token"])

        if not user_info or not user_info.get("email"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get users information from OAuth provider",
            )

        # Check if users exists
        if provider == "google":
            user = user_crud.get_by_google_id(db, google_id=user_info["id"])
        else:  # Apple
            user = user_crud.get_by_apple_id(db, apple_id=user_info["id"])

        if not user:
            # Check if users exists with same email
            user = user_crud.get_by_email(db, email=user_info["email"])

            if user:
                # Link OAuth account to existing users
                if provider == "google":
                    user.google_id = user_info["id"]
                else:  # Apple
                    user.apple_id = user_info["id"]
                db.add(user)
                db.commit()
            else:
                # Create new users
                oauth_data = {
                    "email": user_info["email"],
                    "full_name": user_info.get("name", ""),
                    "is_verified": user_info.get("email_verified", True),
                }

                if provider == "google":
                    oauth_data["google_id"] = user_info["id"]
                else:  # Apple
                    oauth_data["apple_id"] = user_info["id"]

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
            device_type="web",
        )

        # Update last login
        user_crud.update_last_login(db, user=user)

        # Redirect to frontend with tokens
        redirect_url = f"{settings.FRONTEND_URL}/auth/success?access_token={access_token}&refresh_token={refresh_token}"
        return RedirectResponse(url=redirect_url)

    except Exception:
        error_url = f"{settings.FRONTEND_URL}/auth/error?error=oauth_failed"
        return RedirectResponse(url=error_url)


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    *,
    db: Session = Depends(get_db),
    request: RefreshTokenRequest,
    client_request: Request,
):
    new_access_token, new_refresh_token = auth_service.refresh_token_service(
        db, request, client_request
    )
    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post("/signout", status_code=status.HTTP_200_OK)
async def sign_out(
    *,
    db: Session = Depends(get_db),
    refresh_token: Optional[str] = None,
    current_user_id: Optional[str] = Depends(user_crud.get_optional_current_user_id),
):
    message = auth_service.sign_out_service(db, refresh_token, current_user_id)
    return {"message": message, "signed_out_at": datetime.now(timezone.utc).isoformat()}


@router.post("/forgot-password", status_code=status.HTTP_200_OK)
async def forgot_password(
    *,
    db: Session = Depends(get_db),
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
):
    auth_service.forgot_password_service(db, request, background_tasks)
    return {
        "message": "If an account exists with this email, you will receive password reset instructions.",
        "requested_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(*, db: Session = Depends(get_db), request: ResetPasswordRequest):
    auth_service.reset_password_service(db, request)
    return {
        "message": "Password updated successfully. Please sign in with your new password.",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    *,
    db: Session = Depends(get_db),
    request: ChangePasswordRequest,
    current_user: User = Depends(user_crud.get_current_user),
):
    auth_service.change_password_service(db, request, current_user)
    return {
        "message": "Password changed successfully. Please sign in again.",
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

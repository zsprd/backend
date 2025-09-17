from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth.oauth.service import oauth_manager
from app.auth.service import (
    create_access_token,
    create_refresh_token,
    get_client_ip,
)
from app.core.config import settings
from app.core.database import get_db
from app.user.accounts.crud import user_crud
from app.user.sessions.crud import user_session_crud

router = APIRouter()


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
            user_agent=request.headers.get("UserProfile-Agent"),
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

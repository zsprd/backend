from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth import utils
from app.auth.service import AuthService
from app.core.database import get_db
from app.users.profile.crud import user_profile_crud
from app.users.profile.model import UserProfile
from app.users.profile.service import UserProfileService

# Security scheme
security = HTTPBearer()


# Dependency functions for FastAPI
def get_auth_service() -> AuthService:
    """Get auth service instance."""
    return AuthService()


def get_user_profile_service() -> UserProfileService:
    """Get user profile service instance."""
    return UserProfileService()


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> UserProfile:
    """Get current authenticated user from JWT token."""

    token = credentials.credentials

    try:
        token_data = utils.verify_token(token, utils.TOKEN_TYPE_ACCESS)
        if not token_data or not token_data.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    try:
        user_id = UUID(token_data["sub"])
        user = user_profile_crud.get_active(db, id=user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(
    current_user: Annotated[UserProfile, Depends(get_current_user)],
) -> UserProfile:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def get_current_verified_user(
    current_user: Annotated[UserProfile, Depends(get_current_active_user)],
) -> UserProfile:
    """Get current verified user."""
    if not current_user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")
    return current_user

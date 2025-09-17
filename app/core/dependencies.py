from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.auth import utils
from app.auth.service import AuthService
from app.core.database import get_db
from app.user.accounts.crud import user_account_crud
from app.user.accounts.model import UserAccount
from app.user.accounts.service import UserAccountService

# Security scheme
security = HTTPBearer()

# Global rate limiter instance
limiter = Limiter(key_func=get_remote_address)


# Rate limiter dependency (example: 5 requests per 15 minutes)
def rate_limiter(request: Request) -> None:
    limiter.limit("50/15minutes")(lambda request: None)(request)


# Exception handler for rate limit exceeded
def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded. Please try again later."},
    )


# Dependency functions for FastAPI
def get_auth_service() -> AuthService:
    """Get auth service instance."""
    return AuthService()


def get_user_profile_service() -> UserAccountService:
    """Get user profile service instance."""
    return UserAccountService()


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> UserAccount:
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
        user = user_account_crud.get_active(db, id=user_id)
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
    current_user: Annotated[UserAccount, Depends(get_current_user)],
) -> UserAccount:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


def get_current_verified_user(
    current_user: Annotated[UserAccount, Depends(get_current_active_user)],
) -> UserAccount:
    """Get current verified user."""
    if not current_user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")
    return current_user

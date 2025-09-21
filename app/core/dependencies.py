import logging
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import utils
from app.auth.service import AuthError, AuthService
from app.core.database import get_async_db
from app.user.accounts.crud import user_account_crud
from app.user.accounts.model import UserAccount
from app.user.accounts.service import UserAccountService

# Configure logger
logger = logging.getLogger(__name__)

security = HTTPBearer()


def get_auth_service(db: Annotated[AsyncSession, Depends(get_async_db)]) -> AuthService:
    """Return an instance of AuthService with injected DB session."""
    return AuthService(db=db)


def get_user_account_service(
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> UserAccountService:
    """Return an instance of UserAccountService with injected DB session."""
    return UserAccountService(db=db)


async def get_current_user(
    db: Annotated[AsyncSession, Depends(get_async_db)],
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> UserAccount:
    """Get the current authenticated user from JWT access token."""
    token = credentials.credentials

    try:
        token_data = utils.verify_token(token, utils.TOKEN_TYPE_ACCESS)
        if not token_data or not token_data.get("sub"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = UUID(token_data["sub"])
    except (ValueError, TypeError, AuthError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = await user_account_crud.get_active(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


async def get_current_active_user(
    current_user: Annotated[UserAccount, Depends(get_current_user)],
) -> UserAccount:
    """Ensure the user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user


async def get_current_verified_user(
    current_user: Annotated[UserAccount, Depends(get_current_active_user)],
) -> UserAccount:
    """Ensure the user has verified their email."""
    if not current_user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")
    return current_user


async def get_user_by_id(
    user_id: UUID, db: Annotated[AsyncSession, Depends(get_async_db)]
) -> UserAccount:
    """Fetch any user by UUID. Raises 404 if not found."""
    user = await user_account_crud.get_active(db, id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user

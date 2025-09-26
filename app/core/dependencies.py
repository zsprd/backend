import logging
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import tokens
from app.auth.service import AuthService
from app.core.database import get_async_db
from app.user.accounts.crud import CRUDUserAccount
from app.user.accounts.model import UserAccount
from app.user.accounts.service import UserService
from app.user.sessions.crud import CRUDUserSession

logger = logging.getLogger(__name__)
security = HTTPBearer()


# Repository Dependencies (Infrastructure Layer)
def get_user_repository(db: Annotated[AsyncSession, Depends(get_async_db)]) -> CRUDUserAccount:
    """Get user repository with database session."""
    return CRUDUserAccount(db)


def get_session_repository(db: Annotated[AsyncSession, Depends(get_async_db)]) -> CRUDUserSession:
    """Get session repository with database session."""
    return CRUDUserSession(db)


# Service Dependencies (Business Logic Layer)
def get_user_service(
    user_repo: Annotated[CRUDUserAccount, Depends(get_user_repository)],
) -> UserService:
    """Get user service with injected repository."""
    return UserService(user_repo)


def get_auth_service(
    user_repo: Annotated[CRUDUserAccount, Depends(get_user_repository)],
    session_repo: Annotated[CRUDUserSession, Depends(get_session_repository)],
) -> AuthService:
    """Get auth service with injected repositories."""
    return AuthService(user_repo, session_repo)


# Authentication Dependencies
async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> UserAccount:
    """Get the current authenticated user from JWT access token."""
    token = credentials.credentials

    try:
        token_data = tokens.verify_token(token, tokens.TOKEN_TYPE_ACCESS)
        user_id = UUID(token_data["sub"])
        user = await auth_service.user_crud.get_user_by_id(user_id)

        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        return user

    except Exception as e:
        logger.warning(f"Invalid token format: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )


async def get_current_active_user(
    current_user: Annotated[UserAccount, Depends(get_current_user)],
) -> UserAccount:
    """Ensure the user is active."""
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    return current_user

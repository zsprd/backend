import logging
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import tokens
from app.auth.service import AuthService
from app.core.database import get_async_db
from app.user.accounts.crud import UserAccountRepository
from app.user.accounts.model import UserAccount
from app.user.sessions.crud import UserSessionRepository

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_auth_service(db: AsyncSession = Depends(get_async_db)) -> AuthService:
    return AuthService(
        user_repo=UserAccountRepository(db),
        session_repo=UserSessionRepository(db),
    )


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
        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
        return user

    except Exception as e:
        logger.warning(f"Invalid token format: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

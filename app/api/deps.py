from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user_id, get_current_user
from app.models.user import User
from app.crud.user import user_crud


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.
    Raises HTTPException if user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get the current verified user.
    Raises HTTPException if user is not verified.
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User email not verified"
        )
    return current_user


# Common pagination parameters
class CommonQueryParams:
    def __init__(
        self, 
        skip: int = 0, 
        limit: int = 100,
        search: Optional[str] = None
    ):
        self.skip = skip
        self.limit = min(limit, 1000)  # Max 1000 items per request
        self.search = search
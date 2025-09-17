from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_user_profile_service
from app.user.accounts.model import UserAccount
from app.user.accounts.schema import UserAccountRead, UserAccountUpdate
from app.user.accounts.service import UserAccountService

router = APIRouter()


@router.get("/me", response_model=UserAccountRead)
def get_current_user_profile(
    current_user: Annotated[UserAccount, Depends(get_current_user)],
):
    """Get current user's profile."""
    return current_user


@router.put("/me", response_model=UserAccountRead)
def update_current_user_profile(
    profile_update: UserAccountUpdate,
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    user_service: Annotated[UserAccountService, Depends(get_user_profile_service)],
):
    """Update current user's profile."""
    updated_user = user_service.update_user_profile(
        db, user=current_user, profile_update=profile_update
    )
    return updated_user

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.dependencies import get_current_active_user
from app.user.accounts import schema
from app.user.accounts.model import UserAccount
from app.user.accounts.service import user_account_service

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/me", response_model=schema.UserAccountRead, status_code=status.HTTP_200_OK)
async def get_current_user_profile(
    current_user: Annotated[UserAccount, Depends(get_current_active_user)],
) -> schema.UserAccountRead:
    """
    Get current user's profile information.

    Returns the authenticated user's profile data including
    email, name, preferences, and account status.
    """
    logger.info(f"Profile requested for user: {current_user.id}")
    return schema.UserAccountRead.model_validate(current_user)


@router.patch("/me", response_model=schema.UserAccountRead, status_code=status.HTTP_200_OK)
async def update_current_user_profile(
    profile_update: schema.UserAccountUpdate,
    current_user: Annotated[UserAccount, Depends(get_current_active_user)],
    db: Annotated[AsyncSession, Depends(get_async_db)],
) -> schema.UserAccountRead:
    """
    Update current user's profile information.

    Allows users to update their profile fields like name,
    language, country, and currency preferences.
    Email updates require separate verification process.
    """
    logger.info(f"Profile update requested for user: {current_user.id}")

    try:
        updated_user = await user_account_service.update_user_profile(
            db=db, user=current_user, profile_update=profile_update
        )

        logger.info(f"Profile updated successfully for user: {current_user.id}")
        return schema.UserAccountRead.model_validate(updated_user)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile update failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update profile"
        )

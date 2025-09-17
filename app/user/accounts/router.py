from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.dependencies import get_current_user, get_user_profile_service
from app.user.accounts import schema
from app.user.accounts.model import UserAccount
from app.user.accounts.service import UserProfileService

router = APIRouter()


@router.get("/me", response_model=schema.UserAccountRead)
def get_current_user_profile(
    current_user: Annotated[UserAccount, Depends(get_current_user)],
):
    """Get current user's profile."""
    return current_user


@router.put("/me", response_model=schema.UserAccountRead)
def update_current_user_profile(
    profile_update: schema.UserAccountUpdate,
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    user_service: Annotated[UserProfileService, Depends(get_user_profile_service)],
):
    """Update current user's profile."""
    updated_user = user_service.update_user_profile(
        db, user=current_user, profile_update=profile_update
    )
    return updated_user


@router.get("/me/preferences")
def get_user_preferences(
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    user_service: Annotated[UserProfileService, Depends(get_user_profile_service)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get user preferences."""
    return user_service.get_user_preferences(db, current_user)


@router.put("/me/preferences")
def update_user_preferences(
    preferences: dict,
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    user_service: Annotated[UserProfileService, Depends(get_user_profile_service)],
):
    """Update user preferences."""
    updated_user = user_service.update_user_preferences(
        db, user=current_user, preferences=preferences
    )
    return {"message": "Preferences updated successfully"}


@router.get("/me/completion")
def get_profile_completion(
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    user_service: Annotated[UserProfileService, Depends(get_user_profile_service)],
):
    """Get profile completion status."""
    completeness = user_service.validate_profile_completeness(current_user)
    completion_percentage = user_service.get_profile_completion_percentage(current_user)

    return {
        "completion_percentage": completion_percentage,
        "completeness_details": completeness,
    }

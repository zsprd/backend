from typing import Dict, Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.users.profile.crud import user_profile_crud
from app.users.profile.model import UserProfile
from app.users.profile.schema import UserProfileCreate, UserProfileUpdate


class UserProfileService:
    """Service layer for user profile operations (non-auth related)."""

    def __init__(self):
        self.crud = user_profile_crud

    # ----------------------
    # Core Profile Operations
    # ----------------------
    def get_user_by_id(self, db: Session, user_id: UUID) -> Optional[UserProfile]:
        """Get active user by ID."""
        return self.crud.get_active(db, id=user_id)

    def get_user_by_email(self, db: Session, email: str) -> Optional[UserProfile]:
        """Get active user by email."""
        return self.crud.get_active_by_email(db, email=email)

    def update_user_profile(
        self,
        db: Session,
        user: UserProfile,
        profile_update: UserProfileUpdate,
    ) -> UserProfile:
        """Update user profile information."""
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update profile for inactive account",
            )

        return self.crud.update(db, db_obj=user, obj_in=profile_update)

    def get_user_preferences(self, db: Session, user: UserProfile) -> Dict[str, str]:
        """Get user preferences as a dictionary."""
        return {
            "timezone": user.timezone,
            "base_currency": user.base_currency,
            "language": user.language,
            "theme_preference": user.theme_preference,
        }

    def update_user_preferences(
        self,
        db: Session,
        user: UserProfile,
        preferences: Dict[str, str],
    ) -> UserProfile:
        """Update user preferences."""
        # Create update object from preferences
        update_data = UserProfileUpdate(**preferences)
        return self.update_user_profile(db, user=user, profile_update=update_data)

    # ----------------------
    # Profile Validation & Checks
    # ----------------------
    def is_email_available(
        self, db: Session, email: str, exclude_user_id: Optional[UUID] = None
    ) -> bool:
        """Check if email is available for use."""
        existing_user = self.crud.get_by_email(db, email=email)
        if not existing_user:
            return True

        # If excluding a specific user (for updates), check if it's the same user
        if exclude_user_id and existing_user.id == exclude_user_id:
            return True

        return False

    def validate_profile_completeness(self, user: UserProfile) -> Dict[str, bool]:
        """Check profile completeness for onboarding."""
        return {
            "has_full_name": bool(user.full_name and user.full_name.strip()),
            "email_verified": user.is_verified,
            "timezone_set": user.timezone != "UTC",  # Assuming UTC is default
            "preferences_configured": all(
                [
                    user.base_currency != "USD",  # Assuming USD is default
                    user.language != "en",  # Assuming en is default
                    user.theme_preference != "system",  # Assuming system is default
                ]
            ),
        }

    def get_profile_completion_percentage(self, user: UserProfile) -> int:
        """Calculate profile completion percentage."""
        completeness = self.validate_profile_completeness(user)
        completed_items = sum(completeness.values())
        total_items = len(completeness)
        return int((completed_items / total_items) * 100)

    # ----------------------
    # Internal Use (Called by Auth Service)
    # ----------------------
    def create_user_profile(self, db: Session, profile_data: UserProfileCreate) -> UserProfile:
        """Create user profile (used internally by auth service)."""
        return self.crud.create(db, obj_in=profile_data)

    def mark_email_verified(self, db: Session, user: UserProfile) -> UserProfile:
        """Mark user email as verified (used by auth service)."""
        return self.crud.verify_email(db, user=user)

    def deactivate_user_account(self, db: Session, user: UserProfile) -> UserProfile:
        """Deactivate user account (used by auth service)."""
        return self.crud.deactivate(db, user=user)

    def update_last_login(self, db: Session, user: UserProfile) -> UserProfile:
        """Update last login timestamp (used by auth service)."""
        return self.crud.update_last_login(db, user=user)


# Singleton instance
user_profile_service = UserProfileService()

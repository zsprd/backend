from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.user.accounts.crud import user_account_crud
from app.user.accounts.model import UserAccount
from app.user.accounts.schema import UserAccountCreate, UserAccountUpdate


class UserAccountService:
    """Service layer for user profile operations (non-auth related)."""

    def __init__(self):
        self.crud = user_account_crud

    # ----------------------
    # Core Profile Operations
    # ----------------------
    def get_user_by_id(self, db: Session, user_id: UUID) -> Optional[UserAccount]:
        """Get active user by ID."""
        return self.crud.get_active(db, id=user_id)

    def get_user_by_email(self, db: Session, email: str) -> Optional[UserAccount]:
        """Get active user by email."""
        return self.crud.get_active_by_email(db, email=email)

    def update_user_profile(
        self,
        db: Session,
        user: UserAccount,
        profile_update: UserAccountUpdate,
    ) -> UserAccount:
        """Update user profile information."""
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update profile for inactive account",
            )

        return self.crud.update(db, db_obj=user, obj_in=profile_update)

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

    # ----------------------
    # Internal Use (Called by Auth Service)
    # ----------------------
    def create_user_profile(self, db: Session, profile_data: UserAccountCreate) -> UserAccount:
        """Create user profile (used internally by auth service)."""
        return self.crud.create(db, obj_in=profile_data)

    def mark_email_verified(self, db: Session, user: UserAccount) -> UserAccount:
        """Mark user email as verified (used by auth service)."""
        return self.crud.verify_email(db, user=user)

    def deactivate_user_account(self, db: Session, user: UserAccount) -> UserAccount:
        """Deactivate user account (used by auth service)."""
        return self.crud.deactivate(db, user=user)

    def update_last_login(self, db: Session, user: UserAccount) -> UserAccount:
        """Update last login timestamp (used by auth service)."""
        return self.crud.update_last_login(db, user=user)


# Singleton instance
user_account_service = UserAccountService()

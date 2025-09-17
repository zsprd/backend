from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.user.accounts.crud import user_profile_crud
from app.user.accounts.model import UserProfile


class CRUDAuth:
    """Auth-specific CRUD operations."""

    def __init__(self):
        self.user_crud = user_profile_crud

    def authenticate_user(self, db: Session, *, email: str, password: str) -> Optional[UserProfile]:
        """Authenticate user with email and password."""
        from app.auth.utils import verify_password  # Avoid circular imports

        user = self.user_crud.get_active_by_email(db, email=email)
        if not user or not user.password_hash:
            return None

        if not verify_password(password, user.password_hash):
            return None

        # Update last login
        self.user_crud.update_last_login(db, user=user)
        return user

    def create_user_with_password(
        self, db: Session, *, user_data: dict, password_hash: str
    ) -> UserProfile:
        """Create user with password hash (for email/password registration)."""
        from app.user.accounts.schema import UserProfileCreate

        profile_data = UserProfileCreate(**user_data)
        return self.user_crud.create_with_password(
            db, obj_in=profile_data, password_hash=password_hash
        )

    def create_oauth_user(self, db: Session, *, user_data: dict) -> UserProfile:
        """Create OAuth user (no password required)."""
        from app.user.accounts.schema import UserProfileCreate

        profile_data = UserProfileCreate(**user_data)
        return self.user_crud.create_oauth_user(db, obj_in=profile_data)

    def update_password(
        self, db: Session, *, user: UserProfile, new_password_hash: str
    ) -> UserProfile:
        """Update user password hash."""
        if not user or not user.is_active:
            raise ValueError("Cannot update password for inactive user")

        user.password_hash = new_password_hash
        user.updated_at = datetime.now(timezone.utc)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def remove_password(self, db: Session, *, user: UserProfile) -> UserProfile:
        """Remove password (convert to OAuth-only account)."""
        user.password_hash = None
        user.updated_at = datetime.now(timezone.utc)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def verify_user_email(self, db: Session, *, user_id: UUID) -> Optional[UserProfile]:
        """Verify user email by ID."""
        user = self.user_crud.get(db, id=user_id)
        if not user:
            return None
        return self.user_crud.verify_email(db, user=user)

    def deactivate_user_account(self, db: Session, *, user_id: UUID) -> Optional[UserProfile]:
        """Deactivate user account by ID."""
        user = self.user_crud.get(db, id=user_id)
        if not user:
            return None
        return self.user_crud.deactivate(db, user=user)

    def delete_user_account(
        self, db: Session, *, user_id: UUID, hard_delete: bool = False
    ) -> Optional[UserProfile]:
        """Delete user account (soft delete by default)."""
        user = self.user_crud.get(db, id=user_id)
        if not user:
            return None

        if hard_delete:
            self.user_crud.hard_delete(db, user=user)
            return None
        else:
            return self.user_crud.soft_delete(db, user=user)

    def check_email_exists(self, db: Session, *, email: str) -> bool:
        """Check if email already exists in the system."""
        user = self.user_crud.get_by_email(db, email=email)
        return user is not None

    def get_user_for_token_validation(self, db: Session, *, user_id: UUID) -> Optional[UserProfile]:
        """Get active user for token validation."""
        return self.user_crud.get_active(db, id=user_id)


# Singleton instance
auth_crud = CRUDAuth()

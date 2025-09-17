from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.crud import CRUDBase
from app.user.accounts.model import UserAccount
from app.user.accounts.schema import UserAccountCreate, UserAccountUpdate


class CRUDUserAccount(CRUDBase[UserAccount, UserAccountCreate, UserAccountUpdate]):
    """CRUD operations for user profiles."""

    def get(self, db: Session, id: UUID) -> Optional[UserAccount]:
        """Get user by ID."""
        return db.query(UserAccount).filter(UserAccount.id == id).first()

    def get_by_email(self, db: Session, *, email: str) -> Optional[UserAccount]:
        """Get user by email address."""
        return db.query(UserAccount).filter(UserAccount.email == email).first()

    def get_active(self, db: Session, *, id: UUID) -> Optional[UserAccount]:
        """Get active user by ID."""
        return (
            db.query(UserAccount)
            .filter(and_(UserAccount.id == id, UserAccount.is_active == True))
            .first()
        )

    def get_active_by_email(self, db: Session, *, email: str) -> Optional[UserAccount]:
        """Get active user by email."""
        return (
            db.query(UserAccount)
            .filter(and_(UserAccount.email == email, UserAccount.is_active == True))
            .first()
        )

    def create(self, db: Session, *, obj_in: UserAccountCreate) -> UserAccount:
        """Create new user profile."""
        db_obj = UserAccount(
            email=str(obj_in.email),
            full_name=obj_in.full_name,
            timezone=obj_in.timezone,
            base_currency=obj_in.base_currency,
            is_active=True,
            is_verified=False,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def create_with_password(
        self, db: Session, *, obj_in: UserAccountCreate, password_hash: str
    ) -> UserAccount:
        """Create new user profile with password hash (for registration)."""
        db_obj = UserAccount(
            email=str(obj_in.email),
            full_name=obj_in.full_name,
            timezone=obj_in.timezone,
            base_currency=obj_in.base_currency,
            password_hash=password_hash,
            is_active=True,
            is_verified=False,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def create_oauth_user(self, db: Session, *, obj_in: UserAccountCreate) -> UserAccount:
        """Create new OAuth user (no password, pre-verified)."""
        db_obj = UserAccount(
            email=str(obj_in.email),
            full_name=obj_in.full_name,
            timezone=obj_in.timezone,
            base_currency=obj_in.base_currency,
            password_hash=None,  # OAuth users don't have passwords
            is_active=True,
            is_verified=True,  # OAuth users are pre-verified
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: UserAccount,
        obj_in: UserAccountUpdate,
    ) -> UserAccount:
        """Update user profile."""
        update_data = obj_in.model_dump(exclude_unset=True)

        # List of allowed fields for profile updates
        allowed_fields = {
            "full_name",
            "base_currency",
            "timezone",
            "language",
            "theme_preference",
        }

        # Filter and process update data
        for field in list(update_data.keys()):
            if field not in allowed_fields:
                del update_data[field]
            elif field == "base_currency" and update_data[field]:
                update_data[field] = update_data[field].upper()
            elif field == "language" and update_data[field]:
                update_data[field] = update_data[field].lower()

        # Apply updates
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db_obj.updated_at = datetime.now(timezone.utc)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_last_login(self, db: Session, *, user: UserAccount) -> UserAccount:
        """Update user's last login timestamp."""
        user.last_login_at = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def verify_email(self, db: Session, *, user: UserAccount) -> UserAccount:
        """Mark user email as verified."""
        user.is_verified = True
        user.updated_at = datetime.now(timezone.utc)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def deactivate(self, db: Session, *, user: UserAccount) -> UserAccount:
        """Deactivate user account."""
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def reactivate(self, db: Session, *, user: UserAccount) -> UserAccount:
        """Reactivate user account."""
        user.is_active = True
        user.updated_at = datetime.now(timezone.utc)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def soft_delete(self, db: Session, *, user: UserAccount) -> UserAccount:
        """Soft delete user by setting deleted_at timestamp."""
        now = datetime.now(timezone.utc)
        user.deleted_at = now
        user.is_active = False
        user.updated_at = now
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def hard_delete(self, db: Session, *, user: UserAccount) -> bool:
        """Permanently delete user (use with caution)."""
        db.delete(user)
        db.commit()
        return True


# Create singleton instance
user_account_crud = CRUDUserAccount(UserAccount)

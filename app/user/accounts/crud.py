import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crud import CRUDBase
from app.user.accounts.model import UserAccount
from app.user.accounts.schema import UserAccountCreate, UserAccountUpdate

logger = logging.getLogger(__name__)


class CRUDUserAccount(CRUDBase[UserAccount, UserAccountCreate, UserAccountUpdate]):
    """
    CRUD operations for user accounts.

    Provides database operations for user account management including
    creation, updates, soft deletion, and various query methods.
    """

    async def get(self, db: AsyncSession, id: UUID) -> Optional[UserAccount]:
        """Get user by ID."""
        result = await db.execute(select(UserAccount).where(UserAccount.id == id))
        return result.scalar_one_or_none()

    async def get_active(self, db: AsyncSession, id: UUID) -> Optional[UserAccount]:
        """Get active user by ID."""
        result = await db.execute(
            select(UserAccount).where(UserAccount.id == id, UserAccount.is_active == True)
        )
        return result.scalar_one_or_none()

    async def get_active_by_email(self, db: AsyncSession, email: str) -> Optional[UserAccount]:
        """Get active user by email."""
        result = await db.execute(
            select(UserAccount).where(
                UserAccount.email == email.lower(), UserAccount.is_active == True
            )
        )
        return result.scalar_one_or_none()

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[UserAccount]:
        """Get user by email (including inactive)."""
        result = await db.execute(select(UserAccount).where(UserAccount.email == email.lower()))
        return result.scalar_one_or_none()

    async def is_email_available(self, db: AsyncSession, email: str) -> bool:
        """Check if email is available for registration."""
        result = await db.execute(select(exists().where(UserAccount.email == email.lower())))
        return not result.scalar()

    async def create_with_password(
        self, db: AsyncSession, obj_in: UserAccountCreate, hashed_password: str
    ) -> UserAccount:
        """Create user with hashed password."""
        logger.debug(f"Creating user with password: {obj_in.email}")

        db_obj = UserAccount(
            email=obj_in.email.lower(),
            full_name=obj_in.full_name,
            hashed_password=hashed_password,
            language=obj_in.language,
            country=obj_in.country,
            currency=obj_in.currency,
            is_verified=False,
            is_active=True,
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)

        logger.info(f"User created with ID: {db_obj.id}")
        return db_obj

    async def create_oauth_user(self, db: AsyncSession, obj_in: UserAccountCreate) -> UserAccount:
        """Create OAuth user (no password, pre-verified)."""
        logger.debug(f"Creating OAuth user: {obj_in.email}")

        db_obj = UserAccount(
            email=obj_in.email.lower(),
            full_name=obj_in.full_name,
            language=obj_in.language,
            country=obj_in.country,
            currency=obj_in.currency,
            is_verified=True,  # OAuth users are pre-verified
            is_active=True,
            hashed_password=None,  # No password for OAuth users
        )

        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)

        logger.info(f"OAuth user created with ID: {db_obj.id}")
        return db_obj

    async def update_last_login(self, db: AsyncSession, user: UserAccount) -> UserAccount:
        """Update user's last login timestamp."""
        user.last_login_at = datetime.now(timezone.utc)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def mark_email_verified(self, db: AsyncSession, user: UserAccount) -> UserAccount:
        """Mark user email as verified."""
        user.is_verified = True
        user.updated_at = datetime.now(timezone.utc)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(f"Email verified for user: {user.id}")
        return user

    async def deactivate(self, db: AsyncSession, user: UserAccount) -> UserAccount:
        """Deactivate user account."""
        user.is_active = False
        user.updated_at = datetime.now(timezone.utc)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(f"Account deactivated for user: {user.id}")
        return user

    async def soft_delete(self, db: AsyncSession, user: UserAccount) -> UserAccount:
        """Soft delete user by setting deleted_at timestamp."""
        user.deleted_at = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)
        user.is_active = False
        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(f"Account soft deleted for user: {user.id}")
        return user

    async def hard_delete(self, db: AsyncSession, user: UserAccount) -> bool:
        """Permanently delete user (use with caution)."""
        await db.delete(user)
        await db.commit()

        logger.warning(f"Account HARD DELETED for user: {user.id}")
        return True

    async def get_multi_active(
        self, db: AsyncSession, skip: int = 0, limit: int = 100
    ) -> List[UserAccount]:
        """Get multiple active users with pagination."""
        result = await db.execute(
            select(UserAccount)
            .where(UserAccount.is_active == True, UserAccount.deleted_at.is_(None))
            .offset(skip)
            .limit(limit)
            .order_by(UserAccount.created_at.desc())
        )
        return result.scalars().all()

    async def count_users(self, db: AsyncSession, active_only: bool = True) -> int:
        """Count total users."""
        query = select(func.count(UserAccount.id))

        if active_only:
            query = query.where(UserAccount.is_active == True, UserAccount.deleted_at.is_(None))

        result = await db.execute(query)
        return result.scalar() or 0

    async def count_verified_users(self, db: AsyncSession) -> int:
        """Count users with verified emails."""
        result = await db.execute(
            select(func.count(UserAccount.id)).where(
                UserAccount.is_verified == True,
                UserAccount.is_active == True,
                UserAccount.deleted_at.is_(None),
            )
        )
        return result.scalar() or 0

    async def search_by_email_pattern(
        self, db: AsyncSession, email_pattern: str, limit: int = 10
    ) -> List[UserAccount]:
        """Search users by email pattern (admin use)."""
        result = await db.execute(
            select(UserAccount)
            .where(UserAccount.email.ilike(f"%{email_pattern}%"), UserAccount.deleted_at.is_(None))
            .limit(limit)
        )
        return result.scalars().all()


# Create singleton instance
user_account_crud = CRUDUserAccount(UserAccount)

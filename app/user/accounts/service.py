import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.user.accounts.crud import user_account_crud
from app.user.accounts.model import UserAccount
from app.user.accounts.schema import UserAccountUpdate

logger = logging.getLogger(__name__)


class UserAccountService:
    """
    Service layer for user profile operations (non-auth related).

    This service handles user profile management, preferences,
    and account status operations. Authentication-related operations
    are handled by the AuthService.
    """

    def __init__(self):
        self.crud = user_account_crud

    # ----------------------
    # Core Profile Operations
    # ----------------------
    async def get_user_by_id(self, db: AsyncSession, user_id: UUID) -> Optional[UserAccount]:
        """Get user by ID."""
        logger.debug(f"Fetching user by ID: {user_id}")
        return await self.crud.get(db, id=user_id)

    async def get_user_by_email(self, db: AsyncSession, email: str) -> Optional[UserAccount]:
        """Get user by email address."""
        logger.debug(f"Fetching user by email: {email}")
        return await self.crud.get_user_by_email(db, email=email)

    async def update_user_profile(
        self,
        db: AsyncSession,
        user: UserAccount,
        profile_update: UserAccountUpdate,
    ) -> UserAccount:
        """
        Update user profile information.

        Only updates fields that are provided in the update object.
        Does not allow updating authentication-related fields.
        """
        logger.info(f"Updating profile for user: {user.id}")

        # Check if account is active
        if not user.is_active:
            logger.warning(f"Profile update attempted on inactive account: {user.id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update profile for inactive account",
            )

        # Filter out None values from update
        update_data = profile_update.model_dump(exclude_unset=True)

        if not update_data:
            logger.info(f"No fields to update for user: {user.id}")
            return user

        # Update the fields
        for field, value in update_data.items():
            setattr(user, field, value)

        # Update timestamp
        user.updated_at = datetime.now(timezone.utc)

        # Save to database
        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(f"Profile updated successfully for user: {user.id}")
        return user

    # ----------------------
    # Profile Validation & Checks
    # ----------------------
    async def is_email_available(self, db: AsyncSession, email: str) -> bool:
        """Check if an email address is available for registration."""
        logger.debug(f"Checking email availability: {email}")
        return await self.crud.is_email_available(db, email=email)

    async def validate_user_active(self, db: AsyncSession, user_id: UUID) -> bool:
        """Check if a user account is active."""
        user = await self.crud.get(db, id=user_id)
        return user and user.is_active

    # ----------------------
    # Internal Use (Called by Auth Service)
    # ----------------------
    async def mark_email_verified(self, db: AsyncSession, user: UserAccount) -> UserAccount:
        """
        Mark user's email as verified.

        This is called by the auth service after email verification.
        """
        logger.info(f"Marking email as verified for user: {user.id}")
        return await self.crud.mark_email_verified(db, user=user)

    async def deactivate_user_account(self, db: AsyncSession, user: UserAccount) -> UserAccount:
        """
        Deactivate a user account.

        This prevents the user from logging in but preserves their data.
        """
        logger.info(f"Deactivating account for user: {user.id}")
        return await self.crud.deactivate(db, user=user)

    async def update_last_login(self, db: AsyncSession, user: UserAccount) -> UserAccount:
        """
        Update last login timestamp.

        This is called by the auth service on successful login.
        """
        logger.debug(f"Updating last login for user: {user.id}")
        return await self.crud.update_last_login(db, user=user)

    async def increment_failed_login_attempts(
        self, db: AsyncSession, user: UserAccount
    ) -> UserAccount:
        """
        Increment failed login attempts counter.

        Used by auth service for account lockout functionality.
        """
        user.failed_login_attempts += 1
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def reset_failed_login_attempts(self, db: AsyncSession, user: UserAccount) -> UserAccount:
        """
        Reset failed login attempts after successful login.

        Used by auth service after successful authentication.
        """
        user.failed_login_attempts = 0
        user.locked_until = None
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    async def lock_account_until(
        self, db: AsyncSession, user: UserAccount, locked_until: datetime
    ) -> UserAccount:
        """
        Lock account until specified time.

        Used by auth service for temporary account lockout.
        """
        user.locked_until = locked_until
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    # ----------------------
    # Statistics and Analytics
    # ----------------------
    async def get_user_count(self, db: AsyncSession, active_only: bool = True) -> int:
        """Get total number of users."""
        logger.debug(f"Getting user count (active_only={active_only})")
        return await self.crud.count_users(db, active_only=active_only)

    async def get_verified_user_count(self, db: AsyncSession) -> int:
        """Get number of users with verified emails."""
        logger.debug("Getting verified user count")
        return await self.crud.count_verified_users(db)


# Singleton instance
user_account_service = UserAccountService()

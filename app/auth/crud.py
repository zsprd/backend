import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.user.accounts.crud import user_account_crud
from app.user.accounts.model import UserAccount
from app.user.accounts.schema import UserAccountCreate

logger = logging.getLogger(__name__)


class CRUDAuth:
    """Auth-specific CRUD operations."""

    def __init__(self):
        self.user_crud = user_account_crud

    async def authenticate_user(
        self, db: AsyncSession, *, email: str, password: str
    ) -> Optional[UserAccount]:
        """Authenticate user with email and password."""
        from app.auth.utils import verify_password  # Avoid circular imports

        logger.debug(f"Authenticating user with email: {email}")

        # Get active user by email
        user = await self.user_crud.get_active_by_email(db, email=email)
        if not user or not user.hashed_password:
            logger.debug(f"Authentication failed: User not found or no password hash for {email}")
            return None

        # Verify password
        if not verify_password(password, user.hashed_password):
            logger.debug(f"Authentication failed: Invalid password for {email}")
            return None

        # Check if password needs rehashing
        from app.auth.utils import hash_password, needs_rehash

        if needs_rehash(user.hashed_password):
            logger.info(f"Rehashing password for user: {user.id}")
            user.hashed_password = hash_password(password)
            db.add(user)
            await db.commit()

        # Update last login
        await self.user_crud.update_last_login(db, user=user)

        logger.info(f"Authentication successful for user: {user.id}")
        return user

    async def create_user_with_password(
        self, db: AsyncSession, *, user_data: dict, hashed_password: str
    ) -> UserAccount:
        """Create user with password hash (for email/password registration)."""
        logger.debug(f"Creating user with password for email: {user_data.get('email')}")

        profile_data = UserAccountCreate(**user_data)
        user = await self.user_crud.create_with_password(
            db, obj_in=profile_data, hashed_password=hashed_password
        )

        logger.info(f"User created with password, ID: {user.id}")
        return user

    async def create_oauth_user(self, db: AsyncSession, *, user_data: dict) -> UserAccount:
        """Create OAuth user (no password required)."""
        logger.debug(f"Creating OAuth user for email: {user_data.get('email')}")

        profile_data = UserAccountCreate(**user_data)
        user = await self.user_crud.create_oauth_user(db, obj_in=profile_data)

        logger.info(f"OAuth user created, ID: {user.id}")
        return user

    async def update_password(
        self, db: AsyncSession, *, user: UserAccount, new_hashed_password: str
    ) -> UserAccount:
        """Update user password hash."""
        if not user or not user.is_active:
            logger.error("Attempted to update password for inactive or non-existent user")
            raise ValueError("Cannot update password for inactive user")

        logger.debug(f"Updating password for user: {user.id}")

        user.hashed_password = new_hashed_password
        user.updated_at = datetime.now(timezone.utc)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(f"Password updated for user: {user.id}")
        return user

    async def remove_password(self, db: AsyncSession, *, user: UserAccount) -> UserAccount:
        """Remove password (convert to OAuth-only account)."""
        logger.debug(f"Removing password for user: {user.id}")

        user.hashed_password = None
        user.updated_at = datetime.now(timezone.utc)
        db.add(user)
        await db.commit()
        await db.refresh(user)

        logger.info(f"Password removed for user: {user.id}")
        return user

    async def deactivate_user_account(
        self, db: AsyncSession, *, user_id: UUID
    ) -> Optional[UserAccount]:
        """Deactivate user account by ID."""
        logger.debug(f"Deactivating user account: {user_id}")

        user = await self.user_crud.get(db, id=user_id)
        if not user:
            logger.warning(f"User not found for deactivation: {user_id}")
            return None

        deactivated = await self.user_crud.deactivate(db, user=user)
        logger.info(f"User account deactivated: {user_id}")
        return deactivated

    async def delete_user_account(
        self, db: AsyncSession, *, user_id: UUID, hard_delete: bool = False
    ) -> Optional[UserAccount]:
        """Delete user account (soft delete by default)."""
        logger.debug(f"Deleting user account: {user_id} (hard_delete={hard_delete})")

        user = await self.user_crud.get(db, id=user_id)
        if not user:
            logger.warning(f"User not found for deletion: {user_id}")
            return None

        if hard_delete:
            await self.user_crud.hard_delete(db, user=user)
            logger.info(f"User account hard deleted: {user_id}")
            return None
        else:
            deleted = await self.user_crud.soft_delete(db, user=user)
            logger.info(f"User account soft deleted: {user_id}")
            return deleted

    async def get_user_for_token_validation(
        self, db: AsyncSession, *, user_id: str
    ) -> Optional[UserAccount]:
        """Get active user for token validation."""
        logger.debug(f"Getting user for token validation: {user_id}")

        # Convert string to UUID if needed
        try:
            user_uuid = UUID(user_id) if isinstance(user_id, str) else user_id
        except ValueError:
            logger.error(f"Invalid user ID format: {user_id}")
            return None

        user = await self.user_crud.get_active(db, id=user_uuid)

        if user:
            logger.debug(f"User found for token validation: {user_id}")
        else:
            logger.debug(f"User not found or inactive: {user_id}")

        return user


# Singleton instance
auth_crud = CRUDAuth()

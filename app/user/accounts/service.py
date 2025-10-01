import logging
from typing import Optional
from uuid import UUID

from app.user.accounts import schema
from app.user.accounts.crud import UserAccountRepository
from app.user.accounts.model import UserAccount

logger = logging.getLogger(__name__)


class UserError(Exception):
    """Custom exception for user-related errors."""

    pass


class UserService:
    """User business logic service."""

    def __init__(self, user_repo: UserAccountRepository):
        self.user_crud = user_repo

    async def get_user_profile(self, user_id: UUID) -> schema.UserAccountRead:
        """Get user profile by ID."""
        try:
            logger.debug(f"Fetching user profile for ID: {user_id}")
            user = await self.user_crud.get_user_by_id(user_id, False)

            if not user:
                logger.warning(f"User profile not found for ID: {user_id}")
                raise UserError("User profile not found")

            logger.debug(f"User profile found for ID: {user_id}")
            return schema.UserAccountRead.model_validate(user)

        except UserError:
            raise
        except Exception as e:
            logger.error(f"Failed to get user profile: {type(e).__name__}: {str(e)}")
            raise UserError("Failed to retrieve user profile")

    async def get_user_by_email(self, email: str) -> Optional[schema.UserAccountRead]:
        """Get user by email address."""
        try:
            # Validate email format
            if not email or "@" not in email:
                logger.warning("Invalid email format provided")
                raise UserError("Invalid email format")

            logger.debug(f"Fetching user by email: {email[:3]}***")

            user = await self.user_crud.get_user_by_email(email)

            if not user:
                return None

            return schema.UserAccountRead.model_validate(user)

        except UserError:
            raise
        except Exception as e:
            logger.error(f"Failed to get user by email: {type(e).__name__}: {str(e)}")
            raise UserError("Failed to retrieve user by email")

    async def update_user_profile(
        self, user: UserAccount, profile_update: schema.UserAccountUpdate
    ) -> schema.UserAccountRead:
        """Update user profile information."""
        try:
            logger.info(f"Updating profile for user: {user.id}")

            # Validate user state
            await self._validate_user_for_update(user)

            # Update user profile (this is now async)
            updated_user = await self.user_crud.update_profile(user, profile_update)

            if not updated_user:
                logger.error(f"Failed to update profile for user: {user.id}")
                raise UserError("Failed to update user profile")

            logger.info(f"Profile updated successfully for user: {user.id}")
            return schema.UserAccountRead.model_validate(updated_user)

        except UserError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to update profile for user {user.id}: {type(e).__name__}: {str(e)}"
            )
            raise UserError("Failed to update user profile")

    async def change_password(
        self, user: UserAccount, password_update: schema.UserAccountPasswordUpdate
    ) -> None:
        """Change user password."""
        try:
            logger.info(f"Password change requested for user: {user.id}")

            # Validate user can change password
            await self._validate_user_for_update(user)

            # Delegate to CRUD layer for secure password handling
            updated_user = await self.user_crud.update_password(
                user, password_update.current_password, password_update.new_password
            )

            if not updated_user:
                logger.error(f"Failed to change password for user: {user.id}")
                raise UserError("Current password is incorrect or password change failed")

            logger.info(f"Password changed successfully for user: {user.id}")

        except UserError:
            raise
        except Exception as e:
            logger.error(f"Password change failed for user {user.id}: {type(e).__name__}: {str(e)}")
            raise UserError("Failed to change password")

    async def mark_email_verified(self, user: UserAccount) -> UserAccount:
        """Mark user's email as verified."""
        try:
            logger.info(f"Marking email as verified for user: {user.id}")

            verified_user = await self.user_crud.mark_email_verified(user)
            if not verified_user:
                raise UserError("Failed to verify email")

            return verified_user

        except UserError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to mark email verified for user {user.id}: {type(e).__name__}: {str(e)}"
            )
            raise UserError("Failed to verify email")

    async def deactivate_user_account(self, user: UserAccount) -> UserAccount:
        """Deactivate a user account."""
        try:
            logger.info(f"Deactivating account for user: {user.id}")

            deactivated_user = await self.user_crud.deactivate_account(user)
            if not deactivated_user:
                raise UserError("Failed to deactivate account")

            return deactivated_user

        except UserError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to deactivate account for user {user.id}: {type(e).__name__}: {str(e)}"
            )
            raise UserError("Failed to deactivate account")

    async def delete_user_account(self, user: UserAccount) -> bool:
        """Permanently delete a user account."""
        try:
            logger.info(f"Deleting account for user: {user.id}")

            success = await self.user_crud.delete_account(user)
            if not success:
                raise UserError("Failed to delete account")

            logger.info(f"Account deleted successfully for user: {user.id}")
            return True

        except UserError:
            raise
        except Exception as e:
            logger.error(
                f"Failed to delete account for user {user.id}: {type(e).__name__}: {str(e)}"
            )
            raise UserError("Failed to delete account")

    async def _validate_user_for_update(self, user: UserAccount) -> None:
        """Validate user can be updated."""
        if not user:
            raise UserError("User not found")

        if not user.is_active:
            logger.warning(f"Update attempted on inactive account: {user.id}")
            raise UserError("Cannot update inactive account")

        if user.is_locked:
            lockout_remaining = user.lockout_time_remaining or 0
            logger.warning(f"Update attempted on locked account: {user.id}")
            raise UserError(f"Account is locked. Try again in {lockout_remaining} minutes.")

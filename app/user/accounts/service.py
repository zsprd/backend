import logging
from typing import Optional
from uuid import UUID

from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.user.accounts.model import UserAccount
from app.user.accounts.repository import UserAccountRepository
from app.user.accounts.schemas import (
    UserAccountPasswordUpdate,
    UserAccountRead,
    UserAccountUpdate,
)

logger = logging.getLogger(__name__)


class UserError(Exception):
    """Custom exception for user-related errors."""

    pass


class UserAccountService:
    """Service layer for user account business logic."""

    def __init__(self, repository: UserAccountRepository):
        self.repository = repository

    async def get_user_profile(self, user_id: UUID) -> UserAccountRead:
        """Get user profile by ID."""
        try:
            logger.debug(f"Fetching user profile for ID: {user_id}")
            user = await self.repository.get_user_by_id(user_id)

            if not user:
                logger.warning(f"User profile not found for ID: {user_id}")
                raise UserError("User profile not found")

            logger.debug(f"User profile found for ID: {user_id}")
            return UserAccountRead.model_validate(user)

        except UserError:
            raise
        except Exception as e:
            logger.error(f"Failed to get user profile: {type(e).__name__}: {str(e)}")
            raise UserError("Failed to retrieve user profile")

    async def get_user_by_email(self, email: str) -> Optional[UserAccountRead]:
        """Get user by email address."""
        try:
            if not email or "@" not in email:
                logger.warning("Invalid email format provided")
                raise UserError("Invalid email format")

            logger.debug(f"Fetching user by email: {email[:3]}***")

            user = await self.repository.get_user_by_email(email)

            if not user:
                return None

            return UserAccountRead.model_validate(user)

        except UserError:
            raise
        except Exception as e:
            logger.error(f"Failed to get user by email: {type(e).__name__}: {str(e)}")
            raise UserError("Failed to retrieve user by email")

    async def update_user_profile(
        self, user: UserAccount, profile_update: UserAccountUpdate
    ) -> UserAccountRead:
        """Update user profile information."""
        try:
            logger.info(f"Updating profile for user: {user.id}")

            self._validate_user_for_update(user)

            # TODO: Add audit log before update - log what fields are being changed
            # await audit_log.log_profile_update_attempt(
            #     user_id=user.id,
            #     changes=profile_update.model_dump(exclude_unset=True),
            #     timestamp=datetime.now(timezone.utc)
            # )

            update_data = profile_update.model_dump(exclude_unset=True)
            updated_user = await self.repository.update_profile(user, update_data)

            if not updated_user:
                logger.error(f"Failed to update profile for user: {user.id}")
                raise UserError("Failed to update user profile")

            # TODO: Add audit log after successful update
            # await audit_log.log_profile_updated(
            #     user_id=user.id,
            #     changes=update_data,
            #     timestamp=datetime.now(timezone.utc)
            # )

            logger.info(f"Profile updated successfully for user: {user.id}")
            return UserAccountRead.model_validate(updated_user)

        except UserError:
            raise
        except IntegrityError as e:
            logger.error(f"Integrity error updating profile for user {user.id}: {str(e)}")
            raise UserError("Invalid data provided for profile update")
        except SQLAlchemyError as e:
            logger.error(f"Database error updating profile for user {user.id}: {str(e)}")
            raise UserError("Failed to update user profile")
        except Exception as e:
            logger.error(f"Unexpected error updating profile for user {user.id}: {str(e)}")
            raise UserError("Failed to update user profile")

    async def change_password(
        self, user: UserAccount, password_update: UserAccountPasswordUpdate
    ) -> None:
        """Change user password."""
        try:
            logger.info(f"Password change requested for user: {user.id}")

            self._validate_user_for_update(user)

            # TODO: Add security audit log before password change
            # await audit_log.log_password_change_attempt(
            #     user_id=user.id,
            #     ip_address=request.client.host,  # Pass from router
            #     timestamp=datetime.now(timezone.utc)
            # )

            updated_user = await self.repository.update_password(
                user, password_update.current_password, password_update.new_password
            )

            if not updated_user:
                # TODO: Add audit log for failed password change
                # await audit_log.log_password_change_failed(
                #     user_id=user.id,
                #     reason="incorrect_current_password",
                #     timestamp=datetime.now(timezone.utc)
                # )
                logger.error(f"Failed to change password for user: {user.id}")
                raise UserError("Current password is incorrect or password change failed")

            # TODO: Add security audit log for successful password change
            # await audit_log.log_password_changed(
            #     user_id=user.id,
            #     timestamp=datetime.now(timezone.utc)
            # )

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

            verified_user = await self.repository.mark_email_verified(user)
            if not verified_user:
                raise UserError("Failed to verify email")

            return verified_user

        except UserError:
            raise
        except Exception as e:
            logger.error(f"Failed to mark email verified for user {user.id}: {str(e)}")
            raise UserError("Failed to verify email")

    async def deactivate_user_account(self, user: UserAccount) -> UserAccount:
        """Deactivate a user account."""
        try:
            logger.info(f"Deactivating account for user: {user.id}")

            deactivated_user = await self.repository.deactivate_account(user)
            if not deactivated_user:
                raise UserError("Failed to deactivate account")

            return deactivated_user

        except UserError:
            raise
        except Exception as e:
            logger.error(f"Failed to deactivate account for user {user.id}: {str(e)}")
            raise UserError("Failed to deactivate account")

    async def delete_user_account(self, user: UserAccount) -> bool:
        """Permanently delete a user account."""
        try:
            logger.info(f"Deleting account for user: {user.id}")

            # TODO: Add audit log before deletion - critical for compliance
            # await audit_log.log_account_deletion(
            #     user_id=user.id,
            #     email=user.email,
            #     timestamp=datetime.now(timezone.utc),
            #     retention_required=True  # For GDPR/compliance
            # )

            success = await self.repository.delete_account(user)
            if not success:
                raise UserError("Failed to delete account")

            logger.info(f"Account deleted successfully for user: {user.id}")
            return True

        except UserError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete account for user {user.id}: {str(e)}")
            raise UserError("Failed to delete account")

    def _validate_user_for_update(self, user: UserAccount) -> None:
        """Validate user can be updated."""
        if not user:
            raise UserError("User not found")

        if not user.is_active:
            logger.warning(f"Update attempted on inactive account: {user.id}")
            raise UserError("Cannot update inactive account")

        # Use the @property method from model
        if user.is_locked:
            lockout_minutes = user.lockout_time_remaining or 0
            logger.warning(f"Update attempted on locked account: {user.id}")
            raise UserError(f"Account is locked. Try again in {lockout_minutes} minutes.")

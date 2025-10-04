import logging
from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.account.master.repository import AccountRepository
from app.account.master.schemas import (
    AccountRead,
    AccountCreate,
    AccountUpdate,
)

logger = logging.getLogger(__name__)


class AccountError(Exception):
    """Custom exception for account account-related errors."""

    pass


class AccountService:
    """Portfolio account business logic service."""

    def __init__(self, db: AsyncSession):
        self.repo = AccountRepository(db)

    async def get_user_accounts(
        self, user_id: UUID, limit: int = 100, include_inactive: bool = False
    ) -> List[AccountRead]:
        """Get all account master for a user with pagination."""
        try:
            logger.debug(f"Fetching account master for user: {user_id}")

            accounts = await self.repo.get_multi_by_user(
                user_id=user_id, limit=limit, include_inactive=include_inactive
            )

            logger.debug(f"Found {len(accounts)} account master for user: {user_id}")
            return [
                AccountRead.model_validate(account, from_attributes=True) for account in accounts
            ]

        except Exception as e:
            logger.error(f"Failed to get user account master: {type(e).__name__}: {str(e)}")
            raise AccountError("Failed to retrieve account master")

    async def get_account_by_id(self, user_id: UUID, account_id: UUID) -> AccountRead:
        """Get a specific account account by ID for a user."""
        try:
            logger.debug(f"Fetching account account {account_id} for user: {user_id}")

            account = await self.repo.get_by_user_and_id(user_id=user_id, account_id=account_id)

            if not account:
                logger.warning(f"Portfolio account {account_id} not found for user: {user_id}")
                raise AccountError("Portfolio account not found")

            logger.debug(f"Portfolio account {account_id} found for user: {user_id}")
            return AccountRead.model_validate(account, from_attributes=True)

        except AccountError:
            raise
        except Exception as e:
            logger.error(f"Failed to get account account: {type(e).__name__}: {str(e)}")
            raise AccountError("Failed to retrieve account account")

    async def create_account(self, user_id: UUID, account_data: AccountCreate) -> AccountRead:
        """Create a new account account for a user."""
        try:
            logger.debug(f"Creating account account for user: {user_id}")

            # Set the user_id in the account data
            account_data.user_id = user_id

            account = await self.repo.create(account_data)

            logger.info(f"Portfolio account {account.id} created for user: {user_id}")
            return AccountRead.model_validate(account, from_attributes=True)

        except Exception as e:
            logger.error(f"Failed to create account account: {type(e).__name__}: {str(e)}")
            raise AccountError("Failed to create account account")

    async def update_account(
        self, user_id: UUID, account_id: UUID, account_update: AccountUpdate
    ) -> AccountRead:
        """Update a account account for a user."""
        try:
            logger.debug(f"Updating account account {account_id} for user: {user_id}")

            # First verify the account exists and belongs to the user
            existing_account = await self.repo.get_by_user_and_id(
                user_id=user_id, account_id=account_id
            )

            if not existing_account:
                logger.warning(f"Portfolio account {account_id} not found for user: {user_id}")
                raise AccountError("Portfolio account not found")

            updated_account = await self.repo.update(db_obj=existing_account, obj_in=account_update)

            logger.info(f"Portfolio account {account_id} updated for user: {user_id}")
            return AccountRead.model_validate(updated_account, from_attributes=True)

        except AccountError:
            raise
        except Exception as e:
            logger.error(f"Failed to update account account: {type(e).__name__}: {str(e)}")
            raise AccountError("Failed to update account account")

    async def deactivate_account(self, user_id: UUID, account_id: UUID) -> bool:
        """Deactivate a account account (soft delete)."""
        try:
            logger.debug(f"Deactivating account account {account_id} for user: {user_id}")

            # First verify the account exists and belongs to the user
            existing_account = await self.repo.get_by_user_and_id(
                user_id=user_id, account_id=account_id
            )

            if not existing_account:
                logger.warning(f"Portfolio account {account_id} not found for user: {user_id}")
                raise AccountError("Portfolio account not found")

            # Update the account to mark as inactive
            deactivate_data = AccountUpdate(is_active=False)
            await self.repo.update(db_obj=existing_account, obj_in=deactivate_data)

            logger.info(f"Portfolio account {account_id} deactivated for user: {user_id}")
            return True

        except AccountError:
            raise
        except Exception as e:
            logger.error(f"Failed to deactivate account account: {type(e).__name__}: {str(e)}")
            raise AccountError("Failed to deactivate account account")

    async def get_accounts_by_type(
        self, user_id: UUID, account_type: str, include_inactive: bool = False
    ) -> List[AccountRead]:
        """Get account master filtered by type."""
        try:
            logger.debug(f"Fetching account master by type {account_type} for user: {user_id}")

            accounts = await self.repo.get_by_type(
                user_id=user_id, account_type=account_type, include_inactive=include_inactive
            )

            logger.debug(
                f"Found {len(accounts)} account master of type {account_type} for user: {user_id}"
            )
            return [
                AccountRead.model_validate(account, from_attributes=True) for account in accounts
            ]

        except Exception as e:
            logger.error(f"Failed to get account master by type: {type(e).__name__}: {str(e)}")
            raise AccountError("Failed to retrieve account master by type")

    async def get_account_count(self, user_id: UUID, include_inactive: bool = False) -> int:
        """Get count of account master for a user."""
        try:
            logger.debug(f"Counting account master for user: {user_id}")

            count = await self.repo.count_by_user(user_id, include_inactive)

            logger.debug(f"Found {count} account master for user: {user_id}")
            return count

        except Exception as e:
            logger.error(f"Failed to count account master: {type(e).__name__}: {str(e)}")
            raise AccountError("Failed to count account master")

    async def search_accounts(
        self, user_id: UUID, search_term: str, limit: int = 10
    ) -> List[AccountRead]:
        """Search account master by name."""
        try:
            logger.debug(f"Searching account master for user: {user_id}, term: {search_term}")

            accounts = await self.repo.search_accounts(
                user_id=user_id, search_term=search_term, limit=limit
            )

            logger.debug(
                f"Found {len(accounts)} account master matching '{search_term}' for user: {user_id}"
            )
            return [
                AccountRead.model_validate(account, from_attributes=True) for account in accounts
            ]

        except Exception as e:
            logger.error(f"Failed to search account master: {type(e).__name__}: {str(e)}")
            raise AccountError("Failed to search account master")

    async def get_account_statistics(self, user_id: UUID) -> dict:
        """Get comprehensive statistics for a user's account master."""
        try:
            logger.debug(f"Fetching account account statistics for user: {user_id}")

            stats = await self.repo.get_user_account_statistics(user_id)

            logger.debug(f"Portfolio account statistics retrieved for user: {user_id}")
            return stats

        except Exception as e:
            logger.error(f"Failed to get account account statistics: {type(e).__name__}: {str(e)}")
            raise AccountError("Failed to retrieve account account statistics")

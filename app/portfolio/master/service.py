import logging
from typing import List
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.portfolio.master.repository import PortfolioRepository
from app.portfolio.master.schemas import (
    PortfolioMasterRead,
    PortfolioMasterCreate,
    PortfolioMasterUpdate,
)

logger = logging.getLogger(__name__)


class PortfolioError(Exception):
    """Custom exception for portfolio account-related errors."""

    pass


class PortfolioService:
    """Portfolio account business logic service."""

    def __init__(self, db: AsyncSession):
        self.repo = PortfolioRepository(db)

    async def get_user_accounts(
        self, user_id: UUID, limit: int = 100, include_inactive: bool = False
    ) -> List[PortfolioMasterRead]:
        """Get all portfolio master for a user with pagination."""
        try:
            logger.debug(f"Fetching portfolio master for user: {user_id}")

            accounts = await self.repo.get_multi_by_user(
                user_id=user_id, limit=limit, include_inactive=include_inactive
            )

            logger.debug(f"Found {len(accounts)} portfolio master for user: {user_id}")
            return [
                PortfolioMasterRead.model_validate(account, from_attributes=True)
                for account in accounts
            ]

        except Exception as e:
            logger.error(f"Failed to get user portfolio master: {type(e).__name__}: {str(e)}")
            raise PortfolioError("Failed to retrieve portfolio master")

    async def get_account_by_id(self, user_id: UUID, account_id: UUID) -> PortfolioMasterRead:
        """Get a specific portfolio account by ID for a user."""
        try:
            logger.debug(f"Fetching portfolio account {account_id} for user: {user_id}")

            account = await self.repo.get_by_user_and_id(user_id=user_id, account_id=account_id)

            if not account:
                logger.warning(f"Portfolio account {account_id} not found for user: {user_id}")
                raise PortfolioError("Portfolio account not found")

            logger.debug(f"Portfolio account {account_id} found for user: {user_id}")
            return PortfolioMasterRead.model_validate(account, from_attributes=True)

        except PortfolioError:
            raise
        except Exception as e:
            logger.error(f"Failed to get portfolio account: {type(e).__name__}: {str(e)}")
            raise PortfolioError("Failed to retrieve portfolio account")

    async def create_account(
        self, user_id: UUID, account_data: PortfolioMasterCreate
    ) -> PortfolioMasterRead:
        """Create a new portfolio account for a user."""
        try:
            logger.debug(f"Creating portfolio account for user: {user_id}")

            # Set the user_id in the account data
            account_data.user_id = user_id

            account = await self.repo.create(account_data)

            logger.info(f"Portfolio account {account.id} created for user: {user_id}")
            return PortfolioMasterRead.model_validate(account, from_attributes=True)

        except Exception as e:
            logger.error(f"Failed to create portfolio account: {type(e).__name__}: {str(e)}")
            raise PortfolioError("Failed to create portfolio account")

    async def update_account(
        self, user_id: UUID, account_id: UUID, account_update: PortfolioMasterUpdate
    ) -> PortfolioMasterRead:
        """Update a portfolio account for a user."""
        try:
            logger.debug(f"Updating portfolio account {account_id} for user: {user_id}")

            # First verify the account exists and belongs to the user
            existing_account = await self.repo.get_by_user_and_id(
                user_id=user_id, account_id=account_id
            )

            if not existing_account:
                logger.warning(f"Portfolio account {account_id} not found for user: {user_id}")
                raise PortfolioError("Portfolio account not found")

            updated_account = await self.repo.update(db_obj=existing_account, obj_in=account_update)

            logger.info(f"Portfolio account {account_id} updated for user: {user_id}")
            return PortfolioMasterRead.model_validate(updated_account, from_attributes=True)

        except PortfolioError:
            raise
        except Exception as e:
            logger.error(f"Failed to update portfolio account: {type(e).__name__}: {str(e)}")
            raise PortfolioError("Failed to update portfolio account")

    async def deactivate_account(self, user_id: UUID, account_id: UUID) -> bool:
        """Deactivate a portfolio account (soft delete)."""
        try:
            logger.debug(f"Deactivating portfolio account {account_id} for user: {user_id}")

            # First verify the account exists and belongs to the user
            existing_account = await self.repo.get_by_user_and_id(
                user_id=user_id, account_id=account_id
            )

            if not existing_account:
                logger.warning(f"Portfolio account {account_id} not found for user: {user_id}")
                raise PortfolioError("Portfolio account not found")

            # Update the account to mark as inactive
            deactivate_data = PortfolioMasterUpdate(is_active=False)
            await self.repo.update(db_obj=existing_account, obj_in=deactivate_data)

            logger.info(f"Portfolio account {account_id} deactivated for user: {user_id}")
            return True

        except PortfolioError:
            raise
        except Exception as e:
            logger.error(f"Failed to deactivate portfolio account: {type(e).__name__}: {str(e)}")
            raise PortfolioError("Failed to deactivate portfolio account")

    async def get_accounts_by_type(
        self, user_id: UUID, account_type: str, include_inactive: bool = False
    ) -> List[PortfolioMasterRead]:
        """Get portfolio master filtered by type."""
        try:
            logger.debug(f"Fetching portfolio master by type {account_type} for user: {user_id}")

            accounts = await self.repo.get_by_type(
                user_id=user_id, account_type=account_type, include_inactive=include_inactive
            )

            logger.debug(
                f"Found {len(accounts)} portfolio master of type {account_type} for user: {user_id}"
            )
            return [
                PortfolioMasterRead.model_validate(account, from_attributes=True)
                for account in accounts
            ]

        except Exception as e:
            logger.error(f"Failed to get portfolio master by type: {type(e).__name__}: {str(e)}")
            raise PortfolioError("Failed to retrieve portfolio master by type")

    async def get_account_count(self, user_id: UUID, include_inactive: bool = False) -> int:
        """Get count of portfolio master for a user."""
        try:
            logger.debug(f"Counting portfolio master for user: {user_id}")

            count = await self.repo.count_by_user(user_id, include_inactive)

            logger.debug(f"Found {count} portfolio master for user: {user_id}")
            return count

        except Exception as e:
            logger.error(f"Failed to count portfolio master: {type(e).__name__}: {str(e)}")
            raise PortfolioError("Failed to count portfolio master")

    async def search_accounts(
        self, user_id: UUID, search_term: str, limit: int = 10
    ) -> List[PortfolioMasterRead]:
        """Search portfolio master by name."""
        try:
            logger.debug(f"Searching portfolio master for user: {user_id}, term: {search_term}")

            accounts = await self.repo.search_accounts(
                user_id=user_id, search_term=search_term, limit=limit
            )

            logger.debug(
                f"Found {len(accounts)} portfolio master matching '{search_term}' for user: {user_id}"
            )
            return [
                PortfolioMasterRead.model_validate(account, from_attributes=True)
                for account in accounts
            ]

        except Exception as e:
            logger.error(f"Failed to search portfolio master: {type(e).__name__}: {str(e)}")
            raise PortfolioError("Failed to search portfolio master")

    async def get_account_statistics(self, user_id: UUID) -> dict:
        """Get comprehensive statistics for a user's portfolio master."""
        try:
            logger.debug(f"Fetching portfolio account statistics for user: {user_id}")

            stats = await self.repo.get_user_account_statistics(user_id)

            logger.debug(f"Portfolio account statistics retrieved for user: {user_id}")
            return stats

        except Exception as e:
            logger.error(
                f"Failed to get portfolio account statistics: {type(e).__name__}: {str(e)}"
            )
            raise PortfolioError("Failed to retrieve portfolio account statistics")

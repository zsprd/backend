import logging
from typing import List
from uuid import UUID

from app.portfolio.accounts import schema
from app.portfolio.accounts.crud import CRUDPortfolioAccount

logger = logging.getLogger(__name__)


class PortfolioAccountError(Exception):
    """Custom exception for portfolio account-related errors."""

    pass


class PortfolioAccountService:
    """Portfolio account business logic service."""

    def __init__(self, portfolio_account_repo: CRUDPortfolioAccount):
        self.portfolio_account_repo = portfolio_account_repo

    async def get_user_accounts(
        self, user_id: UUID, limit: int = 100, include_inactive: bool = False
    ) -> List[schema.PortfolioAccountRead]:
        """Get all portfolio accounts for a user with pagination."""
        try:
            logger.debug(f"Fetching portfolio accounts for user: {user_id}")

            accounts = await self.portfolio_account_repo.get_multi_by_user(
                user_id=user_id, limit=limit, include_inactive=include_inactive
            )

            logger.debug(f"Found {len(accounts)} portfolio accounts for user: {user_id}")
            return [
                schema.PortfolioAccountRead.model_validate(account, from_attributes=True)
                for account in accounts
            ]

        except Exception as e:
            logger.error(f"Failed to get user portfolio accounts: {type(e).__name__}: {str(e)}")
            raise PortfolioAccountError("Failed to retrieve portfolio accounts")

    async def get_account_by_id(
        self, user_id: UUID, account_id: UUID
    ) -> schema.PortfolioAccountRead:
        """Get a specific portfolio account by ID for a user."""
        try:
            logger.debug(f"Fetching portfolio account {account_id} for user: {user_id}")

            account = await self.portfolio_account_repo.get_by_user_and_id(
                user_id=user_id, account_id=account_id
            )

            if not account:
                logger.warning(f"Portfolio account {account_id} not found for user: {user_id}")
                raise PortfolioAccountError("Portfolio account not found")

            logger.debug(f"Portfolio account {account_id} found for user: {user_id}")
            return schema.PortfolioAccountRead.model_validate(account, from_attributes=True)

        except PortfolioAccountError:
            raise
        except Exception as e:
            logger.error(f"Failed to get portfolio account: {type(e).__name__}: {str(e)}")
            raise PortfolioAccountError("Failed to retrieve portfolio account")

    async def create_account(
        self, user_id: UUID, account_data: schema.PortfolioAccountCreate
    ) -> schema.PortfolioAccountRead:
        """Create a new portfolio account for a user."""
        try:
            logger.debug(f"Creating portfolio account for user: {user_id}")

            # Set the user_id in the account data
            account_data.user_id = user_id

            account = await self.portfolio_account_repo.create(account_data)

            logger.info(f"Portfolio account {account.id} created for user: {user_id}")
            return schema.PortfolioAccountRead.model_validate(account, from_attributes=True)

        except Exception as e:
            logger.error(f"Failed to create portfolio account: {type(e).__name__}: {str(e)}")
            raise PortfolioAccountError("Failed to create portfolio account")

    async def update_account(
        self, user_id: UUID, account_id: UUID, account_update: schema.PortfolioAccountUpdate
    ) -> schema.PortfolioAccountRead:
        """Update a portfolio account for a user."""
        try:
            logger.debug(f"Updating portfolio account {account_id} for user: {user_id}")

            # First verify the account exists and belongs to the user
            existing_account = await self.portfolio_account_repo.get_by_user_and_id(
                user_id=user_id, account_id=account_id
            )

            if not existing_account:
                logger.warning(f"Portfolio account {account_id} not found for user: {user_id}")
                raise PortfolioAccountError("Portfolio account not found")

            updated_account = await self.portfolio_account_repo.update(
                db_obj=existing_account, obj_in=account_update
            )

            logger.info(f"Portfolio account {account_id} updated for user: {user_id}")
            return schema.PortfolioAccountRead.model_validate(updated_account, from_attributes=True)

        except PortfolioAccountError:
            raise
        except Exception as e:
            logger.error(f"Failed to update portfolio account: {type(e).__name__}: {str(e)}")
            raise PortfolioAccountError("Failed to update portfolio account")

    async def deactivate_account(self, user_id: UUID, account_id: UUID) -> bool:
        """Deactivate a portfolio account (soft delete)."""
        try:
            logger.debug(f"Deactivating portfolio account {account_id} for user: {user_id}")

            # First verify the account exists and belongs to the user
            existing_account = await self.portfolio_account_repo.get_by_user_and_id(
                user_id=user_id, account_id=account_id
            )

            if not existing_account:
                logger.warning(f"Portfolio account {account_id} not found for user: {user_id}")
                raise PortfolioAccountError("Portfolio account not found")

            # Update the account to mark as inactive
            deactivate_data = schema.PortfolioAccountUpdate(is_active=False)
            await self.portfolio_account_repo.update(
                db_obj=existing_account, obj_in=deactivate_data
            )

            logger.info(f"Portfolio account {account_id} deactivated for user: {user_id}")
            return True

        except PortfolioAccountError:
            raise
        except Exception as e:
            logger.error(f"Failed to deactivate portfolio account: {type(e).__name__}: {str(e)}")
            raise PortfolioAccountError("Failed to deactivate portfolio account")

    async def get_accounts_by_type(
        self, user_id: UUID, account_type: str, include_inactive: bool = False
    ) -> List[schema.PortfolioAccountRead]:
        """Get portfolio accounts filtered by type."""
        try:
            logger.debug(f"Fetching portfolio accounts by type {account_type} for user: {user_id}")

            accounts = await self.portfolio_account_repo.get_by_type(
                user_id=user_id, account_type=account_type, include_inactive=include_inactive
            )

            logger.debug(
                f"Found {len(accounts)} portfolio accounts of type {account_type} for user: {user_id}"
            )
            return [
                schema.PortfolioAccountRead.model_validate(account, from_attributes=True)
                for account in accounts
            ]

        except Exception as e:
            logger.error(f"Failed to get portfolio accounts by type: {type(e).__name__}: {str(e)}")
            raise PortfolioAccountError("Failed to retrieve portfolio accounts by type")

    async def get_account_count(self, user_id: UUID, include_inactive: bool = False) -> int:
        """Get count of portfolio accounts for a user."""
        try:
            logger.debug(f"Counting portfolio accounts for user: {user_id}")

            count = await self.portfolio_account_repo.count_by_user(user_id, include_inactive)

            logger.debug(f"Found {count} portfolio accounts for user: {user_id}")
            return count

        except Exception as e:
            logger.error(f"Failed to count portfolio accounts: {type(e).__name__}: {str(e)}")
            raise PortfolioAccountError("Failed to count portfolio accounts")

    async def search_accounts(
        self, user_id: UUID, search_term: str, limit: int = 10
    ) -> List[schema.PortfolioAccountRead]:
        """Search portfolio accounts by name."""
        try:
            logger.debug(f"Searching portfolio accounts for user: {user_id}, term: {search_term}")

            accounts = await self.portfolio_account_repo.search_accounts(
                user_id=user_id, search_term=search_term, limit=limit
            )

            logger.debug(
                f"Found {len(accounts)} portfolio accounts matching '{search_term}' for user: {user_id}"
            )
            return [
                schema.PortfolioAccountRead.model_validate(account, from_attributes=True)
                for account in accounts
            ]

        except Exception as e:
            logger.error(f"Failed to search portfolio accounts: {type(e).__name__}: {str(e)}")
            raise PortfolioAccountError("Failed to search portfolio accounts")

    async def get_account_statistics(self, user_id: UUID) -> dict:
        """Get comprehensive statistics for a user's portfolio accounts."""
        try:
            logger.debug(f"Fetching portfolio account statistics for user: {user_id}")

            stats = await self.portfolio_account_repo.get_user_account_statistics(user_id)

            logger.debug(f"Portfolio account statistics retrieved for user: {user_id}")
            return stats

        except Exception as e:
            logger.error(
                f"Failed to get portfolio account statistics: {type(e).__name__}: {str(e)}"
            )
            raise PortfolioAccountError("Failed to retrieve portfolio account statistics")

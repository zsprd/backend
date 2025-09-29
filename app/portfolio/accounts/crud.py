import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.crud import CRUDBase
from app.portfolio.accounts import schema
from app.portfolio.accounts.model import PortfolioAccount

logger = logging.getLogger(__name__)


class CRUDPortfolioAccount(
    CRUDBase[PortfolioAccount, schema.PortfolioAccountCreate, schema.PortfolioAccountUpdate]
):

    def __init__(self, db: AsyncSession):
        super().__init__(PortfolioAccount)
        self.db = db

    async def get_multi_by_user(
        self, user_id: UUID, limit: int = 100, include_inactive: bool = False
    ) -> List[PortfolioAccount]:
        """Get multiple portfolio accounts for a user with pagination."""
        try:
            query = select(PortfolioAccount).where(PortfolioAccount.user_id == user_id)

            if not include_inactive:
                query = query.where(PortfolioAccount.is_active == True)

            query = query.limit(limit).order_by(PortfolioAccount.created_at.desc())

            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Failed to get portfolio accounts for user {user_id}: {str(e)}")
            raise

    async def get_by_user_and_id(
        self, user_id: UUID, account_id: UUID
    ) -> Optional[PortfolioAccount]:
        """Get a specific portfolio account by user ID and account ID."""
        try:
            query = select(PortfolioAccount).where(
                and_(PortfolioAccount.user_id == user_id, PortfolioAccount.id == account_id)
            )

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(
                f"Failed to get portfolio account {account_id} for user {user_id}: {str(e)}"
            )
            raise

    async def get_active_by_user(self, user_id: UUID) -> List[PortfolioAccount]:
        """Get all active portfolio accounts for a user."""
        try:
            query = (
                select(PortfolioAccount)
                .where(
                    and_(PortfolioAccount.user_id == user_id, PortfolioAccount.is_active == True)
                )
                .order_by(PortfolioAccount.created_at.desc())
            )

            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Failed to get active portfolio accounts for user {user_id}: {str(e)}")
            raise

    async def get_by_type(
        self, user_id: UUID, account_type: str, include_inactive: bool = False
    ) -> List[PortfolioAccount]:
        """Get portfolio accounts by type for a user."""
        try:
            query = select(PortfolioAccount).where(
                and_(
                    PortfolioAccount.user_id == user_id,
                    PortfolioAccount.account_type == account_type,
                )
            )

            if not include_inactive:
                query = query.where(PortfolioAccount.is_active == True)

            query = query.order_by(PortfolioAccount.created_at.desc())

            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(
                f"Failed to get portfolio accounts by type {account_type} for user {user_id}: {str(e)}"
            )
            raise

    async def create(self, obj_in: schema.PortfolioAccountCreate) -> PortfolioAccount:
        """Create a new portfolio account."""
        try:
            db_obj = PortfolioAccount(**obj_in.model_dump())
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
            return db_obj

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create portfolio account: {str(e)}")
            raise

    async def update(
        self, db_obj: PortfolioAccount, obj_in: schema.PortfolioAccountUpdate
    ) -> PortfolioAccount:
        """Update a portfolio account."""
        try:
            obj_data = obj_in.model_dump(exclude_unset=True)

            for field, value in obj_data.items():
                setattr(db_obj, field, value)

            await self.db.commit()
            await self.db.refresh(db_obj)
            return db_obj

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to update portfolio account {db_obj.id}: {str(e)}")
            raise

    async def count_by_user(self, user_id: UUID, include_inactive: bool = False) -> int:
        """Count portfolio accounts for a user."""
        try:
            query = select(func.count(PortfolioAccount.id)).where(
                PortfolioAccount.user_id == user_id
            )

            if not include_inactive:
                query = query.where(PortfolioAccount.is_active == True)

            result = await self.db.execute(query)
            return result.scalar()

        except Exception as e:
            logger.error(f"Failed to count portfolio accounts for user {user_id}: {str(e)}")
            raise

    async def search_accounts(
        self, user_id: UUID, search_term: str, limit: int = 10
    ) -> List[PortfolioAccount]:
        """Search portfolio accounts by name for a user."""
        try:
            query = (
                select(PortfolioAccount)
                .where(
                    and_(
                        PortfolioAccount.user_id == user_id,
                        PortfolioAccount.name.ilike(f"%{search_term}%"),
                        PortfolioAccount.is_active == True,
                    )
                )
                .limit(limit)
                .order_by(PortfolioAccount.name)
            )

            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(f"Failed to search portfolio accounts for user {user_id}: {str(e)}")
            raise

    async def get_user_account_statistics(self, user_id: UUID) -> dict:
        """Get comprehensive statistics for a user's portfolio accounts."""
        try:
            # Get basic counts
            total_query = select(func.count(PortfolioAccount.id)).where(
                PortfolioAccount.user_id == user_id
            )
            active_query = select(func.count(PortfolioAccount.id)).where(
                and_(PortfolioAccount.user_id == user_id, PortfolioAccount.is_active == True)
            )

            total_result = await self.db.execute(total_query)
            active_result = await self.db.execute(active_query)

            total_accounts = total_result.scalar()
            active_accounts = active_result.scalar()

            # Get account type breakdown
            type_query = (
                select(
                    PortfolioAccount.account_type, func.count(PortfolioAccount.id).label("count")
                )
                .where(
                    and_(PortfolioAccount.user_id == user_id, PortfolioAccount.is_active == True)
                )
                .group_by(PortfolioAccount.account_type)
            )

            type_result = await self.db.execute(type_query)
            account_types = {row.account_type: row.count for row in type_result}

            return {
                "total_accounts": total_accounts,
                "active_accounts": active_accounts,
                "inactive_accounts": total_accounts - active_accounts,
                "account_types": account_types,
                "last_updated": None,  # You can add logic to track last sync/update
            }

        except Exception as e:
            logger.error(f"Failed to get portfolio account statistics for user {user_id}: {str(e)}")
            raise

    async def get_accounts_with_holdings(self, user_id: UUID) -> List[PortfolioAccount]:
        """Get portfolio accounts with their holdings preloaded."""
        try:
            query = (
                select(PortfolioAccount)
                .options(selectinload(PortfolioAccount.portfolio_holdings))
                .where(
                    and_(PortfolioAccount.user_id == user_id, PortfolioAccount.is_active == True)
                )
                .order_by(PortfolioAccount.created_at.desc())
            )

            result = await self.db.execute(query)
            return result.scalars().all()

        except Exception as e:
            logger.error(
                f"Failed to get portfolio accounts with holdings for user {user_id}: {str(e)}"
            )
            raise

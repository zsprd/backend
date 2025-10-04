import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.portfolio.master.model import PortfolioMaster

logger = logging.getLogger(__name__)


class PortfolioRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_multi_by_user(
        self, user_id: UUID, limit: int = 100, include_inactive: bool = False
    ) -> List[PortfolioMaster]:
        """Get multiple portfolio master for a user with pagination."""
        try:
            query = select(PortfolioMaster).where(PortfolioMaster.user_id == user_id)

            if not include_inactive:
                query = query.where(PortfolioMaster.is_active == True)

            query = query.limit(limit).order_by(PortfolioMaster.created_at.desc())

            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Failed to get portfolio master for user {user_id}: {str(e)}")
            raise

    async def get_by_user_and_id(
        self, user_id: UUID, account_id: UUID
    ) -> Optional[PortfolioMaster]:
        """Get a specific portfolio account by user ID and account ID."""
        try:
            query = select(PortfolioMaster).where(
                and_(PortfolioMaster.user_id == user_id, PortfolioMaster.id == account_id)
            )

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(
                f"Failed to get portfolio account {account_id} for user {user_id}: {str(e)}"
            )
            raise

    async def get_active_by_user(self, user_id: UUID) -> List[PortfolioMaster]:
        """Get all active portfolio master for a user."""
        try:
            query = (
                select(PortfolioMaster)
                .where(and_(PortfolioMaster.user_id == user_id, PortfolioMaster.is_active == True))
                .order_by(PortfolioMaster.created_at.desc())
            )

            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Failed to get active portfolio master for user {user_id}: {str(e)}")
            raise

    async def get_by_type(
        self, user_id: UUID, account_type: str, include_inactive: bool = False
    ) -> List[PortfolioMaster]:
        """Get portfolio master by type for a user."""
        try:
            query = select(PortfolioMaster).where(
                and_(
                    PortfolioMaster.user_id == user_id,
                    PortfolioMaster.account_type == account_type,
                )
            )

            if not include_inactive:
                query = query.where(PortfolioMaster.is_active == True)

            query = query.order_by(PortfolioMaster.created_at.desc())

            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(
                f"Failed to get portfolio master by type {account_type} for user {user_id}: {str(e)}"
            )
            raise

    async def create(self, obj_in) -> PortfolioMaster:
        """Create a new portfolio account."""
        try:
            # Accept a dict or model, but do not depend on Pydantic
            if hasattr(obj_in, "model_dump"):
                data = obj_in.model_dump(mode="json")
            elif isinstance(obj_in, dict):
                data = obj_in
            else:
                raise TypeError("obj_in must be a dict or have model_dump method")
            db_obj = PortfolioMaster(**data)
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
            return db_obj

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create portfolio account: {str(e)}")
            raise

    async def update(self, db_obj: PortfolioMaster, obj_in) -> PortfolioMaster:
        """Update a portfolio account."""
        try:
            # Accept a dict or model, but do not depend on Pydantic
            if hasattr(obj_in, "model_dump"):
                obj_data = obj_in.model_dump(exclude_unset=True, mode="json")
            elif isinstance(obj_in, dict):
                obj_data = obj_in
            else:
                raise TypeError("obj_in must be a dict or have model_dump method")

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
        """Count portfolio master for a user."""
        try:
            query = select(func.count(PortfolioMaster.id)).where(PortfolioMaster.user_id == user_id)

            if not include_inactive:
                query = query.where(PortfolioMaster.is_active == True)

            result = await self.db.execute(query)
            return result.scalar()

        except Exception as e:
            logger.error(f"Failed to count portfolio master for user {user_id}: {str(e)}")
            raise

    async def search_accounts(
        self, user_id: UUID, search_term: str, limit: int = 10
    ) -> List[PortfolioMaster]:
        """Search portfolio master by name for a user."""
        try:
            query = (
                select(PortfolioMaster)
                .where(
                    and_(
                        PortfolioMaster.user_id == user_id,
                        PortfolioMaster.name.ilike(f"%{search_term}%"),
                        PortfolioMaster.is_active == True,
                    )
                )
                .limit(limit)
                .order_by(PortfolioMaster.name)
            )

            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Failed to search portfolio master for user {user_id}: {str(e)}")
            raise

    async def get_user_account_statistics(self, user_id: UUID) -> dict:
        """Get comprehensive statistics for a user's portfolio master."""
        try:
            # Get basic counts
            total_query = select(func.count(PortfolioMaster.id)).where(
                PortfolioMaster.user_id == user_id
            )
            active_query = select(func.count(PortfolioMaster.id)).where(
                and_(PortfolioMaster.user_id == user_id, PortfolioMaster.is_active == True)
            )

            total_result = await self.db.execute(total_query)
            active_result = await self.db.execute(active_query)

            total_accounts = total_result.scalar()
            active_accounts = active_result.scalar()

            # Get account type breakdown
            type_query = (
                select(PortfolioMaster.account_type, func.count(PortfolioMaster.id).label("count"))
                .where(and_(PortfolioMaster.user_id == user_id, PortfolioMaster.is_active == True))
                .group_by(PortfolioMaster.account_type)
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

    async def get_accounts_with_holdings(self, user_id: UUID) -> List[PortfolioMaster]:
        """Get portfolio master with their holdings preloaded."""
        try:
            query = (
                select(PortfolioMaster)
                .options(selectinload(PortfolioMaster.portfolio_holdings))
                .where(and_(PortfolioMaster.user_id == user_id, PortfolioMaster.is_active == True))
                .order_by(PortfolioMaster.created_at.desc())
            )

            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(
                f"Failed to get portfolio master with holdings for user {user_id}: {str(e)}"
            )
            raise

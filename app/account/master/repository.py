import logging
from typing import List, Optional
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.account.master.model import Account

logger = logging.getLogger(__name__)


class AccountRepository:

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_multi_by_user(
        self, user_id: UUID, limit: int = 100, include_inactive: bool = False
    ) -> List[Account]:
        """Get multiple account master for a user with pagination."""
        try:
            query = select(Account).where(Account.user_id == user_id)

            if not include_inactive:
                query = query.where(Account.is_active == True)

            query = query.limit(limit).order_by(Account.created_at.desc())

            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Failed to get account master for user {user_id}: {str(e)}")
            raise

    async def get_by_user_and_id(self, user_id: UUID, account_id: UUID) -> Optional[Account]:
        """Get a specific account account by user ID and account ID."""
        try:
            query = select(Account).where(
                and_(Account.user_id == user_id, Account.id == account_id)
            )

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Failed to get account account {account_id} for user {user_id}: {str(e)}")
            raise

    async def get_active_by_user(self, user_id: UUID) -> List[Account]:
        """Get all active account master for a user."""
        try:
            query = (
                select(Account)
                .where(and_(Account.user_id == user_id, Account.is_active == True))
                .order_by(Account.created_at.desc())
            )

            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Failed to get active account master for user {user_id}: {str(e)}")
            raise

    async def get_by_type(
        self, user_id: UUID, account_type: str, include_inactive: bool = False
    ) -> List[Account]:
        """Get account master by type for a user."""
        try:
            query = select(Account).where(
                and_(
                    Account.user_id == user_id,
                    Account.account_type == account_type,
                )
            )

            if not include_inactive:
                query = query.where(Account.is_active == True)

            query = query.order_by(Account.created_at.desc())

            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(
                f"Failed to get account master by type {account_type} for user {user_id}: {str(e)}"
            )
            raise

    async def create(self, obj_in) -> Account:
        """Create a new account account."""
        try:
            # Accept a dict or model, but do not depend on Pydantic
            if hasattr(obj_in, "model_dump"):
                data = obj_in.model_dump(mode="json")
            elif isinstance(obj_in, dict):
                data = obj_in
            else:
                raise TypeError("obj_in must be a dict or have model_dump method")
            db_obj = Account(**data)
            self.db.add(db_obj)
            await self.db.commit()
            await self.db.refresh(db_obj)
            return db_obj

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Failed to create account account: {str(e)}")
            raise

    async def update(self, db_obj: Account, obj_in) -> Account:
        """Update a account account."""
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
            logger.error(f"Failed to update account account {db_obj.id}: {str(e)}")
            raise

    async def count_by_user(self, user_id: UUID, include_inactive: bool = False) -> int:
        """Count account master for a user."""
        try:
            query = select(func.count(Account.id)).where(Account.user_id == user_id)

            if not include_inactive:
                query = query.where(Account.is_active == True)

            result = await self.db.execute(query)
            return result.scalar()

        except Exception as e:
            logger.error(f"Failed to count account master for user {user_id}: {str(e)}")
            raise

    async def search_accounts(
        self, user_id: UUID, search_term: str, limit: int = 10
    ) -> List[Account]:
        """Search account master by name for a user."""
        try:
            query = (
                select(Account)
                .where(
                    and_(
                        Account.user_id == user_id,
                        Account.name.ilike(f"%{search_term}%"),
                        Account.is_active == True,
                    )
                )
                .limit(limit)
                .order_by(Account.name)
            )

            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Failed to search account master for user {user_id}: {str(e)}")
            raise

    async def get_user_account_statistics(self, user_id: UUID) -> dict:
        """Get comprehensive statistics for a user's account master."""
        try:
            # Get basic counts
            total_query = select(func.count(Account.id)).where(Account.user_id == user_id)
            active_query = select(func.count(Account.id)).where(
                and_(Account.user_id == user_id, Account.is_active == True)
            )

            total_result = await self.db.execute(total_query)
            active_result = await self.db.execute(active_query)

            total_accounts = total_result.scalar()
            active_accounts = active_result.scalar()

            # Get account type breakdown
            type_query = (
                select(Account.account_type, func.count(Account.id).label("count"))
                .where(and_(Account.user_id == user_id, Account.is_active == True))
                .group_by(Account.account_type)
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
            logger.error(f"Failed to get account account statistics for user {user_id}: {str(e)}")
            raise

    async def get_accounts_with_holdings(self, user_id: UUID) -> List[Account]:
        """Get account master with their holdings preloaded."""
        try:
            query = (
                select(Account)
                .options(selectinload(Account.portfolio_holdings))
                .where(and_(Account.user_id == user_id, Account.is_active == True))
                .order_by(Account.created_at.desc())
            )

            result = await self.db.execute(query)
            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Failed to get account master with holdings for user {user_id}: {str(e)}")
            raise

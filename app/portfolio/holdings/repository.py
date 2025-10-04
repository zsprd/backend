from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.portfolio.holdings.model import PortfolioHolding


class HoldingRepository:
    """CRUD operations for PortfolioHolding model."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_holding(self, holding_id: UUID) -> Optional[PortfolioHolding]:
        """Retrieve a holding by its ID."""
        stmt = select(PortfolioHolding).where(PortfolioHolding.id == holding_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_holding(self, holding_data: Dict[str, Any]) -> PortfolioHolding:
        """Create a new holding."""
        holding = PortfolioHolding(**holding_data)
        self.db.add(holding)
        await self.db.commit()
        await self.db.refresh(holding)
        return holding

    async def update_holding(
        self, holding_id: UUID, update_data: Dict[str, Any]
    ) -> Optional[PortfolioHolding]:
        """Update an existing holding by ID."""
        stmt = select(PortfolioHolding).where(PortfolioHolding.id == holding_id)
        result = await self.db.execute(stmt)
        holding = result.scalar_one_or_none()
        if not holding:
            return None
        for key, value in update_data.items():
            setattr(holding, key, value)
        await self.db.commit()
        await self.db.refresh(holding)
        return holding

    async def delete_holding(self, holding_id: UUID) -> bool:
        """Delete a holding by ID. Returns True if deleted, False if not found."""
        stmt = select(PortfolioHolding).where(PortfolioHolding.id == holding_id)
        result = await self.db.execute(stmt)
        holding = result.scalar_one_or_none()
        if not holding:
            return False
        await self.db.delete(holding)
        await self.db.commit()
        return True

    async def get_by_account(
        self,
        account_id: UUID,
        as_of_date: Optional[date] = None,
    ) -> List[PortfolioHolding]:
        """Get holdings for a specific account, optionally as of a specific date."""
        stmt = (
            select(PortfolioHolding)
            .options(joinedload(PortfolioHolding.security_master))
            .where(PortfolioHolding.account_id == account_id)
        )

        if as_of_date:
            stmt = stmt.where(PortfolioHolding.as_of_date <= as_of_date)

        # Get most recent holdings per securities
        stmt = stmt.order_by(PortfolioHolding.security_id, desc(PortfolioHolding.as_of_date))
        result = await self.db.execute(stmt)
        holdings = list(result.scalars().all())

        # Filter to most recent per securities
        latest_holdings = {}
        for holding in holdings:
            if holding.security_id not in latest_holdings:
                latest_holdings[holding.security_id] = holding

        return list(latest_holdings.values())

    async def get_current_holdings_by_account(self, account_id: UUID) -> List[PortfolioHolding]:
        """Get current holdings for an account (latest as_of_date per securities)."""
        # Subquery to get latest date per securities for the account
        latest_date_subq = (
            select(
                PortfolioHolding.security_id,
                func.max(PortfolioHolding.as_of_date).label("max_date"),
            )
            .where(PortfolioHolding.account_id == account_id)
            .group_by(PortfolioHolding.security_id)
            .subquery()
        )

        # Main query to get holdings with latest dates
        stmt = (
            select(PortfolioHolding)
            .options(joinedload(PortfolioHolding.security_master))
            .join(
                latest_date_subq,
                and_(
                    PortfolioHolding.security_id == latest_date_subq.c.security_id,
                    PortfolioHolding.as_of_date == latest_date_subq.c.max_date,
                ),
            )
            .where(PortfolioHolding.account_id == account_id)
            .where(PortfolioHolding.quantity > 0)
        )

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_holdings_summary(
        self,
        account_id: Union[str, UUID],
        base_currency: str = "USD",
    ) -> Dict[str, Any]:
        """Get comprehensive holdings summary for an account."""
        holdings = await self.get_current_holdings_by_account(account_id)

        total_market_value = sum(h.market_value or Decimal("0") for h in holdings)
        total_cost_basis = sum(h.cost_basis or Decimal("0") for h in holdings)
        unrealized_gain_loss = total_market_value - total_cost_basis
        unrealized_gain_loss_percent = (
            (unrealized_gain_loss / total_cost_basis * 100)
            if total_cost_basis > 0
            else Decimal("0")
        )

        # Calculate allocation by asset type
        allocation_by_type = {}
        allocation_by_currency = {}

        for holding in holdings:
            # Allocation by asset type (from securities)
            asset_type = (
                holding.security_master.security_type if holding.security_master else "unknown"
            )
            current_value = allocation_by_type.get(asset_type, Decimal("0"))
            allocation_by_type[asset_type] = current_value + (holding.market_value or Decimal("0"))

            # Allocation by currency
            currency = holding.currency
            current_currency_value = allocation_by_currency.get(currency, Decimal("0"))
            allocation_by_currency[currency] = current_currency_value + (
                holding.market_value or Decimal("0")
            )

        # Convert to percentages
        allocation_by_type_percent = {}
        allocation_by_currency_percent = {}

        if total_market_value > 0:
            for asset_type, value in allocation_by_type.items():
                allocation_by_type_percent[asset_type] = round(
                    (value / total_market_value * 100), 2
                )

            for currency, value in allocation_by_currency.items():
                allocation_by_currency_percent[currency] = round(
                    (value / total_market_value * 100), 2
                )

        return {
            "account_id": str(account_id),
            "base_currency": base_currency,
            "total_market_value": total_market_value,
            "total_cost_basis": total_cost_basis,
            "unrealized_gain_loss": unrealized_gain_loss,
            "unrealized_gain_loss_percent": round(unrealized_gain_loss_percent, 2),
            "holdings_count": len(holdings),
            "allocation_by_type": allocation_by_type,
            "allocation_by_type_percent": allocation_by_type_percent,
            "allocation_by_currency": allocation_by_currency,
            "allocation_by_currency_percent": allocation_by_currency_percent,
            "largest_positions": sorted(
                holdings, key=lambda h: h.market_value or Decimal("0"), reverse=True
            )[:10],
            "summary_date": datetime.now(timezone.utc).date(),
        }

    async def get_holding_history(
        self,
        account_id: UUID,
        security_id: UUID,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
    ) -> List[PortfolioHolding]:
        """Get historical holdings for a specific securities in an account."""
        stmt = select(PortfolioHolding).where(
            and_(
                PortfolioHolding.account_id == account_id,
                PortfolioHolding.security_id == security_id,
            )
        )

        if start_date:
            stmt = stmt.where(PortfolioHolding.as_of_date >= start_date)
        if end_date:
            stmt = stmt.where(PortfolioHolding.as_of_date <= end_date)

        stmt = stmt.order_by(desc(PortfolioHolding.as_of_date)).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

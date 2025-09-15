from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Union
from uuid import UUID as UUIDType

from sqlalchemy import and_, desc, func, select, update
from sqlalchemy.orm import Session, joinedload

from app.core.crud import CRUDBase
from app.portfolios.holding.model import PortfolioHolding
from app.portfolios.holding.schema import HoldingCreate, HoldingUpdate


class CRUDHolding(CRUDBase[PortfolioHolding, HoldingCreate, HoldingUpdate]):
    """CRUD operations for PortfolioHolding model."""

    @staticmethod
    def _to_uuid(value: Union[str, UUIDType]) -> UUIDType:
        """Ensure a value is a UUID instance."""
        if isinstance(value, UUIDType):
            return value
        # Let ValueError propagate to surface invalid IDs clearly
        return UUIDType(str(value))

    def get_by_account(
        self,
        db: Session,
        *,
        account_id: Union[str, UUIDType],
        as_of_date: Optional[date] = None,
    ) -> List[PortfolioHolding]:
        """Get holdings for a specific account, optionally as of a specific date."""
        account_uuid = self._to_uuid(account_id)
        stmt = (
            select(PortfolioHolding)
            .options(joinedload(PortfolioHolding.security))
            .where(PortfolioHolding.account_id == account_uuid)
        )

        if as_of_date:
            stmt = stmt.where(PortfolioHolding.as_of_date <= as_of_date)

        # Get most recent holdings per securities
        stmt = stmt.order_by(PortfolioHolding.security_id, desc(PortfolioHolding.as_of_date))
        result = db.execute(stmt)
        holdings = list(result.scalars().all())

        # Filter to most recent per securities
        latest_holdings = {}
        for holding in holdings:
            if holding.security_id not in latest_holdings:
                latest_holdings[holding.security_id] = holding

        return list(latest_holdings.values())

    def get_current_holdings_by_account(
        self, db: Session, *, account_id: Union[str, UUIDType]
    ) -> List[PortfolioHolding]:
        """Get current holdings for an account (latest as_of_date per securities)."""
        account_uuid = self._to_uuid(account_id)
        # Subquery to get latest date per securities for the account
        latest_date_subq = (
            select(
                PortfolioHolding.security_id,
                func.max(PortfolioHolding.as_of_date).label("max_date"),
            )
            .where(PortfolioHolding.account_id == account_uuid)
            .group_by(PortfolioHolding.security_id)
            .subquery()
        )

        # Main query to get holdings with latest dates
        stmt = (
            select(PortfolioHolding)
            .options(joinedload(PortfolioHolding.security))
            .join(
                latest_date_subq,
                and_(
                    PortfolioHolding.security_id == latest_date_subq.c.security_id,
                    PortfolioHolding.as_of_date == latest_date_subq.c.max_date,
                ),
            )
            .where(PortfolioHolding.account_id == account_uuid)
            .where(PortfolioHolding.quantity > 0)  # Only non-zero positions
        )

        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_holdings_summary(
        self,
        db: Session,
        *,
        account_id: Union[str, UUIDType],
        base_currency: str = "USD",
    ) -> Dict[str, Any]:
        """Get comprehensive holdings summary for an account."""
        holdings = self.get_current_holdings_by_account(db, account_id=account_id)

        total_market_value = sum(h.market_value or Decimal("0") for h in holdings)
        total_cost_basis = sum(h.cost_basis_total or Decimal("0") for h in holdings)
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
            asset_type = holding.security.security_type if holding.security else "unknown"
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

    def get_holding_history(
        self,
        db: Session,
        *,
        account_id: Union[str, UUIDType],
        security_id: Union[str, UUIDType],
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
    ) -> List[PortfolioHolding]:
        """Get historical holdings for a specific securities in an account."""
        account_uuid = self._to_uuid(account_id)
        security_uuid = self._to_uuid(security_id)
        stmt = select(PortfolioHolding).where(
            and_(
                PortfolioHolding.account_id == account_uuid,
                PortfolioHolding.security_id == security_uuid,
            )
        )

        if start_date:
            stmt = stmt.where(PortfolioHolding.as_of_date >= start_date)
        if end_date:
            stmt = stmt.where(PortfolioHolding.as_of_date <= end_date)

        stmt = stmt.order_by(desc(PortfolioHolding.as_of_date)).limit(limit)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def update_market_values(self, db: Session, *, holdings_updates: List[Dict[str, Any]]) -> int:
        """Bulk update market values for holdings."""
        updated_count = 0
        for holding_update in holdings_updates:
            holding_id = holding_update.get("holding_id")
            if not holding_id:
                continue
            holding_uuid = self._to_uuid(holding_id)
            stmt = (
                update(PortfolioHolding)
                .where(PortfolioHolding.id == holding_uuid)
                .values(
                    market_value=holding_update.get("market_value"),
                    institution_price=holding_update.get("price"),
                    updated_at=datetime.now(timezone.utc),
                )
            )
            result = db.execute(stmt)
            updated_count += result.rowcount

        db.commit()
        return updated_count

    def create_holding_snapshot(
        self,
        db: Session,
        *,
        account_id: Union[str, UUIDType],
        as_of_date: date,
        holdings_data: List[Dict[str, Any]],
    ) -> List[PortfolioHolding]:
        """Create a complete holdings snapshot for an account as of a specific date."""
        holdings = []
        account_uuid = self._to_uuid(account_id)

        for holding_data in holdings_data:
            security_uuid = self._to_uuid(holding_data["security_id"])
            holding = PortfolioHolding(
                account_id=account_uuid,
                security_id=security_uuid,
                quantity=holding_data["quantity"],
                cost_basis_per_share=holding_data.get("cost_basis_per_share"),
                cost_basis_total=holding_data.get("cost_basis_total"),
                market_value=holding_data.get("market_value"),
                currency=holding_data["currency"],
                as_of_date=as_of_date,
                plaid_account_id=holding_data.get("plaid_account_id"),
                plaid_security_id=holding_data.get("plaid_security_id"),
                institution_price=holding_data.get("institution_price"),
                institution_value=holding_data.get("institution_value"),
            )
            holdings.append(holding)

        db.add_all(holdings)
        db.commit()

        for holding in holdings:
            db.refresh(holding)

        return holdings

    def get_portfolio_allocation(
        self, db: Session, *, user_id: Union[str, UUIDType], base_currency: str = "USD"
    ) -> Dict[str, Any]:
        """Get portfolios allocation across all users accounts."""
        # You'll need to join with PortfolioAccount table to filter by user_id
        from app.portfolios.account.model import PortfolioAccount

        user_uuid = self._to_uuid(user_id)
        stmt = (
            select(PortfolioHolding)
            .join(PortfolioAccount, PortfolioHolding.account_id == PortfolioAccount.id)
            .options(joinedload(PortfolioHolding.security))
            .where(PortfolioAccount.user_id == user_uuid)
        )

        result = db.execute(stmt)
        all_holdings = list(result.scalars().all())

        # Get current holdings only (latest per securities per account)
        current_holdings = {}
        for holding in all_holdings:
            key = (holding.account_id, holding.security_id)
            if key not in current_holdings or holding.as_of_date > current_holdings[key].as_of_date:
                current_holdings[key] = holding

        holdings = list(current_holdings.values())

        total_value = sum(h.market_value or Decimal("0") for h in holdings)

        # Calculate allocations
        by_asset_type = {}
        by_currency = {}
        by_account = {}

        for holding in holdings:
            # By asset type
            asset_type = holding.security.security_type if holding.security else "unknown"
            by_asset_type[asset_type] = by_asset_type.get(asset_type, Decimal("0")) + (
                holding.market_value or Decimal("0")
            )

            # By currency
            currency = holding.currency
            by_currency[currency] = by_currency.get(currency, Decimal("0")) + (
                holding.market_value or Decimal("0")
            )

            # By account
            account_id_str = str(holding.account_id)
            by_account[account_id_str] = by_account.get(account_id_str, Decimal("0")) + (
                holding.market_value or Decimal("0")
            )

        return {
            "total_portfolio_value": total_value,
            "base_currency": base_currency,
            "allocation_by_asset_type": by_asset_type,
            "allocation_by_currency": by_currency,
            "allocation_by_account": by_account,
            "total_holdings": len(holdings),
            "last_updated": datetime.now(timezone.utc),
        }


# Create instance
holding_crud = CRUDHolding(PortfolioHolding)

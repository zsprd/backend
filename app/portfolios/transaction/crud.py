from datetime import date
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, extract, select
from sqlalchemy.orm import Session, joinedload

from app.core.crud import CRUDBase
from app.portfolios.transaction.model import PortfolioTransaction
from app.portfolios.transaction.schema import TransactionCreate, TransactionUpdate


class CRUDTransaction(CRUDBase[PortfolioTransaction, TransactionCreate, TransactionUpdate]):
    """CRUD operations for PortfolioTransaction model."""

    def get_by_account(
        self,
        db: Session,
        *,
        account_id: str,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        transaction_category: Optional[str] = None,
    ) -> List[PortfolioTransaction]:
        """Get transactions for a specific account with filtering."""
        stmt = (
            select(PortfolioTransaction)
            .options(joinedload(PortfolioTransaction.security))
            .where(PortfolioTransaction.account_id == account_id)
        )

        if start_date:
            stmt = stmt.where(PortfolioTransaction.trade_date >= start_date)
        if end_date:
            stmt = stmt.where(PortfolioTransaction.trade_date <= end_date)
        if transaction_category:
            stmt = stmt.where(PortfolioTransaction.transaction_category == transaction_category)

        stmt = stmt.order_by(
            desc(PortfolioTransaction.trade_date), desc(PortfolioTransaction.created_at)
        )
        stmt = stmt.offset(skip).limit(limit)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_by_user(
        self,
        db: Session,
        *,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[PortfolioTransaction]:
        """Get transactions for all users accounts."""
        from app.portfolios.account.model import PortfolioAccount

        stmt = (
            select(PortfolioTransaction)
            .join(PortfolioAccount, PortfolioTransaction.account_id == PortfolioAccount.id)
            .options(joinedload(PortfolioTransaction.security))
            .where(PortfolioAccount.user_id == user_id)
        )

        if start_date:
            stmt = stmt.where(PortfolioTransaction.trade_date >= start_date)
        if end_date:
            stmt = stmt.where(PortfolioTransaction.trade_date <= end_date)

        stmt = stmt.order_by(
            desc(PortfolioTransaction.trade_date), desc(PortfolioTransaction.created_at)
        )
        stmt = stmt.offset(skip).limit(limit)

        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_transaction_summary(
        self,
        db: Session,
        *,
        account_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get transaction summary for an account."""
        stmt = select(PortfolioTransaction).where(PortfolioTransaction.account_id == account_id)

        if start_date:
            stmt = stmt.where(PortfolioTransaction.trade_date >= start_date)
        if end_date:
            stmt = stmt.where(PortfolioTransaction.trade_date <= end_date)

        result = db.execute(stmt)
        transactions = list(result.scalars().all())

        # Initialize counters
        total_invested = Decimal("0")
        total_divested = Decimal("0")
        total_fees = Decimal("0")
        total_dividends = Decimal("0")
        total_interest = Decimal("0")
        by_category = {}
        by_security = {}

        for t in transactions:
            category = t.transaction_category
            by_category[category] = by_category.get(category, 0) + 1

            if t.security_id:
                security_symbol = t.security.symbol if t.security else "Unknown"
                by_security[security_symbol] = by_security.get(security_symbol, 0) + 1

            # Calculate totals based on transaction type
            if t.transaction_side == "buy":
                total_invested += abs(t.amount)
            elif t.transaction_side == "sell":
                total_divested += abs(t.amount)
            elif category == "dividend":
                total_dividends += abs(t.amount)
            elif category == "interest":
                total_interest += abs(t.amount)

            # Add fees
            if t.fees:
                total_fees += abs(t.fees)

        # Recent transactions (last 10)
        recent_transactions = sorted(transactions, key=lambda x: x.trade_date, reverse=True)[:10]

        return {
            "account_id": account_id,
            "total_transactions": len(transactions),
            "total_invested": total_invested,
            "total_divested": total_divested,
            "net_invested": total_invested - total_divested,
            "total_fees": total_fees,
            "total_dividends": total_dividends,
            "total_interest": total_interest,
            "by_category": by_category,
            "by_security": by_security,
            "date_range": {
                "start": (min(t.trade_date for t in transactions) if transactions else None),
                "end": (max(t.trade_date for t in transactions) if transactions else None),
            },
            "recent_transactions": recent_transactions,
        }

    def get_portfolio_summary(
        self,
        db: Session,
        *,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get transaction summary across all users accounts."""
        from app.portfolios.account.model import PortfolioAccount

        stmt = (
            select(PortfolioTransaction)
            .join(PortfolioAccount, PortfolioTransaction.account_id == PortfolioAccount.id)
            .where(PortfolioAccount.user_id == user_id)
        )

        if start_date:
            stmt = stmt.where(PortfolioTransaction.trade_date >= start_date)
        if end_date:
            stmt = stmt.where(PortfolioTransaction.trade_date <= end_date)

        result = db.execute(stmt)
        transactions = list(result.scalars().all())

        # Group by account
        by_account = {}
        total_invested = Decimal("0")
        total_divested = Decimal("0")
        total_fees = Decimal("0")
        total_dividends = Decimal("0")

        for t in transactions:
            account_id = str(t.account_id)
            if account_id not in by_account:
                by_account[account_id] = {
                    "transactions": 0,
                    "invested": Decimal("0"),
                    "divested": Decimal("0"),
                    "fees": Decimal("0"),
                    "dividends": Decimal("0"),
                }

            by_account[account_id]["transactions"] += 1

            if t.transaction_side == "buy":
                by_account[account_id]["invested"] += abs(t.amount)
                total_invested += abs(t.amount)
            elif t.transaction_side == "sell":
                by_account[account_id]["divested"] += abs(t.amount)
                total_divested += abs(t.amount)
            elif t.transaction_category == "dividend":
                by_account[account_id]["dividends"] += abs(t.amount)
                total_dividends += abs(t.amount)

            if t.fees:
                by_account[account_id]["fees"] += abs(t.fees)
                total_fees += abs(t.fees)

        return {
            "user_id": user_id,
            "total_transactions": len(transactions),
            "total_invested": total_invested,
            "total_divested": total_divested,
            "net_invested": total_invested - total_divested,
            "total_fees": total_fees,
            "total_dividends": total_dividends,
            "by_account": by_account,
            "date_range": {
                "start": (min(t.trade_date for t in transactions) if transactions else None),
                "end": (max(t.trade_date for t in transactions) if transactions else None),
            },
        }

    def get_monthly_activity(
        self, db: Session, *, account_id: str, year: int, month: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get monthly transaction activity for an account."""
        stmt = select(PortfolioTransaction).where(
            and_(
                PortfolioTransaction.account_id == account_id,
                extract("year", PortfolioTransaction.trade_date) == year,
            )
        )

        if month:
            stmt = stmt.where(extract("month", PortfolioTransaction.trade_date) == month)

        result = db.execute(stmt)
        transactions = list(result.scalars().all())

        # Group by month
        monthly_data = {}
        for t in transactions:
            month_key = f"{t.trade_date.year}-{t.trade_date.month:02d}"

            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "transactions": 0,
                    "invested": Decimal("0"),
                    "divested": Decimal("0"),
                    "dividends": Decimal("0"),
                    "fees": Decimal("0"),
                }

            monthly_data[month_key]["transactions"] += 1

            if t.transaction_side == "buy":
                monthly_data[month_key]["invested"] += abs(t.amount)
            elif t.transaction_side == "sell":
                monthly_data[month_key]["divested"] += abs(t.amount)
            elif t.transaction_category == "dividend":
                monthly_data[month_key]["dividends"] += abs(t.amount)

            if t.fees:
                monthly_data[month_key]["fees"] += abs(t.fees)

        return {
            "account_id": account_id,
            "year": year,
            "month": month,
            "monthly_data": monthly_data,
            "total_months": len(monthly_data),
        }

    def get_security_transactions(
        self,
        db: Session,
        *,
        security_id: str,
        account_id: Optional[str] = None,
        user_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[PortfolioTransaction]:
        """Get transactions for a specific securities."""
        stmt = select(PortfolioTransaction).where(PortfolioTransaction.security_id == security_id)

        if account_id:
            stmt = stmt.where(PortfolioTransaction.account_id == account_id)
        elif user_id:
            from app.portfolios.account.model import PortfolioAccount

            stmt = stmt.join(
                PortfolioAccount, PortfolioTransaction.account_id == PortfolioAccount.id
            ).where(PortfolioAccount.user_id == user_id)

        if start_date:
            stmt = stmt.where(PortfolioTransaction.trade_date >= start_date)
        if end_date:
            stmt = stmt.where(PortfolioTransaction.trade_date <= end_date)

        stmt = stmt.order_by(desc(PortfolioTransaction.trade_date))
        result = db.execute(stmt)
        return list(result.scalars().all())

    def calculate_realized_gains_losses(
        self,
        db: Session,
        *,
        account_id: str,
        security_id: Optional[str] = None,
        tax_year: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Calculate realized gains/losses for tax reporting."""
        stmt = select(PortfolioTransaction).where(
            and_(
                PortfolioTransaction.account_id == account_id,
                PortfolioTransaction.transaction_side == "sell",
            )
        )

        if security_id:
            stmt = stmt.where(PortfolioTransaction.security_id == security_id)

        if tax_year:
            stmt = stmt.where(extract("year", PortfolioTransaction.trade_date) == tax_year)

        result = db.execute(stmt)
        sell_transactions = list(result.scalars().all())

        realized_gains = Decimal("0")
        realized_losses = Decimal("0")
        total_proceeds = Decimal("0")
        total_cost_basis = Decimal("0")

        for sell_tx in sell_transactions:
            proceeds = abs(sell_tx.amount)
            total_proceeds += proceeds

            # For proper cost basis calculation, you'd need to implement
            # FIFO, LIFO, or specific lot identification methods
            # This is a simplified calculation
            if sell_tx.price and sell_tx.quantity:
                cost_basis = abs(sell_tx.quantity * sell_tx.price)
                total_cost_basis += cost_basis

                gain_loss = proceeds - cost_basis
                if gain_loss > 0:
                    realized_gains += gain_loss
                else:
                    realized_losses += abs(gain_loss)

        net_realized = realized_gains - realized_losses

        return {
            "account_id": account_id,
            "security_id": security_id,
            "tax_year": tax_year,
            "total_sells": len(sell_transactions),
            "total_proceeds": total_proceeds,
            "total_cost_basis": total_cost_basis,
            "realized_gains": realized_gains,
            "realized_losses": realized_losses,
            "net_realized": net_realized,
            "transactions": sell_transactions,
        }

    def bulk_import_transactions(
        self, db: Session, *, transactions_data: List[Dict[str, Any]]
    ) -> List[PortfolioTransaction]:
        """Bulk import transactions efficiently."""
        transactions = []

        for tx_data in transactions_data:
            transaction = PortfolioTransaction(**tx_data)
            transactions.append(transaction)

        db.add_all(transactions)
        db.commit()

        for transaction in transactions:
            db.refresh(transaction)

        return transactions


# Create instance
transaction_crud = CRUDTransaction(PortfolioTransaction)

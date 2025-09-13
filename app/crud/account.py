from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, or_, update
from sqlalchemy.orm import Session, joinedload

from app.crud.base import CRUDBase
from app.models.core.account import Account
from app.schemas.account import AccountCreate, AccountUpdate


class CRUDAccount(CRUDBase[Account, AccountCreate, AccountUpdate]):

    def get_multi_by_user(
        self,
        db: Session,
        *,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False,
    ) -> List[Account]:
        """Get multiple accounts for a specific user with optional filters."""
        query = (
            db.query(Account)
            .options(joinedload(Account.institution))
            .filter(Account.user_id == user_id)
        )

        if not include_inactive:
            query = query.filter(Account.is_active)

        return query.offset(skip).limit(limit).all()

    def get_by_user_and_id(
        self, db: Session, *, user_id: str, account_id: str
    ) -> Optional[Account]:
        """Get a specific account for a user."""
        return (
            db.query(Account)
            .options(joinedload(Account.institution))
            .filter(and_(Account.id == account_id, Account.user_id == user_id))
            .first()
        )

    def count_by_user(self, db: Session, *, user_id: str) -> int:
        """Count total accounts for a user."""
        return db.query(Account).filter(Account.user_id == user_id).count()

    def get_account_summary(
        self, db: Session, *, account_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get account summary with calculated values."""
        account = self.get_by_user_and_id(db, user_id=user_id, account_id=account_id)
        if not account:
            return None

        # Get holdings summary
        from app.crud.holding import holding_crud

        holdings = holding_crud.get_by_account(db, account_id=account_id)

        total_market_value = sum(h.market_value or Decimal("0") for h in holdings)
        total_cost_basis = sum(h.cost_basis_total or Decimal("0") for h in holdings)
        unrealized_gain_loss = total_market_value - total_cost_basis
        unrealized_gain_loss_percent = (
            (unrealized_gain_loss / total_cost_basis * 100)
            if total_cost_basis > 0
            else Decimal("0")
        )

        # Get cash transactions for cash balance (simplified)
        from app.crud.transaction import transaction_crud

        transactions = transaction_crud.get_by_account(db, account_id=account_id)
        cash_balance = sum(
            t.amount
            for t in transactions
            if getattr(t, "category", None) in ["deposit", "interest"]
        ) - sum(
            abs(t.amount)
            for t in transactions
            if getattr(t, "category", None) in ["withdrawal", "purchase"]
        )
        cash_balance = float(max(cash_balance, Decimal("0")))
        return {
            "account_id": account_id,
            "name": account.name,
            "currency": account.currency,
            "total_market_value": total_market_value,
            "total_cost_basis": total_cost_basis,
            "unrealized_gain_loss": unrealized_gain_loss,
            "unrealized_gain_loss_percent": unrealized_gain_loss_percent,
            "cash_balance": cash_balance,
            "holdings_count": len(holdings),
            "last_updated": account.updated_at,
        }

    def soft_delete(self, db: Session, *, account_id: str, user_id: str) -> Optional[Account]:
        """Soft delete an account by setting is_active to False."""
        account = self.get_by_user_and_id(db, user_id=user_id, account_id=account_id)
        if account:
            account.is_active = False
            db.commit()
            db.refresh(account)
        return account

    def get_accounts_with_balances(
        self, db: Session, *, user_id: str, currency: str = "USD"
    ) -> List[dict]:
        """Get accounts with current balance calculations."""
        accounts = self.get_multi_by_user(db, user_id=user_id)

        accounts_with_balances = []
        for account in accounts:
            summary = self.get_account_summary(db, account_id=str(account.id), user_id=user_id)
            if summary:
                accounts_with_balances.append({**summary, "account": account})

        return accounts_with_balances

    def update_account_last_sync(
        self,
        db: Session,
        *,
        account_id: str,
        user_id: str,
        sync_status: Optional[str] = "completed",
    ) -> Optional[Account]:
        """Update account last sync timestamp and status."""
        account = self.get_by_user_and_id(db, user_id=user_id, account_id=account_id)
        if account:
            account.updated_at = datetime.now(timezone.utc)
            db.add(account)
            db.commit()
            db.refresh(account)
        return account

    def bulk_update_sync_status(
        self, db: Session, *, user_id: str, account_ids: List[str], sync_status: str
    ) -> int:
        """Bulk update sync status for multiple accounts."""
        stmt = (
            update(Account)
            .where(and_(Account.user_id == user_id, Account.id.in_(account_ids)))
            .values(sync_status=sync_status, updated_at=datetime.now(timezone.utc))
        )
        result = db.execute(stmt)
        db.commit()
        return result.rowcount

    def get_multi_by_category(
        self,
        db: Session,
        *,
        user_id: str,
        account_category: str,
        include_inactive: bool = False,
    ) -> List[Account]:
        """Get accounts filtered by category/type."""
        query = db.query(Account).filter(
            and_(Account.user_id == user_id, Account.account_category == account_category)
        )

        if not include_inactive:
            query = query.filter(Account.is_active)

        return query.all()

    def get_portfolio_overview(
        self, db: Session, *, user_id: str, base_currency: str = "USD"
    ) -> Dict[str, Any]:
        """Get comprehensive portfolio overview across all accounts."""
        accounts = self.get_multi_by_user(db, user_id=user_id)

        total_value = Decimal("0")
        total_cost_basis = Decimal("0")
        by_account_type = {}
        by_currency = {}
        account_summaries = []

        for account in accounts:
            summary = self.get_account_summary(db, account_id=str(account.id), user_id=user_id)

            if summary:
                account_summaries.append({"account": account, "summary": summary})

                # Add to totals
                market_value = summary.get("total_market_value", Decimal("0"))
                cost_basis = summary.get("total_cost_basis", Decimal("0"))

                total_value += market_value
                total_cost_basis += cost_basis

                # Group by account type
                account_type = account.account_category
                if account_type not in by_account_type:
                    by_account_type[account_type] = {
                        "count": 0,
                        "total_value": Decimal("0"),
                        "accounts": [],
                    }

                by_account_type[account_type]["count"] += 1
                by_account_type[account_type]["total_value"] += market_value
                by_account_type[account_type]["accounts"].append(account.id)

                # Group by currency
                currency = account.currency
                if currency not in by_currency:
                    by_currency[currency] = Decimal("0")
                by_currency[currency] += market_value

        unrealized_gain_loss = total_value - total_cost_basis
        unrealized_gain_loss_percent = (
            (unrealized_gain_loss / total_cost_basis * 100)
            if total_cost_basis > 0
            else Decimal("0")
        )

        return {
            "user_id": user_id,
            "base_currency": base_currency,
            "total_accounts": len(accounts),
            "active_accounts": len([a for a in accounts if a.is_active]),
            "total_portfolio_value": total_value,
            "total_cost_basis": total_cost_basis,
            "unrealized_gain_loss": unrealized_gain_loss,
            "unrealized_gain_loss_percent": round(unrealized_gain_loss_percent, 2),
            "by_account_type": by_account_type,
            "by_currency": by_currency,
            "account_summaries": account_summaries,
            "last_updated": datetime.now(timezone.utc),
        }

    def get_user_account_statistics(self, db: Session, *, user_id: str) -> Dict[str, Any]:
        """Get comprehensive account statistics for a user."""
        accounts = self.get_multi_by_user(db, user_id=user_id, include_inactive=True)

        total_accounts = len(accounts)
        active_accounts = len([a for a in accounts if a.is_active])
        inactive_accounts = total_accounts - active_accounts

        # Group by account category
        by_category = {}
        for account in accounts:
            category = account.account_category
            if category not in by_category:
                by_category[category] = {"active": 0, "inactive": 0, "total": 0}

            by_category[category]["total"] += 1
            if account.is_active:
                by_category[category]["active"] += 1
            else:
                by_category[category]["inactive"] += 1

        # Recently created accounts (last 30 days)
        from datetime import timedelta

        recent_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        recent_accounts = [a for a in accounts if a.created_at >= recent_cutoff]

        return {
            "user_id": user_id,
            "total_accounts": total_accounts,
            "active_accounts": active_accounts,
            "inactive_accounts": inactive_accounts,
            "recent_accounts_30d": len(recent_accounts),
            "by_category": by_category,
            "oldest_account": (min(accounts, key=lambda x: x.created_at) if accounts else None),
            "newest_account": (max(accounts, key=lambda x: x.created_at) if accounts else None),
        }

    def search_by_name(
        self, db: Session, *, user_id: str, search_term: str, limit: int = 10
    ) -> List[Account]:
        """Search user accounts by name or official name."""
        from sqlalchemy import or_

        query = (
            db.query(Account)
            .filter(
                and_(
                    Account.user_id == user_id,
                    Account.is_active,
                    or_(
                        Account.name.ilike(f"%{search_term}%"),
                        Account.official_name.ilike(f"%{search_term}%"),
                    ),
                )
            )
            .limit(limit)
        )

        return query.all()

    def get_stale_accounts(
        self, db: Session, *, user_id: Optional[str] = None, hours_since_sync: int = 24
    ) -> List[Account]:
        """Get accounts that haven't been synced recently."""
        from datetime import timedelta

        sync_cutoff = datetime.now(timezone.utc) - timedelta(hours=hours_since_sync)

        query = db.query(Account).filter(
            and_(
                Account.is_active,
                or_(Account.updated_at < sync_cutoff, Account.updated_at.is_(None)),
            )
        )

        if user_id:
            query = query.filter(Account.user_id == user_id)

        return query.all()


# Create instance
account_crud = CRUDAccount(Account)

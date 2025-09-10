from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func
from decimal import Decimal

from app.crud.base import CRUDBase
from app.models.account import Account, Institution
from app.schemas.account import AccountCreate, AccountUpdate


class CRUDAccount(CRUDBase[Account, AccountCreate, AccountUpdate]):
    def get_multi_by_user(
        self,
        db: Session,
        *,
        user_id: str,
        skip: int = 0,
        limit: int = 100,
        include_inactive: bool = False
    ) -> List[Account]:
        """Get multiple accounts for a specific user with optional filters."""
        query = db.query(Account).options(joinedload(Account.institution)).filter(
            Account.user_id == user_id
        )
        
        if not include_inactive:
            query = query.filter(Account.is_active == True)
        
        return query.offset(skip).limit(limit).all()

    def get_by_user_and_id(
        self, 
        db: Session, 
        *, 
        user_id: str, 
        account_id: str
    ) -> Optional[Account]:
        """Get a specific account for a user."""
        return db.query(Account).options(joinedload(Account.institution)).filter(
            and_(Account.id == account_id, Account.user_id == user_id)
        ).first()

    def count_by_user(self, db: Session, *, user_id: str) -> int:
        """Count total accounts for a user."""
        return db.query(Account).filter(Account.user_id == user_id).count()

    def get_account_summary(self, db: Session, *, account_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get account summary with calculated values."""
        account = self.get_by_user_and_id(db, user_id=user_id, account_id=account_id)
        if not account:
            return None
        
        # Get holdings summary
        from app.crud.holding import holding_crud
        holdings = holding_crud.get_by_account(db, account_id=account_id)
        
        total_market_value = sum(h.market_value or Decimal('0') for h in holdings)
        total_cost_basis = sum(h.cost_basis_total or Decimal('0') for h in holdings)
        unrealized_gain_loss = total_market_value - total_cost_basis
        unrealized_gain_loss_percent = (unrealized_gain_loss / total_cost_basis * 100) if total_cost_basis > 0 else Decimal('0')
        
        # Get cash transactions for cash balance (simplified)
        from app.crud.transaction import transaction_crud
        transactions = transaction_crud.get_by_account(db, account_id=account_id)
        cash_balance = sum(t.amount for t in transactions if getattr(t, 'category', None) in ['deposit', 'interest']) - \
                      sum(abs(t.amount) for t in transactions if getattr(t, 'category', None) in ['withdrawal', 'purchase'])
        return {
            "account_id": account_id,
            "name": account.name,
            "currency": account.currency,
            "total_market_value": total_market_value,
            "total_cost_basis": total_cost_basis,
            "unrealized_gain_loss": unrealized_gain_loss,
            "unrealized_gain_loss_percent": unrealized_gain_loss_percent,
            "cash_balance": max(cash_balance, Decimal('0')),
            "holdings_count": len(holdings),
            "last_updated": account.updated_at
        }

    def soft_delete(self, db: Session, *, account_id: str, user_id: str) -> Optional[Account]:
        """Soft delete an account by setting is_active to False."""
        account = self.get_by_user_and_id(db, user_id=user_id, account_id=account_id)
        if account:
            account.is_active = False
            db.commit()
            db.refresh(account)
        return account


# Create instance
account_crud = CRUDAccount(Account)
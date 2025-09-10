from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, desc, asc
from datetime import date, datetime, timedelta
from decimal import Decimal

from app.crud.base import CRUDBase
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class CRUDTransaction(CRUDBase[Transaction, TransactionCreate, TransactionUpdate]):
    def get_by_account(
        self,
        db: Session,
        *,
        account_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        """Get transactions for a specific account."""
        query = db.query(Transaction).options(
            joinedload(Transaction.security)
        ).filter(Transaction.account_id == account_id)
        
        if start_date:
            query = query.filter(Transaction.trade_date >= start_date)
        if end_date:
            query = query.filter(Transaction.trade_date <= end_date)
        
        return query.order_by(desc(Transaction.trade_date)).offset(skip).limit(limit).all()

    def get_by_user_accounts(
        self,
        db: Session,
        *,
        user_id: str,
        account_ids: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        transaction_types: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        """Get transactions across multiple accounts for a user."""
        from app.models.account import Account
        
        query = db.query(Transaction).options(
            joinedload(Transaction.security)
        ).join(Account).filter(Account.user_id == user_id)
        
        if account_ids:
            query = query.filter(Transaction.account_id.in_(account_ids))
        
        if start_date:
            query = query.filter(Transaction.trade_date >= start_date)
        if end_date:
            query = query.filter(Transaction.trade_date <= end_date)
        
        if transaction_types:
            query = query.filter(Transaction.category.in_(transaction_types))
        
        return query.order_by(desc(Transaction.trade_date)).offset(skip).limit(limit).all()

    def get_recent_transactions(
        self,
        db: Session,
        *,
        user_id: str,
        limit: int = 10
    ) -> List[Transaction]:
        """Get recent transactions for a user."""
        return self.get_by_user_accounts(
            db,
            user_id=user_id,
            start_date=date.today() - timedelta(days=30),
            limit=limit
        )

    def get_transactions_summary(
        self,
        db: Session,
        *,
        user_id: str,
        account_id: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get transaction summary for user or specific account."""
        if account_id:
            transactions = self.get_by_account(
                db,
                account_id=account_id,
                start_date=start_date,
                end_date=end_date,
                limit=10000  # Get all transactions for summary
            )
        else:
            transactions = self.get_by_user_accounts(
                db,
                user_id=user_id,
                start_date=start_date,
                end_date=end_date,
                limit=10000  # Get all transactions for summary
            )
        
        total_invested = Decimal('0')
        total_fees = Decimal('0')
        total_dividends = Decimal('0')
        by_category = {}
        
        for txn in transactions:
            # Calculate totals
            if txn.category in ['buy', 'sell']:
                if txn.category == 'buy':
                    total_invested += abs(txn.amount)
            elif txn.category == 'dividend':
                total_dividends += txn.amount
            
            if txn.fees:
                total_fees += txn.fees
            
            # Group by category
            category = txn.category
            if category not in by_category:
                by_category[category] = {'count': 0, 'amount': Decimal('0')}
            by_category[category]['count'] += 1
            by_category[category]['amount'] += txn.amount
        
        # Get recent transactions
        recent_transactions = transactions[:10] if transactions else []
        
        return {
            "account_id": account_id,
            "total_transactions": len(transactions),
            "total_invested": total_invested,
            "total_fees": total_fees,
            "total_dividends": total_dividends,
            "date_range": {
                "start_date": start_date,
                "end_date": end_date
            },
            "by_category": {k: {'count': v['count'], 'amount': float(v['amount'])} for k, v in by_category.items()},
            "recent_transactions": recent_transactions
        }


# Create instance
transaction_crud = CRUDTransaction(Transaction)
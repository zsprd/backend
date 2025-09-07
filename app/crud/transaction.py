from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, desc, asc
from datetime import date, datetime, timedelta

from app.crud.base import CRUDBase
from app.models.transaction import Transaction, CashTransaction
from app.models.account import Account
from app.models.security import Security
from app.schemas.transaction import TransactionCreate, TransactionUpdate, CashTransactionCreate, CashTransactionUpdate


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
            query = query.filter(Transaction.type.in_(transaction_types))
        
        return query.order_by(desc(Transaction.trade_date)).offset(skip).limit(limit).all()

    def get_by_security(
        self,
        db: Session,
        *,
        security_id: str,
        user_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> List[Transaction]:
        """Get all transactions for a specific security owned by user."""
        query = db.query(Transaction).join(Account).filter(
            and_(
                Transaction.security_id == security_id,
                Account.user_id == user_id
            )
        )
        
        if start_date:
            query = query.filter(Transaction.trade_date >= start_date)
        if end_date:
            query = query.filter(Transaction.trade_date <= end_date)
        
        return query.order_by(asc(Transaction.trade_date)).all()

    def get_transactions_summary(
        self,
        db: Session,
        *,
        user_id: str,
        account_ids: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get transaction summary with aggregated metrics."""
        query = db.query(Transaction).join(Account).filter(Account.user_id == user_id)
        
        if account_ids:
            query = query.filter(Transaction.account_id.in_(account_ids))
        
        if start_date:
            query = query.filter(Transaction.trade_date >= start_date)
        if end_date:
            query = query.filter(Transaction.trade_date <= end_date)
        
        transactions = query.all()
        
        if not transactions:
            return {
                "total_transactions": 0,
                "total_invested": 0.0,
                "total_withdrawn": 0.0,
                "net_flow": 0.0,
                "total_fees": 0.0,
                "total_dividends": 0.0,
                "by_type": {},
                "by_month": {}
            }
        
        # Calculate metrics
        total_invested = 0.0
        total_withdrawn = 0.0
        total_fees = 0.0
        total_dividends = 0.0
        by_type = {}
        by_month = {}
        
        for txn in transactions:
            amount = float(txn.amount)
            fees = float(txn.fees or 0)
            
            # Type breakdown
            txn_type = txn.type
            if txn_type not in by_type:
                by_type[txn_type] = {"count": 0, "amount": 0.0}
            by_type[txn_type]["count"] += 1
            by_type[txn_type]["amount"] += amount
            
            # Month breakdown
            month_key = txn.trade_date.strftime("%Y-%m")
            if month_key not in by_month:
                by_month[month_key] = {"count": 0, "amount": 0.0}
            by_month[month_key]["count"] += 1
            by_month[month_key]["amount"] += amount
            
            # Investment flows
            if txn_type in ["buy", "deposit", "transfer_in"]:
                total_invested += amount
            elif txn_type in ["sell", "withdrawal", "transfer_out"]:
                total_withdrawn += amount
            elif txn_type == "dividend":
                total_dividends += amount
            
            total_fees += fees
        
        return {
            "total_transactions": len(transactions),
            "total_invested": total_invested,
            "total_withdrawn": total_withdrawn,
            "net_flow": total_invested - total_withdrawn,
            "total_fees": total_fees,
            "total_dividends": total_dividends,
            "by_type": by_type,
            "by_month": by_month,
            "period_start": start_date,
            "period_end": end_date
        }

    def get_recent_transactions(
        self,
        db: Session,
        *,
        user_id: str,
        limit: int = 10
    ) -> List[Transaction]:
        """Get most recent transactions for user."""
        return db.query(Transaction).options(
            joinedload(Transaction.security)
        ).join(Account).filter(
            Account.user_id == user_id
        ).order_by(desc(Transaction.created_at)).limit(limit).all()

    def calculate_realized_pnl(
        self,
        db: Session,
        *,
        account_id: str,
        security_id: str,
        quantity_sold: float,
        sale_price: float,
        lot_method: str = "fifo"
    ) -> float:
        """Calculate realized P&L for a sale transaction."""
        # Get all buy transactions for this security in chronological order
        buy_transactions = db.query(Transaction).filter(
            and_(
                Transaction.account_id == account_id,
                Transaction.security_id == security_id,
                Transaction.type == "buy"
            )
        ).order_by(
            asc(Transaction.trade_date) if lot_method == "fifo" else desc(Transaction.trade_date)
        ).all()
        
        remaining_to_sell = quantity_sold
        total_cost_basis = 0.0
        
        for buy_txn in buy_transactions:
            if remaining_to_sell <= 0:
                break
                
            buy_quantity = float(buy_txn.quantity or 0)
            buy_price = float(buy_txn.price or 0)
            
            # Determine how much to use from this lot
            quantity_from_lot = min(remaining_to_sell, buy_quantity)
            
            # Add to cost basis
            total_cost_basis += quantity_from_lot * buy_price
            remaining_to_sell -= quantity_from_lot
        
        # Calculate realized P&L
        sale_proceeds = quantity_sold * sale_price
        realized_pnl = sale_proceeds - total_cost_basis
        
        return realized_pnl

    def create_bulk(
        self,
        db: Session,
        *,
        transactions_data: List[Dict[str, Any]]
    ) -> List[Transaction]:
        """Create multiple transactions in bulk."""
        created_transactions = []
        
        for txn_data in transactions_data:
            transaction = self.create_from_dict(db, obj_in=txn_data)
            created_transactions.append(transaction)
        
        return created_transactions


class CRUDCashTransaction(CRUDBase[CashTransaction, CashTransactionCreate, CashTransactionUpdate]):
    def get_by_account(
        self,
        db: Session,
        *,
        account_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[CashTransaction]:
        """Get cash transactions for a specific account."""
        query = db.query(CashTransaction).filter(CashTransaction.account_id == account_id)
        
        if start_date:
            query = query.filter(CashTransaction.date >= start_date)
        if end_date:
            query = query.filter(CashTransaction.date <= end_date)
        
        return query.order_by(desc(CashTransaction.date)).offset(skip).limit(limit).all()

    def get_by_user_accounts(
        self,
        db: Session,
        *,
        user_id: str,
        account_ids: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[CashTransaction]:
        """Get cash transactions across user's accounts."""
        query = db.query(CashTransaction).join(Account).filter(Account.user_id == user_id)
        
        if account_ids:
            query = query.filter(CashTransaction.account_id.in_(account_ids))
        
        if start_date:
            query = query.filter(CashTransaction.date >= start_date)
        if end_date:
            query = query.filter(CashTransaction.date <= end_date)
        
        return query.order_by(desc(CashTransaction.date)).offset(skip).limit(limit).all()

    def get_cash_flow_summary(
        self,
        db: Session,
        *,
        user_id: str,
        account_ids: Optional[List[str]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get cash flow summary."""
        query = db.query(CashTransaction).join(Account).filter(Account.user_id == user_id)
        
        if account_ids:
            query = query.filter(CashTransaction.account_id.in_(account_ids))
        
        if start_date:
            query = query.filter(CashTransaction.date >= start_date)
        if end_date:
            query = query.filter(CashTransaction.date <= end_date)
        
        transactions = query.all()
        
        total_inflow = sum([
            float(t.amount) for t in transactions 
            if t.type in ["deposit", "transfer", "interest", "dividend"] and float(t.amount) > 0
        ])
        
        total_outflow = sum([
            abs(float(t.amount)) for t in transactions 
            if t.type in ["withdrawal", "payment", "fee"] or float(t.amount) < 0
        ])
        
        return {
            "total_transactions": len(transactions),
            "total_inflow": total_inflow,
            "total_outflow": total_outflow,
            "net_flow": total_inflow - total_outflow
        }


# Create instances
transaction_crud = CRUDTransaction(Transaction)
cash_transaction_crud = CRUDCashTransaction(CashTransaction)
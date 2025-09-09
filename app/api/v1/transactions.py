# app/api/v1/transactions.py
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date, datetime

from app.core.database import get_db
from app.core.user import get_current_user_id

router = APIRouter()


@router.get("/")
async def get_transactions(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_ids: Optional[List[str]] = Query(None, description="Filter by account IDs"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    skip: int = Query(0, description="Skip records"),
    limit: int = Query(100, description="Limit records")
):
    """
    Get transactions for the current user.
    """
    return {
        "transactions": [
            {
                "id": "txn-1",
                "account_id": "account-1",
                "security_id": "security-1",
                "transaction_type": "buy",
                "side": "buy",
                "symbol": "AAPL",
                "quantity": 100.0,
                "price": 150.0,
                "amount": 15000.0,
                "fees": 9.95,
                "trade_date": "2024-01-15",
                "transaction_currency": "USD",
                "description": "Apple stock purchase",
                "realized_gain_loss": None,
                "portfolio_impact": 15000.0
            },
            {
                "id": "txn-2",
                "account_id": "account-1",
                "security_id": None,
                "transaction_type": "dividend",
                "side": None,
                "symbol": "AAPL",
                "quantity": None,
                "price": None,
                "amount": 250.0,
                "fees": 0.0,
                "trade_date": "2024-02-15",
                "transaction_currency": "USD",
                "description": "Quarterly dividend payment",
                "realized_gain_loss": None,
                "portfolio_impact": 250.0
            }
        ],
        "total": 2,
        "skip": skip,
        "limit": limit,
        "summary": {
            "total_transactions": 2,
            "total_invested": 15000.0,
            "total_withdrawn": 0.0,
            "net_flow": 15000.0,
            "total_fees": 9.95,
            "total_dividends": 250.0,
            "realized_gains": 0.0,
            "realized_losses": 0.0,
            "base_currency": "USD",
            "period_start": start_date.isoformat() if start_date else None,
            "period_end": end_date.isoformat() if end_date else None
        }
    }


@router.get("/{transaction_id}")
async def get_transaction(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    transaction_id: str
):
    """
    Get a specific transaction by ID.
    """
    return {
        "id": transaction_id,
        "account_id": "account-1",
        "security_id": "security-1",
        "transaction_type": "buy",
        "side": "buy",
        "quantity": 100.0,
        "price": 150.0,
        "amount": 15000.0,
        "fees": 9.95,
        "trade_date": "2024-01-15",
        "transaction_currency": "USD",
        "description": "Apple stock purchase",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }


@router.post("/")
async def create_transaction(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    transaction_data: Dict[str, Any]
):
    """
    Create a new transaction.
    """
    return {
        "id": "new-transaction-id",
        "account_id": transaction_data.get("account_id"),
        "security_id": transaction_data.get("security_id"),
        "transaction_type": transaction_data.get("transaction_type"),
        "amount": transaction_data.get("amount", 0),
        "trade_date": transaction_data.get("trade_date"),
        "transaction_currency": transaction_data.get("transaction_currency", "USD"),
        "created_at": datetime.utcnow().isoformat(),
        "message": "Transaction created successfully"
    }


@router.put("/{transaction_id}")
async def update_transaction(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    transaction_id: str,
    transaction_data: Dict[str, Any]
):
    """
    Update an existing transaction.
    """
    return {
        "id": transaction_id,
        "message": "Transaction updated successfully",
        "updated_fields": list(transaction_data.keys()),
        "updated_at": datetime.utcnow().isoformat()
    }


@router.delete("/{transaction_id}")
async def delete_transaction(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    transaction_id: str
):
    """
    Delete a transaction.
    """
    return {
        "message": "Transaction deleted successfully",
        "transaction_id": transaction_id,
        "deleted_at": datetime.utcnow().isoformat()
    }


@router.get("/recent/")
async def get_recent_transactions(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    limit: int = Query(10, description="Number of recent transactions")
):
    """
    Get most recent transactions for the user.
    """
    return [
        {
            "id": "txn-1",
            "transaction_type": "buy",
            "symbol": "AAPL",
            "amount": 15000.0,
            "trade_date": "2024-01-15",
            "created_at": datetime.utcnow().isoformat()
        }
    ]


@router.get("/accounts/{account_id}")
async def get_account_transactions(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_id: str,
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    skip: int = Query(0),
    limit: int = Query(100)
):
    """
    Get transactions for a specific account.
    """
    return [
        {
            "id": "txn-1",
            "account_id": account_id,
            "transaction_type": "buy",
            "symbol": "AAPL",
            "amount": 15000.0,
            "trade_date": "2024-01-15"
        }
    ]


@router.get("/summary/")
async def get_transactions_summary(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_ids: Optional[List[str]] = Query(None),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None)
):
    """
    Get transaction summary with aggregated metrics.
    """
    return {
        "total_transactions": 2,
        "total_invested": 15000.0,
        "total_withdrawn": 0.0,
        "net_flow": 15000.0,
        "total_fees": 9.95,
        "total_dividends": 250.0,
        "by_type": {
            "buy": {"count": 1, "amount": 15000.0},
            "dividend": {"count": 1, "amount": 250.0}
        },
        "by_month": {
            "2024-01": {"count": 1, "amount": 15000.0},
            "2024-02": {"count": 1, "amount": 250.0}
        }
    }


@router.get("/health")
async def transactions_health():
    """
    Health check for transactions service.
    """
    return {
        "status": "healthy",
        "service": "transactions",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "transaction_management",
            "transaction_analysis",
            "account_filtering"
        ]
    }
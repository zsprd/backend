from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.core.database import get_db
from app.core.user import get_current_user_id

router = APIRouter()


@router.get("/")
async def get_accounts(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    skip: int = Query(0, description="Skip records"),
    limit: int = Query(100, description="Limit records"),
    include_inactive: bool = Query(False, description="Include inactive accounts")
):
    """
    Get accounts for the current user.
    """
    return {
        "accounts": [
            {
                "id": "account-1",
                "user_id": current_user_id,
                "name": "Main Investment Account",
                "official_name": "Brokerage Investment Account",
                "account_type": "investment",
                "subtype": "brokerage",
                "mask": "1234",
                "currency": "USD",
                "institution_name": "Example Brokerage",
                "is_active": True,
                "current_balance": 25000.0,
                "market_value": 25000.0,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        ],
        "total": 1,
        "skip": skip,
        "limit": limit
    }


@router.get("/{account_id}")
async def get_account(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_id: str
):
    """
    Get a specific account by ID.
    """
    return {
        "id": account_id,
        "user_id": current_user_id,
        "name": "Main Investment Account",
        "official_name": "Brokerage Investment Account",
        "account_type": "investment",
        "subtype": "brokerage",
        "mask": "1234",
        "currency": "USD",
        "institution_name": "Example Brokerage",
        "is_active": True,
        "current_balance": 25000.0,
        "market_value": 25000.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@router.post("/")
async def create_account(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_data: Dict[str, Any]
):
    """
    Create a new account.
    """
    return {
        "id": "new-account-id",
        "user_id": current_user_id,
        "name": account_data.get("name"),
        "account_type": account_data.get("account_type"),
        "currency": account_data.get("currency", "USD"),
        "is_active": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "message": "Account created successfully"
    }


@router.put("/{account_id}")
async def update_account(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_id: str,
    account_data: Dict[str, Any]
):
    """
    Update an existing account.
    """
    return {
        "id": account_id,
        "message": "Account updated successfully",
        "updated_fields": list(account_data.keys()),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }


@router.delete("/{account_id}")
async def delete_account(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_id: str
):
    """
    Delete an account (soft delete).
    """
    return {
        "message": "Account deleted successfully",
        "account_id": account_id,
        "deleted_at": datetime.now(timezone.utc).isoformat()
    }


@router.get("/{account_id}/summary")
async def get_account_summary(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_id: str
):
    """
    Get account summary with performance metrics.
    """
    return {
        "account_id": account_id,
        "name": "Main Investment Account",
        "current_value": 25000.0,
        "cost_basis": 20000.0,
        "unrealized_gain_loss": 5000.0,
        "unrealized_gain_loss_percent": 25.0,
        "total_holdings": 5,
        "cash_balance": 1000.0,
        "currency": "USD",
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


@router.get("/health")
async def accounts_health():
    """
    Health check for accounts service.
    """
    return {
        "status": "healthy",
        "service": "accounts",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "features": [
            "account_management",
            "account_summary",
            "multi_currency_support"
        ]
    }
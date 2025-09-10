from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta

from app.core.database import get_db
from app.core.user import get_current_user_id
from app.crud.transaction import transaction_crud
from app.crud.account import account_crud
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionSummaryResponse
)

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def get_transactions(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_ids: Optional[str] = Query(None, description="Comma-separated account IDs"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    transaction_types: Optional[str] = Query(None, description="Comma-separated transaction types"),
    skip: int = Query(0, description="Skip records"),
    limit: int = Query(100, description="Limit records")
):
    """Get transactions for the current user."""
    try:
        account_id_list = None
        if account_ids:
            account_id_list = [id.strip() for id in account_ids.split(",")]
        
        transaction_type_list = None
        if transaction_types:
            transaction_type_list = [t.strip() for t in transaction_types.split(",")]
        
        transactions = transaction_crud.get_by_user_accounts(
            db,
            user_id=current_user_id,
            account_ids=account_id_list,
            start_date=start_date,
            end_date=end_date,
            transaction_types=transaction_type_list,
            skip=skip,
            limit=limit
        )
        
        # Get summary
        summary = transaction_crud.get_transactions_summary(
            db,
            user_id=current_user_id,
            start_date=start_date,
            end_date=end_date
        )
        
        return {
            "transactions": transactions,
            "summary": summary,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving transactions: {str(e)}"
        )


@router.get("/recent/", response_model=List[TransactionResponse])
async def get_recent_transactions(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    limit: int = Query(10, description="Number of recent transactions")
):
    """Get recent transactions for the current user."""
    transactions = transaction_crud.get_recent_transactions(
        db, user_id=current_user_id, limit=limit
    )
    return transactions


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    transaction_id: str
):
    """Get a specific transaction by ID."""
    transaction = transaction_crud.get(db, id=transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Verify user owns the account for this transaction
    account = account_crud.get_by_user_and_id(
        db, user_id=current_user_id, account_id=transaction.account_id
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return transaction


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    transaction_data: TransactionCreate
):
    """Create a new transaction."""
    # Verify user owns the account
    account = account_crud.get_by_user_and_id(
        db, user_id=current_user_id, account_id=str(transaction_data.account_id)
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied or account not found"
        )
    
    try:
        transaction = transaction_crud.create(db, obj_in=transaction_data)
        return transaction
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating transaction: {str(e)}"
        )


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    transaction_id: str,
    transaction_data: TransactionUpdate
):
    """Update an existing transaction."""
    transaction = transaction_crud.get(db, id=transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Verify user owns the account
    account = account_crud.get_by_user_and_id(
        db, user_id=current_user_id, account_id=transaction.account_id
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        updated_transaction = transaction_crud.update(db, db_obj=transaction, obj_in=transaction_data)
        return updated_transaction
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating transaction: {str(e)}"
        )


@router.delete("/{transaction_id}")
async def delete_transaction(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    transaction_id: str
):
    """Delete a transaction."""
    transaction = transaction_crud.get(db, id=transaction_id)
    
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found"
        )
    
    # Verify user owns the account
    account = account_crud.get_by_user_and_id(
        db, user_id=current_user_id, account_id=transaction.account_id
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        transaction_crud.delete(db, id=transaction_id)
        return {
            "message": "Transaction deleted successfully",
            "transaction_id": transaction_id,
            "deleted_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting transaction: {str(e)}"
        )


@router.get("/accounts/{account_id}", response_model=List[TransactionResponse])
async def get_account_transactions(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_id: str,
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    skip: int = Query(0, description="Skip records"),
    limit: int = Query(100, description="Limit records")
):
    """Get transactions for a specific account."""
    # Verify user owns the account
    account = account_crud.get_by_user_and_id(
        db, user_id=current_user_id, account_id=account_id
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied or account not found"
        )
    
    transactions = transaction_crud.get_by_account(
        db,
        account_id=account_id,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    return transactions


@router.get("/summary/{account_id}", response_model=TransactionSummaryResponse)
async def get_account_transaction_summary(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_id: str,
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter")
):
    """Get transaction summary for a specific account."""
    # Verify user owns the account
    account = account_crud.get_by_user_and_id(
        db, user_id=current_user_id, account_id=account_id
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied or account not found"
        )
    
    summary = transaction_crud.get_transactions_summary(
        db,
        user_id=current_user_id,
        account_id=account_id,
        start_date=start_date,
        end_date=end_date
    )
    return summary


@router.get("/health")
async def transactions_health():
    """Health check for transactions service."""
    return {
        "status": "healthy",
        "service": "transactions",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "transaction_management",
            "transaction_summaries",
            "filtering_and_search",
            "bulk_operations"
        ]
    }
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.user import get_current_user_id
from app.crud.account import account_crud
from app.schemas.account import (
    AccountCreate,
    AccountUpdate, 
    AccountResponse,
    AccountSummaryResponse
)

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def get_accounts(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    skip: int = Query(0, description="Skip records"),
    limit: int = Query(100, description="Limit records"),
    include_inactive: bool = Query(False, description="Include inactive accounts")
):
    """Get accounts for the current user."""
    try:
        accounts = account_crud.get_multi_by_user(
            db,
            user_id=current_user_id,
            skip=skip,
            limit=limit,
            include_inactive=include_inactive
        )
        # Explicitly convert ORM objects to Pydantic models for correct enum handling
        from app.schemas.account import AccountResponse
        accounts_response = [AccountResponse.model_validate(acc, from_attributes=True) for acc in accounts]
        total = account_crud.count_by_user(db, user_id=current_user_id)
        return {
            "accounts": accounts_response,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving accounts: {str(e)}"
        )


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_id: str
):
    """Get a specific account by ID."""
    account = account_crud.get_by_user_and_id(
        db, user_id=current_user_id, account_id=account_id
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    return account


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_data: AccountCreate
):
    """Create a new account."""
    try:
        # Convert Pydantic model to dict and add user_id
        account_dict = account_data.model_dump()  # Pydantic v2 syntax
        account_dict["user_id"] = current_user_id
        
        account = account_crud.create_from_dict(db, obj_in=account_dict)
        return account
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating account: {str(e)}"
        )


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_id: str,
    account_data: AccountUpdate
):
    """Update an existing account."""
    account = account_crud.get_by_user_and_id(
        db, user_id=current_user_id, account_id=account_id
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    try:
        # Only include non-None values in update
        update_dict = account_data.model_dump(exclude_unset=True)  # Pydantic v2 syntax
        updated_account = account_crud.update(db, db_obj=account, obj_in=update_dict)
        return updated_account
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating account: {str(e)}"
        )


@router.delete("/{account_id}")
async def delete_account(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_id: str
):
    """Delete an account (soft delete)."""
    account = account_crud.soft_delete(db, account_id=account_id, user_id=current_user_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    return {
        "message": "Account deleted successfully",
        "account_id": account_id,
        "deleted_at": datetime.utcnow().isoformat()
    }


@router.get("/{account_id}/summary", response_model=AccountSummaryResponse)
async def get_account_summary(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_id: str
):
    """Get account summary with performance metrics."""
    summary = account_crud.get_account_summary(
        db, account_id=account_id, user_id=current_user_id
    )
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    return summary


@router.get("/health")
async def accounts_health():
    """Health check for accounts service."""
    return {
        "status": "healthy",
        "service": "accounts",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "account_management",
            "account_summary",
            "multi_currency_support",
            "soft_delete"
        ]
    }
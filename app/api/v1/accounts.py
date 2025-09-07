from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user_id
from app.api.deps import CommonQueryParams
from app.crud.account import account_crud
from app.schemas.account import Account, AccountCreate, AccountUpdate
from app.models.enums import AccountType, AccountSubtype

router = APIRouter()


@router.get("/", response_model=List[Account])
async def get_accounts(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    commons: CommonQueryParams = Depends(),
    account_type: Optional[AccountType] = Query(None, description="Filter by account type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
):
    """
    Get all accounts for the current user.
    """
    filters = {"user_id": current_user_id}
    
    if account_type is not None:
        filters["type"] = account_type
    
    if is_active is not None:
        filters["is_active"] = is_active
    
    accounts = account_crud.get_multi_by_user(
        db=db,
        user_id=current_user_id,
        skip=commons.skip,
        limit=commons.limit,
        filters=filters
    )
    
    return accounts


@router.get("/{account_id}", response_model=Account)
async def get_account(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_id: str
):
    """
    Get a specific account by ID.
    """
    account = account_crud.get(db=db, id=account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Ensure user owns this account
    if str(account.user_id) != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this account"
        )
    
    return account


@router.post("/", response_model=Account)
async def create_account(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_in: AccountCreate
):
    """
    Create a new account.
    """
    # Add the current user ID to the account data
    account_data = account_in.dict()
    account_data["user_id"] = current_user_id
    
    account = account_crud.create(db=db, obj_in=account_data)
    return account


@router.put("/{account_id}", response_model=Account)
async def update_account(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_id: str,
    account_in: AccountUpdate
):
    """
    Update an existing account.
    """
    account = account_crud.get(db=db, id=account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Ensure user owns this account
    if str(account.user_id) != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this account"
        )
    
    account = account_crud.update(db=db, db_obj=account, obj_in=account_in)
    return account


@router.delete("/{account_id}")
async def delete_account(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_id: str
):
    """
    Delete an account (soft delete by setting is_active to False).
    """
    account = account_crud.get(db=db, id=account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Ensure user owns this account
    if str(account.user_id) != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this account"
        )
    
    # Soft delete by setting is_active to False
    account = account_crud.update(
        db=db, 
        db_obj=account, 
        obj_in={"is_active": False}
    )
    
    return {"message": "Account deactivated successfully"}


@router.get("/{account_id}/summary")
async def get_account_summary(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_id: str
):
    """
    Get account summary with basic analytics.
    """
    account = account_crud.get(db=db, id=account_id)
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    # Ensure user owns this account
    if str(account.user_id) != current_user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this account"
        )
    
    # TODO: Implement account summary calculations
    # This would include current balance, total holdings, etc.
    summary = {
        "account_id": account_id,
        "account_name": account.name,
        "account_type": account.type,
        "currency": account.currency,
        "total_value": 0.0,  # Calculate from holdings
        "holdings_count": 0,  # Count holdings
        "last_transaction_date": None,  # Get from transactions
        "performance_ytd": 0.0,  # Calculate YTD performance
    }
    
    return summary
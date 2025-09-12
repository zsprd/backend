from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.user import get_current_user_id
from app.crud.account import account_crud
from app.crud.audit_log import audit_log_crud
from app.schemas.account import (
    AccountCreate,
    AccountUpdate, 
    AccountResponse
)

router = APIRouter()


# ===================================================================
# Account CRUD Endpoints
# ===================================================================

@router.get("/", response_model=Dict[str, Any])
async def get_user_accounts(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    skip: int = Query(0, description="Skip records", ge=0),
    limit: int = Query(100, description="Limit records", ge=1, le=500),
    include_inactive: bool = Query(False, description="Include inactive accounts"),
    account_category: Optional[str] = Query(None, description="Filter by account category")
):
    """Get all accounts for the current user with pagination and filtering."""
    try:
        if account_category:
            accounts = account_crud.get_accounts_by_type(
                db,
                user_id=current_user_id,
                account_category=account_category,
                include_inactive=include_inactive
            )
            # Apply manual pagination for filtered results
            paginated_accounts = accounts[skip:skip + limit]
        else:
            paginated_accounts = account_crud.get_multi_by_user(
                db,
                user_id=current_user_id,
                skip=skip,
                limit=limit,
                include_inactive=include_inactive
            )
        
        # Convert to response models
        accounts_response = [
            AccountResponse.model_validate(acc, from_attributes=True) 
            for acc in paginated_accounts
        ]
        
        total = account_crud.count_by_user(db, user_id=current_user_id)
        
        return {
            "accounts": accounts_response,
            "total": total,
            "skip": skip,
            "limit": limit,
            "count": len(accounts_response)
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
    
    return AccountResponse.model_validate(account, from_attributes=True)


@router.post("/", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_data: AccountCreate
):
    """Create a new account for the current user."""
    try:
        # Add user_id to the account data
        create_data = account_data.model_dump()
        create_data["user_id"] = current_user_id
        
        account = account_crud.create_from_dict(db, obj_in=create_data)
        
        # Log the creation
        audit_log_crud.log_user_action(
            db,
            user_id=current_user_id,
            action="create",
            target_category="account",
            target_id=str(account.id),
            description=f"Created account: {account.name}"
        )
        
        return AccountResponse.model_validate(account, from_attributes=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating account: {str(e)}"
        )


@router.put("/{account_id}", response_model=AccountResponse)
async def update_account(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_id: str,
    account_update: AccountUpdate
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
        # Store old values for audit
        old_values = {
            "name": account.name,
            "official_name": account.official_name,
            "account_category": account.account_category
        }
        
        updated_account = account_crud.update(
            db, db_obj=account, obj_in=account_update
        )
        
        # Log the update
        audit_log_crud.log_data_change(
            db,
            user_id=current_user_id,
            action="update",
            target_category="account",
            target_id=account_id,
            old_values=old_values,
            new_values=account_update.model_dump(exclude_unset=True)
        )
        
        return AccountResponse.model_validate(updated_account, from_attributes=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating account: {str(e)}"
        )


@router.delete("/{account_id}")
async def delete_account(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_id: str,
    hard_delete: bool = Query(False, description="Permanently delete account")
):
    """Delete or deactivate an account."""
    account = account_crud.get_by_user_and_id(
        db, user_id=current_user_id, account_id=account_id
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    try:
        if hard_delete:
            # Permanent deletion (use with caution)
            account_crud.delete(db, id=account_id)
            action = "delete"
            message = "Account permanently deleted"
        else:
            # Soft delete (recommended)
            account_crud.soft_delete(db, account_id=account_id, user_id=current_user_id)
            action = "deactivate"
            message = "Account deactivated"
        
        # Log the action
        audit_log_crud.log_user_action(
            db,
            user_id=current_user_id,
            action=action,
            target_category="account",
            target_id=account_id,
            description=f"{action.title()} account: {account.name}"
        )
        
        return {
            "message": message,
            "account_id": account_id,
            "deleted_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting account: {str(e)}"
        )


# ===================================================================
# Account Summary & Analytics Endpoints
# ===================================================================

@router.get("/{account_id}/summary")
async def get_account_summary(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_id: str,
    base_currency: str = Query("USD", description="Base currency for calculations")
):
    """Get comprehensive account summary with holdings and performance."""
    account = account_crud.get_by_user_and_id(
        db, user_id=current_user_id, account_id=account_id
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found"
        )
    
    try:
        summary = account_crud.get_account_summary(
            db, account_id=account_id, user_id=current_user_id
        )
        
        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Account summary not available"
            )
        
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving account summary: {str(e)}"
        )


@router.get("/portfolio/overview")
async def get_portfolio_overview(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    base_currency: str = Query("USD", description="Base currency for calculations")
):
    """Get comprehensive portfolio overview across all user accounts."""
    try:
        overview = account_crud.get_portfolio_overview(
            db, user_id=current_user_id, base_currency=base_currency
        )
        return overview
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving portfolio overview: {str(e)}"
        )


@router.get("/with-balances")
async def get_accounts_with_balances(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    currency: str = Query("USD", description="Currency for balance calculations")
):
    """Get all accounts with current balance calculations."""
    try:
        accounts_with_balances = account_crud.get_accounts_with_balances(
            db, user_id=current_user_id, currency=currency
        )
        return {
            "accounts": accounts_with_balances,
            "total": len(accounts_with_balances),
            "currency": currency
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving accounts with balances: {str(e)}"
        )


# ===================================================================
# Account Management Endpoints
# ===================================================================


@router.get("/search")
async def search_accounts(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    q: str = Query(..., description="Search term", min_length=2),
    limit: int = Query(20, description="Maximum results", ge=1, le=100)
):
    """Search user accounts by name or official name."""
    try:
        accounts = account_crud.search_accounts(
            db, user_id=current_user_id, search_term=q, limit=limit
        )
        
        accounts_response = [
            AccountResponse.model_validate(acc, from_attributes=True) 
            for acc in accounts
        ]
        
        return {
            "accounts": accounts_response,
            "query": q,
            "count": len(accounts_response)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching accounts: {str(e)}"
        )


@router.get("/statistics")
async def get_account_statistics(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Get comprehensive account statistics for the current user."""
    try:
        stats = account_crud.get_user_account_statistics(db, user_id=current_user_id)
        return stats
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving account statistics: {str(e)}"
        )


@router.post("/bulk-sync")
async def bulk_sync_accounts(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_ids: List[str]
):
    """Trigger bulk synchronization for multiple accounts."""
    if not account_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No account IDs provided"
        )
    
    try:
        # Update sync status for all accounts
        updated_count = account_crud.bulk_update_sync_status(
            db, user_id=current_user_id, account_ids=account_ids, sync_status="syncing"
        )
        
        # Log bulk sync
        audit_log_crud.log_user_action(
            db,
            user_id=current_user_id,
            action="bulk_sync",
            target_category="account",
            description=f"Initiated bulk sync for {len(account_ids)} accounts",
            metadata={"account_ids": account_ids}
        )
        
        # TODO: Trigger actual bulk sync jobs here
        
        return {
            "message": "Bulk sync initiated",
            "accounts_updated": updated_count,
            "account_ids": account_ids,
            "sync_status": "syncing"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initiating bulk sync: {str(e)}"
        )


# ===================================================================
# Health Check
# ===================================================================

@router.get("/health")
async def accounts_health():
    """Health check for accounts service."""
    return {
        "status": "healthy",
        "service": "accounts",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "account_management",
            "portfolio_overview",
            "sync_integration",
            "search_and_analytics"
        ]
    }
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime, date

from app.core.database import get_db
from app.core.user import get_current_user_id
from app.crud.holding import holding_crud
from app.crud.account import account_crud
from app.schemas.holding import (
    HoldingCreate,
    HoldingUpdate,
    HoldingResponse,
    HoldingSummaryResponse
)

router = APIRouter()


@router.get("/", response_model=Dict[str, Any])
async def get_holdings(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_ids: Optional[str] = Query(None, description="Comma-separated account IDs"),
    as_of_date: Optional[date] = Query(None, description="Holdings as of specific date"),
    skip: int = Query(0, description="Skip records"),
    limit: int = Query(100, description="Limit records")
):
    """Get holdings for the current user across accounts."""
    try:
        account_id_list = None
        if account_ids:
            account_id_list = [id.strip() for id in account_ids.split(",")]
        
        holdings = holding_crud.get_by_user_accounts(
            db,
            user_id=current_user_id,
            account_ids=account_id_list,
            as_of_date=as_of_date
        )
        
        # Calculate summary
        from decimal import Decimal
        total_market_value = sum(h.market_value or Decimal('0') for h in holdings)
        total_cost_basis = sum(h.cost_basis_total or Decimal('0') for h in holdings)
        
        return {
            "holdings": holdings[skip:skip+limit],
            "summary": {
                "total_holdings": len(holdings),
                "total_market_value": float(total_market_value),
                "total_cost_basis": float(total_cost_basis),
                "unrealized_gain_loss": float(total_market_value - total_cost_basis)
            },
            "skip": skip,
            "limit": limit
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving holdings: {str(e)}"
        )


@router.get("/{holding_id}", response_model=HoldingResponse)
async def get_holding(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    holding_id: str
):
    """Get a specific holding by ID."""
    holding = holding_crud.get(db, id=holding_id)
    
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holding not found"
        )
    
    # Verify user owns the account for this holding
    account = account_crud.get_by_user_and_id(
        db, user_id=current_user_id, account_id=holding.account_id
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return holding


@router.post("/", response_model=HoldingResponse, status_code=status.HTTP_201_CREATED)
async def create_holding(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    holding_data: HoldingCreate
):
    """Create a new holding."""
    # Verify user owns the account
    account = account_crud.get_by_user_and_id(
        db, user_id=current_user_id, account_id=str(holding_data.account_id)
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied or account not found"
        )
    
    try:
        holding = holding_crud.create(db, obj_in=holding_data)
        return holding
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating holding: {str(e)}"
        )


@router.put("/{holding_id}", response_model=HoldingResponse)
async def update_holding(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    holding_id: str,
    holding_data: HoldingUpdate
):
    """Update an existing holding."""
    holding = holding_crud.get(db, id=holding_id)
    
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holding not found"
        )
    
    # Verify user owns the account
    account = account_crud.get_by_user_and_id(
        db, user_id=current_user_id, account_id=holding.account_id
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        updated_holding = holding_crud.update(db, db_obj=holding, obj_in=holding_data)
        return updated_holding
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating holding: {str(e)}"
        )


@router.delete("/{holding_id}")
async def delete_holding(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    holding_id: str
):
    """Delete a holding."""
    holding = holding_crud.get(db, id=holding_id)
    
    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Holding not found"
        )
    
    # Verify user owns the account
    account = account_crud.get_by_user_and_id(
        db, user_id=current_user_id, account_id=holding.account_id
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    try:
        holding_crud.delete(db, id=holding_id)
        return {
            "message": "Holding deleted successfully",
            "holding_id": holding_id,
            "deleted_at": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting holding: {str(e)}"
        )


@router.get("/accounts/{account_id}", response_model=List[HoldingResponse])
async def get_account_holdings(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_id: str,
    as_of_date: Optional[date] = Query(None, description="Holdings as of specific date")
):
    """Get holdings for a specific account."""
    # Verify user owns the account
    account = account_crud.get_by_user_and_id(
        db, user_id=current_user_id, account_id=account_id
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied or account not found"
        )
    
    holdings = holding_crud.get_by_account(db, account_id=account_id, as_of_date=as_of_date)
    return holdings


@router.get("/summary/{account_id}", response_model=HoldingSummaryResponse)
async def get_account_holdings_summary(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    account_id: str,
    base_currency: str = Query("USD", description="Base currency")
):
    """Get holdings summary for a specific account."""
    # Verify user owns the account
    account = account_crud.get_by_user_and_id(
        db, user_id=current_user_id, account_id=account_id
    )
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied or account not found"
        )
    
    summary = holding_crud.get_holdings_summary(
        db, account_id=account_id, base_currency=base_currency
    )
    return summary


@router.get("/health")
async def holdings_health():
    """Health check for holdings service."""
    return {
        "status": "healthy",
        "service": "holdings",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "holdings_management",
            "portfolio_summaries",
            "asset_allocation",
            "historical_snapshots"
        ]
    }

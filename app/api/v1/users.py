from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user_id, get_current_user
from app.crud.user import user_crud
from app.crud.account import account_crud
from app.schemas.user import User, UserUpdate, UserPreferences, UserProfile, UserStats
from app.models.user import User as UserModel

router = APIRouter()


@router.get("/profile", response_model=UserProfile)
async def get_user_profile(
    *,
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get current user's profile information.
    """
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        profile_image=current_user.profile_image,
        country=current_user.country,
        base_currency=current_user.base_currency,
        theme_preference=current_user.theme_preference,
        is_verified=current_user.is_verified,
        is_premium=current_user.is_premium,
        member_since=current_user.created_at
    )


@router.put("/profile", response_model=User)
async def update_user_profile(
    *,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    user_update: UserUpdate
):
    """
    Update current user's profile information.
    """
    updated_user = user_crud.update(
        db=db, 
        db_obj=current_user, 
        obj_in=user_update
    )
    return updated_user


@router.put("/preferences", response_model=User)
async def update_user_preferences(
    *,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
    preferences: UserPreferences
):
    """
    Update user preferences (currency, theme, notifications, etc.).
    """
    updated_user = user_crud.update(
        db=db,
        db_obj=current_user,
        obj_in=preferences.dict(exclude_unset=True)
    )
    return updated_user


@router.get("/stats", response_model=UserStats)
async def get_user_stats(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get user statistics including account counts and portfolio metrics.
    """
    # Count accounts
    total_accounts = account_crud.count_by_user(db, user_id=current_user_id)
    active_accounts = account_crud.count_active_by_user(db, user_id=current_user_id)
    
    # TODO: Add actual calculations for holdings, transactions, portfolio value
    # These would require implementing the corresponding CRUD operations
    
    stats = UserStats(
        total_accounts=total_accounts,
        total_holdings=0,  # TODO: Calculate from holdings table
        total_transactions=0,  # TODO: Calculate from transactions table
        portfolio_value=0.0,  # TODO: Calculate current portfolio value
        last_activity=None,  # TODO: Get from recent transactions/activities
        days_active=0  # TODO: Calculate days since registration with activity
    )
    
    return stats


@router.post("/verify-email")
async def verify_email(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Mark user's email as verified.
    In a production system, this would require an email verification token.
    """
    user = user_crud.verify_email(db, user_id=current_user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "message": "Email verified successfully",
        "user_id": current_user_id,
        "email_verified": True
    }


@router.post("/deactivate")
async def deactivate_account(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Deactivate user account (soft delete).
    This sets is_active to False but preserves all data.
    """
    user = user_crud.deactivate_user(db, user_id=current_user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "message": "Account deactivated successfully",
        "user_id": current_user_id,
        "status": "deactivated"
    }


@router.post("/reactivate")
async def reactivate_account(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Reactivate a deactivated user account.
    """
    user = user_crud.activate_user(db, user_id=current_user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "message": "Account reactivated successfully",
        "user_id": current_user_id,
        "status": "active"
    }


@router.get("/dashboard-summary")
async def get_dashboard_summary(
    *,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user)
):
    """
    Get user dashboard summary with key metrics.
    """
    # Get basic user info
    user_stats = await get_user_stats(db=db, current_user_id=str(current_user.id))
    
    # Get recent accounts
    recent_accounts = account_crud.get_active_accounts_by_user(
        db, user_id=str(current_user.id), limit=5
    )
    
    summary = {
        "user": {
            "id": str(current_user.id),
            "name": current_user.full_name or current_user.first_name,
            "email": current_user.email,
            "base_currency": current_user.base_currency,
            "is_premium": current_user.is_premium,
            "member_since": current_user.created_at.isoformat()
        },
        "stats": user_stats,
        "recent_accounts": [
            {
                "id": str(account.id),
                "name": account.name,
                "type": account.type,
                "currency": account.currency
            } for account in recent_accounts
        ],
        "quick_actions": [
            {"label": "Add Account", "action": "create_account"},
            {"label": "Import Transactions", "action": "import_transactions"},
            {"label": "View Analytics", "action": "view_analytics"},
            {"label": "Generate Report", "action": "generate_report"}
        ]
    }
    
    return summary


@router.get("/health")
async def users_health():
    """
    Health check for users service.
    """
    return {
        "status": "healthy",
        "service": "users",
        "features": [
            "profile_management",
            "preferences",
            "user_stats",
            "dashboard_summary"
        ]
    }
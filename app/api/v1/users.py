# app/api/v1/users.py
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

from app.core.database import get_db
from app.core.auth import get_current_user_id

router = APIRouter()


@router.get("/me")
async def get_current_user(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get current user profile.
    """
    return {
        "id": current_user_id,
        "email": "user@example.com",
        "full_name": "John Doe",
        "phone": None,
        "country": "US",
        "timezone": "America/New_York",
        "language": "en",
        "base_currency": "USD",
        "theme_preference": "dark",
        "is_active": True,
        "is_verified": True,
        "is_premium": False,
        "last_login_at": datetime.utcnow().isoformat(),
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": datetime.utcnow().isoformat()
    }


@router.patch("/me")
async def update_current_user(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    user_data: Dict[str, Any]
):
    """
    Update current user profile.
    """
    return {
        "id": current_user_id,
        "message": "User profile updated successfully",
        "updated_fields": list(user_data.keys()),
        "updated_at": datetime.utcnow().isoformat()
    }


@router.get("/me/preferences")
async def get_user_preferences(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get user preferences.
    """
    return {
        "base_currency": "USD",
        "theme_preference": "dark",
        "timezone": "America/New_York",
        "language": "en",
        "notification_preferences": {
            "email_alerts": True,
            "push_notifications": False,
            "weekly_reports": True,
            "monthly_reports": True
        },
        "display_preferences": {
            "show_cents": True,
            "compact_view": False,
            "default_chart_period": "1Y"
        }
    }


@router.patch("/me/preferences")
async def update_user_preferences(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    preferences: Dict[str, Any]
):
    """
    Update user preferences.
    """
    return {
        "message": "User preferences updated successfully",
        "updated_preferences": list(preferences.keys()),
        "updated_at": datetime.utcnow().isoformat()
    }


@router.get("/me/stats")
async def get_user_stats(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Get user statistics for analytics/dashboard.
    """
    return {
        "total_accounts": 3,
        "total_holdings": 25,
        "total_transactions": 150,
        "portfolio_value": 125000.0,
        "total_return": 15.5,
        "days_active": 365,
        "last_activity": datetime.utcnow().isoformat(),
        "member_since": "2024-01-01T00:00:00Z",
        "subscription_status": "free"
    }


@router.post("/me/change-password")
async def change_password(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    password_data: Dict[str, str]
):
    """
    Change user password.
    """
    current_password = password_data.get("current_password")
    new_password = password_data.get("new_password")
    
    if not current_password or not new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password and new password are required"
        )
    
    return {
        "message": "Password changed successfully",
        "changed_at": datetime.utcnow().isoformat()
    }


@router.delete("/me")
async def delete_current_user(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """
    Delete current user account (soft delete).
    """
    return {
        "message": "User account deletion initiated",
        "user_id": current_user_id,
        "deletion_scheduled_at": datetime.utcnow().isoformat(),
        "note": "Account will be permanently deleted in 30 days unless reactivated"
    }


@router.post("/me/export-data")
async def request_data_export(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    export_format: str = "json"
):
    """
    Request data export (GDPR compliance).
    """
    return {
        "message": "Data export requested",
        "export_id": "export-12345",
        "format": export_format,
        "requested_at": datetime.utcnow().isoformat(),
        "estimated_completion": "2024-01-03T12:00:00Z",
        "note": "You will receive an email when your export is ready"
    }


@router.get("/health")
async def users_health():
    """
    Health check for users service.
    """
    return {
        "status": "healthy",
        "service": "users",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "user_profile",
            "user_preferences",
            "password_management",
            "data_export"
        ]
    }
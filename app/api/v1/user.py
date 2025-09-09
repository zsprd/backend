from typing import Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.models.user import User
from app.crud.user import user_crud
from app.core.database import get_db
from app.core.user import get_current_user

router = APIRouter()


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    base_currency: str
    timezone: str
    language: str
    theme_preference: str
    is_verified: bool
    is_premium: bool
    is_active: bool
    created_at: str
    last_login_at: Optional[str]


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    base_currency: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    theme_preference: Optional[str] = None


@router.get("/me", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get current user profile."""
    return UserProfileResponse(**current_user.to_dict())


@router.put("/me", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
async def update_user_profile(
    *,
    db: Session = Depends(get_db),
    request: UserProfileUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update user profile."""
    update_data = request.dict(exclude_unset=True)
    updated_user = user_crud.update_profile(db, user=current_user, update_data=update_data)
    return UserProfileResponse(**updated_user.to_dict())

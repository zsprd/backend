from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.user import user_crud
from app.models.core.user import User
from app.schemas.user import UserProfileResponse, UserProfileUpdate

router = APIRouter()


@router.get("/me", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
async def get_current_user_profile(current_user: User = Depends(user_crud.get_current_user)):
    """Get current user profile."""
    return UserProfileResponse(**current_user.to_dict())


@router.put("/me", response_model=UserProfileResponse, status_code=status.HTTP_200_OK)
async def update_user_profile(
    *,
    db: Session = Depends(get_db),
    request: UserProfileUpdate,
    current_user: User = Depends(user_crud.get_current_user),
):
    """Update user profile."""
    update_data = request.model_dump(exclude_unset=True)
    updated_user = user_crud.update_profile(db, user=current_user, update_data=update_data)
    return UserProfileResponse(**updated_user.to_dict())

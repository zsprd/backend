import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.rate_limiter import rate_limit
from app.core.config import settings
from app.core.database import get_async_db
from app.user.accounts import schema
from app.user.accounts.crud import CRUDUserAccount
from app.user.accounts.model import UserAccount
from app.user.accounts.service import UserError, UserService

logger = logging.getLogger(__name__)
router = APIRouter()


def get_user_service(db: AsyncSession = Depends(get_async_db)) -> UserService:
    """Get user service with injected repository."""
    return UserService(user_repo=CRUDUserAccount(db))


@router.get(
    "/me",
    response_model=schema.UserAccountRead,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Retrieve the authenticated user's profile information including email, name, preferences, and account status.",
)
async def get_current_user_profile(
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> schema.UserAccountRead:
    """Get current user's profile information."""
    try:
        logger.info(
            "Profile requested", extra={"user_id": current_user.id, "action": "get_profile"}
        )
        user = await service.get_user_profile(current_user.id)
        logger.info(
            "Profile data retrieved successfully",
            extra={"user_id": current_user.id, "action": "get_profile"},
        )
        return user
    except UserError as e:
        logger.error(f"Failed to get profile: {str(e)}")
        raise handle_user_error(e)


@router.patch(
    "/me",
    response_model=schema.UserAccountRead,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    description="Update the authenticated user's profile information such as name, language, country, and currency preferences.",
)
@rate_limit(settings.RATE_LIMIT_UPDATE)
async def update_current_user_profile(
    profile_update: schema.UserAccountUpdate,
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> schema.UserAccountRead:
    """Update current user's profile information."""
    try:
        logger.info(
            "Profile update requested",
            extra={"user_id": current_user.id, "action": "update_profile"},
        )
        updated_user = await service.update_user_profile(current_user, profile_update)
        logger.info(
            "Profile updated successfully",
            extra={"user_id": current_user.id, "action": "update_profile"},
        )
        return updated_user
    except UserError as e:
        logger.error(f"Service error updating profile: {str(e)}")
        raise handle_user_error(e)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user account",
    description="Permanently delete the current user's account and all associated data.",
)
async def delete_user_account(
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> Response:
    """Delete current user's account (soft delete for MVP)."""
    try:
        logger.info(
            "Account deletion requested",
            extra={"user_id": current_user.id, "action": "delete_account"},
        )
        await service.delete_user_account(current_user)
        logger.info(
            "Account deleted successfully",
            extra={"user_id": current_user.id, "action": "delete_account"},
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except UserError as e:
        logger.error(f"Account deletion failed: {str(e)}")
        raise handle_user_error(e)


@router.post(
    "/me/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change user password",
    description="Change the authenticated user's password with current password verification.",
)
@rate_limit(settings.RATE_LIMIT_PASSWORD)
async def change_user_password(
    password_update: schema.UserAccountPasswordUpdate,
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    service: Annotated[UserService, Depends(get_user_service)],
) -> Response:
    """Change current user's password."""
    try:
        logger.info(
            "Password change requested",
            extra={"user_id": current_user.id, "action": "change_password"},
        )
        await service.change_password(current_user, password_update)
        logger.info(
            "Password changed successfully",
            extra={"user_id": current_user.id, "action": "change_password"},
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except UserError as e:
        logger.error(f"Service error changing password: {str(e)}")
        raise handle_user_error(e)


def handle_user_error(e: UserError) -> HTTPException:
    """Convert UserError to appropriate HTTP status code."""
    error_msg = str(e).lower()

    # Expired token/session errors -> 410 Gone
    if any(phrase in error_msg for phrase in ["expired token", "expired session", "has expired"]):
        return HTTPException(status_code=status.HTTP_410_GONE, detail=str(e))

    # Not found errors -> 404 Not Found
    if "not found" in error_msg:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    # Invalid credentials -> 401 Unauthorized
    if "invalid credentials" in error_msg:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    # Email not verified -> 403 Forbidden
    if "not verified" in error_msg:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    # Account locked -> 423 Locked
    if "temporarily locked" in error_msg:
        return HTTPException(status_code=status.HTTP_423_LOCKED, detail=str(e))

    # Already exists -> 409 Conflict
    if "already exists" in error_msg:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    if "unexpected error" in error_msg:
        return HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

    # Default to 400 Bad Request
    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

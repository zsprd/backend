import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.rate_limiter import rate_limit
from app.core.config import settings
from app.core.database import get_async_db
from app.user.accounts.model import UserAccount
from app.user.accounts.schemas import UserAccountPasswordUpdate, UserAccountRead, UserAccountUpdate
from app.user.accounts.service import UserAccountService, UserError

router = APIRouter()
logger = logging.getLogger(__name__)


def get_user_service(db: Annotated[AsyncSession, Depends(get_async_db)]) -> UserAccountService:
    """Dependency injection for user service."""
    return UserAccountService(db)


@router.get(
    "/me",
    response_model=UserAccountRead,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Retrieve the authenticated user's profile information.",
)
async def get_current_user_profile(
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    service: Annotated[UserAccountService, Depends(get_user_service)],
) -> UserAccountRead:
    """Get current user's profile information."""
    try:
        logger.info("Profile requested", extra={"user_id": current_user.id})
        user = await service.get_user_profile(current_user.id)
        logger.info("Profile retrieved successfully", extra={"user_id": current_user.id})
        return user
    except UserError as e:
        logger.error(f"Failed to get profile: {str(e)}")
        raise handle_user_error(e)


@router.patch(
    "/me",
    response_model=UserAccountRead,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    description="Update the authenticated user's profile information.",
)
@rate_limit(settings.RATE_LIMIT_UPDATE)
async def update_current_user_profile(
    profile_update: UserAccountUpdate,
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    service: Annotated[UserAccountService, Depends(get_user_service)],
) -> UserAccountRead:
    """Update current user's profile information."""
    try:
        logger.info("Profile update requested", extra={"user_id": current_user.id})
        updated_user = await service.update_user_profile(current_user, profile_update)
        logger.info("Profile updated successfully", extra={"user_id": current_user.id})
        return updated_user
    except UserError as e:
        logger.error(f"Error updating profile: {str(e)}")
        raise handle_user_error(e)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user account",
    description="Permanently delete the current user's account.",
)
async def delete_user_account(
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    service: Annotated[UserAccountService, Depends(get_user_service)],
) -> Response:
    """Delete current user's account."""
    try:
        logger.info("Account deletion requested", extra={"user_id": current_user.id})
        await service.delete_user_account(current_user)
        logger.info("Account deleted successfully", extra={"user_id": current_user.id})
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except UserError as e:
        logger.error(f"Account deletion failed: {str(e)}")
        raise handle_user_error(e)


@router.post(
    "/me/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change user password",
    description="Change the authenticated user's password.",
)
@rate_limit(settings.RATE_LIMIT_PASSWORD)
async def change_user_password(
    password_update: UserAccountPasswordUpdate,
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    service: Annotated[UserAccountService, Depends(get_user_service)],
) -> Response:
    """Change current user's password."""
    try:
        logger.info("Password change requested", extra={"user_id": current_user.id})
        await service.change_password(current_user, password_update)
        logger.info("Password changed successfully", extra={"user_id": current_user.id})
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except UserError as e:
        logger.error(f"Error changing password: {str(e)}")
        raise handle_user_error(e)


def handle_user_error(e: UserError) -> HTTPException:
    """Convert UserError to appropriate HTTP status code."""
    error_msg = str(e).lower()

    if any(phrase in error_msg for phrase in ["expired", "has expired"]):
        return HTTPException(status_code=status.HTTP_410_GONE, detail=str(e))

    if "not found" in error_msg:
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if "invalid credentials" in error_msg or "incorrect" in error_msg:
        return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    if "not verified" in error_msg:
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))

    if "locked" in error_msg:
        return HTTPException(status_code=status.HTTP_423_LOCKED, detail=str(e))

    if "already exists" in error_msg:
        return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))

    if "invalid data" in error_msg:
        return HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

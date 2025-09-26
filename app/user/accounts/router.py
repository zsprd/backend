import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.core.dependencies import get_current_active_user, get_user_service
from app.user.accounts import schema
from app.user.accounts.model import UserAccount
from app.user.accounts.service import UserError, UserService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/me",
    response_model=schema.UserAccountRead,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Retrieve the authenticated user's profile information including email, name, preferences, and account status.",
)
async def get_current_user_profile(
    current_user: Annotated[UserAccount, Depends(get_current_active_user)],
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
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))


@router.patch(
    "/me",
    response_model=schema.UserAccountRead,
    status_code=status.HTTP_200_OK,
    summary="Update current user profile",
    description="Update the authenticated user's profile information such as name, language, country, and currency preferences.",
)
async def update_current_user_profile(
    profile_update: schema.UserAccountUpdate,
    current_user: Annotated[UserAccount, Depends(get_current_active_user)],
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
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/me/change-password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Change user password",
    description="Change the authenticated user's password with current password verification.",
)
async def change_user_password(
    password_update: schema.UserAccountPasswordUpdate,
    current_user: Annotated[UserAccount, Depends(get_current_active_user)],
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
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    summary="User service health check",
    description="Check the health status of the user service.",
    include_in_schema=False,
)
async def user_health_check() -> dict:
    """Health check endpoint."""
    logger.info("User service health check requested", extra={"action": "health_check"})
    return {"status": "ok", "service": "user"}

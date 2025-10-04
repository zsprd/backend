import logging
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.account.master.schemas import (
    AccountRead,
    AccountCreate,
    AccountUpdate,
)
from app.account.master.service import AccountError, AccountService
from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.user.master.model import User

router = APIRouter()
logger = logging.getLogger(__name__)


def get_portfolio_service(db: AsyncSession = Depends(get_db)) -> AccountService:
    """Get user service with injected repository."""
    return AccountService(db)


@router.get(
    "/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get user's account master",
    description="Retrieve all account master for the authenticated user with pagination and filtering options.",
)
async def get_user_accounts(
    user: User = Depends(get_current_user),
    service: AccountService = Depends(get_portfolio_service),
    limit: int = Query(100, ge=1, le=500, description="Limit records"),
    include_inactive: bool = Query(False, description="Include inactive master"),
    account_type: Optional[str] = Query(None, description="Filter by account type"),
) -> Dict[str, Any]:
    """Get all account master for the current user with pagination and filtering."""
    try:
        logger.info(
            "Portfolio master requested",
            extra={
                "user_id": user.id,
                "limit": limit,
                "include_inactive": include_inactive,
                "account_type": account_type,
                "action": "get_accounts",
            },
        )

        if account_type:
            # Use type filtering if specified
            accounts = await service.get_accounts_by_type(
                user_id=user.id,
                account_type=account_type,
                include_inactive=include_inactive,
            )
            # Apply manual pagination for filtered results
            paginated_accounts = accounts[:limit]
        else:
            # Use regular pagination
            paginated_accounts = await service.get_user_accounts(
                user_id=user.id, limit=limit, include_inactive=include_inactive
            )

        # Get total count for pagination info
        total = await service.get_account_count(user.id, include_inactive)

        logger.info(
            "Portfolio master retrieved successfully",
            extra={
                "user_id": user.id,
                "count": len(paginated_accounts),
                "total": total,
                "action": "get_accounts",
            },
        )

        return {
            "master": paginated_accounts,
            "total": total,
            "limit": limit,
            "count": len(paginated_accounts),
        }

    except AccountError as e:
        logger.error(f"Portfolio account service error: {str(e)}")
        raise handle_portfolio_account_error(e)


@router.get(
    "/{account_id}",
    response_model=AccountRead,
    status_code=status.HTTP_200_OK,
    summary="Get specific account account",
    description="Retrieve a specific account account by ID for the authenticated user.",
)
async def get_account(
    account_id: UUID,
    user: User = Depends(get_current_user),
    service: AccountService = Depends(get_portfolio_service),
) -> AccountRead:
    """Get a specific account account by ID."""
    try:
        logger.info(
            "Portfolio account requested",
            extra={"user_id": user.id, "account_id": account_id, "action": "get_account"},
        )

        account = await service.get_account_by_id(user.id, account_id)

        logger.info(
            "Portfolio account retrieved successfully",
            extra={"user_id": user.id, "account_id": account_id, "action": "get_account"},
        )

        return account

    except AccountError as e:
        logger.error(f"Portfolio account service error: {str(e)}")
        raise handle_portfolio_account_error(e)


@router.post(
    "/",
    response_model=AccountRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create account account",
    description="Create a new account account for the authenticated user.",
)
async def create_account(
    payload: AccountCreate,
    user: User = Depends(get_current_user),
    service: AccountService = Depends(get_portfolio_service),
) -> AccountRead:
    """Create a new account account for the current user."""
    try:
        logger.info(
            "Portfolio account creation requested",
            extra={
                "user_id": user.id,
                "account_name": payload.name,
                "account_type": payload.account_type,
                "action": "create_account",
            },
        )

        account = await service.create_account(user.id, payload)

        logger.info(
            "Portfolio account created successfully",
            extra={
                "user_id": user.id,
                "account_id": account.id,
                "account_name": account.name,
                "action": "create_account",
            },
        )

        return account

    except AccountError as e:
        logger.error(f"Portfolio account service error: {str(e)}")
        raise handle_portfolio_account_error(e)


@router.patch(
    "/{account_id}",
    response_model=AccountRead,
    status_code=status.HTTP_200_OK,
    summary="Update account account",
    description="Update a specific account account for the authenticated user.",
)
async def update_account(
    account_id: UUID,
    payload: AccountUpdate,
    user: User = Depends(get_current_user),
    service: AccountService = Depends(get_portfolio_service),
) -> AccountRead:
    """Update a specific account account."""
    try:
        logger.info(
            "Portfolio account update requested",
            extra={
                "user_id": user.id,
                "account_id": account_id,
                "action": "update_account",
            },
        )

        account = await service.update_account(user.id, account_id, payload)

        logger.info(
            "Portfolio account updated successfully",
            extra={
                "user_id": user.id,
                "account_id": account_id,
                "action": "update_account",
            },
        )

        return account

    except AccountError as e:
        logger.error(f"Portfolio account service error: {str(e)}")
        raise handle_portfolio_account_error(e)


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate account account",
    description="Deactivate (soft delete) a specific account account for the authenticated user.",
)
async def deactivate_account(
    account_id: UUID,
    user: User = Depends(get_current_user),
    service: AccountService = Depends(get_portfolio_service),
):
    """Deactivate a specific account account (soft delete)."""
    try:
        logger.info(
            "Portfolio account deactivation requested",
            extra={
                "user_id": user.id,
                "account_id": account_id,
                "action": "deactivate_account",
            },
        )

        await service.deactivate_account(user.id, account_id)

        logger.info(
            "Portfolio account deactivated successfully",
            extra={
                "user_id": user.id,
                "account_id": account_id,
                "action": "deactivate_account",
            },
        )

    except AccountError as e:
        logger.error(f"Portfolio account service error: {str(e)}")
        raise handle_portfolio_account_error(e)


@router.get(
    "/statistics/overview",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get account statistics",
    description="Get comprehensive statistics for the user's account master.",
)
async def get_account_statistics(
    user: User = Depends(get_current_user),
    service: AccountService = Depends(get_portfolio_service),
) -> Dict[str, Any]:
    """Get comprehensive account statistics for the current user."""
    try:
        logger.info(
            "Portfolio account statistics requested",
            extra={"user_id": user.id, "action": "get_statistics"},
        )

        stats = await service.get_account_statistics(user.id)

        logger.info(
            "Portfolio account statistics retrieved successfully",
            extra={"user_id": user.id, "action": "get_statistics"},
        )

        return stats

    except AccountError as e:
        logger.error(f"Portfolio account service error: {str(e)}")
        raise handle_portfolio_account_error(e)


@router.get(
    "/search",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Search account master",
    description="Search account master by name for the authenticated user.",
)
async def search_accounts(
    user: User = Depends(get_current_user),
    service: AccountService = Depends(get_portfolio_service),
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
) -> Dict[str, Any]:
    """Search account master by name."""
    try:
        logger.info(
            "Portfolio account search requested",
            extra={"user_id": user.id, "query": q, "action": "search_accounts"},
        )

        accounts = await service.search_accounts(user.id, q, limit)

        logger.info(
            "Portfolio account search completed",
            extra={
                "user_id": user.id,
                "query": q,
                "results_count": len(accounts),
                "action": "search_accounts",
            },
        )

        return {
            "master": accounts,
            "query": q,
            "count": len(accounts),
        }

    except AccountError as e:
        logger.error(f"Portfolio account service error: {str(e)}")
        raise handle_portfolio_account_error(e)


def handle_portfolio_account_error(e: AccountError) -> HTTPException:
    """Convert PortfolioAccountError to appropriate HTTPException."""
    error_message = str(e)

    if "not found" in error_message.lower():
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
    elif "access denied" in error_message.lower() or "forbidden" in error_message.lower():
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_message)
    else:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)

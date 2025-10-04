import logging
from typing import Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.portfolio.master.schemas import (
    PortfolioMasterRead,
    PortfolioMasterCreate,
    PortfolioMasterUpdate,
)
from app.portfolio.master.service import PortfolioError, PortfolioService
from app.user.accounts.model import UserAccount

router = APIRouter()
logger = logging.getLogger(__name__)


def get_portfolio_service(db: AsyncSession = Depends(get_db)) -> PortfolioService:
    """Get user service with injected repository."""
    return PortfolioService(db)


@router.get(
    "/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get user's portfolio master",
    description="Retrieve all portfolio master for the authenticated user with pagination and filtering options.",
)
async def get_user_accounts(
    user: UserAccount = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
    limit: int = Query(100, ge=1, le=500, description="Limit records"),
    include_inactive: bool = Query(False, description="Include inactive master"),
    account_type: Optional[str] = Query(None, description="Filter by account type"),
) -> Dict[str, Any]:
    """Get all portfolio master for the current user with pagination and filtering."""
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

    except PortfolioError as e:
        logger.error(f"Portfolio account service error: {str(e)}")
        raise handle_portfolio_account_error(e)


@router.get(
    "/{account_id}",
    response_model=PortfolioMasterRead,
    status_code=status.HTTP_200_OK,
    summary="Get specific portfolio account",
    description="Retrieve a specific portfolio account by ID for the authenticated user.",
)
async def get_account(
    account_id: UUID,
    user: UserAccount = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioMasterRead:
    """Get a specific portfolio account by ID."""
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

    except PortfolioError as e:
        logger.error(f"Portfolio account service error: {str(e)}")
        raise handle_portfolio_account_error(e)


@router.post(
    "/",
    response_model=PortfolioMasterRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create portfolio account",
    description="Create a new portfolio account for the authenticated user.",
)
async def create_account(
    payload: PortfolioMasterCreate,
    user: UserAccount = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioMasterRead:
    """Create a new portfolio account for the current user."""
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

    except PortfolioError as e:
        logger.error(f"Portfolio account service error: {str(e)}")
        raise handle_portfolio_account_error(e)


@router.patch(
    "/{account_id}",
    response_model=PortfolioMasterRead,
    status_code=status.HTTP_200_OK,
    summary="Update portfolio account",
    description="Update a specific portfolio account for the authenticated user.",
)
async def update_account(
    account_id: UUID,
    payload: PortfolioMasterUpdate,
    user: UserAccount = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
) -> PortfolioMasterRead:
    """Update a specific portfolio account."""
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

    except PortfolioError as e:
        logger.error(f"Portfolio account service error: {str(e)}")
        raise handle_portfolio_account_error(e)


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate portfolio account",
    description="Deactivate (soft delete) a specific portfolio account for the authenticated user.",
)
async def deactivate_account(
    account_id: UUID,
    user: UserAccount = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
):
    """Deactivate a specific portfolio account (soft delete)."""
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

    except PortfolioError as e:
        logger.error(f"Portfolio account service error: {str(e)}")
        raise handle_portfolio_account_error(e)


@router.get(
    "/statistics/overview",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get account statistics",
    description="Get comprehensive statistics for the user's portfolio master.",
)
async def get_account_statistics(
    user: UserAccount = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
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

    except PortfolioError as e:
        logger.error(f"Portfolio account service error: {str(e)}")
        raise handle_portfolio_account_error(e)


@router.get(
    "/search",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Search portfolio master",
    description="Search portfolio master by name for the authenticated user.",
)
async def search_accounts(
    user: UserAccount = Depends(get_current_user),
    service: PortfolioService = Depends(get_portfolio_service),
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
) -> Dict[str, Any]:
    """Search portfolio master by name."""
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

    except PortfolioError as e:
        logger.error(f"Portfolio account service error: {str(e)}")
        raise handle_portfolio_account_error(e)


def handle_portfolio_account_error(e: PortfolioError) -> HTTPException:
    """Convert PortfolioAccountError to appropriate HTTPException."""
    error_message = str(e)

    if "not found" in error_message.lower():
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
    elif "access denied" in error_message.lower() or "forbidden" in error_message.lower():
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_message)
    else:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)

import logging
from typing import Annotated, Any, Dict, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_async_db
from app.portfolio.accounts import schema
from app.portfolio.accounts.repository import PortfolioAccountRepository
from app.portfolio.accounts.service import PortfolioAccountError, PortfolioAccountService
from app.user.accounts.model import UserAccount

logger = logging.getLogger(__name__)
router = APIRouter()


def get_portfolio_service(db: AsyncSession = Depends(get_async_db)) -> PortfolioAccountService:
    """Get user service with injected repository."""
    return PortfolioAccountService(PortfolioAccountRepository(db))


def handle_portfolio_account_error(e: PortfolioAccountError) -> HTTPException:
    """Convert PortfolioAccountError to appropriate HTTPException."""
    error_message = str(e)

    if "not found" in error_message.lower():
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=error_message)
    elif "access denied" in error_message.lower() or "forbidden" in error_message.lower():
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=error_message)
    else:
        return HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_message)


@router.get(
    "/",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get user's portfolio accounts",
    description="Retrieve all portfolio accounts for the authenticated user with pagination and filtering options.",
)
async def get_user_accounts(
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    service: Annotated[PortfolioAccountService, Depends(get_portfolio_service)],
    limit: int = Query(100, ge=1, le=500, description="Limit records"),
    include_inactive: bool = Query(False, description="Include inactive accounts"),
    account_type: Optional[str] = Query(None, description="Filter by account type"),
) -> Dict[str, Any]:
    """Get all portfolio accounts for the current user with pagination and filtering."""
    try:
        logger.info(
            "Portfolio accounts requested",
            extra={
                "user_id": current_user.id,
                "limit": limit,
                "include_inactive": include_inactive,
                "account_type": account_type,
                "action": "get_accounts",
            },
        )

        if account_type:
            # Use type filtering if specified
            accounts = await service.get_accounts_by_type(
                user_id=current_user.id,
                account_type=account_type,
                include_inactive=include_inactive,
            )
            # Apply manual pagination for filtered results
            paginated_accounts = accounts[:limit]
        else:
            # Use regular pagination
            paginated_accounts = await service.get_user_accounts(
                user_id=current_user.id, limit=limit, include_inactive=include_inactive
            )

        # Get total count for pagination info
        total = await service.get_account_count(current_user.id, include_inactive)

        logger.info(
            "Portfolio accounts retrieved successfully",
            extra={
                "user_id": current_user.id,
                "count": len(paginated_accounts),
                "total": total,
                "action": "get_accounts",
            },
        )

        return {
            "accounts": paginated_accounts,
            "total": total,
            "limit": limit,
            "count": len(paginated_accounts),
        }

    except PortfolioAccountError as e:
        logger.error(f"Portfolio account service error: {str(e)}")
        raise handle_portfolio_account_error(e)


@router.get(
    "/{account_id}",
    response_model=schema.PortfolioAccountRead,
    status_code=status.HTTP_200_OK,
    summary="Get specific portfolio account",
    description="Retrieve a specific portfolio account by ID for the authenticated user.",
)
async def get_account(
    account_id: UUID,
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    service: Annotated[PortfolioAccountService, Depends(get_portfolio_service)],
) -> schema.PortfolioAccountRead:
    """Get a specific portfolio account by ID."""
    try:
        logger.info(
            "Portfolio account requested",
            extra={"user_id": current_user.id, "account_id": account_id, "action": "get_account"},
        )

        account = await service.get_account_by_id(current_user.id, account_id)

        logger.info(
            "Portfolio account retrieved successfully",
            extra={"user_id": current_user.id, "account_id": account_id, "action": "get_account"},
        )

        return account

    except PortfolioAccountError as e:
        logger.error(f"Portfolio account service error: {str(e)}")
        raise handle_portfolio_account_error(e)


@router.post(
    "/",
    response_model=schema.PortfolioAccountRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create portfolio account",
    description="Create a new portfolio account for the authenticated user.",
)
async def create_account(
    account_data: schema.PortfolioAccountCreate,
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    service: Annotated[PortfolioAccountService, Depends(get_portfolio_service)],
) -> schema.PortfolioAccountRead:
    """Create a new portfolio account for the current user."""
    try:
        logger.info(
            "Portfolio account creation requested",
            extra={
                "user_id": current_user.id,
                "account_name": account_data.name,
                "account_type": account_data.account_type,
                "action": "create_account",
            },
        )

        account = await service.create_account(current_user.id, account_data)

        logger.info(
            "Portfolio account created successfully",
            extra={
                "user_id": current_user.id,
                "account_id": account.id,
                "account_name": account.name,
                "action": "create_account",
            },
        )

        return account

    except PortfolioAccountError as e:
        logger.error(f"Portfolio account service error: {str(e)}")
        raise handle_portfolio_account_error(e)


@router.patch(
    "/{account_id}",
    response_model=schema.PortfolioAccountRead,
    status_code=status.HTTP_200_OK,
    summary="Update portfolio account",
    description="Update a specific portfolio account for the authenticated user.",
)
async def update_account(
    account_id: UUID,
    account_update: schema.PortfolioAccountUpdate,
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    service: Annotated[PortfolioAccountService, Depends(get_portfolio_service)],
) -> schema.PortfolioAccountRead:
    """Update a specific portfolio account."""
    try:
        logger.info(
            "Portfolio account update requested",
            extra={
                "user_id": current_user.id,
                "account_id": account_id,
                "action": "update_account",
            },
        )

        account = await service.update_account(current_user.id, account_id, account_update)

        logger.info(
            "Portfolio account updated successfully",
            extra={
                "user_id": current_user.id,
                "account_id": account_id,
                "action": "update_account",
            },
        )

        return account

    except PortfolioAccountError as e:
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
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    service: Annotated[PortfolioAccountService, Depends(get_portfolio_service)],
):
    """Deactivate a specific portfolio account (soft delete)."""
    try:
        logger.info(
            "Portfolio account deactivation requested",
            extra={
                "user_id": current_user.id,
                "account_id": account_id,
                "action": "deactivate_account",
            },
        )

        await service.deactivate_account(current_user.id, account_id)

        logger.info(
            "Portfolio account deactivated successfully",
            extra={
                "user_id": current_user.id,
                "account_id": account_id,
                "action": "deactivate_account",
            },
        )

    except PortfolioAccountError as e:
        logger.error(f"Portfolio account service error: {str(e)}")
        raise handle_portfolio_account_error(e)


@router.get(
    "/statistics/overview",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get account statistics",
    description="Get comprehensive statistics for the user's portfolio accounts.",
)
async def get_account_statistics(
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    service: Annotated[PortfolioAccountService, Depends(get_portfolio_service)],
) -> Dict[str, Any]:
    """Get comprehensive account statistics for the current user."""
    try:
        logger.info(
            "Portfolio account statistics requested",
            extra={"user_id": current_user.id, "action": "get_statistics"},
        )

        stats = await service.get_account_statistics(current_user.id)

        logger.info(
            "Portfolio account statistics retrieved successfully",
            extra={"user_id": current_user.id, "action": "get_statistics"},
        )

        return stats

    except PortfolioAccountError as e:
        logger.error(f"Portfolio account service error: {str(e)}")
        raise handle_portfolio_account_error(e)


@router.get(
    "/search",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Search portfolio accounts",
    description="Search portfolio accounts by name for the authenticated user.",
)
async def search_accounts(
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    service: Annotated[PortfolioAccountService, Depends(get_portfolio_service)],
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
) -> Dict[str, Any]:
    """Search portfolio accounts by name."""
    try:
        logger.info(
            "Portfolio account search requested",
            extra={"user_id": current_user.id, "query": q, "action": "search_accounts"},
        )

        accounts = await service.search_accounts(current_user.id, q, limit)

        logger.info(
            "Portfolio account search completed",
            extra={
                "user_id": current_user.id,
                "query": q,
                "results_count": len(accounts),
                "action": "search_accounts",
            },
        )

        return {
            "accounts": accounts,
            "query": q,
            "count": len(accounts),
        }

    except PortfolioAccountError as e:
        logger.error(f"Portfolio account service error: {str(e)}")
        raise handle_portfolio_account_error(e)

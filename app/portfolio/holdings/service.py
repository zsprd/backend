import logging
from datetime import date
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import HTTPException, status, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.data.integrations.csv.service import get_csv_processor
from app.portfolio.accounts.crud import PortfolioAccountRepository
from app.portfolio.holdings.repository import HoldingRepository
from app.portfolio.holdings.schemas import HoldingRead
from app.user.accounts.model import UserAccount

logger = logging.getLogger(__name__)


class PortfolioHoldingsService:
    """Service layer for portfolio holdings business logic."""

    async def import_holdings_csv(
        self,
        db: AsyncSession,
        account_id: UUID | str,
        file: UploadFile,
        dry_run: bool,
        current_user: UserAccount,
    ) -> Dict[str, Any]:
        """
        Import holdings from CSV file with validation and ownership check.
        Args:
            db: Database session
            account_id: Portfolio account ID
            file: CSV file to upload
            dry_run: If true, validate only without importing
            current_user: Authenticated user
        Returns:
            Import results as dict
        Raises:
            HTTPException: If validation fails or access denied
        """
        # Ensure account_id is UUID
        if isinstance(account_id, str):
            account_id = UUID(account_id)
        account = await PortfolioAccountRepository.get_by_user_and_id(
            db, user_id=current_user.id, account_id=account_id
        )
        if not account:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied or account not found"
            )
        if not file.filename.endswith(".csv"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a CSV"
            )
        contents = await file.read()
        if len(contents) > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size must be less than 10MB",
            )
        processor = get_csv_processor(db)  # Accept AsyncSession
        result = processor.process_holdings_csv(
            csv_content=contents,
            account_id=account_id,
            source=f"csv_upload_{current_user.id}",
            dry_run=dry_run,
        )
        return result.to_dict()

    async def get_user_holdings(
        self,
        db: AsyncSession,
        current_user: UserAccount,
        account_id: Optional[str | UUID] = None,
        as_of_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[HoldingRead]:
        """
        Retrieve holdings for the current user with optional filtering and pagination.
        Args:
            db: Database session
            current_user: Authenticated user
            account_id: Optional account filter
            as_of_date: Optional date filter
            skip: Pagination skip
            limit: Pagination limit
        Returns:
            List of HoldingResponse
        Raises:
            HTTPException: If error occurs
        """
        try:
            if account_id:
                if isinstance(account_id, str):
                    account_id = UUID(account_id)
                account = await PortfolioAccountRepository.get_by_user_and_id(
                    db, user_id=current_user.id, account_id=account_id
                )
                if not account:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Access denied or account not found",
                    )
                holdings = HoldingRepository.get_by_account(
                    db, account_id=account_id, as_of_date=as_of_date
                )
            else:
                from sqlalchemy import select
                from app.portfolio.accounts.model import PortfolioAccount

                stmt = select(PortfolioAccount.id).where(
                    PortfolioAccount.user_id == current_user.id
                )
                result = await db.execute(stmt)
                account_ids = [row[0] for row in result.fetchall()]
                if not account_ids:
                    return []
                holdings = []
                for acc_id in account_ids:
                    acc_holdings = HoldingRepository.get_by_account(
                        db, account_id=acc_id, as_of_date=as_of_date
                    )
                    holdings.extend(acc_holdings)
            paginated_holdings = holdings[skip : skip + limit]
            return [
                HoldingRead.model_validate(holding, from_attributes=True)
                for holding in paginated_holdings
            ]
        except Exception as e:
            logger.error(f"Error retrieving holdings: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving holdings: {str(e)}",
            )

    async def get_holding(
        self,
        db: AsyncSession,
        current_user: UserAccount,
        holding_id: str | UUID,
    ) -> HoldingRead:
        """
        Get a specific holding by ID with ownership validation.
        Args:
            db: Database session
            current_user: Authenticated user
            holding_id: Holding ID
        Returns:
            HoldingResponse
        Raises:
            HTTPException: If not found or access denied
        """
        if isinstance(holding_id, str):
            holding_id = UUID(holding_id)
        holding = HoldingRepository.get(db, id=holding_id)
        if not holding:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="PortfolioHolding not found"
            )
        account = await PortfolioAccountRepository.get_by_user_and_id(
            db, user_id=current_user.id, account_id=holding.account_id
        )
        if not account:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Access denied or account not found"
            )
        return HoldingRead.model_validate(holding, from_attributes=True)

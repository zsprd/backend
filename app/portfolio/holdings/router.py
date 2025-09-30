import logging
from datetime import UTC, date, datetime
from typing import Any, Dict, List, Optional, Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_async_db
from app.data.integrations.csv.service import CSVProcessorResult, get_csv_processor
from app.portfolio.accounts.crud import CRUDPortfolioAccount
from app.portfolio.holdings.crud import holding_crud
from app.portfolio.holdings.schema import HoldingCreate, HoldingResponse, HoldingUpdate
from app.system.logs.crud import audit_log_crud
from app.user.accounts.model import UserAccount

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/accounts/{account_id}/import-csv")
async def import_holdings_csv(
    account_id: UUID,
    file: Annotated[UploadFile, File()],
    dry_run: Annotated[bool, Query()] = False,
    current_user: Annotated[UserAccount, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_async_db)] = None,
) -> dict:
    """
    Import holdings from CSV file.

    Args:
        account_id: Portfolio account ID
        file: CSV file to upload
        dry_run: If true, validate only without importing

    Returns:
        Import results with success/error counts
    """

    # Verify user owns the account
    account = await CRUDPortfolioAccount.get_by_user_and_id(
        db, user_id=current_user.id, account_id=account_id
    )
    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied or account not found"
        )

    # Validate file
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a CSV")

    # Check file size
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size must be less than 10MB",
        )

    # Process CSV
    processor = get_csv_processor(db)
    result = processor.process_holdings_csv(
        csv_content=contents,
        account_id=account_id,
        source=f"csv_upload_{current_user.id}",
        dry_run=dry_run,
    )

    return result.to_dict()


@router.get("/", response_model=List[HoldingResponse])
async def get_user_holdings(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    as_of_date: Optional[date] = Query(None, description="Holdings as of specific date"),
    skip: int = Query(0, description="Skip records", ge=0),
    limit: int = Query(100, description="Limit records", ge=1, le=500),
):
    """Get holdings for the current users with optional filtering."""
    try:
        if account_id:
            # Verify users owns the account
            account = await CRUDPortfolioAccount.get_by_user_and_id(
                db, user_id=current_user.id, account_id=account_id
            )
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied or account not found",
                )

            holdings = holding_crud.get_by_account(db, account_id=account_id, as_of_date=as_of_date)
        else:
            # Get holdings across all users accounts
            from sqlalchemy import select

            from app.portfolio.accounts.model import PortfolioAccount

            # Get all users account IDs
            stmt = select(PortfolioAccount.id).where(PortfolioAccount.user_id == current_user.id)
            result = await db.execute(stmt)
            account_ids = [str(row[0]) for row in result.fetchall()]

            if not account_ids:
                return []

            holdings = []
            for acc_id in account_ids:
                acc_holdings = holding_crud.get_by_account(
                    db, account_id=acc_id, as_of_date=as_of_date
                )
                holdings.extend(acc_holdings)

        # Apply pagination
        paginated_holdings = holdings[skip : skip + limit]

        return [
            HoldingResponse.model_validate(holding, from_attributes=True)
            for holding in paginated_holdings
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving holdings: {str(e)}",
        )


@router.get("/{holding_id}", response_model=HoldingResponse)
async def get_holding(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    holding_id: str,
):
    """Get a specific holding by ID."""
    holding = holding_crud.get(db, id=holding_id)

    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PortfolioHolding not found"
        )

    # Verify users owns the account
    account = await CRUDPortfolioAccount.get_by_user_and_id(
        db, user_id=current_user.id, account_id=str(holding.account_id)
    )

    if not account:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return HoldingResponse.model_validate(holding, from_attributes=True)


@router.post("/", response_model=HoldingResponse, status_code=status.HTTP_201_CREATED)
async def create_holding(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    holding_data: HoldingCreate,
):
    """Create a new holding."""
    # Verify users owns the account
    account = await CRUDPortfolioAccount.get_by_user_and_id(
        db, user_id=current_user.id, account_id=str(holding_data.account_id)
    )

    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied or account not found",
        )

    try:
        holding = holding_crud.create(db, obj_in=holding_data)

        # Log the creation
        audit_log_crud.log_user_action(
            db,
            user_id=current_user.id,
            action="create",
            target_category="holding",
            target_id=str(holding.id),
            description=f"Created holding for account {holding_data.account_id}",
        )

        return HoldingResponse.model_validate(holding, from_attributes=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating holding: {str(e)}",
        )


@router.put("/{holding_id}", response_model=HoldingResponse)
async def update_holding(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    holding_id: str,
    holding_update: HoldingUpdate,
):
    """Update an existing holding."""
    holding = holding_crud.get(db, id=holding_id)

    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PortfolioHolding not found"
        )

    # Verify users owns the account
    account = await CRUDPortfolioAccount.get_by_user_and_id(
        db, user_id=current_user.id, account_id=str(holding.account_id)
    )

    if not account:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        updated_holding = holding_crud.update(db, db_obj=holding, obj_in=holding_update)

        # Log the update
        audit_log_crud.log_data_change(
            db,
            user_id=current_user.id,
            action="update",
            target_category="holding",
            target_id=holding_id,
            new_values=holding_update.model_dump(exclude_unset=True),
        )

        return HoldingResponse.model_validate(updated_holding, from_attributes=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating holding: {str(e)}",
        )


@router.delete("/{holding_id}")
async def delete_holding(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    holding_id: str,
):
    """Delete a holding."""
    holding = holding_crud.get(db, id=holding_id)

    if not holding:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PortfolioHolding not found"
        )

    # Verify users owns the account
    account = await CRUDPortfolioAccount.get_by_user_and_id(
        db, user_id=current_user.id, account_id=str(holding.account_id)
    )

    if not account:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        holding_crud.delete(db, id=holding_id)

        # Log the deletion
        audit_log_crud.log_user_action(
            db,
            user_id=current_user.id,
            action="delete",
            target_category="holding",
            target_id=holding_id,
            description=f"Deleted holding from account {holding.account_id}",
        )

        return {
            "message": "PortfolioHolding deleted successfully",
            "holding_id": holding_id,
            "deleted_at": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting holding: {str(e)}",
        )


@router.get("/{account_id}", response_model=List[HoldingResponse])
async def get_account_holdings(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    account_id: str,
    as_of_date: Optional[date] = Query(None, description="Holdings as of specific date"),
    current_only: bool = Query(True, description="Get only current holdings (non-zero positions)"),
):
    """Get holdings for a specific account."""
    # Verify users owns the account
    account = await CRUDPortfolioAccount.get_by_user_and_id(
        db, user_id=current_user.id, account_id=account_id
    )

    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied or account not found",
        )

    try:
        if current_only:
            holdings = holding_crud.get_current_holdings_by_account(db, account_id=account_id)
        else:
            holdings = holding_crud.get_by_account(db, account_id=account_id, as_of_date=as_of_date)

        return [
            HoldingResponse.model_validate(holding, from_attributes=True) for holding in holdings
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving account holdings: {str(e)}",
        )


@router.get("/{account_id}/summary")
async def get_account_holdings_summary(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    account_id: str,
    base_currency: str = Query("USD", description="Base currency for calculations"),
):
    """Get comprehensive holdings summary for a specific account."""
    # Verify users owns the account
    account = await CRUDPortfolioAccount.get_by_user_and_id(
        db, user_id=current_user.id, account_id=account_id
    )

    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied or account not found",
        )

    try:
        summary = holding_crud.get_holdings_summary(
            db, account_id=account_id, base_currency=base_currency
        )
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving holdings summary: {str(e)}",
        )


@router.get("/portfolio/allocation")
async def get_portfolio_allocation(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    base_currency: str = Query("USD", description="Base currency for calculations"),
):
    """Get portfolios allocation across all users accounts."""
    try:
        allocation = holding_crud.get_portfolio_allocation(
            db, user_id=current_user.id, base_currency=base_currency
        )
        return allocation
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving portfolios allocation: {str(e)}",
        )


@router.get("/securities/{security_id}/history")
async def get_holding_history(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    security_id: str,
    account_id: Optional[str] = Query(None, description="Filter by account"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    limit: int = Query(100, description="Maximum records", ge=1, le=500),
):
    """Get historical holdings for a specific securities."""
    try:
        if account_id:
            # Verify users owns the account
            account = await CRUDPortfolioAccount.get_by_user_and_id(
                db, user_id=current_user.id, account_id=account_id
            )
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied or account not found",
                )

            holdings = holding_crud.get_holding_history(
                db,
                account_id=account_id,
                security_id=security_id,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
            )
        else:
            # Get holdings across all users accounts for this securities
            from sqlalchemy import select

            from app.portfolio.accounts.model import PortfolioAccount

            # Get all users account IDs
            stmt = select(PortfolioAccount.id).where(PortfolioAccount.user_id == current_user.id)
            result = await db.execute(stmt)
            account_ids = [str(row[0]) for row in result.fetchall()]

            holdings = []
            for acc_id in account_ids:
                acc_holdings = holding_crud.get_holding_history(
                    db,
                    account_id=acc_id,
                    security_id=security_id,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                )
                holdings.extend(acc_holdings)

        # Sort by date and limit
        holdings = sorted(holdings, key=lambda x: x.as_of_date, reverse=True)[:limit]

        return [
            HoldingResponse.model_validate(holding, from_attributes=True) for holding in holdings
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving holding history: {str(e)}",
        )


@router.post("/bulk-update-prices")
async def bulk_update_market_values(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    holdings_updates: List[Dict[str, Any]],
):
    """Bulk update market values for holdings."""
    if not holdings_updates:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No holdings updates provided",
        )

    try:
        # Verify users owns all the holdings
        for update in holdings_updates:
            holding_id = update.get("holding_id")
            if not holding_id:
                continue

            holding = holding_crud.get(db, id=holding_id)
            if not holding:
                continue

            account = await CRUDPortfolioAccount.get_by_user_and_id(
                db, user_id=current_user.id, account_id=str(holding.account_id)
            )
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied for holding {holding_id}",
                )

        updated_count = holding_crud.update_market_values(db, holdings_updates=holdings_updates)

        # Log bulk update
        audit_log_crud.log_user_action(
            db,
            user_id=current_user.id,
            action="bulk_update",
            target_category="holding",
            description=f"Bulk updated market values for {updated_count} holdings",
            metadata={"updated_count": updated_count},
        )

        return {
            "message": "Market values updated successfully",
            "updated_count": updated_count,
            "timestamp": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating market values: {str(e)}",
        )


@router.post("/{account_id}/snapshot")
async def create_holdings_snapshot(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    account_id: str,
    as_of_date: date = Query(..., description="Snapshot date"),
    holdings_data: List[Dict[str, Any]],
):
    """Create a complete holdings snapshot for an account."""
    # Verify users owns the account
    account = await CRUDPortfolioAccount.get_by_user_and_id(
        db, user_id=current_user.id, account_id=account_id
    )

    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied or account not found",
        )

    if not holdings_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No holdings data provided"
        )

    try:
        holdings = holding_crud.create_holding_snapshot(
            db,
            account_id=account_id,
            as_of_date=as_of_date,
            holdings_data=holdings_data,
        )

        # Log snapshot creation
        audit_log_crud.log_user_action(
            db,
            user_id=current_user.id,
            action="create_snapshot",
            target_category="holding",
            target_id=account_id,
            description=f"Created holdings snapshot with {len(holdings)} positions",
            metadata={
                "as_of_date": as_of_date.isoformat(),
                "holdings_count": len(holdings),
            },
        )

        return {
            "message": "Holdings snapshot created successfully",
            "account_id": account_id,
            "as_of_date": as_of_date.isoformat(),
            "holdings_count": len(holdings),
            "holdings": [
                HoldingResponse.model_validate(holding, from_attributes=True)
                for holding in holdings
            ],
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating holdings snapshot: {str(e)}",
        )


@router.post("/{account_id}/csv-upload")
async def upload_holdings_csv(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user: Annotated[UserAccount, Depends(get_current_user)],
    account_id: str,
    file: UploadFile = File(...),
    dry_run: bool = Form(False, description="Validate only, don't import"),
):
    """
    Upload and process holdings CSV file for a specific account.

    Args:
        account_id: PortfolioAccount ID to import holdings into
        file: CSV file to upload
        dry_run: If true, only validate without importing
    """

    # Verify users owns the account
    account = await CRUDPortfolioAccount.get_by_user_and_id(
        db, user_id=current_user.id, account_id=account_id
    )

    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Access denied or account not found"
        )

    # Validate file
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a CSV file"
        )

    # Check file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if file.size and file.size > max_size:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size must be less than 10MB",
        )

    try:
        # Read file content
        content = await file.read()

        # Log the upload attempt
        audit_log_crud.log_user_action(
            db,
            user_id=current_user.id,
            action="csv_upload_attempt",
            target_category="holdings",
            target_id=account_id,
            description=f"Uploaded holdings CSV for account {account.name}: {file.filename}",
        )

        # Process the CSV
        from app.data.integrations.csv.service import get_csv_processor

        processor = get_csv_processor(db)

        if dry_run:
            # Validation only - simulate processing without database changes
            result = _validate_holdings_csv(content, processor)
        else:
            # Full import
            result = processor.process_holdings_csv(
                csv_content=content, account_id=account_id, source="csv_upload"
            )

            # Log the result
            audit_log_crud.log_user_action(
                db,
                user_id=current_user.id,
                action="csv_import_completed",
                target_category="holdings",
                target_id=account_id,
                description=f"Imported {result.success_count} holdings, {result.error_count} errors",
            )

        return {
            "success": result.error_count == 0,
            "dry_run": dry_run,
            "account_id": account_id,
            "account_name": account.name,
            "summary": {
                "processed_count": result.success_count + result.error_count,
                "success_count": result.success_count,
                "error_count": result.error_count,
                "warnings_count": len(result.warnings),
            },
            "created_securities": result.created_securities,
            "failed_securities": result.failed_securities,
            "warnings": result.warnings,
            "errors": result.errors[:50],  # Limit to first 50 errors
            "has_more_errors": len(result.errors) > 50,
        }

    except Exception as e:
        error_msg = f"Failed to process holdings CSV: {str(e)}"
        logger.error(error_msg)

        # Log the error
        audit_log_crud.log_user_action(
            db,
            user_id=current_user.id,
            action="csv_upload_error",
            target_category="holdings",
            target_id=account_id,
            description=error_msg,
        )

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg)


def _validate_holdings_csv(content: bytes, processor) -> CSVProcessorResult:
    """Validate holdings CSV without importing."""
    from app.data.integrations.csv.service import CSVProcessorResult

    result = CSVProcessorResult()

    try:
        # Parse CSV
        df = processor._parse_csv_content(content)

        # Validate structure
        validation_errors = processor.validator.validate_holdings_csv(df)
        result.errors.extend(validation_errors)

        if not validation_errors:
            result.success_count = len(df)
            result.warnings.append(f"CSV validation passed for {len(df)} holdings")
        else:
            result.error_count = len(validation_errors)

    except Exception as e:
        result.errors.append(f"CSV parsing failed: {str(e)}")
        result.error_count = 1

    return result


@router.get("/health")
async def holdings_health():
    """Health check for holdings service."""
    return {
        "status": "healthy",
        "service": "holdings",
        "timestamp": datetime.now(UTC).isoformat(),
        "features": [
            "holdings_management",
            "portfolio_allocation",
            "holding_history",
        ],
    }

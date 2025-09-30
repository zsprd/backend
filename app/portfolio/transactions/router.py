import logging
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Annotated
from typing import Any, Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi import File, UploadFile, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.core.database import get_async_db
from app.data.integrations.csv.service import CSVProcessorResult
from app.data.integrations.csv.service import get_csv_processor
from app.portfolio.accounts.crud import CRUDPortfolioAccount
from app.portfolio.transactions.crud import transaction_crud
from app.portfolio.transactions.schema import (
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
)
from app.system.logs.crud import audit_log_crud
from app.user.accounts.model import UserAccount

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/accounts/{account_id}/import-csv")
async def import_transactions_csv(
    account_id: UUID,
    file: Annotated[UploadFile, File()],
    dry_run: Annotated[bool, Query()] = False,
    current_user: Annotated[UserAccount, Depends(get_current_user)] = None,
    db: Annotated[AsyncSession, Depends(get_async_db)] = None,
) -> dict:
    """
    Import transactions from CSV file.

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

    # Check file size (max 10MB)
    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size must be less than 10MB",
        )

    # Process CSV
    processor = get_csv_processor(db)
    result = processor.process_transactions_csv(
        csv_content=contents,
        account_id=account_id,
        source=f"csv_upload_{current_user.id}",
        dry_run=dry_run,
    )

    return result.to_dict()


@router.get("/", response_model=List[TransactionResponse])
async def get_user_transactions(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: str = Depends(get_current_user.id),
    account_id: Optional[str] = Query(None, description="Filter by account ID"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    transaction_category: Optional[str] = Query(
        None, description="Filter by transaction security_type"
    ),
    skip: int = Query(0, description="Skip records", ge=0),
    limit: int = Query(100, description="Limit records", ge=1, le=500),
):
    """Get transactions for the current users with filtering and pagination."""
    try:
        if account_id:
            # Verify users owns the account
            account = CRUDPortfolioAccount.get_by_user_and_id(
                db, user_id=current_user_id, account_id=account_id
            )
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied or account not found",
                )

            transactions = transaction_crud.get_by_account(
                db,
                account_id=account_id,
                skip=skip,
                limit=limit,
                start_date=start_date,
                end_date=end_date,
                transaction_category=transaction_category,
            )
        else:
            # Get transactions across all users accounts
            transactions = transaction_crud.get_by_user(
                db,
                user_id=current_user_id,
                skip=skip,
                limit=limit,
                start_date=start_date,
                end_date=end_date,
            )

        return [TransactionResponse.model_validate(tx, from_attributes=True) for tx in transactions]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving transactions: {str(e)}",
        )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: str = Depends(get_current_user.id),
    transaction_id: str,
):
    """Get a specific transaction by ID."""
    transaction = transaction_crud.get(db, id=transaction_id)

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PortfolioTransaction not found"
        )

    # Verify users owns the account
    account = CRUDPortfolioAccount.get_by_user_and_id(
        db, user_id=current_user_id, account_id=str(transaction.account_id)
    )

    if not account:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return TransactionResponse.model_validate(transaction, from_attributes=True)


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: str = Depends(get_current_user.id),
    transaction_data: TransactionCreate,
):
    """Create a new transaction."""
    # Verify users owns the account
    account = CRUDPortfolioAccount.get_by_user_and_id(
        db, user_id=current_user_id, account_id=str(transaction_data.account_id)
    )

    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied or account not found",
        )

    try:
        transaction = transaction_crud.create(db, obj_in=transaction_data)

        # Log the creation
        audit_log_crud.log_user_action(
            db,
            user_id=current_user_id,
            action="create",
            target_category="transaction",
            target_id=str(transaction.id),
            description=f"Created {transaction.transaction_category} transaction",
        )

        return TransactionResponse.model_validate(transaction, from_attributes=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating transaction: {str(e)}",
        )


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: str = Depends(get_current_user.id),
    transaction_id: str,
    transaction_update: TransactionUpdate,
):
    """Update an existing transaction."""
    transaction = transaction_crud.get(db, id=transaction_id)

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PortfolioTransaction not found"
        )

    # Verify users owns the account
    account = CRUDPortfolioAccount.get_by_user_and_id(
        db, user_id=current_user_id, account_id=str(transaction.account_id)
    )

    if not account:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        updated_transaction = transaction_crud.update(
            db, db_obj=transaction, obj_in=transaction_update
        )

        # Log the update
        audit_log_crud.log_data_change(
            db,
            user_id=current_user_id,
            action="update",
            target_category="transaction",
            target_id=transaction_id,
            new_values=transaction_update.model_dump(exclude_unset=True),
        )

        return TransactionResponse.model_validate(updated_transaction, from_attributes=True)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error updating transaction: {str(e)}",
        )


@router.delete("/{transaction_id}")
async def delete_transaction(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: str = Depends(get_current_user.id),
    transaction_id: str,
):
    """Delete a transaction."""
    transaction = transaction_crud.get(db, id=transaction_id)

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="PortfolioTransaction not found"
        )

    # Verify users owns the account
    account = CRUDPortfolioAccount.get_by_user_and_id(
        db, user_id=current_user_id, account_id=str(transaction.account_id)
    )

    if not account:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    try:
        transaction_crud.delete(db, id=transaction_id)

        # Log the deletion
        audit_log_crud.log_user_action(
            db,
            user_id=current_user_id,
            action="delete",
            target_category="transaction",
            target_id=transaction_id,
            description=f"Deleted {transaction.transaction_category} transaction",
        )

        return {
            "message": "PortfolioTransaction deleted successfully",
            "transaction_id": transaction_id,
            "deleted_at": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting transaction: {str(e)}",
        )


@router.get("/{account_id}/summary")
async def get_account_transaction_summary(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: str = Depends(get_current_user.id),
    account_id: str,
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
):
    """Get transaction summary for a specific account."""
    # Verify users owns the account
    account = CRUDPortfolioAccount.get_by_user_and_id(
        db, user_id=current_user_id, account_id=account_id
    )

    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied or account not found",
        )

    try:
        summary = transaction_crud.get_transaction_summary(
            db, account_id=account_id, start_date=start_date, end_date=end_date
        )
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving transaction summary: {str(e)}",
        )


@router.get("/portfolio/summary")
async def get_portfolio_transaction_summary(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: str = Depends(get_current_user.id),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
):
    """Get transaction summary across all users accounts."""
    try:
        summary = transaction_crud.get_portfolio_summary(
            db, user_id=current_user_id, start_date=start_date, end_date=end_date
        )
        return summary
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving portfolios transaction summary: {str(e)}",
        )


@router.get("/{account_id}/monthly/{year}")
async def get_monthly_transaction_activity(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: str = Depends(get_current_user.id),
    account_id: str,
    year: int,
    month: Optional[int] = Query(None, description="Specific month (1-12)", ge=1, le=12),
):
    """Get monthly transaction activity for an account."""
    # Verify users owns the account
    account = CRUDPortfolioAccount.get_by_user_and_id(
        db, user_id=current_user_id, account_id=account_id
    )

    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied or account not found",
        )

    try:
        activity = transaction_crud.get_monthly_activity(
            db, account_id=account_id, year=year, month=month
        )
        return activity
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving monthly activity: {str(e)}",
        )


@router.get("/securities/{security_id}")
async def get_security_transactions(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: str = Depends(get_current_user.id),
    security_id: str,
    account_id: Optional[str] = Query(None, description="Filter by account"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
):
    """Get all transactions for a specific securities."""
    try:
        if account_id:
            # Verify users owns the account
            account = CRUDPortfolioAccount.get_by_user_and_id(
                db, user_id=current_user_id, account_id=account_id
            )
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied or account not found",
                )

        transactions = transaction_crud.get_security_transactions(
            db,
            security_id=security_id,
            account_id=account_id,
            user_id=current_user_id if not account_id else None,
            start_date=start_date,
            end_date=end_date,
        )

        return [TransactionResponse.model_validate(tx, from_attributes=True) for tx in transactions]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving securities transactions: {str(e)}",
        )


@router.get("/{account_id}/realized-gains")
async def get_realized_gains_losses(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: str = Depends(get_current_user.id),
    account_id: str,
    tax_year: Optional[int] = Query(None, description="Tax year filter"),
    security_id: Optional[str] = Query(None, description="Filter by securities"),
):
    """Calculate realized gains/losses for tax reporting."""
    # Verify users owns the account
    account = CRUDPortfolioAccount.get_by_user_and_id(
        db, user_id=current_user_id, account_id=account_id
    )

    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied or account not found",
        )

    try:
        gains_losses = transaction_crud.calculate_realized_gains_losses(
            db, account_id=account_id, security_id=security_id, tax_year=tax_year
        )

        # Log tax report access
        audit_log_crud.log_user_action(
            db,
            user_id=current_user_id,
            action="tax_report",
            target_category="transaction",
            target_id=account_id,
            description=f"Generated realized gains/losses report for {tax_year or 'all years'}",
        )

        return gains_losses
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating realized gains/losses: {str(e)}",
        )


@router.get("/tax-summary/{tax_year}")
async def get_tax_summary(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: str = Depends(get_current_user.id),
    tax_year: int,
):
    """Get comprehensive tax summary across all accounts."""
    try:
        # Get all users accounts
        from sqlalchemy import select

        from app.portfolio.accounts.model import PortfolioAccount

        stmt = select(PortfolioAccount.id).where(PortfolioAccount.user_id == current_user_id)
        result = db.execute(stmt)
        account_ids = [str(row[0]) for row in result.fetchall()]

        if not account_ids:
            return {
                "tax_year": tax_year,
                "total_realized_gains": Decimal("0"),
                "total_realized_losses": Decimal("0"),
                "net_realized": Decimal("0"),
                "by_account": {},
            }

        total_gains = Decimal("0")
        total_losses = Decimal("0")
        by_account = {}

        for account_id in account_ids:
            gains_losses = transaction_crud.calculate_realized_gains_losses(
                db, account_id=account_id, tax_year=tax_year
            )

            by_account[account_id] = gains_losses
            total_gains += gains_losses.get("realized_gains", Decimal("0"))
            total_losses += gains_losses.get("realized_losses", Decimal("0"))

        net_realized = total_gains - total_losses

        # Log tax summary access
        audit_log_crud.log_user_action(
            db,
            user_id=current_user_id,
            action="tax_summary",
            target_category="transaction",
            description=f"Generated tax summary for {tax_year}",
            metadata={"tax_year": tax_year},
        )

        return {
            "tax_year": tax_year,
            "total_realized_gains": total_gains,
            "total_realized_losses": total_losses,
            "net_realized": net_realized,
            "by_account": by_account,
            "generated_at": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating tax summary: {str(e)}",
        )


@router.post("/bulk-import")
async def bulk_import_transactions(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: str = Depends(get_current_user.id),
    transactions_data: List[Dict[str, Any]],
):
    """Bulk import transactions."""
    if not transactions_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No transaction data provided",
        )

    try:
        # Verify users owns all accounts referenced
        account_ids = set()
        for tx_data in transactions_data:
            account_id = tx_data.get("account_id")
            if account_id:
                account_ids.add(account_id)

        for account_id in account_ids:
            account = CRUDPortfolioAccount.get_by_user_and_id(
                db, user_id=current_user_id, account_id=account_id
            )
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access denied for account {account_id}",
                )

        transactions = transaction_crud.bulk_import_transactions(
            db, transactions_data=transactions_data
        )

        # Log bulk import
        audit_log_crud.log_user_action(
            db,
            user_id=current_user_id,
            action="bulk_import",
            target_category="transaction",
            description=f"Bulk imported {len(transactions)} transactions",
            metadata={
                "imported_count": len(transactions),
                "account_ids": list(account_ids),
            },
        )

        return {
            "message": "Transactions imported successfully",
            "imported_count": len(transactions),
            "account_ids": list(account_ids),
            "imported_at": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing transactions: {str(e)}",
        )


@router.post("/upload-csv")
async def upload_transactions_csv(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: str = Depends(get_current_user.id),
    account_id: str = Query(..., description="Target account ID"),
    file: UploadFile = File(..., description="CSV file with transactions"),
):
    """Upload and process transactions from CSV file."""
    # Verify users owns the account
    account = CRUDPortfolioAccount.get_by_user_and_id(
        db, user_id=current_user_id, account_id=account_id
    )

    if not account:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied or account not found",
        )

    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="File must be a CSV")

    try:
        # Read CSV content
        import csv
        import io

        content = await file.read()
        csv_content = content.decode("utf-8")
        csv_reader = csv.DictReader(io.StringIO(csv_content))

        transactions_data = []
        for row in csv_reader:
            # Basic CSV parsing - you may need to customize based on CSV format
            tx_data = {
                "account_id": account_id,
                "transaction_category": row.get("security_type", "other"),
                "transaction_side": row.get("side", "buy"),
                "amount": Decimal(row.get("amount", "0")),
                "trade_date": datetime.strptime(row.get("date") or "1970-01-01", "%Y-%m-%d").date(),
                "transaction_currency": row.get("currency", "USD"),
                "description": row.get("description"),
                # Add other fields as needed
            }
            transactions_data.append(tx_data)

        if not transactions_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No valid transactions found in CSV",
            )

        transactions = transaction_crud.bulk_import_transactions(
            db, transactions_data=transactions_data
        )

        # Log CSV import
        audit_log_crud.log_user_action(
            db,
            user_id=current_user_id,
            action="csv_import",
            target_category="transaction",
            target_id=account_id,
            description=f"Imported {len(transactions)} transactions from CSV",
            metadata={"filename": file.filename, "imported_count": len(transactions)},
        )

        return {
            "message": "CSV transactions imported successfully",
            "filename": file.filename,
            "imported_count": len(transactions),
            "account_id": account_id,
            "imported_at": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing CSV: {str(e)}",
        )


@router.get("/search")
async def search_transactions(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: str = Depends(get_current_user.id),
    q: str = Query(..., description="Search term", min_length=2),
    account_id: Optional[str] = Query(None, description="Filter by account"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    limit: int = Query(50, description="Maximum results", ge=1, le=200),
):
    """Search transactions by description, amount, or other criteria."""
    try:
        if account_id:
            # Verify users owns the account
            account = CRUDPortfolioAccount.get_by_user_and_id(
                db, user_id=current_user_id, account_id=account_id
            )
            if not account:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied or account not found",
                )

            transactions = transaction_crud.get_by_account(
                db,
                account_id=account_id,
                start_date=start_date,
                end_date=end_date,
                skip=0,
                limit=limit,
            )
        else:
            transactions = transaction_crud.get_by_user(
                db,
                user_id=current_user_id,
                start_date=start_date,
                end_date=end_date,
                skip=0,
                limit=limit,
            )

        # Filter by search term (simple text matching)
        filtered_transactions = []
        search_lower = q.lower()

        for tx in transactions:
            if (
                (tx.transaction_category and search_lower in tx.transaction_category.lower())
                or (tx.transaction_side and search_lower in tx.transaction_side.lower())
                or str(tx.amount) == q
            ):
                filtered_transactions.append(tx)

        return {
            "transactions": [
                TransactionResponse.model_validate(tx, from_attributes=True)
                for tx in filtered_transactions
            ],
            "query": q,
            "count": len(filtered_transactions),
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching transactions: {str(e)}",
        )


@router.post("/accounts/{account_id}/csv-upload")
async def upload_transactions_csv(
    *,
    db: AsyncSession = Depends(get_async_db),
    current_user_id: str = Depends(get_current_user.id),
    account_id: str,
    file: UploadFile = File(...),
    dry_run: bool = Form(False, description="Validate only, don't import"),
):
    """
    Upload and process transactions CSV file for a specific account.

    Args:
        account_id: PortfolioAccount ID to import transactions into
        file: CSV file to upload
        dry_run: If true, only validate without importing
    """

    # Verify users owns the account
    account = CRUDPortfolioAccount.get_by_user_and_id(
        db, user_id=current_user_id, account_id=account_id
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
            user_id=current_user_id,
            action="csv_upload_attempt",
            target_category="transactions",
            target_id=account_id,
            description=f"Uploaded transactions CSV for account {account.name}: {file.filename}",
        )

        # Process the CSV
        from app.data.integrations.csv.service import get_csv_processor

        processor = get_csv_processor(db)

        if dry_run:
            # Validation only - simulate processing without database changes
            result = _validate_transactions_csv(content, processor)
        else:
            # Full import
            result = processor.process_transactions_csv(
                csv_content=content, account_id=account_id, source="csv_upload"
            )

            # Log the result
            audit_log_crud.log_user_action(
                db,
                user_id=current_user_id,
                action="csv_import_completed",
                target_category="transactions",
                target_id=account_id,
                description=f"Imported {result.success_count} transactions, {result.error_count} errors",
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
        error_msg = f"Failed to process transactions CSV: {str(e)}"
        logger.error(error_msg)

        # Log the error
        audit_log_crud.log_user_action(
            db,
            user_id=current_user_id,
            action="csv_upload_error",
            target_category="transactions",
            target_id=account_id,
            description=error_msg,
        )

        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=error_msg)


def _validate_transactions_csv(content: bytes, processor) -> CSVProcessorResult:
    """Validate transactions CSV without importing."""
    from app.data.integrations.csv.service import CSVProcessorResult

    result = CSVProcessorResult()

    try:
        # Parse CSV
        df = processor._parse_csv_content(content)

        # Validate structure
        validation_errors = processor.validator.validate_transactions_csv(df)
        result.errors.extend(validation_errors)

        if not validation_errors:
            result.success_count = len(df)
            result.warnings.append(f"CSV validation passed for {len(df)} transactions")
        else:
            result.error_count = len(validation_errors)

    except Exception as e:
        result.errors.append(f"CSV parsing failed: {str(e)}")
        result.error_count = 1

    return result


@router.get("/health")
async def transactions_health():
    """Health check for transactions service."""
    return {
        "status": "healthy",
        "service": "transactions",
        "timestamp": datetime.now(UTC).isoformat(),
        "features": [
            "transaction_management",
            "analytics_and_reporting",
            "tax_calculations",
            "bulk_import",
            "csv_upload",
            "search_and_filtering",
        ],
    }

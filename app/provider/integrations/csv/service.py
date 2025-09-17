import io
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple, Union

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.portfolio.accounts.crud import account_crud
from app.portfolio.accounts.model import PortfolioAccount
from app.portfolio.holdings.crud import holding_crud
from app.portfolio.transactions.crud import transaction_crud
from app.provider.integrations.csv.validators import CSVValidator
from app.security.master.model import SecurityReference
from app.security.master.service import SecurityMatcher
from app.security.prices.service import get_market_data_service

logger = logging.getLogger(__name__)


class CSVProcessorResult:
    def __init__(self):
        self.success_count = 0
        self.error_count = 0
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.created_securities: List[Dict[str, str]] = []
        self.failed_securities: List[Dict[str, str]] = []


class CSVProcessor:
    """
    Main CSV processing service for transactions and holdings imports.
    Uses intelligent securities matching and market data integration.
    """

    def __init__(self, db: Session):
        self.db = db
        self.security_matcher = SecurityMatcher(db)
        self.validator = CSVValidator()
        self.market_data_service = get_market_data_service(db)

    def process_transactions_csv(
        self, csv_content: Union[str, bytes], account_id: str, source: str = "csv_upload"
    ) -> CSVProcessorResult:
        """
        Process transactions CSV file for a specific account.

        Args:
            csv_content: CSV file content as string or bytes
            account_id: PortfolioAccount ID from URL path
            source: Source of the import
        """
        result = CSVProcessorResult()

        try:
            # Verify account exists and get account details
            account = account_crud.get(self.db, id=account_id)
            if not account:
                result.errors.append(f"PortfolioAccount {account_id} not found")
                return result

            # Parse CSV content
            df = self._parse_csv_content(csv_content)

            # Validate CSV structure for transactions
            validation_errors = self.validator.validate_transactions_csv(df)
            if validation_errors:
                result.errors.extend(validation_errors)
                return result

            # Process each row
            for idx, row in df.iterrows():
                try:
                    self._process_transaction_row(row, account, source, result)
                except Exception as e:
                    error_msg = f"Row {idx + 2}: {str(e)}"
                    result.errors.append(error_msg)
                    result.error_count += 1
                    logger.error(error_msg)

            # Commit all changes
            self.db.commit()
            logger.info(
                f"Successfully processed {result.success_count} transactions for account {account_id}"
            )

        except Exception as e:
            self.db.rollback()
            result.errors.append(f"Fatal error processing CSV: {str(e)}")
            logger.error(f"CSV processing failed: {str(e)}")

        return result

    def process_holdings_csv(
        self, csv_content: Union[str, bytes], account_id: str, source: str = "csv_upload"
    ) -> CSVProcessorResult:
        """
        Process holdings CSV file for a specific account.
        """
        result = CSVProcessorResult()

        try:
            # Verify account exists and get account details
            account = account_crud.get(self.db, id=account_id)
            if not account:
                result.errors.append(f"PortfolioAccount {account_id} not found")
                return result

            # Parse CSV content
            df = self._parse_csv_content(csv_content)

            # Validate CSV structure for holdings
            validation_errors = self.validator.validate_holdings_csv(df)
            if validation_errors:
                result.errors.extend(validation_errors)
                return result

            # Process each row
            for idx, row in df.iterrows():
                try:
                    self._process_holding_row(row, account, source, result)
                except Exception as e:
                    error_msg = f"Row {idx + 2}: {str(e)}"
                    result.errors.append(error_msg)
                    result.error_count += 1
                    logger.error(error_msg)

            # Commit all changes
            self.db.commit()
            logger.info(
                f"Successfully processed {result.success_count} holdings for account {account_id}"
            )

        except Exception as e:
            self.db.rollback()
            result.errors.append(f"Fatal error processing CSV: {str(e)}")
            logger.error(f"CSV processing failed: {str(e)}")

        return result

    def _parse_csv_content(self, csv_content: Union[str, bytes]) -> pd.DataFrame:
        """Parse CSV content into pandas DataFrame with robust handling."""
        if isinstance(csv_content, bytes):
            csv_content = csv_content.decode("utf-8")

        # Use pandas for robust CSV parsing
        try:
            df = pd.read_csv(
                io.StringIO(csv_content),
                dtype=str,  # Keep everything as string initially
                na_filter=False,  # Don't convert empty strings to NaN
                skipinitialspace=True,
                encoding="utf-8",
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid CSV format: {str(e)}")

        # Strip whitespace from column names
        df.columns = df.columns.str.strip()

        # Strip whitespace from all string values
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

        return df

    def _process_transaction_row(
        self, row: pd.Series, account: PortfolioAccount, source: str, result: CSVProcessorResult
    ) -> None:
        """Process a single transaction row."""

        # Map securities (if symbol provided)
        security = None
        if self._has_security_symbol(row):
            security = self.security_matcher.match_or_create_security(row, result)

        # Parse and validate transaction data
        transaction_data = self._normalize_transaction_data(row, account, security)

        # Create transaction
        transaction = transaction_crud.create(self.db, obj_in=transaction_data)
        result.success_count += 1

        logger.debug(f"Created transaction: {transaction.id}")

    def _process_holding_row(
        self, row: pd.Series, account: PortfolioAccount, source: str, result: CSVProcessorResult
    ) -> None:
        """Process a single holding row."""

        # Map securities (required for holdings)
        security = self.security_matcher.match_or_create_security(row, result)
        if not security:
            raise ValueError("SecurityReference could not be identified or created")

        # Parse and validate holding data
        holding_data = self._normalize_holding_data(row, account, security)

        # Create or update holding
        holding = holding_crud.create(self.db, obj_in=holding_data)
        result.success_count += 1

        logger.debug(f"Created holding: {holding.id}")

    def _has_security_symbol(self, row: pd.Series) -> bool:
        """Check if row contains securities symbol."""
        return bool(row.get("symbol", "").strip())

    def _normalize_transaction_data(
        self, row: pd.Series, account: PortfolioAccount, security: Optional[SecurityReference]
    ) -> Dict[str, Any]:
        """Normalize CSV row data to transaction model format."""

        # Parse numeric values
        quantity = self._parse_decimal(row.get("quantity", "0"))
        price = self._parse_decimal(row.get("price", "0"))
        fees = self._parse_decimal(row.get("fees", "0"))

        # Parse date
        trade_date = self._parse_date(row.get("date", ""))

        # Map transaction type to internal categories
        transaction_type = row.get("type", "").strip().lower()
        transaction_category, transaction_side = self._map_plaid_transaction_type(transaction_type)

        # Calculate amount if not provided
        amount = quantity * price if quantity and price else Decimal("0")

        return {
            "account_id": account.id,
            "security_id": security.id if security else None,
            "transaction_category": transaction_category,
            "transaction_side": transaction_side,
            "quantity": quantity,
            "price": price,
            "amount": amount,
            "fees": fees,
            "trade_date": trade_date,
            "transaction_currency": row.get("currency", account.currency or "USD").upper(),
            "description": row.get("description", "").strip()
            or f"{transaction_type.upper()} {security.symbol if security else 'N/A'}",
            "data_provider": source,
        }

    def _normalize_holding_data(
        self, row: pd.Series, account: PortfolioAccount, security: SecurityReference
    ) -> Dict[str, Any]:
        """Normalize CSV row data to holding model format."""

        quantity = self._parse_decimal(row.get("quantity", "0"))
        cost_basis = self._parse_decimal(row.get("cost_basis", ""))
        institution_price = self._parse_decimal(row.get("institution_price", ""))

        # Calculate values
        cost_basis_total = cost_basis * quantity if cost_basis and quantity else None
        market_value = institution_price * quantity if institution_price and quantity else None

        # Parse date
        as_of_date = self._parse_date(row.get("date", ""))

        return {
            "account_id": account.id,
            "security_id": security.id,
            "quantity": quantity,
            "cost_basis_per_share": cost_basis,
            "cost_basis_total": cost_basis_total,
            "market_value": market_value,
            "currency": row.get("currency", account.currency or "USD").upper(),
            "as_of_date": as_of_date,
            "institution_price": institution_price,
            "data_provider": source,
        }

    def _parse_decimal(self, value: str) -> Optional[Decimal]:
        """Parse decimal value with error handling."""
        if not value or value.strip() == "":
            return None

        try:
            # Remove common formatting
            cleaned = str(value).replace(",", "").replace("$", "").strip()
            return Decimal(cleaned) if cleaned else None
        except (InvalidOperation, ValueError):
            return None

    def _parse_date(self, date_str: str) -> datetime.date:
        """Parse date string with multiple format support."""
        if not date_str:
            return datetime.now().date()

        date_formats = [
            "%Y-%m-%d",  # 2024-01-15
            "%m/%d/%Y",  # 01/15/2024
            "%d/%m/%Y",  # 15/01/2024
            "%Y-%m-%d %H:%M:%S",  # 2024-01-15 10:30:00
            "%d-%m-%Y",  # 15-01-2024
        ]

        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt).date()
            except ValueError:
                continue

        raise ValueError(f"Unable to parse date: {date_str}")

    def _map_plaid_transaction_type(self, transaction_type: str) -> Tuple[str, Optional[str]]:
        """Map Plaid-style transaction types to internal categories."""
        type_mapping = {
            "buy": ("trade", "buy"),
            "sell": ("trade", "sell"),
            "dividend": ("dividend", None),
            "interest": ("interest", None),
            "fee": ("fee", None),
            "deposit": ("cash", "deposit"),
            "withdrawal": ("cash", "withdrawal"),
            "transfer_in": ("transfer", "in"),
            "transfer_out": ("transfer", "out"),
            "split": ("corporate_action", "split"),
            "spinoff": ("corporate_action", "spinoff"),
        }

        return type_mapping.get(transaction_type, ("other", None))


# Convenience function for getting CSV processor
def get_csv_processor(db: Session) -> CSVProcessor:
    """Get CSVProcessor instance with database session."""
    return CSVProcessor(db)

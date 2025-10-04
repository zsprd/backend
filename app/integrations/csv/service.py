"""
CSV Import Service for Portfolio Transactions and Holdings

This module provides a complete, production-ready CSV import service that:
- Validates CSV structure and data
- Intelligently matches or creates securities
- Handles both transactions and holdings imports
- Provides detailed error reporting and logging
- Supports dry-run validation mode
"""

import io
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import UUID

import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession

from app.portfolio.holdings.repository import HoldingRepository
from app.portfolio.holdings.schemas import HoldingCreate
from app.portfolio.master.repository import PortfolioRepository
from app.portfolio.transactions.repository import TransactionRepository
from app.portfolio.transactions.schemas import TransactionCreate
from app.security.master.model import SecurityMaster
from app.security.master.repository import security_crud
from app.security.master.schemas import SecurityCreate

logger = logging.getLogger(__name__)


class CSVProcessorResult:
    """Results from CSV processing including counts, errors, and warnings."""

    def __init__(self):
        self.success_count = 0
        self.error_count = 0
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.created_securities: List[Dict[str, str]] = []
        self.failed_securities: List[Dict[str, str]] = []
        self.processed_rows: List[Dict[str, Any]] = []

    @property
    def is_successful(self) -> bool:
        """Check if processing was successful (no errors)."""
        return self.error_count == 0 and len(self.errors) == 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary for API response."""
        return {
            "success": self.is_successful,
            "summary": {
                "processed_count": self.success_count + self.error_count,
                "success_count": self.success_count,
                "error_count": self.error_count,
                "warnings_count": len(self.warnings),
            },
            "created_securities": self.created_securities,
            "failed_securities": self.failed_securities,
            "warnings": self.warnings[:100],  # Limit to first 100 warnings
            "errors": self.errors[:50],  # Limit to first 50 errors
            "has_more_errors": len(self.errors) > 50,
        }


class CSVValidator:
    """Validates CSV structure and data for transactions and holdings."""

    # Required columns for each template type
    REQUIRED_TRANSACTION_COLUMNS = {"date", "type"}
    REQUIRED_HOLDING_COLUMNS = {"date", "symbol", "quantity"}

    # Optional columns that are recognized
    OPTIONAL_TRANSACTION_COLUMNS = {
        "symbol",
        "quantity",
        "price",
        "fees",
        "currency",
        "description",
    }
    OPTIONAL_HOLDING_COLUMNS = {"cost_basis", "institution_price", "currency"}

    # Valid transaction types
    VALID_TRANSACTION_TYPES = {
        "buy",
        "sell",
        "dividend",
        "interest",
        "fee",
        "deposit",
        "withdrawal",
        "transfer_in",
        "transfer_out",
        "split",
        "spinoff",
    }

    def validate_transactions_csv(self, df: pd.DataFrame) -> List[str]:
        """Validate transactions CSV structure and data."""
        errors = []

        # Normalize column names to lowercase
        df.columns = df.columns.str.strip().str.lower()

        # Check required columns
        missing_cols = self.REQUIRED_TRANSACTION_COLUMNS - set(df.columns)
        if missing_cols:
            errors.append(f"Missing required columns: {', '.join(missing_cols)}")
            return errors  # Can't proceed without required columns

        # Validate each row
        for idx, row in df.iterrows():
            row_num = idx + 2  # Account for header and 0-indexing

            # Check date
            if pd.isna(row.get("date")):
                errors.append(f"Row {row_num}: Missing date")

            # Check type
            tx_type = str(row.get("type", "")).strip().lower()
            if not tx_type:
                errors.append(f"Row {row_num}: Missing transaction type")
            elif tx_type not in self.VALID_TRANSACTION_TYPES:
                errors.append(f"Row {row_num}: Invalid transaction type '{tx_type}'")

            # For buy/sell, symbol is required
            if tx_type in ["buy", "sell"] and not row.get("symbol"):
                errors.append(f"Row {row_num}: Symbol required for {tx_type} transactions")

        return errors

    def validate_holdings_csv(self, df: pd.DataFrame) -> List[str]:
        """Validate holdings CSV structure and data."""
        errors = []

        # Normalize column names
        df.columns = df.columns.str.strip().str.lower()

        # Check required columns
        missing_cols = self.REQUIRED_HOLDING_COLUMNS - set(df.columns)
        if missing_cols:
            errors.append(f"Missing required columns: {', '.join(missing_cols)}")
            return errors

        # Validate each row
        for idx, row in df.iterrows():
            row_num = idx + 2

            # Check date
            if pd.isna(row.get("date")):
                errors.append(f"Row {row_num}: Missing date")

            # Check symbol
            if not row.get("symbol"):
                errors.append(f"Row {row_num}: Missing symbol")

            # Check quantity
            try:
                qty = float(row.get("quantity", 0))
                if qty <= 0:
                    errors.append(f"Row {row_num}: Quantity must be positive")
            except (ValueError, TypeError):
                errors.append(f"Row {row_num}: Invalid quantity")

        return errors


class SecurityMatcher:
    """Intelligently matches securities from CSV data to database records."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._cache: Dict[str, Optional[SecurityMaster]] = {}

    def match_or_create(
        self, symbol: str, name: Optional[str] = None, result: Optional[CSVProcessorResult] = None
    ) -> Optional[SecurityMaster]:
        """
        Match symbol to existing security or create new one.

        Args:
            symbol: Security symbol/ticker
            name: Optional security name
            result: Result object to track created securities

        Returns:
            SecurityMaster object or None if failed
        """
        if not symbol:
            return None

        symbol = symbol.upper().strip()

        # Check cache first
        if symbol in self._cache:
            return self._cache[symbol]

        # Try to find existing security
        security = security_crud.get_by_symbol(self.db, symbol=symbol)

        if not security:
            # Create new security
            security = self._create_security(symbol, name, result)

        # Cache the result
        self._cache[symbol] = security
        return security

    def _create_security(
        self, symbol: str, name: Optional[str] = None, result: Optional[CSVProcessorResult] = None
    ) -> Optional[SecurityMaster]:
        """Create a new security in the database."""
        try:
            # Determine security type based on symbol patterns
            security_type = self._guess_security_type(symbol)

            # Create security data
            security_data = SecurityCreate(
                symbol=symbol,
                name=name or symbol,  # Use symbol as name if not provided
                security_type=security_type,
                currency="USD",  # Default to USD
                is_active=True,
            )

            # Create in database
            security = security_crud.create(self.db, obj_in=security_data)

            # Track creation
            if result:
                result.created_securities.append(
                    {
                        "symbol": symbol,
                        "name": name or symbol,
                        "type": security_type,
                        "status": "created",
                    }
                )

            logger.info(f"Created new security: {symbol}")
            return security

        except Exception as e:
            logger.error(f"Failed to create security {symbol}: {e}")
            if result:
                result.failed_securities.append({"symbol": symbol, "error": str(e)})
            return None

    def _guess_security_type(self, symbol: str) -> str:
        """Guess security type from symbol patterns."""
        symbol = symbol.upper()

        # Crypto patterns
        if symbol in ["BTC", "ETH", "USDT", "USDC", "BNB", "XRP", "ADA", "SOL"]:
            return "crypto"
        if "-USD" in symbol or "USD-" in symbol:
            return "crypto"

        # ETF patterns (3-4 letters, common ETF symbols)
        etf_symbols = {"SPY", "QQQ", "IWM", "VTI", "VOO", "EEM", "GLD", "TLT"}
        if symbol in etf_symbols:
            return "fund"

        # Cash/Money market
        if symbol in ["CASH", "USD", "EUR", "GBP", "MONEY", "MM"]:
            return "cash"

        # Default to equity
        return "equity"


class CSVProcessor:
    """Main CSV processing service for transactions and holdings imports."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.validator = CSVValidator()
        self.security_matcher = SecurityMatcher(db)
        self.portfolio_repo = PortfolioRepository(db)

    def process_transactions_csv(
        self,
        csv_content: Union[str, bytes],
        user_id: UUID,
        account_id: UUID,
        source: str = "csv_upload",
        dry_run: bool = False,
    ) -> CSVProcessorResult:
        """
        Process transactions CSV file for a specific account.

        Args:
            csv_content: CSV file content
            account_id: Portfolio account ID
            source: Source identifier for tracking
            dry_run: If True, validate only without database changes

        Returns:
            Processing result with counts and errors
        """
        result = CSVProcessorResult()

        try:
            # Verify account exists and user has access
            account = self.portfolio_repo.get_by_user_and_id(user_id, account_id)
            if not account:
                result.errors.append(f"Account {account_id} not found")
                return result

            # Parse CSV
            df = self._parse_csv_content(csv_content)
            if df is None or df.empty:
                result.errors.append("CSV file is empty or invalid")
                return result

            # Validate CSV structure
            validation_errors = self.validator.validate_transactions_csv(df)
            if validation_errors:
                result.errors.extend(validation_errors)
                return result

            # Process each row
            for idx, row in df.iterrows():
                try:
                    if not dry_run:
                        self._process_transaction_row(row, account, source, result)
                    else:
                        # In dry run, just validate
                        self._validate_transaction_row(row, result)
                    result.success_count += 1
                except Exception as e:
                    result.error_count += 1
                    result.errors.append(f"Row {idx + 2}: {str(e)}")

            # Commit if not dry run
            if not dry_run and result.is_successful:
                self.db.commit()
                logger.info(
                    f"Imported {result.success_count} transactions for account {account_id}"
                )
            else:
                self.db.rollback()

        except Exception as e:
            self.db.rollback()
            result.errors.append(f"Processing failed: {str(e)}")
            logger.error(f"CSV processing error: {e}")

        return result

    def process_holdings_csv(
        self,
        csv_content: Union[str, bytes],
        user_id: UUID,
        account_id: UUID,
        source: str = "csv_upload",
        dry_run: bool = False,
    ) -> CSVProcessorResult:
        """Process holdings CSV file for a specific account."""
        result = CSVProcessorResult()

        try:
            # Verify account
            account = self.portfolio_repo.get_by_user_and_id(user_id, account_id)
            if not account:
                result.errors.append(f"Account {account_id} not found")
                return result

            # Parse CSV
            df = self._parse_csv_content(csv_content)
            if df is None or df.empty:
                result.errors.append("CSV file is empty or invalid")
                return result

            # Validate structure
            validation_errors = self.validator.validate_holdings_csv(df)
            if validation_errors:
                result.errors.extend(validation_errors)
                return result

            # Process each row
            for idx, row in df.iterrows():
                try:
                    if not dry_run:
                        self._process_holding_row(row, account, source, result)
                    else:
                        self._validate_holding_row(row, result)
                    result.success_count += 1
                except Exception as e:
                    result.error_count += 1
                    result.errors.append(f"Row {idx + 2}: {str(e)}")

            # Commit if successful
            if not dry_run and result.is_successful:
                self.db.commit()
                logger.info(f"Imported {result.success_count} holdings for account {account_id}")
            else:
                self.db.rollback()

        except Exception as e:
            self.db.rollback()
            result.errors.append(f"Processing failed: {str(e)}")
            logger.error(f"CSV processing error: {e}")

        return result

    def _parse_csv_content(self, csv_content: Union[str, bytes]) -> Optional[pd.DataFrame]:
        """Parse CSV content into DataFrame with error handling."""
        try:
            if isinstance(csv_content, bytes):
                csv_content = csv_content.decode("utf-8")

            # Try to parse CSV
            df = pd.read_csv(
                io.StringIO(csv_content),
                dtype=str,  # Read everything as string initially
                na_filter=False,  # Don't convert empty strings to NaN
                skipinitialspace=True,
            )

            # Strip whitespace from column names and values
            df.columns = df.columns.str.strip()
            df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

            return df

        except Exception as e:
            logger.error(f"CSV parsing failed: {e}")
            return None

    def _process_transaction_row(
        self, row: pd.Series, account: Any, source: str, result: CSVProcessorResult
    ):
        """Process a single transaction row."""
        # Normalize column names
        row.index = row.index.str.lower()

        # Parse transaction data
        tx_type = row.get("type", "").lower()
        symbol = row.get("symbol", "").upper() if row.get("symbol") else None

        # Match or create security if needed
        security = None
        if symbol and tx_type in ["buy", "sell", "dividend"]:
            security = self.security_matcher.match_or_create(symbol, result=result)
            if not security and tx_type in ["buy", "sell"]:
                raise ValueError(f"Could not match or create security: {symbol}")

        # Parse numeric fields
        quantity = self._parse_decimal(row.get("quantity", "0"))
        price = self._parse_decimal(row.get("price", "0"))
        fees = self._parse_decimal(row.get("fees", "0"))

        # Parse date
        trade_date = self._parse_date(row.get("date", ""))
        if not trade_date:
            raise ValueError("Invalid or missing date")

        # Map transaction type
        tx_category, tx_side = self._map_transaction_type(tx_type)

        # Create transaction
        tx_data = TransactionCreate(
            account_id=account.id,
            security_id=security.id if security else None,
            transaction_type=tx_category,
            transaction_subtype=tx_side,
            quantity=quantity,
            price=price,
            fees=fees,
            transaction_date=trade_date,
            currency=row.get("currency", account.currency or "USD").upper(),
            description=row.get("description", "") or f"{tx_type.upper()} {symbol or ''}",
        )

        transaction = TransactionRepository.create(self.db, obj_in=tx_data)
        result.processed_rows.append({"type": "transaction", "id": str(transaction.id)})

    def _process_holding_row(
        self, row: pd.Series, account: Any, source: str, result: CSVProcessorResult
    ):
        """Process a single holding row."""
        # Normalize column names
        row.index = row.index.str.lower()

        # Get symbol (required)
        symbol = row.get("symbol", "").upper()
        if not symbol:
            raise ValueError("Symbol is required for holdings")

        # Match or create security
        security = self.security_matcher.match_or_create(symbol, result=result)
        if not security:
            raise ValueError(f"Could not match or create security: {symbol}")

        # Parse numeric fields
        quantity = self._parse_decimal(row.get("quantity", "0"))
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        cost_basis = self._parse_decimal(row.get("cost_basis", ""))

        # Parse date
        as_of_date = self._parse_date(row.get("date", ""))
        if not as_of_date:
            as_of_date = datetime.now().date()

        # Create holding
        holding_data = HoldingCreate(
            account_id=account.id,
            security_id=security.id,
            quantity=quantity,
            cost_basis=cost_basis * quantity if cost_basis else None,
            currency=row.get("currency", account.currency or "USD").upper(),
            as_of_date=as_of_date,
        )

        holding = HoldingRepository.create(self.db, obj_in=holding_data)
        result.processed_rows.append({"type": "holding", "id": str(holding.id)})

    def _validate_transaction_row(self, row: pd.Series, result: CSVProcessorResult):
        """Validate a transaction row without creating it."""
        row.index = row.index.str.lower()

        # Check required fields
        if not row.get("date"):
            raise ValueError("Date is required")
        if not row.get("type"):
            raise ValueError("Transaction type is required")

        tx_type = row.get("type", "").lower()
        if tx_type in ["buy", "sell"] and not row.get("symbol"):
            raise ValueError(f"Symbol required for {tx_type} transactions")

    def _validate_holding_row(self, row: pd.Series, result: CSVProcessorResult):
        """Validate a holding row without creating it."""
        row.index = row.index.str.lower()

        # Check required fields
        if not row.get("symbol"):
            raise ValueError("Symbol is required")
        if not row.get("quantity"):
            raise ValueError("Quantity is required")

    def _parse_decimal(self, value: Any) -> Optional[Decimal]:
        """Parse decimal value with error handling."""
        if not value or value == "":
            return None

        try:
            # Remove common formatting
            if isinstance(value, str):
                value = value.replace(",", "").replace("$", "").strip()
            return Decimal(value) if value else None
        except (InvalidOperation, ValueError):
            return None

    def _parse_date(self, date_str: Any) -> Optional[datetime.date]:
        """Parse date with multiple format support."""
        if not date_str:
            return None

        # Common date formats
        formats = ["%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%m-%d-%Y", "%d-%m-%Y", "%Y/%m/%d"]

        for fmt in formats:
            try:
                return datetime.strptime(str(date_str), fmt).date()
            except ValueError:
                continue

        # Try pandas parser as fallback
        try:
            return pd.to_datetime(date_str).date()
        except:
            return None

    def _map_transaction_type(self, tx_type: str) -> Tuple[str, Optional[str]]:
        """Map CSV transaction types to internal categories."""
        mapping = {
            "buy": ("trade", "buy"),
            "sell": ("trade", "sell"),
            "dividend": ("income", "dividend"),
            "interest": ("income", "interest"),
            "fee": ("expense", "fee"),
            "deposit": ("transfer", "deposit"),
            "withdrawal": ("transfer", "withdrawal"),
            "transfer_in": ("transfer", "in"),
            "transfer_out": ("transfer", "out"),
            "split": ("corporate_action", "split"),
            "spinoff": ("corporate_action", "spinoff"),
        }

        return mapping.get(tx_type, ("other", None))


# Factory function for getting processor
def get_csv_processor(db: AsyncSession) -> CSVProcessor:
    """Get CSV processor instance."""
    return CSVProcessor(db)

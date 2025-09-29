from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Dict, List, Optional, Set

import pandas as pd


class CSVValidator:
    """
    Validates CSV files for transactions and holdings imports.
    Aligned with Plaid taxonomy and simplified column structure.
    """

    # Required columns for each template type
    REQUIRED_TRANSACTION_COLUMNS = {"date", "type"}
    REQUIRED_HOLDING_COLUMNS = {"date", "symbol", "quantity"}

    # Optional columns that should be recognized
    OPTIONAL_TRANSACTION_COLUMNS = {
        "symbol",
        "quantity",
        "price",
        "fees",
        "currency",
        "description",
    }

    OPTIONAL_HOLDING_COLUMNS = {"cost_basis", "institution_price", "currency"}

    # Valid transaction types (Plaid-aligned)
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

    # Valid currency codes (ISO 4217)
    VALID_CURRENCIES = {
        "USD",
        "EUR",
        "GBP",
        "JPY",
        "CAD",
        "AUD",
        "CHF",
        "CNY",
        "HKD",
        "SGD",
        "NZD",
        "SEK",
        "NOK",
        "DKK",
        "PLN",
        "CZK",
        "HUF",
        "RUB",
        "BRL",
        "MXN",
        "KRW",
        "INR",
        "THB",
        "TRY",
    }

    def validate_transactions_csv(self, df: pd.DataFrame) -> List[str]:
        """
        Validate transactions CSV structure and data.

        Args:
            df: DataFrame containing CSV data

        Returns:
            List of validation error messages
        """
        errors = []

        # Check basic structure
        errors.extend(self._validate_basic_structure(df, "transactions"))

        # Check required columns
        errors.extend(
            self._validate_required_columns(df, self.REQUIRED_TRANSACTION_COLUMNS, "transactions")
        )

        # Check for unknown columns
        errors.extend(
            self._validate_known_columns(
                df,
                self.REQUIRED_TRANSACTION_COLUMNS | self.OPTIONAL_TRANSACTION_COLUMNS,
                "transactions",
            )
        )

        # Validate row data
        errors.extend(self._validate_transaction_rows(df))

        return errors

    def validate_holdings_csv(self, df: pd.DataFrame) -> List[str]:
        """
        Validate holdings CSV structure and data.

        Args:
            df: DataFrame containing CSV data

        Returns:
            List of validation error messages
        """
        errors = []

        # Check basic structure
        errors.extend(self._validate_basic_structure(df, "holdings"))

        # Check required columns
        errors.extend(
            self._validate_required_columns(df, self.REQUIRED_HOLDING_COLUMNS, "holdings")
        )

        # Check for unknown columns
        errors.extend(
            self._validate_known_columns(
                df, self.REQUIRED_HOLDING_COLUMNS | self.OPTIONAL_HOLDING_COLUMNS, "holdings"
            )
        )

        # Validate row data
        errors.extend(self._validate_holding_rows(df))

        return errors

    def _validate_basic_structure(self, df: pd.DataFrame, template_type: str) -> List[str]:
        """Validate basic CSV structure."""
        errors = []

        if df.empty:
            errors.append(f"{template_type.title()} CSV is empty")
            return errors

        if len(df.columns) == 0:
            errors.append(f"{template_type.title()} CSV has no columns")

        if len(df) == 0:
            errors.append(f"{template_type.title()} CSV has no data rows")

        # Check for duplicate columns
        duplicate_cols = df.columns[df.columns.duplicated()].tolist()
        if duplicate_cols:
            errors.append(f"Duplicate columns found: {', '.join(duplicate_cols)}")

        return errors

    def _validate_required_columns(
        self, df: pd.DataFrame, required_columns: Set[str], template_type: str
    ) -> List[str]:
        """Validate that all required columns are present."""
        errors = []

        present_columns = set(df.columns.str.strip().str.lower())
        missing_columns = required_columns - present_columns

        if missing_columns:
            errors.append(
                f"Missing required columns in {template_type} CSV: "
                f"{', '.join(sorted(missing_columns))}"
            )

        return errors

    def _validate_known_columns(
        self, df: pd.DataFrame, known_columns: Set[str], template_type: str
    ) -> List[str]:
        """Validate that all columns are recognized (warn about unknown columns)."""
        errors = []

        present_columns = set(df.columns.str.strip().str.lower())
        unknown_columns = present_columns - known_columns

        if unknown_columns:
            # This is a warning, not an error
            errors.append(
                f"Unknown columns in {template_type} CSV will be ignored: "
                f"{', '.join(sorted(unknown_columns))}"
            )

        return errors

    def _validate_transaction_rows(self, df: pd.DataFrame) -> List[str]:
        """Validate individual transaction rows."""
        errors = []

        for idx, row in df.iterrows():
            row_errors = []
            row_num = idx + 2  # +2 for 1-based indexing and header row

            # Validate date
            date_error = self._validate_date(row.get("date", ""), "date")
            if date_error:
                row_errors.append(date_error)

            # Validate transaction type
            tx_type = str(row.get("type", "")).strip().lower()
            if not tx_type:
                row_errors.append("PortfolioTransaction type is required")
            elif tx_type not in self.VALID_TRANSACTION_TYPES:
                row_errors.append(
                    f"Invalid transaction type '{tx_type}'. "
                    f"Valid types: {', '.join(sorted(self.VALID_TRANSACTION_TYPES))}"
                )

            # Validate symbol is provided for buy/sell transactions
            if tx_type in ["buy", "sell"] and not str(row.get("symbol", "")).strip():
                row_errors.append("Symbol is required for buy/sell transactions")

            # Validate numeric fields
            numeric_fields = ["quantity", "price", "fees"]
            for field in numeric_fields:
                value = row.get(field, "")
                if value and str(value).strip():
                    error = self._validate_decimal(str(value).strip(), field)
                    if error:
                        row_errors.append(error)

            # Validate currency
            currency = str(row.get("currency", "")).strip().upper()
            if currency and currency not in self.VALID_CURRENCIES:
                row_errors.append(f"Invalid currency code '{currency}'")

            # Business logic validations
            if tx_type in ["buy", "sell"]:
                quantity = self._parse_decimal_value(row.get("quantity", "0"))
                price = self._parse_decimal_value(row.get("price", "0"))

                if not quantity or quantity <= 0:
                    row_errors.append("Quantity must be greater than 0 for buy/sell transactions")

                if not price or price <= 0:
                    row_errors.append("Price must be greater than 0 for buy/sell transactions")

            # Add row-specific errors
            if row_errors:
                errors.extend([f"Row {row_num}: {error}" for error in row_errors])

        return errors

    def _validate_holding_rows(self, df: pd.DataFrame) -> List[str]:
        """Validate individual holding rows."""
        errors = []

        for idx, row in df.iterrows():
            row_errors = []
            row_num = idx + 2  # +2 for 1-based indexing and header row

            # Validate date
            date_error = self._validate_date(row.get("date", ""), "date")
            if date_error:
                row_errors.append(date_error)

            # Validate symbol (required)
            if not str(row.get("symbol", "")).strip():
                row_errors.append("Symbol is required")

            # Validate quantity (required)
            quantity_error = self._validate_decimal(
                str(row.get("quantity", "")).strip(), "quantity"
            )
            if quantity_error:
                row_errors.append(quantity_error)
            else:
                quantity = self._parse_decimal_value(row.get("quantity", "0"))
                if not quantity or quantity <= 0:
                    row_errors.append("Quantity must be greater than 0")

            # Validate numeric fields
            numeric_fields = ["cost_basis", "institution_price"]
            for field in numeric_fields:
                value = row.get(field, "")
                if value and str(value).strip():
                    error = self._validate_decimal(str(value).strip(), field)
                    if error:
                        row_errors.append(error)

            # Validate currency
            currency = str(row.get("currency", "")).strip().upper()
            if currency and currency not in self.VALID_CURRENCIES:
                row_errors.append(f"Invalid currency code '{currency}'")

            # Add row-specific errors
            if row_errors:
                errors.extend([f"Row {row_num}: {error}" for error in row_errors])

        return errors

    def _validate_date(self, date_str: str, field_name: str) -> Optional[str]:
        """Validate date format."""
        if not str(date_str).strip():
            return f"{field_name} is required"

        date_formats = [
            "%Y-%m-%d",  # 2024-01-15
            "%m/%d/%Y",  # 01/15/2024
            "%d/%m/%Y",  # 15/01/2024
            "%Y-%m-%d %H:%M:%S",  # 2024-01-15 10:30:00
            "%d-%m-%Y",  # 15-01-2024
        ]

        for fmt in date_formats:
            try:
                datetime.strptime(str(date_str).strip(), fmt)
                return None  # Valid date
            except ValueError:
                continue

        return f"Invalid date format for {field_name}: '{date_str}'. Expected formats: YYYY-MM-DD, MM/DD/YYYY, DD/MM/YYYY"

    def _validate_decimal(self, value_str: str, field_name: str) -> Optional[str]:
        """Validate decimal/numeric field."""
        if not value_str:
            return None  # Empty values are allowed for optional fields

        try:
            # Remove common formatting
            cleaned = value_str.replace(",", "").replace("$", "").strip()
            if not cleaned:
                return None

            Decimal(cleaned)
            return None  # Valid decimal
        except (InvalidOperation, ValueError):
            return f"Invalid numeric value for {field_name}: '{value_str}'"

    def _parse_decimal_value(self, value: str) -> Optional[Decimal]:
        """Parse decimal value, return None if invalid."""
        try:
            cleaned = str(value).replace(",", "").replace("$", "").strip()
            return Decimal(cleaned) if cleaned else None
        except (InvalidOperation, ValueError):
            return None

    def get_template_info(self, template_type: str) -> Dict[str, any]:
        """Get information about a template type for help/documentation."""
        if template_type == "transactions":
            return {
                "required_columns": sorted(self.REQUIRED_TRANSACTION_COLUMNS),
                "optional_columns": sorted(self.OPTIONAL_TRANSACTION_COLUMNS),
                "valid_transaction_types": sorted(self.VALID_TRANSACTION_TYPES),
                "supported_currencies": sorted(self.VALID_CURRENCIES),
                "date_formats": ["YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY", "DD-MM-YYYY"],
                "description": "Import transactions for a specific account. PortfolioAccount is selected before upload.",
                "notes": [
                    "Symbol is required for buy/sell transactions",
                    "Quantity and price must be > 0 for buy/sell",
                    "System will intelligently match securities using fuzzy matching",
                    "New securities will be created automatically if not found",
                ],
            }
        elif template_type == "holdings":
            return {
                "required_columns": sorted(self.REQUIRED_HOLDING_COLUMNS),
                "optional_columns": sorted(self.OPTIONAL_HOLDING_COLUMNS),
                "supported_currencies": sorted(self.VALID_CURRENCIES),
                "date_formats": ["YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY", "DD-MM-YYYY"],
                "description": "Import opening positions for a specific account. PortfolioAccount is selected before upload.",
                "notes": [
                    "Symbol and quantity are always required",
                    "Quantity must be > 0",
                    "Cost basis is per-share cost",
                    "System will fetch current market data automatically",
                ],
            }
        else:
            return {}

# app/services/csv/__init__.py

"""
CSV Import Services

This module provides comprehensive CSV import functionality for the portfolios analytics app,
supporting both transactions and holdings imports with intelligent normalization and
securities mapping.

Key Features:
- Flexible securities identification (Symbol, ISIN, CUSIP)
- Automatic account creation and mapping
- Comprehensive validation with helpful error messages
- Market data integration via Alpha Vantage
- Support for multiple import sources (manual, Plaid, broker templates)

Usage:
    from app.services.csv import get_csv_processor

    processor = get_csv_processor(db)
    result = processor.process_transactions_csv(csv_content, user_id)
"""

from .csv_processor import CSVProcessor, CSVProcessorResult, get_csv_processor
from .security_matcher import SecurityMatcher
from .validators import CSVValidator

__all__ = [
    "CSVProcessor",
    "get_csv_processor",
    "CSVProcessorResult",
    "SecurityMatcher",
    "CSVValidator",
]

import enum

from sqlalchemy import Enum


class AccountTypeEnum(enum.Enum):
    """
    Primary account classification for financial accounts.

    High-level categorization that determines how accounts are processed
    and displayed in the user interface.
    """

    INVESTMENT = "investment"  # Brokerage, 401k, IRA accounts
    DEPOSITORY = "depository"  # Checking, savings, money market
    CREDIT = "credit"  # Credit cards, lines of credit
    LOAN = "loan"  # Mortgages, student loans
    OTHER = "other"  # Catch-all for other account types


class AccountSubtypeEnum(enum.Enum):
    """
    Detailed account classification for specific account types.

    Provides granular categorization for specialized handling,
    tax implications, and regulatory compliance.
    """

    # Investment account subtypes
    BROKERAGE = "brokerage"
    IRA = "ira"
    ROTH = "roth"
    FOUR_01K = "401k"
    ISA = "isa"

    # Depository account subtypes
    CHECKING = "checking"
    SAVINGS = "savings"
    MONEY_MARKET = "money market"
    CD = "cd"

    # Credit account subtypes
    CREDIT_CARD = "credit card"
    LINE_OF_CREDIT = "line of credit"

    # Loan account subtypes
    MORTGAGE = "mortgage"
    STUDENT = "student"
    PERSONAL = "personal"
    AUTO = "auto"
    BUSINESS = "business"
    COMMERCIAL = "commercial"

    # Other account subtypes
    CASH_MANAGEMENT = "cash management"
    CRYPTO = "crypto"
    PAYPAL = "paypal"
    LOAN = "loan"
    OTHER = "other"


class TransactionTypeEnum(enum.Enum):
    """
    High-level transaction categories for portfolio activity.

    Primary classification for transaction processing and
    performance calculation workflows.
    """

    BUY = "buy"  # Purchase transactions
    SELL = "sell"  # Sale transactions
    CASH = "cash"  # Cash movements
    TRANSFER = "transfer"  # Asset transfers
    FEE = "fee"  # Fees and expenses
    DIVIDEND = "dividend"  # Dividend payments
    INTEREST = "interest"  # Interest payments
    CANCEL = "cancel"  # Cancelled transactions
    ADJUSTMENT = "adjustment"  # Manual adjustments
    SPLIT = "split"  # Stock splits
    MERGER = "merger"  # Merger transactions
    SPINOFF = "spinoff"  # Spinoff transactions


class TransactionSubtypeEnum(enum.Enum):
    """
    Detailed transaction classifications for specific processing.

    Granular categorization enabling precise transaction handling,
    tax reporting, and performance attribution.
    """

    BUY = "buy"
    SELL = "sell"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    DIVIDEND = "dividend"
    INTEREST = "interest"
    FEE = "fee"
    TRANSFER_IN = "transfer in"
    TRANSFER_OUT = "transfer out"
    CANCEL = "cancel"
    ADJUSTMENT = "adjustment"
    STOCK_SPLIT = "stock split"
    MERGER = "merger"
    SPINOFF = "spinoff"


class DataSourceEnum(enum.Enum):
    """
    Data origin tracking for audit and reliability assessment.

    Critical for data lineage, quality assessment, and
    troubleshooting data inconsistencies.
    """

    PLAID = "plaid"  # Plaid API integration
    YFINANCE = "yfinance"  # Yahoo Finance API
    ALPHAVANTAGE = "alphavantage"  # Alpha Vantage API
    MANUAL = "manual"  # User manual entry
    CSV = "csv"  # CSV/Excel upload
    CALCULATED = "calculated"  # System computed values


# SQLAlchemy Enum type mappings for use in model definitions
ACCOUNT_TYPE_ENUM = Enum(AccountTypeEnum, name="account_type_enum")
ACCOUNT_SUBTYPE_ENUM = Enum(AccountSubtypeEnum, name="account_subtype_enum")
TRANSACTION_TYPE_ENUM = Enum(TransactionTypeEnum, name="transaction_type_enum")
TRANSACTION_SUBTYPE_ENUM = Enum(TransactionSubtypeEnum, name="transaction_subtype_enum")
DATA_SOURCE_ENUM = Enum(DataSourceEnum, name="data_source_enum")

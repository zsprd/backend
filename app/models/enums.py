from enum import Enum


class AccountCategory(str, Enum):
    """Account category enum - single source of truth for both SQLAlchemy and Pydantic."""
    INVESTMENT = "investment"
    DEPOSITORY = "depository"
    CREDIT = "credit"
    LOAN = "loan"
    OTHER = "other"


class AccountSubtypeCategory(str, Enum):
    """Account subtype enum - single source of truth."""
    # Investment subtypes
    BROKERAGE = "brokerage"
    IRA = "ira"
    ROTH_IRA = "roth_ira"
    FOUR_OH_ONE_K = "401k"
    FOUR_OH_THREE_B = "403b"
    
    # Depository subtypes
    CHECKING = "checking"
    SAVINGS = "savings"
    MONEY_MARKET = "money_market"
    CD = "cd"
    
    # Credit subtypes
    CREDIT_CARD = "credit_card"
    
    # Loan subtypes
    MORTGAGE = "mortgage"
    STUDENT = "student"
    PERSONAL = "personal"
    
    # Other
    CASH_MANAGEMENT = "cash_management"
    CRYPTO_EXCHANGE = "crypto_exchange"


class SecurityCategory(str, Enum):
    """Security type enum."""
    EQUITY = "equity"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    BOND = "bond"
    OPTION = "option"
    WARRANT = "warrant"
    CRYPTOCURRENCY = "cryptocurrency"
    CASH = "cash"
    COMMODITY = "commodity"
    DERIVATIVE = "derivative"
    OTHER = "other"


class DataProviderCategory(str, Enum):
    """Data provider enum."""
    ALPHAVANTAGE = "alphavantage"
    PLAID = "plaid"
    MANUAL = "manual"
    CALCULATED = "calculated"


class TransactionCategory(str, Enum):
    """Transaction type enum."""
    # Investment transactions
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    INTEREST = "interest"
    FEE = "fee"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    
    # Corporate actions
    SPLIT = "split"
    MERGER = "merger"
    SPINOFF = "spinoff"
    
    # Cash transactions
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    PAYMENT = "payment"
    PURCHASE = "purchase"
    REFUND = "refund"
    CANCEL = "cancel"
    ADJUSTMENT = "adjustment"
    OTHER = "other"


class TransactionSideCategory(str, Enum):
    """Transaction side enum."""
    BUY = "buy"
    SELL = "sell"


class ImportCategory(str, Enum):
    """Import type enum."""
    TRANSACTIONS = "transactions"
    HOLDINGS = "holdings"
    ACCOUNTS = "accounts"
    MARKET_DATA = "market_data"


class ImportStatusCategory(str, Enum):
    """Import status enum."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ImportProviderCategory(str, Enum):
    """Import provider enum."""
    CSV_UPLOAD = "csv_upload"
    PLAID = "plaid"
    ALPHAVANTAGE = "alphavantage"
    MANUAL = "manual"


class PlaidItemStatusCategory(str, Enum):
    """Plaid item status enum."""
    GOOD = "good"
    PENDING = "pending"
    ERROR = "error"
    LOGIN_REQUIRED = "login_required"
    PENDING_EXPIRATION = "pending_expiration"
    PENDING_DISCONNECT = "pending_disconnect"


class SubscriptionStatusCategory(str, Enum):
    """Subscription status enum."""
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    TRIALING = "trialing"


class AuditActionCategory(str, Enum):
    """Audit action enum."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    IMPORT = "import"
    EXPORT = "export"
    SYNC = "sync"


class ReportTypeCategory(str, Enum):
    """Report type enum."""
    PORTFOLIO_SUMMARY = "portfolio_summary"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    RISK_ANALYSIS = "risk_analysis"
    HOLDINGS_DETAIL = "holdings_detail"
    TRANSACTION_HISTORY = "transaction_history"
    TAX_SUMMARY = "tax_summary"


class ReportFormatCategory(str, Enum):
    """Report format enum."""
    PDF = "pdf"
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"


class ReportStatusCategory(str, Enum):
    """Report status enum."""
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"


class AlertTypeCategory(str, Enum):
    """Alert type enum."""
    PRICE_CHANGE = "price_change"
    PORTFOLIO_VALUE = "portfolio_value"
    ALLOCATION_DRIFT = "allocation_drift"
    DRAWDOWN = "drawdown"
    VOLATILITY = "volatility"
    PERFORMANCE = "performance"


class AlertStatusCategory(str, Enum):
    """Alert status enum."""
    ACTIVE = "active"
    PAUSED = "paused"
    TRIGGERED = "triggered"
    DISABLED = "disabled"


class AlertFrequencyCategory(str, Enum):
    """Alert frequency enum."""
    REAL_TIME = "real_time"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class NotificationTypeCategory(str, Enum):
    """Notification type enum."""
    ALERT = "alert"
    SYSTEM = "system"
    IMPORT = "import"
    ERROR = "error"
    WELCOME = "welcome"


class NotificationChannelCategory(str, Enum):
    """Notification channel enum."""
    IN_APP = "in_app"
    EMAIL = "email"
    PUSH = "push"


class ThresholdOperatorCategory(str, Enum):
    """Threshold operator enum."""
    GT = "gt"  # greater than
    LT = "lt"  # less than
    GTE = "gte"  # greater than or equal
    LTE = "lte"  # less than or equal
    EQ = "eq"  # equal
    NE = "ne"  # not equal


class LotMethodCategory(str, Enum):
    """Lot method enum for tax calculations."""
    FIFO = "fifo"
    LIFO = "lifo"
    AVERAGE_COST = "average_cost"
    SPECIFIC_ID = "specific_id"


class CashTransactionTypeCategory(str, Enum):
    """Cash transaction type enum."""
    PURCHASE = "purchase"
    PAYMENT = "payment"
    TRANSFER = "transfer"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    FEE = "fee"
    INTEREST = "interest"
    DIVIDEND = "dividend"
    OTHER = "other"
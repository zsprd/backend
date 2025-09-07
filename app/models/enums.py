from enum import Enum
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM


class AccountType(str, Enum):
    INVESTMENT = "investment"
    DEPOSITORY = "depository"
    CREDIT = "credit"
    LOAN = "loan"
    OTHER = "other"


class AccountSubtype(str, Enum):
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
    
    # Credit subtypes
    CREDIT_CARD = "credit_card"
    
    # Loan subtypes
    MORTGAGE = "mortgage"
    STUDENT = "student"
    
    # Other
    CASH_MANAGEMENT = "cash_management"
    CRYPTO_EXCHANGE = "crypto_exchange"


class SecurityType(str, Enum):
    EQUITY = "equity"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    BOND = "bond"
    OPTION = "option"
    CRYPTOCURRENCY = "cryptocurrency"
    CASH = "cash"
    COMMODITY = "commodity"
    OTHER = "other"


class DataSource(str, Enum):
    ALPHAVANTAGE = "alphavantage"
    PLAID = "plaid"
    MANUAL = "manual"
    CALCULATED = "calculated"


class LotMethod(str, Enum):
    FIFO = "fifo"
    LIFO = "lifo"
    AVERAGE_COST = "average_cost"
    SPECIFIC_ID = "specific_id"


class TransactionType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    INTEREST = "interest"
    FEE = "fee"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    SPLIT = "split"
    MERGER = "merger"
    SPINOFF = "spinoff"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    ADJUSTMENT = "adjustment"
    OTHER = "other"


class TransactionSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class CashTransactionType(str, Enum):
    PURCHASE = "purchase"
    PAYMENT = "payment"
    TRANSFER = "transfer"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    FEE = "fee"
    INTEREST = "interest"
    DIVIDEND = "dividend"
    OTHER = "other"


class ImportType(str, Enum):
    TRANSACTIONS = "transactions"
    HOLDINGS = "holdings"
    ACCOUNTS = "accounts"
    MARKET_DATA = "market_data"


class ImportStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ImportSource(str, Enum):
    CSV_UPLOAD = "csv_upload"
    PLAID = "plaid"
    ALPHAVANTAGE = "alphavantage"
    MANUAL = "manual"


class PlaidItemStatus(str, Enum):
    GOOD = "good"
    PENDING = "pending"
    ERROR = "error"


class SubscriptionStatus(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"


class AuditAction(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"


# Create PostgreSQL ENUM types for SQLAlchemy
account_type_enum = ENUM(AccountType, name="account_type")
account_subtype_enum = ENUM(AccountSubtype, name="account_subtype")
security_type_enum = ENUM(SecurityType, name="security_type")
data_source_enum = ENUM(DataSource, name="data_source")
lot_method_enum = ENUM(LotMethod, name="lot_method")
transaction_type_enum = ENUM(TransactionType, name="transaction_type")
transaction_side_enum = ENUM(TransactionSide, name="transaction_side")
cash_transaction_type_enum = ENUM(CashTransactionType, name="cash_transaction_type")
import_type_enum = ENUM(ImportType, name="import_type")
import_status_enum = ENUM(ImportStatus, name="import_status")
import_source_enum = ENUM(ImportSource, name="import_source")
plaid_item_status_enum = ENUM(PlaidItemStatus, name="plaid_item_status")
subscription_status_enum = ENUM(SubscriptionStatus, name="subscription_status")
audit_action_enum = ENUM(AuditAction, name="audit_action")
from enum import Enum
from sqlalchemy.dialects.postgresql import ENUM

# Create PostgreSQL ENUM types that match your database schema
# These names must exactly match the enum type names in your PostgreSQL database

class AccountCategory(str, Enum):
    INVESTMENT = "investment"
    DEPOSITORY = "depository"
    CREDIT = "credit"
    LOAN = "loan"
    OTHER = "other"


class AccountSubtypeCategory(str, Enum):
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


class SecurityCategory(str, Enum):
    EQUITY = "equity"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    BOND = "bond"
    OPTION = "option"
    CRYPTOCURRENCY = "cryptocurrency"
    CASH = "cash"
    COMMODITY = "commodity"
    OTHER = "other"


class DataProviderCategory(str, Enum):
    ALPHAVANTAGE = "alphavantage"
    PLAID = "plaid"
    MANUAL = "manual"
    CALCULATED = "calculated"


class TransactionCategory(str, Enum):
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


class TransactionSideCategory(str, Enum):
    BUY = "buy"
    SELL = "sell"


class ImportCategory(str, Enum):
    TRANSACTIONS = "transactions"
    HOLDINGS = "holdings"
    ACCOUNTS = "accounts"
    MARKET_DATA = "market_data"


class ImportStatusCategory(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ImportProviderCategory(str, Enum):
    CSV_UPLOAD = "csv_upload"
    PLAID = "plaid"
    ALPHAVANTAGE = "alphavantage"
    MANUAL = "manual"


class PlaidItemStatusCategory(str, Enum):
    GOOD = "good"
    PENDING = "pending"
    ERROR = "error"


class SubscriptionStatusCategory(str, Enum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"


class AuditActionCategory(str, Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"


account_category = ENUM(AccountCategory, name="account_category")
account_subtype_category = ENUM(AccountSubtypeCategory, name="account_subtype_category")
security_category = ENUM(SecurityCategory, name="security_category")
data_provider_category = ENUM(DataProviderCategory, name="data_provider_category")
transaction_category = ENUM(TransactionCategory, name="transaction_category")
transaction_side_category = ENUM(TransactionSideCategory, name="transaction_side_category")
import_category = ENUM(ImportCategory, name="import_category")
import_status_category = ENUM(ImportStatusCategory, name="import_status_category")
import_provider_category = ENUM(ImportProviderCategory, name="import_provider_category")
plaid_item_status_category = ENUM(PlaidItemStatusCategory, name="plaid_item_status_category")
subscription_status_category = ENUM(SubscriptionStatusCategory, name="subscription_status_category")
audit_action_category = ENUM(AuditActionCategory, name="audit_action_category")
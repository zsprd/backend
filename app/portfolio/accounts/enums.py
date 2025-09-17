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


# SQLAlchemy Enum type mappings for use in model definitions
ACCOUNT_TYPE_ENUM = Enum(AccountTypeEnum, name="account_type_enum")
ACCOUNT_SUBTYPE_ENUM = Enum(AccountSubtypeEnum, name="account_subtype_enum")

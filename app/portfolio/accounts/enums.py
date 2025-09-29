from enum import Enum


class AccountTypeEnum(Enum):
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


class AccountSubtypeEnum(Enum):
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

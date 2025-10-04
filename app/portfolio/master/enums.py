from enum import Enum


class AccountType(str, Enum):
    """Primary account classification for financial master."""

    INVESTMENT = "investment"  # Brokerage, 401k, IRA master
    DEPOSITORY = "depository"  # Checking, savings, money market
    CREDIT = "credit"  # Credit cards, lines of credit
    LOAN = "loan"  # Mortgages, student loans
    OTHER = "other"  # Catch-all for other account types


class AccountSubType(str, Enum):
    """Detailed account classification for specific account types."""

    # Investment account subtypes
    BROKERAGE = "brokerage"
    IRA_TRADITIONAL = "ira_traditional"
    IRA_ROTH = "roth_ira"
    IRA_SEP = "sep_ira"
    IRA_SIMPLE = "simple_ira"
    PLAN_401K = "401k"
    PLAN_403B = "403b"
    PLAN_457 = "457"
    HSA = "hsa"
    PLAN_529 = "529"
    ISA = "isa"
    TRUST = "trust"

    # Depository account subtypes
    CHECKING = "checking"
    SAVINGS = "savings"
    MONEY_MARKET = "money_market"
    CD = "cd"

    # Credit account subtypes
    CREDIT_CARD = "credit_card"
    LINE_OF_CREDIT = "line of credit"

    # Loan account subtypes
    MORTGAGE = "mortgage"
    STUDENT = "student"
    PERSONAL = "personal"
    AUTO = "auto"
    BUSINESS = "business"
    COMMERCIAL = "commercial"
    MARGIN = "margin_loan"

    # Alternative investment subtypes
    PRIVATE_EQUITY = "private_equity"
    VENTURE_CAPITAL = "venture_capital"
    REAL_ESTATE = "real_estate"
    HEDGE_FUND = "hedge_fund"
    ALTERNATIVE = "alternative"

    # Other account subtypes
    CASH = "cash management"
    CRYPTO = "crypto"
    PAYPAL = "paypal"
    LOAN = "loan"
    OTHER = "other"

from sqlalchemy import Enum as SAEnum


# PortfolioAccount classification
def AccountTypeEnum():
    return SAEnum(
        "investment",
        "depository",
        "credit",
        "loan",
        "other",
        name="account_type_enum",
        create_type=False,
    )


# Detailed account subtypes
def AccountSubtypeEnum():
    return SAEnum(
        "brokerage",
        "ira",
        "roth_ira",
        "401k",
        "403b",
        "checking",
        "savings",
        "money_market",
        "cd",
        "credit_card",
        "mortgage",
        "student",
        "personal",
        "cash_management",
        "crypto_exchange",
        name="account_subtype_enum",
        create_type=False,
    )


# SecurityReference types
def SecurityTypeEnum():
    return SAEnum(
        "equity",
        "fund",
        "debt",
        "option",
        "future",
        "forward",
        "swap",
        "cash",
        "digital",
        "other",
        name="security_type_enum",
        create_type=False,
    )


# SecurityReference subtypes
def SecuritySubtypeEnum():
    return SAEnum(
        "common_stock",
        "preferred_stock",
        "etf",
        "mutual_fund",
        "bond",
        "bill",
        "note",
        "option",
        "warrant",
        "cash",
        "cryptocurrency",
        name="security_subtype_enum",
        create_type=False,
    )


# PortfolioTransaction types
def TransactionTypeEnum():
    return SAEnum(
        "buy",
        "sell",
        "cash",
        "transfer",
        "fee",
        "dividend",
        "interest",
        "cancel",
        "adjustment",
        "split",
        "merger",
        "spinoff",
        name="transaction_type_enum",
        create_type=False,
    )


# PortfolioTransaction subtypes
def TransactionSubtypeEnum():
    return SAEnum(
        "buy",
        "sell",
        "deposit",
        "withdrawal",
        "dividend",
        "interest",
        "fee",
        "transfer_in",
        "transfer_out",
        "cancel",
        "adjustment",
        name="transaction_subtype_enum",
        create_type=False,
    )


# Data source tracking
def DataSourceEnum():
    return SAEnum(
        "plaid",
        "manual",
        "bulk",
        "calculated",
        "yfinance",
        "alphavantage",
        name="data_source_enum",
        create_type=False,
    )

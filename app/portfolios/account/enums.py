from sqlalchemy import Enum


def AccountTypeEnum():
    return Enum(
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
    return Enum(
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


def DataSourceEnum():
    return Enum(
        "plaid",
        "manual",
        "imported",
        name="data_source_enum",
        create_type=False,
    )

from sqlalchemy import Enum as Enum


# PortfolioTransaction types
def TransactionTypeEnum():
    return Enum(
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
    return Enum(
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


def DataSourceEnum():
    return Enum(
        "plaid",
        "manual",
        "imported",
        name="data_source_enum",
        create_type=False,
    )

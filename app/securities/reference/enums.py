from sqlalchemy import Enum


# SecurityReference types
def SecurityTypeEnum():
    return Enum(
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
    return Enum(
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


def DataSourceEnum():
    return Enum(
        "plaid",
        "manual",
        "imported",
        name="data_source_enum",
        create_type=False,
    )

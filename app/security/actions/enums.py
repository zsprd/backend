from enum import Enum


class CorporateActionType(str, Enum):
    """Types of corporate actions"""

    DIVIDEND = "dividend"
    SPLIT = "split"
    REVERSE_SPLIT = "reverse_split"
    MERGER = "merger"
    ACQUISITION = "acquisition"
    SPINOFF = "spinoff"
    RIGHTS_OFFERING = "rights_offering"
    TENDER_OFFER = "tender_offer"
    NAME_CHANGE = "name_change"
    SYMBOL_CHANGE = "symbol_change"
    DELISTING = "delisting"
    BANKRUPTCY = "bankruptcy"
    OTHER = "other"


class DividendSubtype(str, Enum):
    """Dividend-specific subtypes"""

    CASH_DIVIDEND = "cash_dividend"
    STOCK_DIVIDEND = "stock_dividend"
    SPECIAL_DIVIDEND = "special_dividend"
    RETURN_OF_CAPITAL = "return_of_capital"
    CAPITAL_GAINS_DISTRIBUTION = "capital_gains_distribution"


class SplitSubtype(str, Enum):
    """Split-specific subtypes"""

    FORWARD_SPLIT = "forward_split"  # e.g., 2-for-1
    REVERSE_SPLIT = "reverse_split"  # e.g., 1-for-10


# Example action_details JSON structures for different action types:
"""
DIVIDEND:
{
    "dividend_type": "qualified" | "non_qualified",
    "is_special": true | false,
    "frequency": "quarterly" | "monthly" | "annual" | "special"
}

SPLIT:
{
    "split_ratio": "2:1",  # 2-for-1 split
    "old_shares": 1,
    "new_shares": 2
}

REVERSE_SPLIT:
{
    "split_ratio": "1:10",  # 1-for-10 reverse split
    "old_shares": 10,
    "new_shares": 1
}

MERGER:
{
    "target_security_id": "uuid",
    "target_symbol": "XYZ",
    "exchange_ratio": "0.5",  # receive 0.5 shares of target per share
    "cash_consideration": 10.50  # additional cash per share
}

SPINOFF:
{
    "new_security_id": "uuid",
    "new_symbol": "NEWSPIN",
    "distribution_ratio": "0.1"  # receive 0.1 shares of spinoff per share held
}

SYMBOL_CHANGE:
{
    "old_symbol": "ABC",
    "new_symbol": "XYZ"
}

NAME_CHANGE:
{
    "old_name": "Old Company Name Inc.",
    "new_name": "New Company Name Corp."
}
"""

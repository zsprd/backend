from enum import Enum


class TransactionType(str, Enum):
    """Primary transaction categories"""

    BUY = "buy"  # Purchase transactions
    SELL = "sell"  # Sale transactions
    CASH = "cash"  # Cash movements
    TRANSFER = "transfer"  # Asset transfers
    FEE = "fee"  # Fees and expenses
    DIVIDEND = "dividend"  # Dividend payments
    INTEREST = "interest"  # Interest payments
    CANCEL = "cancel"  # Cancelled transactions
    ADJUSTMENT = "adjustment"  # Manual adjustments
    SPLIT = "split"  # Stock splits
    MERGER = "merger"  # Merger transactions
    SPINOFF = "spinoff"  # Spinoff transactions
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    CORPORATE_ACTION = "corporate_action"
    TAX = "tax"
    OTHER = "other"


class TransactionSubType(str, Enum):
    """Detailed transaction subtypes"""

    # Buy/Sell subtypes
    MARKET_ORDER = "market_order"
    LIMIT_ORDER = "limit_order"
    STOP_ORDER = "stop_order"
    SHORT_SALE = "short_sale"
    COVER_SHORT = "cover_short"

    # Dividend subtypes
    QUALIFIED_DIVIDEND = "qualified_dividend"
    NON_QUALIFIED_DIVIDEND = "non_qualified_dividend"
    DIVIDEND_REINVESTMENT = "dividend_reinvestment"
    RETURN_OF_CAPITAL = "return_of_capital"
    CAPITAL_GAINS_DISTRIBUTION = "capital_gains_distribution"

    # Fee subtypes
    ADVISORY_FEE = "advisory_fee"
    MANAGEMENT_FEE = "management_fee"
    COMMISSION = "commission"

    # Transfer subtypes
    ACAT = "acat"  # Automated Customer Account Transfer
    JOURNAL = "journal"

    OTHER = "other"

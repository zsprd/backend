from enum import Enum


class TransactionTypeEnum(str, Enum):
    """
    High-level transaction categories for portfolio activity.

    Primary classification for transaction processing and
    performance calculation workflows.
    """

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


class TransactionSubtypeEnum(str, Enum):
    """
    Detailed transaction classifications for specific processing.

    Granular categorization enabling precise transaction handling,
    tax reporting, and performance attribution.
    """

    BUY = "buy"
    SELL = "sell"
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    DIVIDEND = "dividend"
    INTEREST = "interest"
    FEE = "fee"
    TRANSFER_IN = "transfer in"
    TRANSFER_OUT = "transfer out"
    CANCEL = "cancel"
    ADJUSTMENT = "adjustment"
    STOCK_SPLIT = "stock split"
    MERGER = "merger"
    SPINOFF = "spinoff"

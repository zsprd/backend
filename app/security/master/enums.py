from enum import Enum


class SecurityType(str, Enum):
    """
    Broad asset class categories for securities.

    Primary classification used for asset allocation analysis
    and risk management calculations.
    """

    EQUITY = "equity"  # Stocks
    FUND = "fund"  # Mutual funds, ETFs
    DEBT = "debt"  # Bonds, bills, notes
    OPTION = "option"  # Options, warrants
    FUTURE = "future"  # Futures contracts
    FORWARD = "forward"  # Forward contracts
    SWAP = "swap"  # Swaps, CFDs
    CASH = "cash"  # Cash equivalents
    DIGITAL = "digital"  # Digital assets/crypto
    OTHER = "other"  # Commodities, REITs, alternatives


class SecuritySubtype(str, Enum):
    """
    Specific security classifications for detailed analysis.

    Granular categorization enabling precise risk modeling,
    sector analysis, and regulatory reporting.
    """

    COMMON_STOCK = "common_stock"
    PREFERRED_STOCK = "preferred_stock"
    ETF = "etf"
    MUTUAL_FUND = "mutual fund"
    INDEX_FUND = "index fund"
    BOND = "bond"
    BILL = "bill"
    NOTE = "note"
    OPTION = "option"
    WARRANT = "warrant"
    CASH = "cash"
    CRYPTOCURRENCY = "cryptocurrency"
    REIT = "reit"
    COMMODITY = "commodity"

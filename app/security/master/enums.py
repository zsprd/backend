import enum

from sqlalchemy import Enum


class SecurityTypeEnum(enum.Enum):
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


class SecuritySubtypeEnum(enum.Enum):
    """
    Specific security classifications for detailed analysis.

    Granular categorization enabling precise risk modeling,
    sector analysis, and regulatory reporting.
    """

    COMMON_STOCK = "common stock"
    PREFERRED_STOCK = "preferred stock"
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


# SQLAlchemy Enum type mappings for use in model definitions
SECURITY_TYPE_ENUM = Enum(SecurityTypeEnum, name="security_type_enum")
SECURITY_SUBTYPE_ENUM = Enum(SecuritySubtypeEnum, name="security_subtype_enum")

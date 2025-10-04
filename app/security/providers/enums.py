from enum import Enum


class SecurityProviderName(str, Enum):
    """Supported security data providers"""

    # Market data providers
    YFINANCE = "yfinance"
    BLOOMBERG = "bloomberg"
    POLYGON = "polygon"
    ALPHA_VANTAGE = "alpha_vantage"
    IEX_CLOUD = "iex_cloud"

    # Crypto data providers
    COINMARKETCAP = "coinmarketcap"
    COINGECKO = "coingecko"

    # Manual entry
    MANUAL = "manual"

    OTHER = "other"

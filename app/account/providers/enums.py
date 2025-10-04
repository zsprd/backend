from enum import Enum


class ConnectionStatus(str, Enum):
    """Provider connection status"""

    ACTIVE = "active"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PENDING = "pending"
    EXPIRED = "expired"
    REAUTH_REQUIRED = "reauth_required"


class ProviderName(str, Enum):
    """Supported data providers"""

    # External integrations
    PLAID = "plaid"
    YODLEE = "yodlee"
    COINBASE = "coinbase"
    ALPACA = "alpaca"
    INTERACTIVE_BROKERS = "interactive_brokers"

    # Manual data sources
    MANUAL = "manual"
    CSV_UPLOAD = "csv_upload"

    OTHER = "other"


class SyncStatus(str, Enum):
    """Sync attempt status"""

    SUCCESS = "success"
    ERROR = "error"
    PARTIAL = "partial"
    IN_PROGRESS = "in_progress"

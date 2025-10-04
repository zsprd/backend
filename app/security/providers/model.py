import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.security.master.model import SecurityMaster


class SecurityProvider(BaseModel):
    """
    Active data provider for security maintenance.

    Tracks which provider is actively maintaining data for each security, supporting
    transitions between manual entry and automated data feeds. Each security can have
    at most one active provider (one-to-one relationship).

    Examples:
    - User manually creates AAPL security → provider_name='manual'
    - User switches to Yahoo Finance → provider_name='yfinance'
    - System automatically fetches prices from Yahoo Finance
    - Later switches to Bloomberg → provider_name='bloomberg'
    """

    __tablename__ = "security_providers"

    security_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("security_master.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="Reference to the security (one-to-one relationship)",
    )

    provider_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Data provider: manual, yfinance, bloomberg, polygon, alpha_vantage, etc.",
    )

    external_security_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Provider's unique identifier for this security (ticker, symbol, ID)",
    )

    connection_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        index=True,
        comment="Connection state: active, disconnected, error, pending, expired",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether provider connection is active",
    )

    # Sync tracking for automated providers
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Timestamp of last successful data sync",
    )

    last_sync_status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Status of last sync attempt: success, error, partial, in_progress",
    )

    last_error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error message from last failed sync",
    )

    last_error_at: Mapped[Optional[datetime]] = mapped_column(
        nullable=True,
        comment="Timestamp of last sync error",
    )

    # Relationships
    security_master: Mapped["SecurityMaster"] = relationship(
        "SecurityMaster",
        back_populates="security_provider",
    )

    __table_args__ = (
        Index("idx_security_provider_sync", "provider_name", "connection_status", "last_sync_at"),
        {"comment": "Active data providers for security maintenance"},
    )

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.counterparty.master.model import Counterparty
    from app.account.master.model import Account


class AccountProvider(BaseModel):
    """
    Data provider/source for account data.

    Every account has exactly one provider (one-to-one relationship), which can be:
    - External integration (Plaid, Yodlee, Broker, Coinbase, etc.)
    - Manual entry (provider_name='manual')
    - CSV upload (provider_name='csv_upload')

    The provider tracks the data source, associated counterparty/institution,
    connection status, and sync history for automated providers.
    """

    __tablename__ = "portfolio_providers"

    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolio_master.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
        comment="Reference to the account (one-to-one relationship)",
    )

    provider_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Data provider: plaid, yodlee, manual, csv_upload, coinbase, state_street, etc.",
    )

    external_account_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Provider's unique account identifier",
    )

    connection_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="active",
        index=True,
        comment="Connection state: active, disconnected, error, pending, expired, reauth_required",
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
        comment="Timestamp of last successful sync",
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

    counterparty_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("counterparty_master.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Financial institution/broker associated with this account",
    )

    credentials_vault_reference: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Reference to encrypted credentials in external vault",
    )

    # Relationships
    portfolio_master: Mapped["Account"] = relationship(
        "Account",
        back_populates="portfolio_provider",
    )

    counterparty_master: Mapped[Optional["Counterparty"]] = relationship(
        "Counterparty",
        back_populates="portfolio_providers",
    )

    __table_args__ = (
        Index("idx_provider_sync", "provider_name", "connection_status", "last_sync_at"),
        Index("idx_provider_counterparty", "counterparty_id", "provider_name"),
        {"comment": "Data providers and sources for account data"},
    )

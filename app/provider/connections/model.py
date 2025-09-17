from datetime import datetime
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel
from app.portfolio.accounts.model import PortfolioAccount
from app.provider.mappings.model import ProviderMapping

if TYPE_CHECKING:
    from app.provider.institutions.model import ProviderInstitution
    from app.user.accounts.model import UserAccount


class ProviderConnection(BaseModel):
    """
    Data source connections for API integrations and file uploads.

    Manages authenticated connections to external data sources including
    Plaid bank connections, API credentials, and CSV upload sessions.
    Tracks connection health and sync status.
    """

    __tablename__ = "provider_connections"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the user who owns this connection",
    )

    institution_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("provider_institutions.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to the connected institution (if applicable)",
    )

    connection_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="User-friendly name for this connection"
    )

    provider_name: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Technical provider identifier (plaid, csv, yfinance)"
    )

    data_source: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Data source classification for lineage tracking"
    )

    # Connection status and health monitoring
    status: Mapped[str] = mapped_column(
        String(50),
        default="active",
        nullable=False,
        comment="Connection status: active, error, disconnected, expired",
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Last error message if connection failed"
    )

    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of last successful data synchronization",
    )

    # Relationships
    user_accounts: Mapped["UserAccount"] = relationship(
        "UserAccount", back_populates="provider_connections"
    )

    provider_institutions: Mapped[Optional["ProviderInstitution"]] = relationship(
        "ProviderInstitution", back_populates="provider_connections"
    )

    provider_mappings: Mapped[List["ProviderMapping"]] = relationship(
        "ProviderMapping",
        back_populates="provider_connections",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    portfolio_accounts: Mapped[List["PortfolioAccount"]] = relationship(
        "PortfolioAccount", back_populates="provider_connections", passive_deletes=True
    )

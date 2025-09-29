import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel
from app.data.mappings.model import DataMapping
from app.portfolio.accounts.model import PortfolioAccount

if TYPE_CHECKING:
    from app.data.providers.model import DataProvider


class DataConnection(BaseModel):
    __tablename__ = "data_connections"

    provider_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("data_providers.id", ondelete="SET NULL"), nullable=True
    )
    connection_name: Mapped[str] = mapped_column(String(255), nullable=False)
    data_source: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_frequency: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Relationships
    data_providers: Mapped[Optional["DataProvider"]] = relationship(
        "DataProvider", back_populates="data_connections"
    )

    data_mappings: Mapped[List["DataMapping"]] = relationship(
        "DataMapping",
        back_populates="data_connections",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    portfolio_accounts: Mapped[List["PortfolioAccount"]] = relationship(
        "PortfolioAccount", back_populates="data_connections", passive_deletes=True
    )

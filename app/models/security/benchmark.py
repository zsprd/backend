from typing import Optional

from sqlalchemy import UUID, Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Security
from app.models.base import BaseModel


class Benchmark(BaseModel):
    """
    Standard and custom benchmarks for performance comparison.
    """

    __tablename__ = "benchmarks"

    # Basic Information
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500))

    # Classification
    benchmark_type: Mapped[str] = mapped_column(
        String(50), nullable=False, index=True
    )  # equity, bond, commodity, crypto, composite
    geographic_focus: Mapped[Optional[str]] = mapped_column(
        String(100)
    )  # US, Global, Emerging Markets, Europe
    sector_focus: Mapped[Optional[str]] = mapped_column(
        String(100)
    )  # Technology, Healthcare, All Sectors
    style_focus: Mapped[Optional[str]] = mapped_column(String(50))  # Growth, Value, Blend

    # Market Information
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    exchange: Mapped[Optional[str]] = mapped_column(String(10))

    # Data Integration
    security_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("securities.id")
    )  # If benchmark is a tradeable security
    alphavantage_symbol: Mapped[Optional[str]] = mapped_column(String(20))
    yahoo_symbol: Mapped[Optional[str]] = mapped_column(String(20))
    bloomberg_ticker: Mapped[Optional[str]] = mapped_column(String(50))

    # Benchmark Composition (for custom benchmarks)
    composition: Mapped[Optional[dict]] = mapped_column(JSONB)  # Weights of constituent securities
    rebalance_frequency: Mapped[Optional[str]] = mapped_column(
        String(20)
    )  # monthly, quarterly, annually

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_default: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )  # Default benchmarks (SPY, VTI, etc.)
    is_custom: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )  # User-created benchmarks

    # Ownership (for custom benchmarks)
    created_by_user_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id")
    )
    created_by_organization_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id")
    )

    # Relationships
    security: Mapped[Optional["Security"]] = relationship()  # If benchmark is a tradeable security

    def __repr__(self) -> str:
        return f"<Benchmark(symbol={self.symbol}, name={self.name}, type={self.benchmark_type})>"

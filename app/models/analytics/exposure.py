"""
SQLAlchemy model for account exposure analytics (asset class, sector, etc.).
"""

from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DECIMAL,
    UUID,
    Date,
    DateTime,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.portfolios.account import PortfolioAccount


class AnalyticsExposure(BaseModel):
    __tablename__ = "analytics_exposure"

    account_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolio_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    allocation_by_asset_class: Mapped[dict] = mapped_column(JSONB, nullable=False)
    allocation_by_security_type: Mapped[dict] = mapped_column(JSONB, nullable=False)
    allocation_by_security_subtype: Mapped[dict] = mapped_column(JSONB, nullable=False)
    allocation_by_sector: Mapped[dict] = mapped_column(JSONB, nullable=False)
    allocation_by_industry: Mapped[dict] = mapped_column(JSONB, nullable=False)
    allocation_by_region: Mapped[dict] = mapped_column(JSONB, nullable=False)
    allocation_by_country: Mapped[dict] = mapped_column(JSONB, nullable=False)
    allocation_by_currency: Mapped[dict] = mapped_column(JSONB, nullable=False)
    allocation_by_equity_style: Mapped[Optional[dict]] = mapped_column(JSONB)
    allocation_by_debt_style: Mapped[Optional[dict]] = mapped_column(JSONB)
    top_5_weight: Mapped[Decimal] = mapped_column(DECIMAL(5, 2), nullable=False)
    top_10_weight: Mapped[Decimal] = mapped_column(DECIMAL(5, 2), nullable=False)
    largest_position_weight: Mapped[Decimal] = mapped_column(DECIMAL(5, 2), nullable=False)
    top_holdings: Mapped[dict] = mapped_column(JSONB, nullable=False)
    calculation_status: Mapped[str] = mapped_column(String(20), nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )
    account: Mapped["PortfolioAccount"] = relationship(
        "PortfolioAccount", back_populates="analytics_exposure"
    )
    __table_args__ = (
        UniqueConstraint("account_id", "as_of_date", name="uq_exposure_entity_date"),
        Index("idx_exposure_account_date", "account_id", "as_of_date"),
    )

    def __repr__(self) -> str:
        return f"<AnalyticsExposure(account_id={self.account_id}, as_of_date={self.as_of_date})>"

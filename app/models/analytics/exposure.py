from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DECIMAL,
    UUID,
    Date,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from app.models.core.account import Account

from app.models.base import BaseModel


class AnalyticsExposure(BaseModel):
    """
    Exposure and allocation analytics.
    """

    __tablename__ = "analytics_exposure"

    # Foreign Keys
    account_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )

    # Calculation Date
    calculation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Portfolio Totals
    total_market_value: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    total_cost_basis: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    holdings_count: Mapped[int] = mapped_column(nullable=False)

    # Asset Allocation (JSON - percentages)
    allocation_by_asset_class: Mapped[dict] = mapped_column(
        JSONB
    )  # equity, fixed_income, cash, alternatives
    allocation_by_security_type: Mapped[dict] = mapped_column(
        JSONB
    )  # stock, bond, etf, mutual_fund, crypto
    allocation_by_sector: Mapped[dict] = mapped_column(JSONB)  # GICS sectors
    allocation_by_country: Mapped[dict] = mapped_column(JSONB)  # Country exposure
    allocation_by_region: Mapped[dict] = mapped_column(JSONB)  # Regional exposure
    allocation_by_currency: Mapped[dict] = mapped_column(JSONB)  # Currency exposure

    # Style Analysis
    allocation_by_market_cap: Mapped[Optional[dict]] = mapped_column(JSONB)  # Large, Mid, Small cap
    allocation_by_style: Mapped[Optional[dict]] = mapped_column(JSONB)  # Growth, Value, Blend

    # Concentration Metrics
    top_5_weight: Mapped[Decimal] = mapped_column(DECIMAL(5, 2))  # % in top 5 holdings
    top_10_weight: Mapped[Decimal] = mapped_column(DECIMAL(5, 2))  # % in top 10 holdings
    top_20_weight: Mapped[Decimal] = mapped_column(DECIMAL(5, 2))  # % in top 20 holdings
    largest_position_weight: Mapped[Decimal] = mapped_column(DECIMAL(5, 2))  # % in largest holding
    herfindahl_index: Mapped[Decimal] = mapped_column(DECIMAL(6, 4))  # Concentration measure (0-1)

    # Top Holdings Details (JSON)
    top_holdings: Mapped[dict] = mapped_column(JSONB)  # Top 20 with weights, values, sectors

    # Benchmark Comparison
    relative_allocation: Mapped[Optional[dict]] = mapped_column(JSONB)  # Allocation vs benchmark
    active_weights: Mapped[Optional[dict]] = mapped_column(JSONB)  # Over/underweights vs benchmark

    # ESG Exposure (Future Enhancement)
    esg_scores: Mapped[Optional[dict]] = mapped_column(JSONB)  # ESG breakdown

    # Risk Concentrations
    single_issuer_risk: Mapped[Optional[dict]] = mapped_column(JSONB)  # Issuer concentration
    sector_concentration_risk: Mapped[Optional[dict]] = mapped_column(
        JSONB
    )  # Sector concentration warnings
    geographic_concentration_risk: Mapped[Optional[dict]] = mapped_column(
        JSONB
    )  # Geographic concentration

    # Calculation Metadata
    calculation_status: Mapped[str] = mapped_column(String(20), default="completed")
    error_message: Mapped[Optional[str]] = mapped_column(String(500))

    # Relationships
    account: Mapped[Optional["Account"]] = relationship()

    # Constraints
    __table_args__ = (
        UniqueConstraint("account_id", "calculation_date", name="uq_exposure_entity_date"),
        Index("idx_exposure_account_date", "account_id", "calculation_date"),
    )

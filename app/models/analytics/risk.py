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

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.core.account import Account


class AnalyticsRisk(BaseModel):
    """
    Risk analytics including VaR, correlations, and risk decomposition.
    """

    __tablename__ = "analytics_risk"

    # Foreign Keys
    account_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )

    # Calculation Date
    calculation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Value at Risk (Historical Method)
    var_90: Mapped[Decimal] = mapped_column(DECIMAL(8, 4))  # %
    var_95: Mapped[Decimal] = mapped_column(DECIMAL(8, 4))  # %
    var_99: Mapped[Decimal] = mapped_column(DECIMAL(8, 4))  # %

    # Conditional VaR (Expected Shortfall)
    cvar_95: Mapped[Decimal] = mapped_column(DECIMAL(8, 4))  # %
    cvar_99: Mapped[Decimal] = mapped_column(DECIMAL(8, 4))  # %

    # Downside Risk Metrics
    downside_deviation: Mapped[Decimal] = mapped_column(DECIMAL(8, 4))  # %
    downside_capture: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))  # %
    up_capture: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))  # %
    upside_downside_ratio: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))

    # Distribution Metrics
    skewness: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    kurtosis: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))

    # Stress Testing
    market_stress_loss: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(8, 4)
    )  # % loss in market stress
    interest_rate_stress: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(8, 4)
    )  # % loss in rate stress

    # Risk Contributions (JSON for flexibility)
    security_risk_contributions: Mapped[Optional[dict]] = mapped_column(
        JSONB
    )  # By individual security
    sector_risk_contributions: Mapped[Optional[dict]] = mapped_column(JSONB)  # By sector
    country_risk_contributions: Mapped[Optional[dict]] = mapped_column(JSONB)  # By country

    # Correlation Analysis
    correlation_matrix: Mapped[Optional[dict]] = mapped_column(JSONB)  # Holdings correlation matrix
    concentration_risk: Mapped[Optional[dict]] = mapped_column(JSONB)  # Concentration metrics

    # Advanced Risk Metrics
    tail_ratio: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    common_sense_ratio: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    pain_index: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    ulcer_index: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))

    # Model Risk
    model_confidence: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(5, 2)
    )  # % confidence in calculations
    data_coverage: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(5, 2)
    )  # % of holdings with risk data

    # Calculation Metadata
    calculation_status: Mapped[str] = mapped_column(String(20), default="completed")
    error_message: Mapped[Optional[str]] = mapped_column(String(500))

    # Relationships
    account: Mapped[Optional["Account"]] = relationship()

    # Constraints
    __table_args__ = (
        UniqueConstraint("account_id", "calculation_date", name="uq_risk_entity_date"),
        Index("idx_risk_account_date", "account_id", "calculation_date"),
    )

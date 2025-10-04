from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, Optional
from uuid import UUID

from sqlalchemy import DECIMAL, JSON, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.account.master.model import Account


class AnalyticsRisk(BaseModel):
    """
    Portfolio risk metrics and analysis for risk management.

    Comprehensive risk measurement including Value at Risk (VaR),
    concentration risk, tail risk measures, and volatility analysis.
    Essential for institutional risk management and compliance.
    """

    __tablename__ = "analytics_risk"

    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portfolio_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the account account",
    )

    as_of_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="Date for this risk analysis"
    )

    # Value at Risk metrics
    var_95_1d: Mapped[Decimal] = mapped_column(
        DECIMAL(8, 4), nullable=False, comment="1-day Value at Risk at 95% confidence level"
    )

    var_99_1d: Mapped[Decimal] = mapped_column(
        DECIMAL(8, 4), nullable=False, comment="1-day Value at Risk at 99% confidence level"
    )

    cvar_95_1d: Mapped[Decimal] = mapped_column(
        DECIMAL(8, 4), nullable=False, comment="1-day Conditional VaR (Expected Shortfall) at 95%"
    )

    cvar_99_1d: Mapped[Decimal] = mapped_column(
        DECIMAL(8, 4), nullable=False, comment="1-day Conditional VaR (Expected Shortfall) at 99%"
    )

    # Risk ratios and measures
    volatility: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 4), nullable=False, comment="Annualized account volatility"
    )

    downside_deviation: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(8, 4), nullable=True, comment="Downside deviation (volatility of negative returns)"
    )

    skewness: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(8, 4), nullable=True, comment="Return distribution skewness"
    )

    kurtosis: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(8, 4), nullable=True, comment="Return distribution kurtosis (tail heaviness)"
    )

    # Concentration risk measures
    concentration_hhi: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(6, 4), nullable=True, comment="Herfindahl-Hirschman Index for concentration"
    )

    effective_positions: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(8, 2), nullable=True, comment="Effective number of positions (1/HHI)"
    )

    largest_position_pct: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(5, 2), nullable=True, comment="Largest single position as percentage of account"
    )

    top_5_concentration: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(5, 2), nullable=True, comment="Combined weight of top 5 positions"
    )

    top_10_concentration: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(5, 2), nullable=True, comment="Combined weight of top 10 positions"
    )

    # Tail risk measures
    tail_ratio: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(8, 4), nullable=True, comment="Ratio of right tail to left tail returns"
    )

    gain_loss_ratio: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(8, 4), nullable=True, comment="Average gain divided by average loss"
    )

    # Risk time series data
    rolling_volatility: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="30-day rolling volatility history"
    )

    rolling_var: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="30-day rolling VaR history"
    )

    # Relationships
    portfolio_accounts: Mapped["Account"] = relationship("Account", back_populates="analytics_risk")

    # Composite unique constraint on account_id + as_of_date
    __table_args__ = ({"comment": "Comprehensive account risk metrics and analysis"},)

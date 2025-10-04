from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, Optional
from uuid import UUID

from sqlalchemy import DECIMAL, JSON, Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.account.master.model import Account


class AnalyticsPerformance(BaseModel):
    """
    Advanced performance analysis and benchmarking metrics.

    Stores risk-adjusted performance metrics, benchmark comparisons,
    and statistical measures for sophisticated account analysis.
    Used for institutional-grade reporting and performance attribution.
    """

    __tablename__ = "analytics_performance"

    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portfolio_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the account account",
    )

    as_of_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="Date for this performance analysis"
    )

    # Benchmark comparison
    benchmark_symbol: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="Benchmark identifier (SPY, VTI, MSCI_WORLD)"
    )

    alpha: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(8, 4), nullable=True, comment="Alpha versus benchmark (excess return)"
    )

    beta: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(8, 4), nullable=True, comment="Beta versus benchmark (systematic risk)"
    )

    correlation: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(6, 4), nullable=True, comment="Correlation coefficient with benchmark"
    )

    tracking_error: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(8, 4), nullable=True, comment="Standard deviation of alpha (tracking error)"
    )

    # Risk-adjusted performance metrics
    volatility: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(10, 4),
        nullable=True,
        comment="Annualized volatility (standard deviation of returns)",
    )

    sharpe_ratio: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(8, 4), nullable=True, comment="Sharpe ratio (risk-adjusted return)"
    )

    sortino_ratio: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(8, 4), nullable=True, comment="Sortino ratio (downside risk-adjusted return)"
    )

    information_ratio: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(8, 4), nullable=True, comment="Information ratio (alpha per unit tracking error)"
    )

    calmar_ratio: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(8, 4), nullable=True, comment="Calmar ratio (return divided by maximum drawdown)"
    )

    # Drawdown analysis
    max_drawdown: Mapped[Decimal] = mapped_column(
        DECIMAL(8, 4), nullable=False, comment="Maximum drawdown percentage from peak"
    )

    current_drawdown: Mapped[Decimal] = mapped_column(
        DECIMAL(8, 4), nullable=False, comment="Current drawdown percentage from recent peak"
    )

    recovery_days: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Days required to recover from maximum drawdown"
    )

    # Performance distribution statistics
    best_day_return: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(8, 4), nullable=True, comment="Best single day return percentage"
    )

    worst_day_return: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(8, 4), nullable=True, comment="Worst single day return percentage"
    )

    positive_days: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Number of positive return days in analysis period"
    )

    negative_days: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Number of negative return days in analysis period"
    )

    win_rate: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(5, 2), nullable=True, comment="Percentage of positive return days"
    )

    # Time series performance data
    daily_returns: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="252-day daily return history for analysis"
    )

    benchmark_returns: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Benchmark return data for comparison"
    )

    rolling_returns: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Rolling period return analysis"
    )

    # Relationships
    portfolio_accounts: Mapped["Account"] = relationship(
        "Account", back_populates="analytics_performance"
    )

    # Composite unique constraint on account_id + as_of_date
    __table_args__ = ({"comment": "Advanced performance metrics and benchmark analysis"},)

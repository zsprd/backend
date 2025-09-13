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


class AnalyticsPerformance(BaseModel):
    """
    Performance analytics for accounts and portfolios.
    Pre-calculated metrics for fast API responses.
    """

    __tablename__ = "analytics_performance"

    # Foreign Keys
    account_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )

    # Calculation Metadata
    calculation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    period_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    period_days: Mapped[int] = mapped_column(default=730)  # Analysis period length

    # Return Metrics
    total_return: Mapped[Decimal] = mapped_column(DECIMAL(10, 4))  # %
    annualized_return: Mapped[Decimal] = mapped_column(DECIMAL(10, 4))  # %
    volatility: Mapped[Decimal] = mapped_column(DECIMAL(10, 4))  # %

    # Risk-Adjusted Returns
    sharpe_ratio: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    sortino_ratio: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    calmar_ratio: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    omega_ratio: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    treynor_ratio: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))

    # Drawdown Analysis
    max_drawdown: Mapped[Decimal] = mapped_column(DECIMAL(8, 4))  # %
    current_drawdown: Mapped[Decimal] = mapped_column(DECIMAL(8, 4))  # %
    avg_drawdown: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))  # %
    max_drawdown_duration: Mapped[Optional[int]]  # days
    recovery_time: Mapped[Optional[int]]  # days to recover from max drawdown

    # Benchmark Comparison
    benchmark_symbol: Mapped[str] = mapped_column(String(10), default="SPY")
    alpha: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))  # %
    beta: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    correlation: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(6, 4))
    tracking_error: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))  # %
    information_ratio: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    up_capture: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))  # %
    down_capture: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))  # %

    # Performance Extremes
    best_day: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))  # %
    worst_day: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))  # %
    best_month: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))  # %
    worst_month: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))  # %

    # Win/Loss Statistics
    positive_periods: Mapped[Optional[int]]
    negative_periods: Mapped[Optional[int]]
    win_rate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2))  # %

    # Time Series Data (JSON for charts)
    time_series_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    rolling_metrics: Mapped[Optional[dict]] = mapped_column(JSONB)  # 30-day, 90-day rolling metrics

    # Calculation Metadata
    calculation_status: Mapped[str] = mapped_column(String(20), default="completed")
    error_message: Mapped[Optional[str]] = mapped_column(String(500))
    risk_free_rate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(6, 4))  # Used in calculations

    # Relationships
    account: Mapped[Optional["Account"]] = relationship()

    # Constraints
    __table_args__ = (
        UniqueConstraint("account_id", "calculation_date", name="uq_performance_entity_date"),
        Index("idx_performance_account_date", "account_id", "calculation_date"),
    )

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
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.portfolios.account.model import PortfolioAccount


class AnalyticsPerformance(BaseModel):
    __tablename__ = "analytics_performance"

    # Foreign Keys
    account_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolio_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Calculation Metadata
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    # Benchmark Comparison
    benchmark_symbol: Mapped[str] = mapped_column(String(10), nullable=False)
    alpha: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))  # %
    beta: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    correlation: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(6, 4))

    # Performance Extremes
    best_day: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))  # %
    worst_day: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))  # %

    # Win/Loss Statistics
    positive_periods: Mapped[Optional[int]] = mapped_column(Integer)
    negative_periods: Mapped[Optional[int]] = mapped_column(Integer)
    win_rate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2))  # %

    # Distribution Statistics
    skewness: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    kurtosis: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))

    # Time Series Data (JSON for charts)
    time_series_data: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Calculation Metadata
    calculation_status: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="completed, failed"
    )
    error_message: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # Relationships
    account: Mapped["PortfolioAccount"] = relationship(
        "PortfolioAccount", back_populates="analytics_performance"
    )

    # Constraints
    __table_args__ = (
        UniqueConstraint("account_id", "as_of_date", name="uq_performance_entity_date"),
        Index("idx_performance_account_date", "account_id", "as_of_date"),
    )

    def __repr__(self) -> str:
        return f"<AnalyticsPerformance(account_id={self.account_id}, as_of_date={self.as_of_date})>"

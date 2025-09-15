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


class AnalyticsRisk(BaseModel):
    __tablename__ = "analytics_risk"

    account_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolio_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    volatility: Mapped[Decimal] = mapped_column(DECIMAL(10, 4), nullable=False)
    sharpe_ratio: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    sortino_ratio: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    calmar_ratio: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    omega_ratio: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    max_drawdown: Mapped[Decimal] = mapped_column(DECIMAL(8, 4), nullable=False)
    current_drawdown: Mapped[Decimal] = mapped_column(DECIMAL(8, 4), nullable=False)
    average_drawdown: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    max_drawdown_duration: Mapped[Optional[int]] = mapped_column(Integer)
    recovery_time: Mapped[Optional[int]] = mapped_column(Integer)
    var_95: Mapped[Decimal] = mapped_column(DECIMAL(8, 4), nullable=False)
    var_99: Mapped[Decimal] = mapped_column(DECIMAL(8, 4), nullable=False)
    var_99_9: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    cvar_95: Mapped[Decimal] = mapped_column(DECIMAL(8, 4), nullable=False)
    cvar_99: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    downside_deviation: Mapped[Decimal] = mapped_column(DECIMAL(8, 4), nullable=False)
    skewness: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    kurtosis: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    gain_loss_ratio: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    tail_ratio: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    gross_leverage: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    net_leverage: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    long_exposure: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    short_exposure: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    margin_utilization: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(5, 2))
    up_capture_ratio: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    down_capture_ratio: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(8, 4))
    time_series_data: Mapped[Optional[dict]] = mapped_column(JSONB)
    calculation_status: Mapped[str] = mapped_column(String(20), nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(String(500))
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )
    account: Mapped["PortfolioAccount"] = relationship(
        "PortfolioAccount", back_populates="analytics_risk"
    )
    __table_args__ = (
        UniqueConstraint("account_id", "as_of_date", name="uq_risk_entity_date"),
        Index("idx_risk_account_date", "account_id", "as_of_date"),
    )

    def __repr__(self) -> str:
        return f"<AnalyticsRisk(account_id={self.account_id}, as_of_date={self.as_of_date})>"

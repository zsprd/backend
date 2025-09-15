from datetime import date
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
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.portfolios.account.model import PortfolioAccount


class AnalyticsSummary(BaseModel):
    """
    Daily portfolios values for individual accounts.
    Foundation for all analytics calculations.
    """

    __tablename__ = "analytics_summary"

    # Foreign Key
    account_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolio_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Date and Values
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    available_balance: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 2))
    current_balance: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 2))
    balance_limit: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 2))
    market_value: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    cost_basis: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    cash_contributions: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    fees_paid: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=Decimal("0"))

    # Calculated Fields
    total_return: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 4))
    annualized_return: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 4))
    ytd_return: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 4))
    daily_return: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6))

    # Value Breakdown
    equity_value: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=Decimal("0"))
    debt_value: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=Decimal("0"))
    cash_value: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=Decimal("0"))
    alternatives_value: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=Decimal("0"))
    domestic_value: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=Decimal("0"))
    international_value: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=Decimal("0"))

    # Currency and Source
    currency: Mapped[str] = mapped_column(String(3), nullable=False)

    # Data Quality
    holdings_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    data_quality: Mapped[Optional[str]] = mapped_column(String(20))  # complete, estimated, partial
    last_price_date: Mapped[Optional[date]] = mapped_column(Date)  # Last available market data date
    created_at: Mapped[Optional[date]] = mapped_column(DateTime(timezone=True), default=func.now())
    updated_at: Mapped[Optional[date]] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # Relationships
    account: Mapped["PortfolioAccount"] = relationship(
        "PortfolioAccount", back_populates="analytics_summary"
    )

    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint("account_id", "as_of_date", name="uq_summary_entity_date"),
        Index("idx_summary_account_date", "account_id", "as_of_date"),
    )

    def __repr__(self) -> str:
        return f"<AnalyticsSummary(account_id={self.account_id}, date={self.as_of_date}, value=${self.market_value})>"

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


class AnalyticsSummary(BaseModel):
    """
    Account-level summary metrics for account performance and allocation.

    Stores calculated account values, returns, and asset allocation data
    that can be aggregated to create user-level account summaries.
    Updated daily or on-demand for real-time account tracking.
    """

    __tablename__ = "analytics_summary"

    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portfolio_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the account account",
    )

    as_of_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="Date for this analytics snapshot"
    )

    # Core account values
    market_value: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2), nullable=False, comment="Current market value of all holdings"
    )

    cost_basis: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2), nullable=False, comment="Total cost basis of all holdings"
    )

    cash_balance: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2), default=0, nullable=False, comment="Cash and cash equivalents balance"
    )

    unrealized_gain: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2),
        nullable=False,
        comment="Unrealized gains/losses (market_value - cost_basis)",
    )

    realized_gain: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2), default=0, nullable=False, comment="Realized gains/losses year-to-date"
    )

    # Performance returns (as percentages)
    total_return: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(10, 4), nullable=True, comment="Total return percentage since inception"
    )

    daily_return: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(10, 6), nullable=True, comment="1-day return percentage"
    )

    weekly_return: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(10, 4), nullable=True, comment="1-week return percentage"
    )

    monthly_return: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(10, 4), nullable=True, comment="1-month return percentage"
    )

    quarterly_return: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(10, 4), nullable=True, comment="1-quarter return percentage"
    )

    ytd_return: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(10, 4), nullable=True, comment="Year-to-date return percentage"
    )

    annual_return: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(10, 4), nullable=True, comment="1-year return percentage"
    )

    # Asset allocation values for aggregation
    equity_value: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2), default=0, nullable=False, comment="Market value of equity holdings"
    )

    debt_value: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2),
        default=0,
        nullable=False,
        comment="Market value of debt/fixed income holdings",
    )

    fund_value: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2),
        default=0,
        nullable=False,
        comment="Market value of fund holdings (ETFs, mutual funds)",
    )

    cash_value: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2), default=0, nullable=False, comment="Cash and cash equivalents value"
    )

    other_value: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2), default=0, nullable=False, comment="Market value of alternative investments"
    )

    # Geographic allocation
    domestic_value: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2), default=0, nullable=False, comment="Market value of domestic investments"
    )

    international_value: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2),
        default=0,
        nullable=False,
        comment="Market value of international investments",
    )

    # Portfolio metadata
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, comment="Reporting currency for all values"
    )

    holdings_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Number of distinct positions in the account"
    )

    last_price_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Date of the most recent price update"
    )

    # Time series data for charting (JSON arrays)
    value_time_series: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="30-day account value history for trend charts"
    )

    return_time_series: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="30-day return history for performance charts"
    )

    # Relationships
    portfolio_accounts: Mapped["Account"] = relationship(
        "Account", back_populates="analytics_summary"
    )

    # Composite unique constraint on account_id + as_of_date
    __table_args__ = ({"comment": "Daily account summary metrics and asset allocation"},)

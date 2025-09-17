from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import DECIMAL, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.model import BaseModel

if TYPE_CHECKING:
    from app.benchmark.master.model import BenchmarkMaster


class BenchmarkPrice(BaseModel):
    """
    Daily benchmark prices and calculated returns.

    Time series data for benchmark indices including prices and
    pre-calculated return periods. Used for portfolio performance
    comparison and risk-adjusted metrics calculation.
    """

    __tablename__ = "benchmark_prices"

    benchmark_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("benchmark_master.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the benchmark index",
    )

    price_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="Date for this price observation"
    )

    close_price: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 4), nullable=False, comment="Closing price or index level"
    )

    # Pre-calculated returns for performance analysis
    total_return_1d: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(8, 4), nullable=True, comment="1-day total return percentage"
    )

    total_return_ytd: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(8, 4), nullable=True, comment="Year-to-date total return percentage"
    )

    total_return_1y: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(8, 4), nullable=True, comment="1-year total return percentage"
    )

    # Relationships
    benchmark_master: Mapped["BenchmarkMaster"] = relationship(
        "BenchmarkMaster", back_populates="benchmark_prices"
    )

    # Composite unique constraint on benchmark_id + price_date
    __table_args__ = ({"comment": "Daily benchmark prices and performance data"},)

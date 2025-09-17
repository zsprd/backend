from typing import List, Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ...core.model import BaseModel
from ..prices.model import BenchmarkPrice


class BenchmarkMaster(BaseModel):
    """
    Benchmark index definitions for performance comparison.

    Master registry of benchmark indices (S&P 500, FTSE 100, etc.) used
    for portfolio performance comparison and alpha/beta calculations.
    Supports broad market, sector, and regional benchmarks.
    """

    __tablename__ = "benchmark_master"

    symbol: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        comment="Benchmark symbol identifier (SPY, VTI, EAFE, ^GSPC)",
    )

    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Full benchmark name (SPDR S&P 500 ETF Trust)"
    )

    description: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Detailed description of what the benchmark represents"
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
        comment="Base currency for benchmark prices and returns",
    )

    region: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Geographic region: US, International, Emerging, Global"
    )

    asset_class: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Primary asset class: Equity, Fixed Income, Commodity, REIT",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this benchmark is actively maintained",
    )

    # Relationships
    benchmark_prices: Mapped[List["BenchmarkPrice"]] = relationship(
        "BenchmarkPrice",
        back_populates="benchmark_master",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

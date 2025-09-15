"""
SQLAlchemy model for market data (prices, volumes, etc.).
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DECIMAL,
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.core.model import BaseModel
from app.securities.reference.enums import DataSourceEnum

if TYPE_CHECKING:
    from app.securities.reference.model import SecurityReference


class SecurityPrice(BaseModel):
    __tablename__ = "security_price"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    security_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("security_reference.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    as_of_date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)

    # OHLCV Data
    open_price: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 4))
    high_price: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 4))
    low_price: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 4))
    close_price: Mapped[float] = mapped_column(DECIMAL(15, 4), nullable=False)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    adjusted_close: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 4))

    # Metadata
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    data_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    data_source: Mapped[str] = mapped_column(DataSourceEnum(), default="calculated")

    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )

    # Calculated Fields
    daily_return: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6))  # Daily return %

    # Relationships
    security: Mapped["SecurityReference"] = relationship(back_populates="security_price")

    # Unique constraint - one price per securities per date
    __table_args__ = (
        UniqueConstraint("security_id", "as_of_date", name="uq_market_data_security_date"),
    )

    def __repr__(self) -> str:
        return f"<MarketData(security_id={self.security_id}, as_of_date={self.as_of_date}, close_price={self.close_price})>"


class ExchangeRate(BaseModel):
    __tablename__ = "exchange_rates"

    # Currency Pair
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    quote_currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)

    # Date and Rate
    rate_date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    rate: Mapped[Decimal] = mapped_column(DECIMAL(15, 6), nullable=False)

    # Source
    data_provider: Mapped[str] = mapped_column(String(50), nullable=False)

    # Unique constraint - one rate per currency pair per date
    __table_args__ = (
        UniqueConstraint(
            "base_currency",
            "quote_currency",
            "rate_date",
            name="_currency_pair_rate_date_uc",
        ),
    )

    def __repr__(self) -> str:
        return f"<SecurityPrice({self.base_currency}/{self.quote_currency} = {self.rate} on {self.rate_date})>"

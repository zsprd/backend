from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, DECIMAL, Date, BigInteger, UniqueConstraint, ForeignKey, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import BaseModel
from app.models.enums import DataProviderCategory

if TYPE_CHECKING:
    from app.models.security import Security


class MarketData(BaseModel):
    __tablename__ = "market_data"

    # Foreign Key
    security_id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("securities.id", ondelete="CASCADE"), nullable=False, index=True)

    # Date
    price_date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)

    # OHLCV Data
    open_price: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 4))
    high_price: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 4))
    low_price: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 4))
    close_price: Mapped[float] = mapped_column(DECIMAL(15, 4), nullable=False)
    volume: Mapped[Optional[int]] = mapped_column(BigInteger)
    adjusted_close: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 4))

    # Metadata
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    data_provider: Mapped[DataProviderCategory] = mapped_column(
        Enum(DataProviderCategory, native_enum=False, length=50),
        nullable=False
    )

    # Relationships
    security: Mapped["Security"] = relationship(back_populates="market_data")

    # Unique constraint - one price per security per date
    __table_args__ = (
        UniqueConstraint("security_id", "price_date", name="_security_price_date_uc"),
    )

    def __repr__(self) -> str:
        return f"<MarketData(security_id={self.security_id}, price_date={self.price_date}, close_price={self.close_price})>"


class ExchangeRate(BaseModel):
    __tablename__ = "exchange_rates"

    # Currency Pair
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)
    quote_currency: Mapped[str] = mapped_column(String(3), nullable=False, index=True)

    # Date and Rate
    rate_date: Mapped[Date] = mapped_column(Date, nullable=False, index=True)
    rate: Mapped[float] = mapped_column(DECIMAL(15, 6), nullable=False)

    # Source
    data_provider: Mapped[DataProviderCategory] = mapped_column(
        Enum(DataProviderCategory, native_enum=False, length=50),
        nullable=False
    )

    # Unique constraint - one rate per currency pair per date
    __table_args__ = (
        UniqueConstraint("base_currency", "quote_currency", "rate_date", name="_currency_pair_rate_date_uc"),
    )

    def __repr__(self) -> str:
        return f"<ExchangeRate({self.base_currency}/{self.quote_currency} = {self.rate} on {self.rate_date})>"

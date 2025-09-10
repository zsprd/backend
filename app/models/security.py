from typing import TYPE_CHECKING

from sqlalchemy import String, Boolean
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.models.base import BaseModel
from app.models.enums import security_category, data_provider_category

if TYPE_CHECKING:
    from app.models.holding import Holding
    from app.models.transaction import Transaction
    from app.models.market_data import MarketData


class Security(BaseModel):
    __tablename__ = "securities"

    # Basic Information
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(security_category, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Market Information
    exchange: Mapped[str | None] = mapped_column(String(10))  # e.g., NASDAQ, NYSE, LSE
    country: Mapped[str | None] = mapped_column(String(2))    # ISO country code

    # Classification
    sector: Mapped[str | None] = mapped_column(String(100))
    industry: Mapped[str | None] = mapped_column(String(100))

    # Identifiers
    cusip: Mapped[str | None] = mapped_column(String(9))      # US securities identifier
    isin: Mapped[str | None] = mapped_column(String(12))      # International securities identifier
    sedol: Mapped[str | None] = mapped_column(String(7))      # Stock Exchange Daily Official List

    # External Integration
    plaid_security_id: Mapped[str | None] = mapped_column(String(255))
    alphavantage_symbol: Mapped[str | None] = mapped_column(String(20))
    data_provider_category: Mapped[str | None] = mapped_column(data_provider_category)
    is_delisted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    holdings: Mapped[list["Holding"]] = relationship(back_populates="security")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="security")
    market_data: Mapped[list["MarketData"]] = relationship(back_populates="security", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Security(id={self.id}, symbol={self.symbol}, name={self.name})>"

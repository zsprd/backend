from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.holding import Holding
    from app.models.security.market_data import MarketData
    from app.models.transaction import Transaction


class Security(BaseModel):
    __tablename__ = "securities"

    # Basic Information
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    security_category: Mapped[str] = mapped_column(String(50), nullable=False)

    # Market Information
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    exchange: Mapped[Optional[str]] = mapped_column(String(10))  # e.g., NASDAQ, NYSE, LSE
    country: Mapped[Optional[str]] = mapped_column(String(2))  # ISO country code

    # Classification
    sector: Mapped[Optional[str]] = mapped_column(String(100))
    industry: Mapped[Optional[str]] = mapped_column(String(100))

    # External Identifiers
    cusip: Mapped[Optional[str]] = mapped_column(String(9), unique=True)  # US/Canada
    isin: Mapped[Optional[str]] = mapped_column(String(12), unique=True)  # International
    sedol: Mapped[Optional[str]] = mapped_column(String(7), unique=True)  # UK
    ric: Mapped[Optional[str]] = mapped_column(String(20))  # Reuters
    bloomberg_ticker: Mapped[Optional[str]] = mapped_column(String(50))  # Bloomberg

    # External Integration
    # Data Provider Integration
    alphavantage_symbol: Mapped[Optional[str]] = mapped_column(String(20))
    yahoo_symbol: Mapped[Optional[str]] = mapped_column(String(20))
    morningstar_id: Mapped[Optional[str]] = mapped_column(String(50))
    plaid_security_id: Mapped[Optional[str]] = mapped_column(String(255))

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    holdings: Mapped[list["Holding"]] = relationship(back_populates="security")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="security")
    market_data: Mapped[list["MarketData"]] = relationship(
        back_populates="security", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Security(id={self.id}, symbol={self.symbol}, name={self.name})>"

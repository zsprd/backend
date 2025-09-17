from datetime import date
from decimal import Decimal

from sqlalchemy import DECIMAL, Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model import BaseModel


class MarketRate(BaseModel):
    """
    Foreign exchange rates and interest rates for analytics.

    Critical market data including FX rates for currency conversion,
    risk-free rates for Sharpe ratio calculations, and other
    benchmark rates needed for portfolio analytics.
    """

    __tablename__ = "market_rates"

    rate_type: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Rate category: fx, risk_free, libor, corporate_bond"
    )

    from_currency: Mapped[str] = mapped_column(
        String(3), nullable=False, comment="Base currency for FX rates or rate currency"
    )

    to_currency: Mapped[str] = mapped_column(
        String(3), nullable=False, comment="Quote currency for FX rates or rate tenor"
    )

    rate: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 8), nullable=False, comment="Exchange rate or interest rate value"
    )

    rate_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="Date for this rate observation"
    )

    data_source: Mapped[str] = mapped_column(
        String(50), default="calculated", nullable=False, comment="Source of this rate data"
    )

    # Composite unique constraint on rate_type + from_currency + to_currency + rate_date
    __table_args__ = ({"comment": "Foreign exchange and interest rates for analytics"},)

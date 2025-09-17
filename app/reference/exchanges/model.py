from datetime import time
from typing import Optional

from sqlalchemy import Boolean, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model import BaseModel


class ReferenceExchange(BaseModel):
    """
    Stock exchange reference data for trading and settlement.

    Exchange master data including trading hours, time zones,
    and settlement information. Used for market data processing,
    trading calendar calculations, and regulatory reporting.
    """

    __tablename__ = "reference_exchanges"

    exchange_code: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        comment="Exchange identifier (NYSE, NASDAQ, LSE, TSE, ASX)",
    )

    exchange_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Full exchange name (New York Stock Exchange)"
    )

    country_code: Mapped[str] = mapped_column(
        String(2), nullable=False, comment="Country where exchange is located"
    )

    currency_code: Mapped[str] = mapped_column(
        String(3), nullable=False, comment="Primary trading currency for this exchange"
    )

    timezone: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Exchange timezone (America/New_York, Europe/London)"
    )

    market_open: Mapped[Optional[time]] = mapped_column(
        Time, nullable=True, comment="Local market opening time"
    )

    market_close: Mapped[Optional[time]] = mapped_column(
        Time, nullable=True, comment="Local market closing time"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Whether this exchange is active for trading"
    )

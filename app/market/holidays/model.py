from datetime import date

from sqlalchemy import Boolean, Date, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model import BaseModel


class MarketHoliday(BaseModel):
    """
    Trading calendar and market holidays for date calculations.

    Market holiday calendar for different exchanges and countries.
    Used for business day calculations, settlement date computation,
    and performance measurement periods.
    """

    __tablename__ = "market_holidays"

    exchange: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Exchange identifier (NYSE, NASDAQ, LSE, TSE)"
    )

    country: Mapped[str] = mapped_column(
        String(2), nullable=False, comment="ISO country code (US, UK, CA, JP)"
    )

    holiday_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="Date of the market holiday"
    )

    holiday_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Name of the holiday (Christmas Day, Independence Day)"
    )

    is_full_closure: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether it's a full day closure or partial trading day",
    )

    # Composite unique constraint on exchange + holiday_date
    __table_args__ = ({"comment": "Market holidays and trading calendar data"},)

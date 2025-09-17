from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import DECIMAL, BigInteger, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.security.master.model import SecurityMaster


class SecurityPrice(BaseModel):
    """
    Daily market prices and volume data for securities.

    Time series price data essential for portfolio valuation,
    performance calculation, and market analytics. Supports
    both end-of-day and intraday pricing models.
    """

    __tablename__ = "security_prices"

    security_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("security_master.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the security being priced",
    )

    price_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="Date for this price observation"
    )

    close_price: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 4), nullable=False, comment="Closing price for the trading session"
    )

    volume: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="Trading volume in shares/units"
    )

    data_source: Mapped[str] = mapped_column(
        String(50), default="calculated", nullable=False, comment="Source of this price data"
    )

    # Relationships
    security_master: Mapped["SecurityMaster"] = relationship(
        "SecurityMaster", back_populates="security_prices"
    )

    # Composite unique constraint on security_id + price_date
    __table_args__ = ({"comment": "Daily market prices for portfolio valuation"},)

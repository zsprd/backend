from typing import Optional

from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model import BaseModel


class ReferenceCurrency(BaseModel):
    """
    Currency reference data for multi-currency account support.

    Master list of supported currencies with display formatting
    and precision information. Used for account reporting,
    currency conversion, FX tracking, and user interface localization.
    """

    __tablename__ = "reference_currencies"

    currency_code: Mapped[str] = mapped_column(
        String(3),
        unique=True,
        nullable=False,
        index=True,
        comment="ISO 4217 currency code (USD, EUR, GBP, JPY)",
    )

    currency_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Full currency name (United States dollar, Euro, British Pound)",
    )

    symbol: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, comment="Currency symbol for display ($, €, £, ¥)"
    )

    decimal_places: Mapped[int] = mapped_column(
        Integer, default=2, nullable=False, comment="Number of decimal places for this currency"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this currency is supported for new master",
    )

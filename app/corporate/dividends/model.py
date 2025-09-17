from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import DECIMAL, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.security.master.model import SecurityMaster


class CorporateDividend(BaseModel):
    """
    Dividend payments and distribution tracking.

    Records dividend and distribution payments for accurate income
    tracking and performance attribution. Supports regular and
    special dividend classifications.
    """

    __tablename__ = "corporate_dividends"

    security_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("security_master.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the dividend-paying security",
    )

    ex_date: Mapped[date] = mapped_column(
        Date, nullable=False, comment="Ex-dividend date for holder determination"
    )

    pay_date: Mapped[date] = mapped_column(
        Date, nullable=False, comment="Actual payment date for the dividend"
    )

    amount_per_share: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 6),
        nullable=False,
        comment="Dividend amount per share in the security's currency",
    )

    currency: Mapped[str] = mapped_column(
        String(3), default="USD", nullable=False, comment="Currency of the dividend payment"
    )

    frequency: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Payment frequency: quarterly, annual, monthly, irregular",
    )

    dividend_type: Mapped[str] = mapped_column(
        String(20),
        default="regular",
        nullable=False,
        comment="Type of dividend: regular, special, liquidating, return_of_capital",
    )

    # Relationships
    security_master: Mapped["SecurityMaster"] = relationship(
        "SecurityMaster", back_populates="corporate_dividends"
    )

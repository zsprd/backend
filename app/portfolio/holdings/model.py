import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DECIMAL, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.portfolio.accounts.model import PortfolioAccount
    from app.security.master.model import SecurityMaster


class PortfolioHolding(BaseModel):
    """
    Portfolio positions and holdings (point-in-time snapshots).

    Represents security positions held in an account at a specific date.
    Supports both long and short positions, with cost basis tracking
    for performance and tax calculations.
    """

    __tablename__ = "portfolio_holdings"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolio_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the account holding this position",
    )

    cost_basis: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(15, 4), nullable=True, comment="Average cost per share/unit for tax calculations"
    )

    local_price: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(15, 4), nullable=True, comment="Price per share/unit in local currency"
    )

    as_of_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="Date of this position snapshot"
    )

    market_value: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(20, 2),
        nullable=True,
        comment="Total market value of the position in local currency",
    )

    currency: Mapped[str] = mapped_column(
        String(3), default="USD", nullable=False, comment="Currency of the cost basis and valuation"
    )

    quantity: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 6),
        nullable=False,
        comment="Number of shares/units held (negative for short positions)",
    )

    security_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("security_master.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the security being held",
    )

    data_source: Mapped[str] = mapped_column(
        String(50), default="manual", nullable=False, comment="Source of this holding data"
    )

    # Relationships
    portfolio_accounts: Mapped["PortfolioAccount"] = relationship(
        "PortfolioAccount", back_populates="portfolio_holdings"
    )

    security_master: Mapped["SecurityMaster"] = relationship(
        "SecurityMaster", back_populates="portfolio_holdings"
    )

    # Composite unique constraint on account_id + security_id + as_of_date
    __table_args__ = ({"comment": "Portfolio positions at specific points in time"},)

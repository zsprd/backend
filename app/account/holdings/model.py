import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, Date, DECIMAL, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.counterparty.master.model import Counterparty
    from app.account.master.model import Account
    from app.security.master.model import Security


class AccountHolding(BaseModel):
    """
    Portfolio positions and holdings (point-in-time snapshots).

    Represents security positions held in a account at a specific date. Supports both
    long and short positions, with average cost basis tracking for performance calculations.

    Holdings are stored as snapshots for each as_of_date, enabling historical analysis
    and tracking of account changes over time. Query by specific dates rather than
    using is_current flags for flexibility and simplicity.

    NOTE: Cash positions are stored as holdings with security.symbol = 'CASH' where
    quantity = cash_amount and market_value = cash_amount.
    """

    __tablename__ = "portfolio_holdings"

    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolio_master.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the account holding this position",
    )

    security_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("security_master.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the security (or CASH security for cash positions)",
    )

    counterparty_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("counterparty_master.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Broker/custodian holding this position (may differ from account provider)",
    )

    as_of_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Date of this position snapshot",
    )

    quantity: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 6),
        nullable=False,
        comment="Number of shares/units held (negative for short positions, dollar amount for cash)",
    )

    cost_basis: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(15, 4),
        nullable=True,
        comment="Average cost per share/unit for performance calculations",
    )

    local_price: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(15, 4),
        nullable=True,
        comment="Price per share/unit in local currency on as_of_date",
    )

    market_value: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(20, 2),
        nullable=True,
        comment="Total market value of the position in local currency",
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
        comment="Currency of the cost basis and valuation",
    )

    # Relationships
    portfolio_master: Mapped["Account"] = relationship(
        "Account",
        back_populates="portfolio_holdings",
    )

    security_master: Mapped["Security"] = relationship(
        "Security",
        back_populates="portfolio_holdings",
    )

    counterparty_master: Mapped[Optional["Counterparty"]] = relationship(
        "Counterparty",
        back_populates="portfolio_holdings",
    )

    __table_args__ = (
        UniqueConstraint(
            "portfolio_id",
            "security_id",
            "as_of_date",
            name="uq_holding_snapshot",
        ),
        Index("idx_holding_date", "as_of_date", "deleted_at"),
        CheckConstraint("quantity != 0", name="chk_holding_quantity_not_zero"),
        {"comment": "Portfolio positions at specific points in time"},
    )

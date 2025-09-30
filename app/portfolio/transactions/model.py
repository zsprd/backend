from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import DECIMAL, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.portfolio.accounts.model import PortfolioAccount
    from app.security.master.model import SecurityMaster


class PortfolioTransaction(BaseModel):
    """
    Complete transaction history for all portfolio activity.

    Records all portfolio transactions including buys, sells, dividends,
    fees, and corporate actions. Essential for performance calculation,
    tax reporting, and audit trails.
    """

    __tablename__ = "portfolio_transactions"

    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portfolio_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the account where transaction occurred",
    )

    security_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("security_master.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Reference to the security (NULL for cash-only transactions)",
    )

    # Transaction classification
    transaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Primary transaction category: buy, sell, dividend, etc.",
    )

    transaction_subtype: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Specific transaction subtype for detailed classification",
    )

    # Transaction amounts and pricing
    quantity: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(15, 6),
        nullable=True,
        comment="Number of shares/units (positive for buys, negative for sells)",
    )

    price: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(15, 4), nullable=True, comment="Price per share/unit at time of transaction"
    )

    amount: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2),
        nullable=False,
        comment="Total transaction amount (positive for inflows, negative for outflows)",
    )

    fees: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2), default=0, nullable=False, comment="Transaction fees and commissions"
    )

    currency: Mapped[str] = mapped_column(
        String(3), default="USD", nullable=False, comment="Currency of all monetary amounts"
    )

    # Transaction timing
    trade_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="Date when the trade was executed"
    )

    settlement_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Date when the trade settled (cash and securities transferred)"
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Human-readable transaction description"
    )

    data_source: Mapped[str] = mapped_column(
        String(50),
        default="manual",
        nullable=False,
        comment="Source of this transaction data",
    )

    # Relationships
    portfolio_accounts: Mapped["PortfolioAccount"] = relationship(
        "PortfolioAccount", back_populates="portfolio_transactions"
    )

    security_master: Mapped[Optional["SecurityMaster"]] = relationship(
        "SecurityMaster", back_populates="portfolio_transactions"
    )

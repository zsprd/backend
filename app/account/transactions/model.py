import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Date, DECIMAL, ForeignKey, Index, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.counterparty.master.model import Counterparty
    from app.account.master.model import Account
    from app.security.master.model import Security


class AccountTransaction(BaseModel):
    """
    Complete transaction history for all account activity.

    Records all account transactions including buys, sells, dividends, fees, deposits,
    withdrawals, and corporate actions.

    Transactions can be manually entered, imported via CSV, or synced from external
    providers. Uses external_transaction_id for deduplication when importing from providers.

    Counterparty tracking: The counterparty_id represents the actual broker/exchange that
    executed the trade, which may differ from the account's data provider.
    """

    __tablename__ = "portfolio_transactions"

    portfolio_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolio_master.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the account where transaction occurred",
    )

    security_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("security_master.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Reference to the security (NULL for cash-only transactions)",
    )

    counterparty_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("counterparty_master.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Broker/exchange that executed this transaction (may differ from account provider)",
    )

    # Transaction classification
    transaction_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Primary transaction category: buy, sell, dividend, deposit, withdrawal, etc.",
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
        DECIMAL(15, 4),
        nullable=True,
        comment="Price per share/unit at time of transaction",
    )

    amount: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2),
        nullable=False,
        comment="Total transaction amount (positive for inflows, negative for outflows)",
    )

    fees: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 2),
        default=0,
        nullable=False,
        comment="Transaction fees and commissions",
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
        comment="Currency of all monetary amounts",
    )

    # Transaction timing
    trade_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Date when the trade was executed",
    )

    settlement_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date when the trade settled (cash and securities transferred)",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable transaction description",
    )

    # Provider deduplication
    external_transaction_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="Provider's unique transaction identifier for deduplication",
    )

    # Relationships
    portfolio_master: Mapped["Account"] = relationship(
        "Account",
        back_populates="portfolio_transactions",
    )

    security_master: Mapped[Optional["Security"]] = relationship(
        "Security",
        back_populates="portfolio_transactions",
    )

    counterparty_master: Mapped[Optional["Counterparty"]] = relationship(
        "Counterparty",
        back_populates="portfolio_transactions",
    )

    __table_args__ = (
        UniqueConstraint(
            "portfolio_id",
            "external_transaction_id",
            name="uq_transaction_external_id",
        ),
        Index("idx_transaction_date_type", "portfolio_id", "trade_date", "transaction_type"),
        Index("idx_transaction_security", "security_id", "trade_date"),
        {"comment": "Complete transaction history for account activity"},
    )

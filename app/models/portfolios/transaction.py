"""
SQLAlchemy model for account transactions (buys, sells, transfers, etc.).
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DECIMAL, Date, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.portfolios.account import PortfolioAccount
    from app.models.securities.reference import SecurityReference


class PortfolioTransaction(BaseModel):
    __tablename__ = "portfolio_transactions"

    # Foreign Keys
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolio_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    security_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("security_reference.id", ondelete="SET NULL"),
        nullable=True,
    )

    # External identifiers
    plaid_transaction_id: Mapped[Optional[str]] = mapped_column(String(255))
    plaid_account_id: Mapped[Optional[str]] = mapped_column(String(255))
    cancel_transaction_id: Mapped[Optional[str]] = mapped_column(String(255))

    # PortfolioTransaction details (ENUMS as str)
    transaction_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="buy, sell, cash, transfer, fee, dividend, interest, cancel, adjustment, split, merger, spinoff",
    )
    transaction_subtype: Mapped[Optional[str]] = mapped_column(
        String(32),
        comment="buy, sell, deposit, withdrawal, dividend, interest, fee, transfer_in, transfer_out, cancel, adjustment",
    )
    quantity: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 6))
    price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 4))
    amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    fees: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 2), default=0)
    data_source: Mapped[str] = mapped_column(
        String(32),
        default="manual",
        comment="plaid, manual, bulk, calculated, yfinance, alphavantage",
    )

    # Dates
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    trade_date: Mapped[Optional[date]] = mapped_column(Date)
    settlement_date: Mapped[Optional[date]] = mapped_column(Date)

    # Description
    name: Mapped[Optional[str]] = mapped_column(String)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # Relationships
    account: Mapped["PortfolioAccount"] = relationship(back_populates="portfolio_transactions")
    security: Mapped[Optional["SecurityReference"]] = relationship(
        back_populates="portfolio_transactions"
    )

    def __repr__(self) -> str:
        return f"<PortfolioTransaction(id={self.id}, type={self.transaction_type}, amount={self.amount})>"

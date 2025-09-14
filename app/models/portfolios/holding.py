"""
SQLAlchemy model for account holdings (positions in securities).
"""

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DECIMAL, Date, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.portfolios.account import PortfolioAccount
    from app.models.securities.reference import SecurityReference


class PortfolioHolding(BaseModel):
    __tablename__ = "portfolio_holdings"

    # Foreign Keys
    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolio_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    security_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("security_reference.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Plaid reconciliation
    plaid_account_id: Mapped[Optional[str]] = mapped_column(String(255))

    # Position data
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(15, 6), nullable=False)
    cost_basis: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 4))
    institution_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 4))
    institution_value: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 2))
    data_source: Mapped[str] = mapped_column(
        String(32),
        default="manual",
        comment="plaid, manual, bulk, calculated, yfinance, alphavantage",
    )
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # Relationships
    account: Mapped["PortfolioAccount"] = relationship(back_populates="portfolio_holdings")
    security: Mapped["SecurityReference"] = relationship(back_populates="portfolio_holdings")

    __table_args__ = (
        UniqueConstraint(
            "account_id", "security_id", "as_of_date", name="_account_security_date_uc"
        ),
    )

    def __repr__(self) -> str:
        return f"<PortfolioHolding(id={self.id}, account_id={self.account_id}, security_id={self.security_id})>"

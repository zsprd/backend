"""
SQLAlchemy model for securities (stocks, bonds, etc.).
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel
from app.models.enums import DataSourceEnum, SecuritySubtypeEnum, SecurityTypeEnum

if TYPE_CHECKING:
    from app.models.portfolios.holding import PortfolioHolding
    from app.models.portfolios.transaction import PortfolioTransaction


class SecurityReference(BaseModel):
    __tablename__ = "security_reference"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plaid_security_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    institution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("financial_institutions.id")
    )
    institution_security_id: Mapped[Optional[str]] = mapped_column(String(255))
    symbol: Mapped[Optional[str]] = mapped_column(String(50))
    name: Mapped[str] = mapped_column(String(500), nullable=False)
    security_type: Mapped[str] = mapped_column(SecurityTypeEnum(), nullable=False)
    security_subtype: Mapped[Optional[str]] = mapped_column(SecuritySubtypeEnum(), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    exchange: Mapped[Optional[str]] = mapped_column(String(20))
    country: Mapped[Optional[str]] = mapped_column(String(2))
    sector: Mapped[Optional[str]] = mapped_column(String(100))
    industry: Mapped[Optional[str]] = mapped_column(String(100))
    cusip: Mapped[Optional[str]] = mapped_column(String(9))
    isin: Mapped[Optional[str]] = mapped_column(String(12))
    sedol: Mapped[Optional[str]] = mapped_column(String(7))
    is_cash_equivalent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    data_source: Mapped[str] = mapped_column(DataSourceEnum(), default="manual")
    option_details: Mapped[Optional[dict]] = mapped_column(JSONB)
    fixed_income_details: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # Relationships
    holdings: Mapped[list["PortfolioHolding"]] = relationship(back_populates="security_reference")
    transactions: Mapped[list["PortfolioTransaction"]] = relationship(
        back_populates="security_reference"
    )

    def __repr__(self) -> str:
        return f"<SecurityReference(id={self.id}, symbol={self.symbol}, name={self.name})>"

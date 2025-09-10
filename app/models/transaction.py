import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import String, ForeignKey, DECIMAL, Date, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.models.base import BaseModel
from app.models.enums import (
    transaction_category,
    transaction_side_category,
    data_provider_category,
)

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.security import Security


class Transaction(BaseModel):
    __tablename__ = "transactions"

    # Foreign Keys
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    security_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("securities.id", ondelete="SET NULL"), nullable=True)

    # Transaction Details
    category: Mapped[str] = mapped_column(transaction_category, nullable=False)
    side: Mapped[str | None] = mapped_column(transaction_side_category)
    quantity: Mapped[Decimal | None] = mapped_column(DECIMAL(15, 6))
    price: Mapped[Decimal | None] = mapped_column(DECIMAL(15, 4))
    amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    fees: Mapped[Decimal | None] = mapped_column(DECIMAL(15, 2))
    tax: Mapped[Decimal | None] = mapped_column(DECIMAL(15, 2))

    # Dates
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    settlement_date: Mapped[date | None] = mapped_column(Date)

    # Currency and FX
    transaction_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    fx_rate: Mapped[Decimal | None] = mapped_column(DECIMAL(15, 6))

    # Description and Categorization
    description: Mapped[str | None] = mapped_column(Text)
    memo: Mapped[str | None] = mapped_column(Text)
    subcategory: Mapped[str | None] = mapped_column(String(100))

    # External Integration
    plaid_transaction_id: Mapped[str | None] = mapped_column(String(255))
    data_provider: Mapped[str] = mapped_column(data_provider_category, nullable=False)

    # Relationships
    account: Mapped["Account"] = relationship(back_populates="transactions")
    security: Mapped["Security | None"] = relationship(back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, category={self.category}, amount={self.amount})>"

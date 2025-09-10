import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, DECIMAL, Date, Text, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.models.base import BaseModel
from app.models.enums import (
    TransactionCategory,
    TransactionSideCategory,
    DataProviderCategory,
)

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.security import Security


class Transaction(BaseModel):
    __tablename__ = "transactions"

    # Foreign Keys
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    security_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("securities.id", ondelete="SET NULL"), nullable=True)

    # Transaction Details
    category: Mapped[TransactionCategory] = mapped_column(
        Enum(TransactionCategory, native_enum=False, length=50),
        nullable=False
    )
    side: Mapped[Optional[TransactionSideCategory]] = mapped_column(
        Enum(TransactionSideCategory, native_enum=False, length=50),
        nullable=True
    )
    quantity: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 6))
    price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 4))
    amount: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    fees: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 2))
    tax: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 2))

    # Dates
    trade_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    settlement_date: Mapped[Optional[date]] = mapped_column(Date)

    # Currency and FX
    transaction_currency: Mapped[str] = mapped_column(String(3), nullable=False)
    fx_rate: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 6))

    # Description and Categorization
    description: Mapped[Optional[str]] = mapped_column(Text)
    memo: Mapped[Optional[str]] = mapped_column(Text)
    subcategory: Mapped[Optional[str]] = mapped_column(String(100))

    # External Integration
    plaid_transaction_id: Mapped[Optional[str]] = mapped_column(String(255))
    data_provider: Mapped[DataProviderCategory] = mapped_column(
        Enum(DataProviderCategory, native_enum=False, length=50),
        nullable=False
    )

    # Relationships
    account: Mapped["Account"] = relationship(back_populates="transactions")
    security: Mapped[Optional["Security"]] = relationship(back_populates="transactions")

    def __repr__(self) -> str:
        return f"<Transaction(id={self.id}, category={self.category}, amount={self.amount})>"

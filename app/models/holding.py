import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, ForeignKey, DECIMAL, Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.account import Account
    from app.models.security import Security


class Holding(BaseModel):
    __tablename__ = "holdings"

    # Foreign Keys

    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    security_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("securities.id", ondelete="CASCADE"), nullable=False, index=True)

    # Holding Details
    quantity: Mapped[Decimal] = mapped_column(DECIMAL(15, 6), nullable=False)
    cost_basis_per_share: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 4))
    cost_basis_total: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 2))
    market_value: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 2))
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    as_of_date: Mapped[date] = mapped_column(Date, nullable=False)

    # External Integration
    plaid_account_id: Mapped[Optional[str]] = mapped_column(String(255))
    plaid_security_id: Mapped[Optional[str]] = mapped_column(String(255))
    institution_price: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 4))
    institution_value: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(15, 2))

    # Relationships
    account: Mapped["Account"] = relationship(back_populates="holdings")
    security: Mapped["Security"] = relationship(back_populates="holdings")

    # Unique constraint to prevent duplicate holdings for same account/security/date
    __table_args__ = (
        UniqueConstraint("account_id", "security_id", "as_of_date", name="_account_security_date_uc"),
    )

    def __repr__(self) -> str:
        return f"<Holding(id={self.id}, account_id={self.account_id}, security_id={self.security_id})>"

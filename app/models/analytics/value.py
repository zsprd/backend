from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DECIMAL, UUID, Date, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.core.account import Account


class AccountValue(BaseModel):
    """
    Daily portfolio values for individual accounts.
    Foundation for all analytics calculations.
    """

    __tablename__ = "analytics_values"

    # Foreign Key
    account_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Date and Values
    value_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    market_value: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    cost_basis: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), nullable=False)
    cash_value: Mapped[Decimal] = mapped_column(DECIMAL(15, 2), default=Decimal("0"))

    # Calculated Fields
    daily_return: Mapped[Optional[Decimal]] = mapped_column(DECIMAL(10, 6))  # Daily return %

    # Currency and Source
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    calculation_source: Mapped[str] = mapped_column(
        String(20), default="holdings"
    )  # holdings, transactions, manual

    # Data Quality
    data_quality: Mapped[Optional[str]] = mapped_column(String(20))  # complete, estimated, partial
    last_price_date: Mapped[Optional[date]] = mapped_column(Date)  # Last available market data date

    # Relationships
    account: Mapped["Account"] = relationship(back_populates="daily_values")

    # Constraints and Indexes
    __table_args__ = (
        UniqueConstraint("account_id", "value_date", name="uq_account_daily_value"),
        Index("idx_account_daily_values_date", "account_id", "value_date"),
        Index("idx_daily_values_date_desc", "value_date", postgresql_ops={"value_date": "DESC"}),
    )

    def __repr__(self) -> str:
        return f"<AccountValue(account_id={self.account_id}, date={self.value_date}, value=${self.market_value})>"

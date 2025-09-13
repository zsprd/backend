import uuid
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.analytics import (
    AccountValue,
    AnalyticsExposure,
    AnalyticsPerformance,
    AnalyticsRisk,
)
from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.core.user import User
    from app.models.holding import Holding
    from app.models.transaction import Transaction


class Institution(BaseModel):
    __tablename__ = "institutions"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)  # ISO country code
    website_url: Mapped[Optional[str]] = mapped_column(String(255))
    logo_url: Mapped[Optional[str]] = mapped_column(String(500))  # URL to logo
    primary_color: Mapped[Optional[str]] = mapped_column(String(7))  # Hex color code

    # Plaid integration
    plaid_institution_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    supports_investments: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_transactions: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    accounts: Mapped[list["Account"]] = relationship(back_populates="institution")

    def __repr__(self) -> str:
        return f"<Institution(id={self.id}, name={self.name})>"


class Account(BaseModel):
    __tablename__ = "accounts"

    # Foreign Keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    institution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Account Details
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    official_name: Mapped[Optional[str]] = mapped_column(
        String(255)
    )  # Official name from institution

    account_category: Mapped[str] = mapped_column(String(50), nullable=False)
    account_subtype: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    mask: Mapped[Optional[str]] = mapped_column(String(4))  # Last 4 digits of account number
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # External Integration
    plaid_account_id: Mapped[Optional[str]] = mapped_column(String(255))

    # Relationships
    user: Mapped["User"] = relationship(back_populates="accounts")
    institution: Mapped[Optional["Institution"]] = relationship(back_populates="accounts")
    holdings: Mapped[list["Holding"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    transactions: Mapped[list["Transaction"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )

    # Analytics Relationships
    daily_values: Mapped[list["AccountValue"]] = relationship(
        back_populates="account", cascade="all, delete-orphan"
    )
    performance_analytics: Mapped[list["AnalyticsPerformance"]] = relationship(
        cascade="all, delete-orphan"
    )
    risk_analytics: Mapped[list["AnalyticsRisk"]] = relationship(cascade="all, delete-orphan")
    exposure_analytics: Mapped[list["AnalyticsExposure"]] = relationship(
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Account(id={self.id}, name={self.name}, category={self.account_category})>"

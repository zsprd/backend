import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.analytics.exposure import AnalyticsExposure
from app.models.analytics.performance import AnalyticsPerformance
from app.models.analytics.risk import AnalyticsRisk
from app.models.base import BaseModel
from app.models.enums import AccountSubtypeEnum, AccountTypeEnum, DataSourceEnum

if TYPE_CHECKING:
    from app.models.integrations.institution import FinancialInstitution
    from app.models.portfolios.holding import PortfolioHolding
    from app.models.portfolios.transaction import PortfolioTransaction
    from app.models.users.user import User


class PortfolioAccount(BaseModel):
    __tablename__ = "portfolio_accounts"

    # Foreign Keys
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    institution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("financial_institutions.id", ondelete="SET NULL"),
        nullable=True,
    )
    data_connection_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("data_connections.id", ondelete="SET NULL"),
        nullable=True,
    )

    # PortfolioAccount Identifiers
    plaid_account_id: Mapped[Optional[str]] = mapped_column(String(255))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    official_name: Mapped[Optional[str]] = mapped_column(String(255))
    mask: Mapped[Optional[str]] = mapped_column(String(10))

    # PortfolioAccount classification (ENUMS as str)
    account_type: Mapped[str] = mapped_column(AccountTypeEnum(), nullable=False)
    account_subtype: Mapped[Optional[str]] = mapped_column(AccountSubtypeEnum(), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    data_source: Mapped[str] = mapped_column(DataSourceEnum(), default="manual")
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="portfolio_accounts")
    institution: Mapped[Optional["FinancialInstitution"]] = relationship(
        "FinancialInstitution", back_populates="accounts"
    )
    holdings: Mapped[list["PortfolioHolding"]] = relationship(
        back_populates="portfolio_accounts", cascade="all, delete-orphan"
    )
    transactions: Mapped[list["PortfolioTransaction"]] = relationship(
        back_populates="portfolio_accounts", cascade="all, delete-orphan"
    )

    # Analytics Relationships
    analytics_summary: Mapped[list] = relationship(cascade="all, delete-orphan")
    analytics_performance: Mapped[list[AnalyticsPerformance]] = relationship(
        cascade="all, delete-orphan"
    )
    analytics_risk: Mapped[list[AnalyticsRisk]] = relationship(cascade="all, delete-orphan")
    analytics_exposure: Mapped[list[AnalyticsExposure]] = relationship(cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<PortfolioAccount(id={self.id}, name={self.name}, type={self.account_type})>"

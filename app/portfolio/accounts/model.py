from typing import TYPE_CHECKING, List, Optional
from uuid import UUID

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.analytics.exposure.model import AnalyticsExposure
from app.analytics.performance.model import AnalyticsPerformance
from app.analytics.risk.model import AnalyticsRisk
from app.analytics.summary.model import AnalyticsSummary
from app.core.model import BaseModel
from app.portfolio.holdings.model import PortfolioHolding
from app.portfolio.transactions.model import PortfolioTransaction

from .enums import AccountSubtypeEnum, AccountTypeEnum

if TYPE_CHECKING:
    from app.provider.connections.model import ProviderConnection
    from app.provider.institutions.model import ProviderInstitution
    from app.user.accounts.model import UserAccount


class PortfolioAccount(BaseModel):
    """
    Investment accounts for portfolio tracking and analysis.

    Represents individual investment accounts (brokerage, 401k, IRA, etc.)
    that contain securities and cash. Supports multiple account types
    and provider integrations for comprehensive portfolio management.
    """

    __tablename__ = "portfolio_accounts"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the account owner",
    )

    institution_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("provider_institutions.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to the financial institution (if applicable)",
    )

    connection_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("provider_connections.id", ondelete="SET NULL"),
        nullable=True,
        comment="Reference to the provider connection for data sync",
    )

    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="User-friendly account name or nickname"
    )

    # Account classification
    account_type: Mapped[AccountTypeEnum] = mapped_column(
        Enum(AccountTypeEnum, name="account_type_enum", create_type=False),
        nullable=False,
        index=True,
        comment="Primary account category: investment, depository, credit, loan",
    )

    account_subtype: Mapped[Optional[AccountSubtypeEnum]] = mapped_column(
        Enum(AccountSubtypeEnum, name="account_subtype_enum", create_type=False),
        nullable=True,
        comment="Specific account subtype: brokerage, ira, 401k, etc.",
    )

    currency: Mapped[str] = mapped_column(
        String(3), default="USD", nullable=False, comment="Base currency for this account"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False, comment="Whether this account is actively tracked"
    )

    data_source: Mapped[str] = mapped_column(
        String(50), default="manual", nullable=False, comment="Source of this account's data"
    )

    # Relationships
    user_accounts: Mapped["UserAccount"] = relationship(
        "UserAccount", back_populates="portfolio_accounts"
    )

    provider_institutions: Mapped[Optional["ProviderInstitution"]] = relationship(
        "ProviderInstitution", back_populates="portfolio_accounts"
    )

    provider_connections: Mapped[Optional["ProviderConnection"]] = relationship(
        "ProviderConnection", back_populates="portfolio_accounts"
    )

    portfolio_holdings: Mapped[List["PortfolioHolding"]] = relationship(
        "PortfolioHolding",
        back_populates="portfolio_accounts",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    portfolio_transactions: Mapped[List["PortfolioTransaction"]] = relationship(
        "PortfolioTransaction",
        back_populates="portfolio_accounts",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    analytics_summary: Mapped[List["AnalyticsSummary"]] = relationship(
        "AnalyticsSummary",
        back_populates="portfolio_accounts",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    analytics_performance: Mapped[List["AnalyticsPerformance"]] = relationship(
        "AnalyticsPerformance",
        back_populates="portfolio_accounts",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    analytics_risk: Mapped[List["AnalyticsRisk"]] = relationship(
        "AnalyticsRisk",
        back_populates="portfolio_accounts",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    analytics_exposure: Mapped[List["AnalyticsExposure"]] = relationship(
        "AnalyticsExposure",
        back_populates="portfolio_accounts",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

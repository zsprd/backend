import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.analytics.exposure.model import AnalyticsExposure
    from app.analytics.performance.model import AnalyticsPerformance
    from app.analytics.risk.model import AnalyticsRisk
    from app.analytics.summary.model import AnalyticsSummary
    from app.account.holdings.model import AccountHolding
    from app.account.providers.model import AccountProvider
    from app.account.transactions.model import AccountTransaction
    from app.user.master.model import User


class Account(BaseModel):
    """
    Master account entities for investment tracking and analysis.

    Represents individual investment portfolios (brokerage accounts, retirement accounts,
    alternative investments, etc.) that contain securities, cash, and transaction history.

    Design for multi-user access: Portfolios are first-class entities that users can be
    granted access to, supporting both individual HNWI and institutional asset manager use cases.

    Each account has exactly one provider (manual, CSV upload, or external integration like
    Plaid, Yodlee, etc.) that supplies the account data.
    """

    __tablename__ = "portfolio_master"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Primary user/owner of this account",
    )

    account_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="User-friendly account/account name",
    )

    account_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Broad account category: retirement, brokerage, alternative, crypto, liability",
    )

    account_subtype: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Specific account subtype: 401k, roth_ira, traditional_ira, etc.",
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
        comment="Base currency for account (single currency per account)",
    )

    account_number_masked: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Masked account number for display (e.g., *****1234)",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether account is currently active",
    )

    # Relationships
    user_accounts: Mapped["User"] = relationship(
        "User",
        back_populates="portfolio_master",
    )

    portfolio_provider: Mapped["AccountProvider"] = relationship(
        "AccountProvider",
        back_populates="portfolio_master",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    portfolio_holdings: Mapped[List["AccountHolding"]] = relationship(
        "AccountHolding",
        back_populates="portfolio_master",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    portfolio_transactions: Mapped[List["AccountTransaction"]] = relationship(
        "AccountTransaction",
        back_populates="portfolio_master",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    analytics_summary: Mapped[List["AnalyticsSummary"]] = relationship(
        "AnalyticsSummary",
        back_populates="portfolio_master",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    analytics_performance: Mapped[List["AnalyticsPerformance"]] = relationship(
        "AnalyticsPerformance",
        back_populates="portfolio_master",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    analytics_risk: Mapped[List["AnalyticsRisk"]] = relationship(
        "AnalyticsRisk",
        back_populates="portfolio_master",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    analytics_exposure: Mapped[List["AnalyticsExposure"]] = relationship(
        "AnalyticsExposure",
        back_populates="portfolio_master",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("idx_portfolio_user_active", "user_id", "is_active", "deleted_at"),
        Index("idx_portfolio_type", "account_type", "account_subtype"),
        {"comment": "Master account entities for investment tracking"},
    )

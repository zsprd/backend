import uuid
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.analytics.exposure.model import AnalyticsExposure
from app.analytics.performance.model import AnalyticsPerformance
from app.analytics.risk.model import AnalyticsRisk
from app.analytics.summary.model import AnalyticsSummary
from app.core.model import BaseModel
from app.portfolio.holdings.model import PortfolioHolding
from app.portfolio.providers.model import PortfolioProvider
from app.portfolio.transactions.model import PortfolioTransaction

if TYPE_CHECKING:
    from app.user.accounts.model import UserAccount


class PortfolioAccount(BaseModel):
    """
    Investment accounts for portfolio tracking and analysis.

    Represents individual investment accounts (brokerage, 401k, IRA, etc.)
    that contain securities and cash. Supports multiple account types
    and provider integrations for comprehensive portfolio management.
    """

    __tablename__ = "portfolio_accounts"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    account_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    account_subtype: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    account_name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    user_accounts: Mapped["UserAccount"] = relationship(
        "UserAccount", back_populates="portfolio_accounts"
    )

    portfolio_providers: Mapped[List["PortfolioProvider"]] = relationship(
        "PortfolioProvider",
        back_populates="portfolio_accounts",
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

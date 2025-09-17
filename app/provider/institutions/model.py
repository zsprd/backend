from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel
from app.provider.connections.model import ProviderConnection

if TYPE_CHECKING:
    from app.portfolio.accounts.model import PortfolioAccount


class ProviderInstitution(BaseModel):
    """
    Financial institutions and data provider registry.

    Master registry of banks, brokerages, and data providers that can
    be connected to the platform. Supports both account aggregation
    (Plaid) and market data providers (Yahoo Finance, Alpha Vantage).
    """

    __tablename__ = "provider_institutions"

    institution_code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        comment="Unique institution identifier (chase, schwab, yfinance)",
    )

    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Full institution display name"
    )

    institution_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Institution category: bank, broker, data_provider"
    )

    country: Mapped[str] = mapped_column(
        String(2),
        default="US",
        nullable=False,
        comment="ISO country code where institution operates",
    )

    logo_url: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="URL to institution logo for UI display"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this institution is available for new connections",
    )

    # Relationships
    provider_connections: Mapped[List["ProviderConnection"]] = relationship(
        "ProviderConnection", back_populates="provider_institutions", passive_deletes=True
    )

    portfolio_accounts: Mapped[List["PortfolioAccount"]] = relationship(
        "PortfolioAccount", back_populates="provider_institutions"
    )

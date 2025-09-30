from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel
from ..identifiers.model import SecurityIdentifier
from ..prices.model import SecurityPrice
from ...corporate.actions.model import CorporateAction
from ...corporate.dividends.model import CorporateDividend
from ...portfolio.holdings.model import PortfolioHolding
from ...portfolio.transactions.model import PortfolioTransaction


class SecurityMaster(BaseModel):
    """
    Master security reference database for all financial instruments.

    Central repository for securities including stocks, bonds, ETFs, mutual funds,
    options, and other instruments. Stores fundamental characteristics,
    classification data, and metadata for portfolio analytics.
    """

    __tablename__ = "security_master"

    # Basic security identification
    symbol: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True, comment="Primary trading symbol (AAPL, MSFT, SPY)"
    )

    name: Mapped[str] = mapped_column(
        String(500), nullable=False, comment="Full legal name of the security"
    )

    # Security classification for analytics
    security_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Broad asset class: equity, debt, fund, option, etc.",
    )

    security_subtype: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Specific security type: common stock, ETF, corporate bond",
    )

    # Trading and market information
    currency: Mapped[str] = mapped_column(
        String(3), default="USD", nullable=False, comment="Primary trading currency"
    )

    exchange: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Primary exchange where security trades (NYSE, NASDAQ)"
    )

    country: Mapped[Optional[str]] = mapped_column(
        String(2), nullable=True, comment="Country of incorporation or primary listing"
    )

    # Sector and industry classification (GICS standard)
    sector: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="GICS sector classification for industry analysis"
    )

    industry: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="GICS industry classification for detailed analysis"
    )

    # Special characteristics
    is_cash_equivalent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this security should be treated as cash for allocation",
    )

    # Structured details for different security types
    option_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Option-specific data: strike, expiry, type, underlying symbol"
    )

    bond_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Bond-specific data: maturity, coupon, rating, issuer"
    )

    data_source: Mapped[str] = mapped_column(
        String(50),
        default="manual",
        nullable=False,
        comment="Source of this security's reference data",
    )

    # Relationships
    security_prices: Mapped[List["SecurityPrice"]] = relationship(
        "SecurityPrice",
        back_populates="security_master",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    security_identifiers: Mapped[List["SecurityIdentifier"]] = relationship(
        "SecurityIdentifier",
        back_populates="security_master",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    portfolio_holdings: Mapped[List["PortfolioHolding"]] = relationship(
        "PortfolioHolding", back_populates="security_master", passive_deletes=True
    )

    portfolio_transactions: Mapped[List["PortfolioTransaction"]] = relationship(
        "PortfolioTransaction", back_populates="security_master", passive_deletes=True
    )

    corporate_actions: Mapped[List["CorporateAction"]] = relationship(
        "CorporateAction",
        back_populates="security_master",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    corporate_dividends: Mapped[List["CorporateDividend"]] = relationship(
        "CorporateDividend",
        back_populates="security_master",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

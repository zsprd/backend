from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import JSON, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.account.holdings.model import AccountHolding
    from app.account.transactions.model import AccountTransaction
    from app.security.actions.model import CorporateAction
    from app.security.identifiers.model import SecurityIdentifier
    from app.security.prices.model import SecurityPrice
    from app.security.providers.model import SecurityProvider


class Security(BaseModel):
    """
    Master security reference database for all financial instruments.

    Central repository for securities including stocks, bonds, ETFs, mutual funds,
    options, commodities, cryptocurrencies, and other instruments. Stores fundamental
    characteristics, classification data, and metadata for account analytics.

    Each security can have an associated provider that actively maintains its data
    (prices, identifiers, corporate actions). Data provenance is tracked at the
    individual data point level (e.g., each price record tracks its data_provider).

    NOTE: Cash should be represented as a special security with symbol='CASH' and
    security_type='cash' and is_cash_equivalent=True.
    """

    __tablename__ = "security_master"

    # Basic security identification
    symbol: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Primary trading symbol (AAPL, MSFT, SPY, BTC, etc.)",
    )

    security_name: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
        comment="Full legal name of the security",
    )

    # Security classification for analytics
    security_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Broad asset class: equity, debt, fund, option, commodity, crypto, cash, etc.",
    )

    security_subtype: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Specific security type: common_stock, etf, corporate_bond, bitcoin, etc.",
    )

    # Trading and market information
    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
        comment="Primary trading currency",
    )

    exchange: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Primary exchange where security trades (NYSE, NASDAQ, BINANCE, etc.)",
    )

    country: Mapped[Optional[str]] = mapped_column(
        String(2),
        nullable=True,
        comment="Country of incorporation or primary listing (ISO 3166-1 alpha-2)",
    )

    # Sector and industry classification (GICS standard for equities)
    sector: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="GICS sector classification for industry analysis",
    )

    industry: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="GICS industry classification for detailed analysis",
    )

    # Special characteristics
    is_cash_equivalent: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this security should be treated as cash for allocation (e.g., CASH symbol)",
    )

    # Structured details for different security types
    option_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Option-specific data: strike, expiry, type, underlying_symbol",
    )

    bond_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Bond-specific data: maturity, coupon, rating, issuer",
    )

    # Relationships
    security_provider: Mapped[Optional["SecurityProvider"]] = relationship(
        "SecurityProvider",
        back_populates="security_master",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

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

    portfolio_holdings: Mapped[List["AccountHolding"]] = relationship(
        "AccountHolding",
        back_populates="security_master",
        passive_deletes=True,
    )

    portfolio_transactions: Mapped[List["AccountTransaction"]] = relationship(
        "AccountTransaction",
        back_populates="security_master",
        passive_deletes=True,
    )

    corporate_actions: Mapped[List["CorporateAction"]] = relationship(
        "CorporateAction",
        back_populates="security_master",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

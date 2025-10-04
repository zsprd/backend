from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.account.holdings.model import AccountHolding
    from app.account.providers.model import AccountProvider
    from app.account.transactions.model import AccountTransaction


class Counterparty(BaseModel):
    """
    Master reference data for financial institutions and counterparties.

    Central catalog of brokers, banks, exchanges, custodians, and other financial
    institutions that users interact with. Used to track relationships across portfolios,
    holdings, and transactions.

    Examples: Fidelity, Charles Schwab, Interactive Brokers, NYSE, Coinbase, etc.
    """

    __tablename__ = "counterparty_master"

    counterparty_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Full legal name of the counterparty",
    )

    country: Mapped[str] = mapped_column(
        String(2),
        default="US",
        nullable=False,
        comment="Country code (ISO 3166-1 alpha-2)",
    )

    legal_entity_identifier: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="LEI code for regulatory identification",
    )

    web_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Counterparty website URL",
    )

    logo_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="URL to counterparty logo",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether counterparty is currently active",
    )

    # Relationships
    portfolio_providers: Mapped[List["AccountProvider"]] = relationship(
        "AccountProvider",
        back_populates="counterparty_master",
    )

    portfolio_holdings: Mapped[List["AccountHolding"]] = relationship(
        "AccountHolding",
        back_populates="counterparty_master",
    )

    portfolio_transactions: Mapped[List["AccountTransaction"]] = relationship(
        "AccountTransaction",
        back_populates="counterparty_master",
    )

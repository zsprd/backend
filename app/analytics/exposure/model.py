from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict
from uuid import UUID

from sqlalchemy import DECIMAL, JSON, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.account.master.model import Account


class AnalyticsExposure(BaseModel):
    """
    Asset allocation and exposure analysis for diversification insights.

    Detailed breakdown of account exposure across asset classes, sectors,
    geographies, and currencies. Supports both absolute values and
    percentage allocations for comprehensive exposure analysis.
    """

    __tablename__ = "analytics_exposure"

    account_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("portfolio_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the account account",
    )

    as_of_date: Mapped[date] = mapped_column(
        Date, nullable=False, index=True, comment="Date for this exposure analysis"
    )

    # Asset allocation by security type and subtype
    allocation_by_security_type: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment='Asset type allocation percentages {"equity": 70.5, "debt": 25.0}',
    )

    allocation_by_security_subtype: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment='Detailed security allocation {"etf": 35.0, "common_stock": 35.5}',
    )

    # Sector and industry exposure analysis
    allocation_by_sector: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment='GICS sector allocation {"technology": 25.3, "healthcare": 18.2}',
    )

    allocation_by_industry: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment='GICS industry allocation {"software": 12.1, "semiconductors": 8.7}',
    )

    # Geographic exposure analysis
    allocation_by_country: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment='Country allocation percentages {"US": 75.0, "UK": 10.0, "JP": 8.0}',
    )

    allocation_by_region: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment='Regional allocation {"north_america": 75.0, "europe": 15.0}'
    )

    # Currency exposure analysis
    allocation_by_currency: Mapped[Dict[str, Any]] = mapped_column(
        JSON, nullable=False, comment='Currency exposure {"USD": 80.0, "EUR": 12.0, "GBP": 8.0}'
    )

    # Top holdings for concentration analysis
    top_holdings: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment='Top holdings with details [{"symbol": "AAPL", "weight": 5.2, "value": 10400}]',
    )

    # Concentration summary metrics
    top_5_weight: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 2), nullable=False, comment="Combined weight percentage of top 5 holdings"
    )

    top_10_weight: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 2), nullable=False, comment="Combined weight percentage of top 10 holdings"
    )

    largest_position_weight: Mapped[Decimal] = mapped_column(
        DECIMAL(5, 2), nullable=False, comment="Weight percentage of the largest single position"
    )

    # Relationships
    portfolio_accounts: Mapped["Account"] = relationship(
        "Account", back_populates="analytics_exposure"
    )

    # Composite unique constraint on account_id + as_of_date
    __table_args__ = ({"comment": "Detailed account exposure and allocation analysis"},)

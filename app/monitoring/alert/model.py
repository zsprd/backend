"""
SQLAlchemy model for users alerts (notifications, triggers, etc.).
"""

from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.portfolios.account.model import PortfolioAccount


# Note: Need to add these enums to enums.py
class Alert(BaseModel):
    __tablename__ = "monitoring_alerts"

    # Foreign Key
    account_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolio_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    alert_type: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    conditions: Mapped[Optional[dict]] = mapped_column(JSONB)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_triggered_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))
    trigger_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Relationships
    account: Mapped["PortfolioAccount"] = relationship(
        "PortfolioAccount", back_populates="analytics_summary"
    )

from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DECIMAL,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.notification import Notification
    from app.models.user import User


# Note: Need to add these enums to enums.py
class Alert(BaseModel):
    __tablename__ = "alerts"

    # Foreign Key
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Alert Configuration
    alert_category: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # price_change, portfolio_value, etc.
    description: Mapped[Optional[str]] = mapped_column(Text)

    # Target and Conditions
    target_type: Mapped[Optional[str]] = mapped_column(
        String(50)
    )  # portfolio, security, account
    target_id: Mapped[Optional[UUID]] = mapped_column(UUID(as_uuid=True))
    metric: Mapped[Optional[str]] = mapped_column(
        String(100)
    )  # price, value, allocation_percent, etc.

    # Threshold Configuration
    threshold_operator: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    threshold_value: Mapped[Optional[float]] = mapped_column(DECIMAL(15, 4))
    threshold_percent: Mapped[Optional[float]] = mapped_column(DECIMAL(5, 2))

    # Frequency and Status
    frequency: Mapped[Optional[str]] = mapped_column(
        String(20), default="DAILY", nullable=True
    )
    status: Mapped[Optional[str]] = mapped_column(
        String(20), default="ACTIVE", nullable=True
    )

    # Configuration
    conditions: Mapped[Optional[dict]] = mapped_column(JSONB)
    notification_config: Mapped[Optional[dict]] = mapped_column(JSONB)

    # Status Tracking
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_triggered_at: Mapped[Optional[DateTime]] = mapped_column(
        DateTime(timezone=True)
    )
    trigger_count: Mapped[int] = mapped_column(Integer, default=0)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="alerts")
    notifications: Mapped[list["Notification"]] = relationship(
        "Notification", back_populates="alert", cascade="all, delete-orphan"
    )

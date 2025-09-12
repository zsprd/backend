from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.alert import Alert
    from app.models.user import User


class Notification(BaseModel):
    __tablename__ = "notifications"

    # Foreign Keys
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    alert_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True
    )

    # Notification Details
    notification_category: Mapped[str] = mapped_column(String(50), nullable=False)
    notification_channel: Mapped[str] = mapped_column(String(20), nullable=True)

    # Content
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    action_url: Mapped[Optional[str]] = mapped_column(Text)

    # Status
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[Optional[DateTime]] = mapped_column(DateTime(timezone=True))

    # Priority
    priority: Mapped[str] = mapped_column(
        String(20), default="normal"
    )  # low, normal, high, urgent

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")
    alert: Mapped[Optional["Alert"]] = relationship(
        "Alert", back_populates="notifications"
    )

from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.user.accounts.model import UserAccount


class UserNotification(BaseModel):
    """
    System notifications and user alerts.

    Handles all user communications including system alerts,
    data import notifications, and platform announcements.
    Supports read/unread status tracking.
    """

    __tablename__ = "user_notifications"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the user receiving the notification",
    )

    notification_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="Type of notification: alert, system, import, etc."
    )

    title: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Notification title/subject"
    )

    message: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Full notification message content"
    )

    # Read status tracking
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the user has read this notification",
    )

    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the notification was marked as read",
    )

    # Relationships
    user_accounts: Mapped["UserAccount"] = relationship(
        "UserAccount", back_populates="user_notifications"
    )

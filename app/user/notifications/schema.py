from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserNotificationBase(BaseModel):
    """
    Shared fields for UserNotification schemas.
    """

    user_id: UUID = Field(..., description="Reference to the user receiving the notification")
    notification_type: str = Field(
        ..., max_length=50, description="Type of notification: alert, system, import, etc."
    )
    title: str = Field(..., max_length=255, description="Notification title/subject")
    message: str = Field(..., description="Full notification message content")
    is_read: bool = Field(False, description="Whether the user has read this notification")
    read_at: Optional[datetime] = Field(
        None, description="Timestamp when the notification was marked as read"
    )


class UserNotificationCreate(UserNotificationBase):
    """
    Schema for creating a new user notification.
    """

    pass


class UserNotificationRead(UserNotificationBase):
    """
    Schema for reading user notification data (API response).
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique notification ID")

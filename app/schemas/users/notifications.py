from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class UserNotificationBase(BaseModel):
    user_id: UUID
    alert_id: Optional[UUID] = None
    notification_type: str
    title: str
    message: str
    is_read: bool = False
    read_at: Optional[datetime] = None


class UserNotificationCreate(UserNotificationBase):
    pass


class UserNotificationUpdate(BaseModel):
    is_read: Optional[bool] = None
    read_at: Optional[datetime] = None
    title: Optional[str] = None
    message: Optional[str] = None


class UserNotificationResponse(UserNotificationBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

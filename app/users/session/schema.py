from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class UserSessionBase(BaseModel):
    user_id: UUID
    refresh_token: str
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_type: Optional[str] = None


class UserSessionCreate(UserSessionBase):
    pass


class UserSessionUpdate(BaseModel):
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_type: Optional[str] = None


class UserSessionResponse(UserSessionBase):
    id: UUID
    created_at: datetime
    last_used_at: datetime

    class Config:
        from_attributes = True

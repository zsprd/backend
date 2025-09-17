from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UserSessionBase(BaseModel):
    """
    Shared fields for UserSession schemas.
    """

    user_id: UUID = Field(..., description="Reference to the authenticated user")
    refresh_token: str = Field(
        ..., max_length=500, description="Secure refresh token for session renewal"
    )
    expires_at: datetime = Field(
        ..., description="When this session expires and requires re-authentication"
    )
    last_used_at: datetime = Field(
        ..., description="Last activity timestamp for session management"
    )
    ip_address: Optional[str] = Field(None, description="IP address where the session was created")
    user_agent: Optional[str] = Field(
        None, max_length=500, description="Browser/device user agent string"
    )


class UserSessionCreate(UserSessionBase):
    """
    Schema for creating a new user session.
    """

    pass


class UserSessionRead(UserSessionBase):
    """
    Schema for reading user session data (API response).
    """

    id: int = Field(..., description="Unique session ID")

    class Config:
        from_attributes = True


class UserSessionUpdate(BaseModel):
    """
    Schema for updating a user session (PATCH/PUT).
    All fields are optional to allow partial updates.
    """

    user_id: Optional[UUID] = Field(None, description="Reference to the authenticated user")
    refresh_token: Optional[str] = Field(
        None, max_length=500, description="Secure refresh token for session renewal"
    )
    expires_at: Optional[datetime] = Field(
        None, description="When this session expires and requires re-authentication"
    )
    last_used_at: Optional[datetime] = Field(
        None, description="Last activity timestamp for session management"
    )
    ip_address: Optional[str] = Field(None, description="IP address where the session was created")
    user_agent: Optional[str] = Field(
        None, max_length=500, description="Browser/device user agent string"
    )

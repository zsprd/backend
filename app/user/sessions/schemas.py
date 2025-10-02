from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserSessionBase(BaseModel):
    """Base fields for UserSession schemas."""

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class UserSessionRead(UserSessionBase):
    """
    Schema for reading user session data.
    SECURITY: Never includes refresh_token in responses.
    """

    id: UUID = Field(..., description="Unique session identifier")
    user_id: UUID = Field(..., description="Reference to the authenticated user")
    expires_at: datetime = Field(
        ..., description="When this session expires and requires re-authentication"
    )
    last_used_at: datetime = Field(
        ..., description="Last activity timestamp for session management"
    )
    ip_address: Optional[str] = Field(None, description="IP address where the session was created")
    user_agent: Optional[str] = Field(
        None, description="Browser/device user agent string (truncated for security)"
    )
    is_active: bool = Field(..., description="Whether this session is currently active")
    created_at: datetime = Field(..., description="When this session was created")
    updated_at: datetime = Field(..., description="When this session was last updated")


class UserSessionCreate(UserSessionBase):
    """
    Schema for creating a new user session.
    """

    user_id: UUID = Field(..., description="Reference to the authenticated user")
    refresh_token: str = Field(
        ..., min_length=32, max_length=500, description="Secure refresh token for session renewal"
    )
    expires_at: datetime = Field(
        ..., description="When this session expires and requires re-authentication"
    )
    ip_address: Optional[str] = Field(
        None,
        max_length=45,  # IPv6 max length
        description="IP address where the session was created",
    )
    user_agent: Optional[str] = Field(
        None, max_length=500, description="Browser/device user agent string"
    )

    @field_validator("expires_at")
    @classmethod
    def validate_expires_at(cls, v: datetime) -> datetime:
        """Ensure expiration is in the future."""
        if v <= datetime.now(v.tzinfo):
            raise ValueError("expires_at must be in the future")
        return v

    @field_validator("refresh_token")
    @classmethod
    def validate_refresh_token(cls, v: str) -> str:
        """Ensure refresh token meets security requirements."""
        if not v or len(v.strip()) < 32:
            raise ValueError("refresh_token must be at least 32 characters")
        # Check for basic entropy (not all same character)
        if len(set(v)) < 10:
            raise ValueError("refresh_token lacks sufficient entropy")
        return v


class UserSessionUpdate(UserSessionBase):
    """
    Schema for updating a user session (PATCH/PUT).
    All fields are optional to allow partial updates.
    SECURITY: refresh_token updates require special handling.
    """

    refresh_token: Optional[str] = Field(
        None, min_length=32, max_length=500, description="New refresh token for session renewal"
    )
    expires_at: Optional[datetime] = Field(None, description="Updated expiration time")
    last_used_at: Optional[datetime] = Field(None, description="Updated last activity timestamp")
    ip_address: Optional[str] = Field(None, max_length=45, description="Updated IP address")
    user_agent: Optional[str] = Field(None, max_length=500, description="Updated user agent string")

    @field_validator("expires_at")
    @classmethod
    def validate_expires_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Ensure expiration is in the future if provided."""
        if v is not None and v <= datetime.now(v.tzinfo):
            raise ValueError("expires_at must be in the future")
        return v

    @field_validator("refresh_token")
    @classmethod
    def validate_refresh_token(cls, v: Optional[str]) -> Optional[str]:
        """Ensure refresh token meets security requirements if provided."""
        if v is not None:
            if len(v.strip()) < 32:
                raise ValueError("refresh_token must be at least 32 characters")
            if len(set(v)) < 10:
                raise ValueError("refresh_token lacks sufficient entropy")
        return v

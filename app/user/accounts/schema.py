from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserAccountBase(BaseModel):
    """
    Shared fields for UserAccount schemas.
    """

    model_config = ConfigDict(from_attributes=True)
    email: EmailStr = Field(
        ..., description="Primary email address for authentication and communication"
    )
    full_name: Optional[str] = Field(None, description="User's full display name")
    timezone: str = Field("UTC", description="User's preferred timezone for date/time display")
    base_currency: str = Field(
        "USD",
        min_length=3,
        max_length=3,
        description="User's base currency for portfolio reporting",
    )
    is_active: bool = Field(True, description="Whether the account is active and can log in")
    is_verified: bool = Field(False, description="Whether the email address has been verified")
    last_login_at: Optional[datetime] = Field(
        None, description="Timestamp of the user's last successful login"
    )


class UserAccountCreate(UserAccountBase):
    """
    Schema for creating a new user account (registration).
    """

    password: str = Field(..., min_length=8, description="Raw password (will be hashed)")


class UserAccountRead(UserAccountBase):
    """
    Schema for reading user account data (API response).
    """

    id: int = Field(..., description="Unique user account ID")
    # Relationships as lists of IDs (expand as needed)
    user_sessions: Optional[List[int]] = Field(None)
    user_subscriptions: Optional[List[int]] = Field(None)
    user_notifications: Optional[List[int]] = Field(None)
    provider_connections: Optional[List[int]] = Field(None)
    portfolio_accounts: Optional[List[int]] = Field(None)
    system_jobs: Optional[List[int]] = Field(None)


class UserAccountUpdate(BaseModel):
    """
    Schema for updating a user account (PATCH/PUT).
    All fields are optional to allow partial updates.
    """

    email: Optional[EmailStr] = Field(
        None, description="Primary email address for authentication and communication"
    )
    full_name: Optional[str] = Field(None, description="User's full display name")
    timezone: Optional[str] = Field(
        None, description="User's preferred timezone for date/time display"
    )
    base_currency: Optional[str] = Field(
        None, min_length=3, max_length=3, description="User's base currency for portfolio reporting"
    )
    is_active: Optional[bool] = Field(
        None, description="Whether the account is active and can log in"
    )
    is_verified: Optional[bool] = Field(
        None, description="Whether the email address has been verified"
    )
    last_login_at: Optional[datetime] = Field(
        None, description="Timestamp of the user's last successful login"
    )

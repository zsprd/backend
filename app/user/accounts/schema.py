from datetime import datetime
from typing import Optional
from uuid import UUID

import bleach
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def sanitize_input(value: str) -> str:
    """Sanitize user input to prevent XSS and other injection attacks."""
    cleaned = bleach.clean(value, tags=[], strip=True)
    cleaned = " ".join(cleaned.split())
    return cleaned.strip()


# Base schemas for responses
class UserAccountRead(BaseModel):
    """Schema for reading user account information."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="User's unique identifier")
    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(..., description="User's full name")
    language: str = Field(..., description="Preferred language (ISO 639-1)")
    country: str = Field(..., description="Country (ISO 3166-1 alpha-2)")
    currency: str = Field(..., description="Preferred currency (ISO 4217)")

    is_active: bool = Field(..., description="Whether the account is active")
    is_verified: bool = Field(..., description="Whether email is verified")

    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class UserAccountCreate(BaseModel):
    """Schema for creating a new user account (used internally by auth service)."""

    email: EmailStr = Field(..., description="Email address")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name")

    language: str = Field(default="en", max_length=2, description="Preferred language")
    country: str = Field(default="US", max_length=2, description="Country")
    currency: str = Field(default="USD", max_length=3, description="Currency")

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: EmailStr) -> EmailStr:
        return v.lower()

    @field_validator("full_name")
    @classmethod
    def sanitize_full_name(cls, v: str) -> str:
        sanitized = sanitize_input(v)
        if len(sanitized) < 2:
            raise ValueError("Full name must be at least 2 characters long")
        return sanitized


class UserAccountUpdate(BaseModel):
    """Schema for updating user account information."""

    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    language: Optional[str] = Field(None, max_length=2)
    country: Optional[str] = Field(None, max_length=2)
    currency: Optional[str] = Field(None, max_length=3)

    @field_validator("full_name")
    @classmethod
    def sanitize_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        sanitized = sanitize_input(v)
        if len(sanitized) < 2:
            raise ValueError("Full name must be at least 2 characters long")
        return sanitized

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) != 2:
            raise ValueError("Language must be a 2-character ISO 639-1 code")
        return v

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) != 2:
            raise ValueError("Country must be a 2-character ISO 3166-1 code")
        return v

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        if v and len(v) != 3:
            raise ValueError("Currency must be a 3-character ISO 4217 code")
        return v

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserProfileBase(BaseModel):
    """Base schema for user profile data (non-auth related)."""

    email: EmailStr = Field(..., description="Email address (unique, required)")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name")
    timezone: str = Field("UTC", description="Preferred timezone")
    base_currency: str = Field("USD", min_length=3, max_length=3, description="Base currency code")
    language: str = Field("en", min_length=2, max_length=5, description="Preferred language")
    theme_preference: str = Field("system", description="Theme preference (light/dark/system)")

    @field_validator("base_currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Ensure currency code is uppercase."""
        return v.upper() if v else v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Ensure language code is lowercase."""
        return v.lower() if v else v

    @field_validator("theme_preference")
    @classmethod
    def validate_theme(cls, v: str) -> str:
        """Validate theme preference."""
        allowed_themes = {"light", "dark", "system"}
        if v not in allowed_themes:
            raise ValueError(f"Theme must be one of: {', '.join(allowed_themes)}")
        return v


class UserProfileCreate(BaseModel):
    """Schema for creating user profile data only (used internally)."""

    email: EmailStr = Field(..., description="Email address (unique, required)")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name")
    timezone: str = Field("UTC", description="Preferred timezone")
    base_currency: str = Field("USD", min_length=3, max_length=3, description="Base currency code")
    language: str = Field("en", min_length=2, max_length=5, description="Preferred language")
    theme_preference: str = Field("system", description="Theme preference (light/dark/system)")

    @field_validator("base_currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return v.upper() if v else v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        return v.lower() if v else v

    @field_validator("theme_preference")
    @classmethod
    def validate_theme(cls, v: str) -> str:
        allowed_themes = {"light", "dark", "system"}
        if v not in allowed_themes:
            raise ValueError(f"Theme must be one of: {', '.join(allowed_themes)}")
        return v


class UserProfileUpdate(BaseModel):
    """Schema for updating user profile fields."""

    full_name: Optional[str] = Field(None, max_length=255)
    base_currency: Optional[str] = Field(None, min_length=3, max_length=3)
    timezone: Optional[str] = Field(None)
    language: Optional[str] = Field(None, min_length=2, max_length=5)
    theme_preference: Optional[str] = Field(None)

    @field_validator("base_currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        """Ensure currency code is uppercase."""
        return v.upper() if v else v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        """Ensure language code is lowercase."""
        return v.lower() if v else v

    @field_validator("theme_preference")
    @classmethod
    def validate_theme(cls, v: Optional[str]) -> Optional[str]:
        """Validate theme preference."""
        if v:
            allowed_themes = {"light", "dark", "system"}
            if v not in allowed_themes:
                raise ValueError(f"Theme must be one of: {', '.join(allowed_themes)}")
        return v


class UserProfileResponse(UserProfileBase):
    """Schema for returning user profile data in API responses."""

    id: UUID = Field(..., description="Unique user identifier")
    is_active: bool = Field(..., description="Whether the account is active")
    is_verified: bool = Field(..., description="Whether email is verified")
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last profile update timestamp")

    model_config = {"from_attributes": True}


class UserProfileListResponse(BaseModel):
    """Schema for returning paginated user list."""

    users: list[UserProfileResponse]
    total: int
    skip: int
    limit: int

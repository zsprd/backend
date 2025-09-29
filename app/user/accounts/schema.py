import re
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserAccountBase(BaseModel):
    """Base configuration for all user account schemas."""

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )


class UserAccountRead(UserAccountBase):
    """
    Schema for reading user account information.
    SECURITY: Never includes sensitive fields like hashed_password.
    """

    id: UUID = Field(..., description="User's unique identifier")
    email: str = Field(..., description="User's email address")
    full_name: str = Field(..., description="User's full name")
    language: str = Field(..., description="Preferred language (ISO 639-1)")
    country: str = Field(..., description="Country (ISO 3166-1 alpha-2)")
    currency: str = Field(..., description="Preferred currency (ISO 4217)")

    is_active: bool = Field(..., description="Whether the account is active")
    is_verified: bool = Field(..., description="Whether email is verified")

    # Security info (limited for privacy)
    last_login_at: Optional[datetime] = Field(None, description="Last login timestamp")
    is_locked: bool = Field(..., description="Whether account is currently locked")

    # Timestamps
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    active_session: Optional[UUID] = Field(
        None, description="Active session ID if user is currently logged in"
    )


class UserAccountCreate(UserAccountBase):
    """
    Schema for creating a new user account.
    Used internally by auth service with enhanced validation.
    """

    email: str = Field(..., max_length=320, description="Email address")  # RFC 5321 limit
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name")
    password: str = Field(
        ..., min_length=8, max_length=128, description="Password (will be hashed)"
    )

    language: str = Field(
        default="en", min_length=2, max_length=2, description="Preferred language (ISO 639-1)"
    )
    country: str = Field(
        default="US", min_length=2, max_length=2, description="Country (ISO 3166-1 alpha-2)"
    )
    currency: str = Field(
        default="USD", min_length=3, max_length=3, description="Currency (ISO 4217)"
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Validate and normalize email address."""
        email = v.lower().strip()

        # Basic email validation
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")

        # Check for dangerous characters
        if any(char in email for char in ["<", ">", '"', "'"]):
            raise ValueError("Email contains invalid characters")

        # Prevent email injection
        if "\n" in email or "\r" in email:
            raise ValueError("Email contains invalid characters")

        return email

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        """Validate and sanitize full name."""
        name = v.strip()

        if not name:
            raise ValueError("Full name cannot be empty")

        if len(name) < 2:
            raise ValueError("Full name must be at least 2 characters")

        # Allow letters, spaces, hyphens, apostrophes, and basic Unicode
        if not re.match(r"^[\w\s\-'.]+$", name, re.UNICODE):
            raise ValueError("Full name contains invalid characters")

        # Prevent excessive whitespace
        normalized = re.sub(r"\s+", " ", name)

        return normalized

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")

        if len(v) > 128:
            raise ValueError("Password must be less than 128 characters")

        # Check for basic complexity
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)

        if not (has_upper and has_lower and has_digit):
            raise ValueError("Password must contain uppercase, lowercase, and digit")

        # Check for common weak patterns
        if v.lower() in ["password", "12345678", "qwerty123"]:
            raise ValueError("Password is too common")

        return v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        """Validate language code."""
        lang = v.lower().strip()

        if len(lang) != 2:
            raise ValueError("Language must be 2 characters (ISO 639-1)")

        if not re.match(r"^[a-z]{2}$", lang):
            raise ValueError("Invalid language code format")

        # Basic validation for common languages
        valid_languages = {
            "en",
            "es",
            "fr",
            "de",
            "it",
            "pt",
            "ru",
            "ja",
            "ko",
            "zh",
            "ar",
            "hi",
            "tr",
            "pl",
            "nl",
            "sv",
            "da",
            "no",
            "fi",
        }

        if lang not in valid_languages:
            raise ValueError(f"Unsupported language code: {lang}")

        return lang

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: str) -> str:
        """Validate country code."""
        country = v.upper().strip()

        if len(country) != 2:
            raise ValueError("Country must be 2 characters (ISO 3166-1)")

        if not re.match(r"^[A-Z]{2}$", country):
            raise ValueError("Invalid country code format")

        return country

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code."""
        currency = v.upper().strip()

        if len(currency) != 3:
            raise ValueError("Currency must be 3 characters (ISO 4217)")

        if not re.match(r"^[A-Z]{3}$", currency):
            raise ValueError("Invalid currency code format")

        # Basic validation for common currencies
        valid_currencies = {
            "USD",
            "EUR",
            "GBP",
            "JPY",
            "CAD",
            "AUD",
            "CHF",
            "CNY",
            "SEK",
            "NOK",
            "DKK",
            "PLN",
            "CZK",
            "HUF",
            "BGN",
            "RON",
        }

        if currency not in valid_currencies:
            raise ValueError(f"Unsupported currency code: {currency}")

        return currency


class UserAccountUpdate(UserAccountBase):
    """
    Schema for updating user account information.
    All fields optional for partial updates.
    """

    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    language: Optional[str] = Field(None, min_length=2, max_length=2)
    country: Optional[str] = Field(None, min_length=2, max_length=2)
    currency: Optional[str] = Field(None, min_length=3, max_length=3)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate full name if provided."""
        if v is None:
            return v

        # Reuse validation from create schema
        return UserAccountCreate.validate_full_name(v)

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        """Validate language if provided."""
        if v is None:
            return v

        return UserAccountCreate.validate_language(v)

    @field_validator("country")
    @classmethod
    def validate_country(cls, v: Optional[str]) -> Optional[str]:
        """Validate country if provided."""
        if v is None:
            return v

        return UserAccountCreate.validate_country(v)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        """Validate currency if provided."""
        if v is None:
            return v

        return UserAccountCreate.validate_currency(v)


class UserAccountPasswordUpdate(UserAccountBase):
    """Schema for password updates with enhanced security."""

    current_password: str = Field(..., description="Current password for verification")
    new_password: str = Field(..., min_length=8, max_length=128, description="New password")
    confirm_password: str = Field(..., description="Password confirmation")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength."""
        return UserAccountCreate.validate_password(v)

    @field_validator("confirm_password")
    @classmethod
    def validate_password_match(cls, v: str, info) -> str:
        """Ensure passwords match."""
        if "new_password" in info.data and v != info.data["new_password"]:
            raise ValueError("Passwords do not match")
        return v


class UserAccountSecurity(UserAccountBase):
    """Schema for security information (admin/monitoring use)."""

    id: UUID
    email: str
    failed_login_attempts: int
    locked_until: Optional[datetime]
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    # Computed fields
    is_locked: bool = Field(..., description="Whether account is currently locked")
    is_active: bool = Field(..., description="Whether account is active")

import re
from uuid import UUID

import bleach
from pydantic import BaseModel, Field, field_validator, validate_email

from app.user.accounts.schemas import UserAccountRead


class UserRegistrationData(BaseModel):
    """Schema for user registration."""

    full_name: str = Field(
        ..., min_length=2, max_length=255, description="Full name", examples=["John Doe"]
    )
    email: str = Field(..., description="Email address", examples=["john.doe@example.com"])
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 chars, must contain uppercase, lowercase, digit, and special char)",
        examples=["StrongP@ssw0rd!"],
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        return _sanitize_full_name(v)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_email_address(v)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_strong_password(v)


class OAuthUserData(BaseModel):
    """Schema for OAuth user creation (no password required)."""

    email: str = Field(
        ..., description="Email address from OAuth provider", examples=["oauth.user@example.com"]
    )
    full_name: str = Field(
        ..., description="Full name from OAuth provider", examples=["OAuth User"]
    )
    is_verified: bool = Field(True, description="OAuth users are pre-verified", examples=[True])

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        return _sanitize_full_name(v)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_email_address(v)


class EmailConfirmRequest(BaseModel):
    """Schema for email verification."""

    token: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Email verification token",
        examples=["abc123-verification-token"],
    )

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Token cannot be empty")
        # Basic token format validation (alphanumeric, hyphens, underscores)
        if not re.match(r"^[a-zA-Z0-9\-_.]+$", cleaned):
            raise ValueError("Invalid token format")
        return cleaned


class SignInRequest(BaseModel):
    """Schema for user login."""

    email: str = Field(..., description="Email address", examples=["jane.doe@example.com"])
    password: str = Field(..., min_length=1, description="Password", examples=["StrongP@ssw0rd!"])

    @field_validator("email", mode="before")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_email_address(v)

    @field_validator("password")
    @classmethod
    def validate_password_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Password cannot be empty")
        return v


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh."""

    refresh_token: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Current refresh token",
        examples=["refresh-token-xyz987"],
    )

    @field_validator("refresh_token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Refresh token cannot be empty")
        return cleaned


class ForgotPasswordRequest(BaseModel):
    """Schema for password reset request."""

    email: str = Field(..., description="Email address", examples=["jane.doe@example.com"])

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        return _validate_email_address(v)


class ResetPasswordRequest(BaseModel):
    """Schema for password reset."""

    token: str = Field(
        ..., max_length=500, description="Password reset token", examples=["reset-token-abc456"]
    )
    new_password: str = Field(
        ..., min_length=8, max_length=128, description="New password", examples=["NewStr0ngP@ss!"]
    )

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        cleaned = v.strip()
        if not cleaned:
            raise ValueError("Token cannot be empty")
        if not re.match(r"^[a-zA-Z0-9\-_.]+$", cleaned):
            raise ValueError("Invalid token format")
        return cleaned

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_strong_password(v)


class ChangePasswordRequest(BaseModel):
    """Schema for password change (authenticated users)."""

    current_password: str = Field(
        ..., description="Current password", examples=["CurrentP@ssw0rd!"]
    )
    new_password: str = Field(
        ..., min_length=8, max_length=128, description="New password", examples=["NewStr0ngP@ss!"]
    )

    @field_validator(
        "current_password",
    )
    @classmethod
    def validate_current_password(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Current password cannot be empty")
        return v

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _validate_strong_password(value)


# Response schemas
class TokenResponse(BaseModel):
    """Base token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(TokenResponse):
    """Authentication response with user data."""

    user: UserAccountRead


class RegistrationResponse(BaseModel):
    """User registration response."""

    message: str
    user_id: UUID
    email_verification_required: bool = True
    user: UserAccountRead


class EmailVerificationResponse(BaseModel):
    """Email verification response."""

    message: str
    user: UserAccountRead


class PasswordResetResponse(BaseModel):
    """Password reset response."""

    message: str


class PasswordChangeResponse(BaseModel):
    message: str


class ForgotPasswordResponse(BaseModel):
    """Response for password reset request."""

    message: str


class LogoutResponse(BaseModel):
    """Response for user logout."""

    message: str


def _validate_email_address(email: str) -> str:
    """Validate and normalize email address."""
    try:
        validate_email(email)
    except Exception:
        raise ValueError(f"Invalid email address: {email}")

    return email.lower()


def _sanitize_full_name(value: str) -> str:
    """Sanitize user input to prevent XSS and other injection attacks."""
    # Remove all HTML tags and JavaScript
    cleaned = bleach.clean(value, tags=[], strip=True)
    cleaned = " ".join(cleaned.split())
    sanitized = cleaned.strip()
    if not sanitized:
        raise ValueError("Full name cannot be empty")
    if len(sanitized) < 2:
        raise ValueError("Full name must be at least 2 characters long")
    # Check for valid name characters (letters, spaces, hyphens, apostrophes)
    if not re.match(r"^[a-zA-Z\s\-'.]+$", sanitized):
        raise ValueError("Full name can only contain letters, spaces, hyphens, and apostrophes")

    return sanitized


def _validate_strong_password(value: str) -> str:
    """Validate password meets security requirements."""
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if len(value) > 128:
        raise ValueError("Password must not exceed 128 characters")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", value):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", value):
        raise ValueError("Password must contain at least one number")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
        raise ValueError("Password must contain at least one special character")

    # Check for common patterns
    common_patterns = [
        "password",
        "12345678",
        "qwerty",
        "letmein",
        "welcome",
        "admin",
        "user",
        "abc123",
        "iloveyou",
        "monkey",
        "dragon",
        "football",
        "baseball",
        "master",
        "sunshine",
        "shadow",
        "123123",
    ]

    if any(pattern in value.lower() for pattern in common_patterns):
        raise ValueError("Password is too common. Please choose a stronger password")

    return value

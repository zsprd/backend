import re
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.user.accounts.schema import UserAccountBase


class UserRegistrationData(BaseModel):
    """Schema for user registration."""

    full_name: str = Field(..., min_length=2, max_length=255, description="Full name")
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password (min 8 chars, must contain uppercase, lowercase, digit, and special char)",
    )

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Full name cannot be empty")
        return v.strip()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_strong_password(v)


class OAuthUserData(BaseModel):
    """Schema for OAuth user creation (no password required)."""

    email: EmailStr = Field(..., description="Email address from OAuth provider")
    full_name: str = Field(..., description="Full name from OAuth provider")
    is_verified: bool = Field(True, description="OAuth users are pre-verified")


class EmailConfirmRequest(BaseModel):
    """Schema for email verification."""

    token: str = Field(..., min_length=1, description="Email verification token")


class SignInRequest(BaseModel):
    """Schema for user login."""

    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., min_length=1, description="Password")

    @field_validator("password")
    @classmethod
    def validate_password_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Password cannot be empty")
        return v


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh."""

    refresh_token: str = Field(..., min_length=1, description="Current refresh token")


class ForgotPasswordRequest(BaseModel):
    """Schema for password reset request."""

    email: EmailStr = Field(..., description="Email address")


class ResetPasswordRequest(BaseModel):
    """Schema for password reset."""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        return _validate_strong_password(v)


class ChangePasswordRequest(BaseModel):
    """Schema for password change (authenticated users)."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

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

    user: UserAccountBase


class RegistrationResponse(BaseModel):
    """User registration response."""

    message: str
    user_id: UUID
    email_verification_required: bool = True
    user: UserAccountBase


class EmailVerificationResponse(BaseModel):
    """Email verification response."""

    message: str
    user: UserAccountBase


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


def _validate_strong_password(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long")
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", value):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", value):
        raise ValueError("Password must contain at least one number")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
        raise ValueError("Password must contain at least one special character")
    return value

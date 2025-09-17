from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.auth.utils import validate_strong_password
from app.user.accounts.schema import UserProfileResponse


class UserRegistrationData(BaseModel):
    """Schema for user registration including both auth and profile data."""

    # Auth-specific fields
    password: str = Field(..., min_length=8, description="Password")

    # Profile fields that are required during registration
    email: EmailStr = Field(..., description="Email address")
    full_name: str = Field(..., min_length=2, max_length=255, description="Full name")

    # Optional profile fields with defaults
    timezone: str = Field("UTC", description="Preferred timezone")
    base_currency: str = Field("USD", min_length=3, max_length=3, description="Base currency code")
    language: str = Field("en", min_length=2, max_length=5, description="Preferred language")
    theme_preference: str = Field("system", description="Theme preference (light/dark/system)")

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_strong_password(value)

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


class OAuthUserData(BaseModel):
    """Schema for OAuth user creation (no password required)."""

    email: EmailStr = Field(..., description="Email address from OAuth provider")
    full_name: str = Field(..., description="Full name from OAuth provider")
    is_verified: bool = Field(True, description="OAuth users are pre-verified")

    # Optional profile fields with defaults
    timezone: str = Field("UTC", description="Preferred timezone")
    base_currency: str = Field("USD", min_length=3, max_length=3, description="Base currency code")
    language: str = Field("en", min_length=2, max_length=5, description="Preferred language")
    theme_preference: str = Field("system", description="Theme preference")

    @field_validator("base_currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return v.upper() if v else v

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        return v.lower() if v else v


class EmailConfirmRequest(BaseModel):
    """Schema for email verification."""

    token: str = Field(..., description="Email verification token")


class SignInRequest(BaseModel):
    """Schema for user login."""

    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")


class RefreshTokenRequest(BaseModel):
    """Schema for token refresh."""

    refresh_token: str = Field(..., description="Current refresh token")


class ForgotPasswordRequest(BaseModel):
    """Schema for password reset request."""

    email: EmailStr = Field(..., description="Email address")


class ResetPasswordRequest(BaseModel):
    """Schema for password reset."""

    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_strong_password(value)


class ChangePasswordRequest(BaseModel):
    """Schema for password change (authenticated users)."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return validate_strong_password(value)


# Response schemas
class TokenResponse(BaseModel):
    """Base token response schema."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthResponse(TokenResponse):
    """Authentication response with user data."""

    user: UserProfileResponse


class RegistrationResponse(BaseModel):
    """User registration response."""

    message: str
    user_id: UUID
    email_verification_required: bool = True
    user: UserProfileResponse


class EmailVerificationResponse(BaseModel):
    """Email verification response."""

    message: str
    user: UserProfileResponse


class PasswordResetResponse(BaseModel):
    """Password reset response."""

    message: str

from typing import Optional
from pydantic import BaseModel, EmailStr, Field, UUID4

class SignUpRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="Password")
    full_name: str = Field(..., min_length=1, max_length=255, description="Full name")


class SignUpResponse(BaseModel):
    message: str
    user_id: UUID4
    email_verification_required: bool = True
    user: dict


class EmailConfirmRequest(BaseModel):
    token: str = Field(..., description="Email verification token")


class SignInRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address")
    password: str = Field(..., description="Password")


class SignInResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(..., description="Current refresh token")


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Email address")


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., description="Password reset token")
    new_password: str = Field(..., min_length=8, description="New password")


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")


class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str]
    base_currency: str
    timezone: str
    language: str
    theme_preference: str
    is_verified: bool
    is_premium: bool
    is_active: bool
    created_at: str
    last_login_at: Optional[str]


class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    base_currency: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    theme_preference: Optional[str] = None


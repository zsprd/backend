from typing import Optional
from pydantic import BaseModel, EmailStr, Field, UUID4, field_validator
from datetime import datetime

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

class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: Optional[str] = Field(None, min_length=8, description="Password")
    full_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Full name")
    google_id: Optional[str] = Field(None, max_length=255, description="Google OAuth ID")
    apple_id: Optional[str] = Field(None, max_length=255, description="Apple OAuth ID")
    base_currency: str = Field("USD", max_length=3, description="Base currency")
    timezone: str = Field("UTC", max_length=50, description="User timezone")
    language: str = Field("en", max_length=5, description="Language preference")
    is_verified: bool = Field(False, description="Email verification status")

    @field_validator('base_currency')
    @classmethod
    def validate_currency(cls, v: str) -> str:
        return v.upper()

    @field_validator('language') 
    @classmethod
    def validate_language(cls, v: str) -> str:
        return v.lower()


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    base_currency: Optional[str] = Field(None, max_length=3)
    timezone: Optional[str] = Field(None, max_length=50)
    language: Optional[str] = Field(None, max_length=5)
    theme_preference: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    is_premium: Optional[bool] = None

    @field_validator('base_currency')
    @classmethod
    def validate_currency(cls, v: Optional[str]) -> Optional[str]:
        return v.upper() if v else v

    @field_validator('language')
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        return v.lower() if v else v


# ===== USER SESSION SCHEMAS =====

class UserSessionCreate(BaseModel):
    user_id: UUID4 = Field(..., description="User ID")
    refresh_token: str = Field(..., min_length=1, max_length=500, description="Refresh token")
    expires_at: datetime = Field(..., description="Token expiration")
    ip_address: Optional[str] = Field(None, description="Client IP address")
    user_agent: Optional[str] = Field(None, max_length=500, description="User agent")
    device_type: Optional[str] = Field("web", max_length=50, description="Device type")


class UserSessionUpdate(BaseModel):
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = Field(None, max_length=500)
    device_type: Optional[str] = Field(None, max_length=50)


class UserSessionResponse(BaseModel):
    id: UUID4
    user_id: UUID4
    refresh_token: str
    expires_at: datetime
    created_at: datetime
    last_used_at: datetime
    ip_address: Optional[str]
    user_agent: Optional[str]
    device_type: Optional[str]
    is_expired: bool
    is_active: bool
    
    class Config:
        from_attributes = True
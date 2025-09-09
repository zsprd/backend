from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
import uuid


class UserBase(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    full_name: Optional[str] = Field(None, description="Full name")


class UserCreate(UserBase):
    password: Optional[str] = Field(None, description="Password (for email registration)")
    phone: Optional[str] = Field(None, description="Phone number")
    country: Optional[str] = Field(None, max_length=2, description="ISO country code")
    base_currency: str = Field("USD", max_length=3, description="Preferred base currency")
    timezone: str = Field("UTC", description="User timezone")
    language: str = Field("en", max_length=10, description="Preferred language")


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    base_currency: Optional[str] = None
    theme_preference: Optional[str] = None


class UserPreferences(BaseModel):
    """User preferences update"""
    base_currency: Optional[str] = Field(None, max_length=3)
    theme_preference: Optional[str] = Field(None, description="light, dark, or auto")
    timezone: Optional[str] = None
    language: Optional[str] = None
    notification_preferences: Optional[dict] = None


class User(UserBase):
    id: str
    phone: Optional[str]
    date_of_birth: Optional[datetime]
    country: Optional[str]
    timezone: str
    language: str
    base_currency: str
    theme_preference: str
    is_active: bool
    is_verified: bool
    is_premium: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    """Public user profile information"""
    id: str
    email: EmailStr
    full_name: Optional[str]
    country: Optional[str]
    base_currency: str
    theme_preference: str
    is_verified: bool
    is_premium: bool
    member_since: datetime
    
    class Config:
        from_attributes = True


class UserStats(BaseModel):
    """User statistics for admin/analytics"""
    total_accounts: int
    total_holdings: int
    total_transactions: int
    portfolio_value: float
    last_activity: Optional[datetime]
    days_active: int


# Additional schemas for auth endpoints
class UserSignUpRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str = Field(..., min_length=1)
    base_currency: str = Field("USD", pattern="^[A-Z]{3}$")
    timezone: str = Field("UTC")


class UserSignInRequest(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response for auth endpoints"""
    id: str
    email: str
    full_name: Optional[str]
    base_currency: str
    theme_preference: str
    timezone: str
    language: str
    is_verified: bool
    is_premium: bool
    is_active: bool
    created_at: str
    last_login_at: Optional[str]
    
    class Config:
        from_attributes = True
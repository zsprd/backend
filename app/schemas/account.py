from typing import Optional, List
from pydantic import BaseModel, Field, UUID4
from datetime import datetime
from app.models.enums import AccountCategory, AccountSubtypeCategory 


class InstitutionBase(BaseModel):
    name: str = Field(..., description="Institution name")
    country: str = Field(..., max_length=2, description="ISO country code")
    url: Optional[str] = Field(None, description="Institution website URL")
    logo: Optional[str] = Field(None, description="Logo URL")
    primary_color: Optional[str] = Field(None, description="Brand color in hex")


class InstitutionCreate(InstitutionBase):
    plaid_institution_id: Optional[str] = None
    supports_investments: bool = False
    supports_transactions: bool = False


class InstitutionUpdate(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    url: Optional[str] = None
    logo: Optional[str] = None
    primary_color: Optional[str] = None
    supports_investments: Optional[bool] = None
    supports_transactions: Optional[bool] = None


class Institution(InstitutionBase):
    id: UUID4
    plaid_institution_id: Optional[str]
    supports_investments: bool
    supports_transactions: bool
    created_at: datetime
    updated_at: datetime


class AccountBase(BaseModel):
    name: str = Field(..., description="Account name")
    official_name: Optional[str] = Field(None, description="Official account name from institution")
    account_type: AccountCategory = Field(..., description="Account type")
    subtype: Optional[AccountSubtypeCategory] = Field(None, description="Account subtype")
    mask: Optional[str] = Field(None, max_length=4, description="Last 4 digits of account")
    currency: str = Field("USD", max_length=3, description="Account base currency")


class AccountCreate(AccountBase):
    institution_id: Optional[UUID4] = Field(None, description="Institution ID")
    plaid_account_id: Optional[str] = Field(None, description="Plaid account ID")


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    official_name: Optional[str] = None
    account_type: Optional[AccountCategory] = None
    subtype: Optional[AccountSubtypeCategory] = None
    mask: Optional[str] = None
    currency: Optional[str] = None
    is_active: Optional[bool] = None


class Account(AccountBase):
    id: UUID4
    user_id: UUID4
    institution_id: Optional[UUID4]
    plaid_account_id: Optional[str]
    plaid_item_id: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    institution: Optional[Institution] = None


class AccountWithBalances(Account):
    """Account with current balance information"""
    current_balance: Optional[float] = Field(None, description="Current account balance")
    available_balance: Optional[float] = Field(None, description="Available balance")
    limit: Optional[float] = Field(None, description="Credit limit for credit accounts")
    market_value: Optional[float] = Field(None, description="Market value for investment accounts")
    cash_value: Optional[float] = Field(None, description="Cash value for investment accounts")
    last_updated: Optional[datetime] = Field(None, description="Last balance update")


class AccountSummary(BaseModel):
    """Account summary for dashboard"""
    id: UUID4
    name: str
    account_type: str
    currency: str
    current_balance: Optional[float]
    market_value: Optional[float]
    total_return: Optional[float]
    total_return_percent: Optional[float]
    is_active: bool

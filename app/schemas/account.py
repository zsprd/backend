from typing import Optional, List
from pydantic import BaseModel, Field, UUID4
from datetime import datetime
from app.models.enums import AccountType, AccountSubtype


# Institution Schemas
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
    
    class Config:
        from_attributes = True


# Account Schemas
class AccountBase(BaseModel):
    name: str = Field(..., description="Account name")
    official_name: Optional[str] = Field(None, description="Official account name from institution")
    type: AccountType = Field(..., description="Account type")
    subtype: Optional[AccountSubtype] = Field(None, description="Account subtype")
    mask: Optional[str] = Field(None, max_length=4, description="Last 4 digits of account")
    currency: str = Field("USD", max_length=3, description="Account base currency")


class AccountCreate(AccountBase):
    institution_id: Optional[UUID4] = Field(None, description="Institution ID")
    plaid_account_id: Optional[str] = Field(None, description="Plaid account ID")


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    official_name: Optional[str] = None
    type: Optional[AccountType] = None
    subtype: Optional[AccountSubtype] = None
    mask: Optional[str] = None
    currency: Optional[str] = None
    institution_id: Optional[UUID4] = None
    is_active: Optional[bool] = None


class Account(AccountBase):
    id: UUID4
    user_id: UUID4
    institution_id: Optional[UUID4]
    plaid_account_id: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Optional nested institution data
    institution: Optional[Institution] = None
    
    class Config:
        from_attributes = True


class AccountSummary(BaseModel):
    """Account summary with calculated metrics"""
    account_id: UUID4
    account_name: str
    account_type: AccountType
    currency: str
    total_value: float = Field(..., description="Current total value")
    holdings_count: int = Field(..., description="Number of holdings")
    last_transaction_date: Optional[datetime] = Field(None, description="Date of last transaction")
    performance_ytd: float = Field(..., description="Year-to-date performance percentage")
    
    class Config:
        from_attributes = True


# List response schemas
class AccountList(BaseModel):
    accounts: List[Account]
    total: int
    skip: int
    limit: int
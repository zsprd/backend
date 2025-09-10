from typing import Optional
from pydantic import BaseModel, Field, UUID4, field_validator, model_validator
from datetime import datetime
from decimal import Decimal


# Institution Schemas
class InstitutionBase(BaseModel):
    name: str = Field(..., max_length=255, description="Institution name")
    country: str = Field(..., max_length=2, description="ISO country code")
    website_url: Optional[str] = Field(None, max_length=255, description="Institution website")
    logo_url: Optional[str] = Field(None, max_length=500, description="Logo URL")
    primary_color: Optional[str] = Field(None, max_length=7, description="Hex color code")


class InstitutionCreate(InstitutionBase):
    plaid_institution_id: Optional[str] = Field(None, max_length=255)
    supports_investments: bool = Field(False, description="Supports investment accounts")
    supports_transactions: bool = Field(False, description="Supports transaction sync")


class InstitutionResponse(InstitutionBase):
    id: UUID4
    plaid_institution_id: Optional[str]
    supports_investments: bool
    supports_transactions: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Account Schemas
from app.models.enums import AccountCategory, AccountSubtypeCategory

class AccountBase(BaseModel):
    name: str = Field(..., max_length=255, description="Account display name")
    official_name: Optional[str] = Field(None, max_length=255, description="Official account name")
    account_category: AccountCategory = Field(..., description="Account category")
    account_subtype: Optional[AccountSubtypeCategory] = Field(None, description="Account subtype")
    mask: Optional[str] = Field(None, max_length=4, description="Last 4 digits")
    currency: str = Field("USD", max_length=3, description="Account currency")


    @model_validator(mode="before")
    @classmethod
    def coerce_enums(cls, values):
        # Coerce account_category to enum if it's a string
        ac = values.get("account_category")
        if ac is not None and not isinstance(ac, AccountCategory):
            try:
                values["account_category"] = AccountCategory(ac.lower())
            except Exception:
                pass
        # Coerce account_subtype to enum if it's a string
        ast = values.get("account_subtype")
        if ast is not None and not isinstance(ast, AccountSubtypeCategory):
            try:
                values["account_subtype"] = AccountSubtypeCategory(ast.lower())
            except Exception:
                pass
        # Ensure currency is uppercase
        cur = values.get("currency")
        if cur is not None and isinstance(cur, str):
            values["currency"] = cur.upper()
        return values


class AccountCreate(AccountBase):
    institution_id: Optional[UUID4] = Field(None, description="Institution ID")
    plaid_account_id: Optional[str] = Field(None, max_length=255)


class AccountUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    official_name: Optional[str] = Field(None, max_length=255)
    account_category: Optional[AccountCategory] = None
    account_subtype: Optional[AccountSubtypeCategory] = None
    currency: Optional[str] = Field(None, max_length=3)
    is_active: Optional[bool] = None

    @field_validator('account_category', mode='before')
    @classmethod
    def ensure_account_category_lower(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

    @field_validator('account_subtype', mode='before')
    @classmethod
    def ensure_account_subtype_lower(cls, v):
        if v is not None and isinstance(v, str):
            return v.lower()
        return v

    @field_validator('currency', mode='before')
    @classmethod
    def ensure_currency_upper(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v


class AccountResponse(AccountBase):
    id: UUID4
    user_id: UUID4
    institution_id: Optional[UUID4]
    is_active: bool
    plaid_account_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    institution: Optional[InstitutionResponse] = None
    

    @model_validator(mode="before")
    @classmethod
    def coerce_enums(cls, values):
        ac = values.get("account_category")
        if ac is not None and not isinstance(ac, AccountCategory):
            try:
                values["account_category"] = AccountCategory(ac.lower())
            except Exception:
                pass
        ast = values.get("account_subtype")
        if ast is not None and not isinstance(ast, AccountSubtypeCategory):
            try:
                values["account_subtype"] = AccountSubtypeCategory(ast.lower())
            except Exception:
                pass
        cur = values.get("currency")
        if cur is not None and isinstance(cur, str):
            values["currency"] = cur.upper()
        return values

    class Config:
        from_attributes = True


class AccountSummaryResponse(BaseModel):
    account_id: UUID4
    name: str
    currency: str
    total_market_value: Decimal
    total_cost_basis: Decimal
    unrealized_gain_loss: Decimal
    unrealized_gain_loss_percent: Decimal
    cash_balance: Decimal
    holdings_count: int
    last_updated: datetime
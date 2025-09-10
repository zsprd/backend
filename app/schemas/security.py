from typing import Optional
from app.models.enums import SecurityCategory
from pydantic import BaseModel, Field, UUID4
from datetime import datetime


class SecurityBase(BaseModel):
    symbol: str = Field(..., max_length=20, description="Trading symbol")
    name: str = Field(..., max_length=255, description="Security name")
    category: SecurityCategory = Field(..., description="Security category (equity, etf, etc.)")
    currency: str = Field("USD", max_length=3, description="Trading currency")
    exchange: Optional[str] = Field(None, max_length=10, description="Exchange code")
    country: Optional[str] = Field(None, max_length=2, description="Country code")
    sector: Optional[str] = Field(None, max_length=100, description="Sector")
    industry: Optional[str] = Field(None, max_length=100, description="Industry")

    @classmethod
    def _ensure_category_lower(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

    @classmethod
    def _ensure_currency_upper(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v

    @classmethod
    def __get_pydantic_core_schema__(cls, *args, **kwargs):
        from pydantic import GetCoreSchemaHandler
        from pydantic_core import core_schema
        schema = super().__get_pydantic_core_schema__(*args, **kwargs)
        schema = core_schema.no_info_after_validator_function(
            lambda v: cls._ensure_category_lower(v) if v is not None else v,
            schema
        )
        schema = core_schema.no_info_after_validator_function(
            lambda v: cls._ensure_currency_upper(v) if v is not None else v,
            schema
        )
        return schema


class SecurityCreate(SecurityBase):
    cusip: Optional[str] = Field(None, max_length=9)
    isin: Optional[str] = Field(None, max_length=12)
    sedol: Optional[str] = Field(None, max_length=7)
    plaid_security_id: Optional[str] = Field(None, max_length=255)
    alphavantage_symbol: Optional[str] = Field(None, max_length=20)
    data_provider_category: Optional[str] = None


class SecurityUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    sector: Optional[str] = Field(None, max_length=100)
    industry: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    is_delisted: Optional[bool] = None


class SecurityResponse(SecurityBase):
    id: UUID4
    cusip: Optional[str]
    isin: Optional[str]
    sedol: Optional[str]
    plaid_security_id: Optional[str]
    alphavantage_symbol: Optional[str]
    data_provider_category: Optional[str]
    is_active: bool
    is_delisted: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SecurityBasicInfo(BaseModel):
    """Lightweight security info for nested responses"""
    id: UUID4
    symbol: str
    name: str
    category: SecurityCategory
    currency: str
    exchange: Optional[str]
    sector: Optional[str]

    @classmethod
    def _ensure_category_lower(cls, v):
        if isinstance(v, str):
            return v.lower()
        return v

    @classmethod
    def _ensure_currency_upper(cls, v):
        if isinstance(v, str):
            return v.upper()
        return v

    @classmethod
    def __get_pydantic_core_schema__(cls, *args, **kwargs):
        from pydantic import GetCoreSchemaHandler
        from pydantic_core import core_schema
        schema = super().__get_pydantic_core_schema__(*args, **kwargs)
        schema = core_schema.no_info_after_validator_function(
            lambda v: cls._ensure_category_lower(v) if v is not None else v,
            schema
        )
        schema = core_schema.no_info_after_validator_function(
            lambda v: cls._ensure_currency_upper(v) if v is not None else v,
            schema
        )
        return schema
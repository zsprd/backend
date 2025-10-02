from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SecurityBase(BaseModel):
    plaid_security_id: Optional[str] = None
    institution_id: Optional[UUID] = None
    institution_security_id: Optional[str] = None
    symbol: Optional[str] = None
    name: str
    security_type: str
    security_subtype: Optional[str] = None
    currency: str = Field("USD", max_length=3)
    exchange: Optional[str] = None
    country: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    cusip: Optional[str] = None
    isin: Optional[str] = None
    sedol: Optional[str] = None
    is_cash_equivalent: Optional[bool] = False
    data_source: str = Field("manual")
    option_details: Optional[dict] = None
    fixed_income_details: Optional[dict] = None


class SecurityCreate(SecurityBase):
    pass


class SecurityUpdate(BaseModel):
    name: Optional[str] = None
    security_type: Optional[str] = None
    security_subtype: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    is_cash_equivalent: Optional[bool] = None
    option_details: Optional[dict] = None
    fixed_income_details: Optional[dict] = None
    data_source: Optional[str] = None
    institution_id: Optional[UUID] = None
    institution_security_id: Optional[str] = None
    symbol: Optional[str] = None
    currency: Optional[str] = None
    exchange: Optional[str] = None
    country: Optional[str] = None
    cusip: Optional[str] = None

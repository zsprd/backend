from typing import Optional
from pydantic import BaseModel, Field, UUID4
from datetime import datetime
from app.models.enums import SecurityCategory


class SecurityBase(BaseModel):
    symbol: str = Field(..., max_length=20, description="Security symbol")
    name: str = Field(..., max_length=255, description="Security name")
    security_type: SecurityCategory = Field(..., description="Security type")
    currency: str = Field("USD", max_length=3, description="Security currency")
    exchange: Optional[str] = Field(None, max_length=10, description="Exchange")
    country: Optional[str] = Field(None, max_length=2, description="ISO country code")
    sector: Optional[str] = Field(None, max_length=100, description="Sector")
    industry: Optional[str] = Field(None, max_length=100, description="Industry")


class SecurityCreate(SecurityBase):
    cusip: Optional[str] = Field(None, max_length=9, description="CUSIP identifier")
    isin: Optional[str] = Field(None, max_length=12, description="ISIN identifier")
    sedol: Optional[str] = Field(None, max_length=7, description="SEDOL identifier")
    plaid_security_id: Optional[str] = Field(None, description="Plaid security ID")
    alphavantage_symbol: Optional[str] = Field(None, description="Alpha Vantage symbol")


class SecurityUpdate(BaseModel):
    name: Optional[str] = None
    security_type: Optional[SecurityCategory] = Field(None, alias="type")  # FIXED
    currency: Optional[str] = None
    exchange: Optional[str] = None
    country: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    cusip: Optional[str] = None
    isin: Optional[str] = None
    sedol: Optional[str] = None
    is_active: Optional[bool] = None


class Security(SecurityBase):
    id: UUID4
    cusip: Optional[str]
    isin: Optional[str]
    sedol: Optional[str]
    plaid_security_id: Optional[str]
    alphavantage_symbol: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class SecurityWithPrice(Security):
    """Security with current price information"""
    current_price: Optional[float] = Field(None, description="Current market price")
    previous_close: Optional[float] = Field(None, description="Previous close price")
    price_change: Optional[float] = Field(None, description="Price change")
    price_change_percent: Optional[float] = Field(None, description="Price change percentage")
    last_updated: Optional[datetime] = Field(None, description="Last price update")
    volume: Optional[int] = Field(None, description="Trading volume")


class SecuritySearch(BaseModel):
    """Security search result"""
    symbol: str
    name: str
    security_type: str = Field(alias="type")  # FIXED
    exchange: Optional[str]
    currency: str
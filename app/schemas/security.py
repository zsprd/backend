from typing import Optional, List
from pydantic import BaseModel, Field, UUID4
from datetime import datetime
from app.models.enums import SecurityType, DataSource


class SecurityBase(BaseModel):
    symbol: str = Field(..., max_length=20, description="Security symbol")
    name: str = Field(..., max_length=255, description="Security name")
    type: SecurityType = Field(..., description="Security type")
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
    type: Optional[SecurityType] = None
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
    
    class Config:
        from_attributes = True


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
    id: UUID4
    symbol: str
    name: str
    type: SecurityType
    exchange: Optional[str]
    currency: str
    sector: Optional[str]
    current_price: Optional[float]
    market_cap: Optional[float] = Field(None, description="Market capitalization")
    
    class Config:
        from_attributes = True


class SecurityPerformance(BaseModel):
    """Security performance metrics"""
    security_id: UUID4
    symbol: str
    name: str
    
    # Price metrics
    current_price: float
    day_change: float
    day_change_percent: float
    
    # Period returns
    return_1d: Optional[float] = None
    return_1w: Optional[float] = None
    return_1m: Optional[float] = None
    return_3m: Optional[float] = None
    return_6m: Optional[float] = None
    return_1y: Optional[float] = None
    return_ytd: Optional[float] = None
    
    # Risk metrics
    volatility_30d: Optional[float] = None
    volatility_90d: Optional[float] = None
    beta: Optional[float] = None
    
    # Trading metrics
    volume_avg_30d: Optional[int] = None
    volume_today: Optional[int] = None


class SecurityList(BaseModel):
    """Paginated securities list"""
    securities: List[SecurityWithPrice]
    total: int
    skip: int
    limit: int
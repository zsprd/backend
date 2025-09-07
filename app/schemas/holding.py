from typing import Optional, List
from pydantic import BaseModel, Field, UUID4
from datetime import datetime, date
from decimal import Decimal


# Security Schemas (for nested responses)
class SecurityBasicInfo(BaseModel):
    id: UUID4
    symbol: str
    name: str
    type: str
    currency: str
    exchange: Optional[str]
    sector: Optional[str]
    
    class Config:
        from_attributes = True


# Holding Schemas
class HoldingBase(BaseModel):
    quantity: Decimal = Field(..., description="Number of shares/units held")
    cost_basis_per_share: Optional[Decimal] = Field(None, description="Average cost per share")
    cost_basis_total: Optional[Decimal] = Field(None, description="Total cost basis")
    market_value: Optional[Decimal] = Field(None, description="Current market value")
    currency: str = Field(..., max_length=3, description="Currency of the holding")
    as_of_date: date = Field(..., description="Date of the holding snapshot")


class HoldingCreate(HoldingBase):
    account_id: UUID4 = Field(..., description="Account ID")
    security_id: UUID4 = Field(..., description="Security ID")
    plaid_account_id: Optional[str] = Field(None, description="Plaid account ID")
    plaid_security_id: Optional[str] = Field(None, description="Plaid security ID")
    institution_price: Optional[Decimal] = Field(None, description="Price from institution")
    institution_value: Optional[Decimal] = Field(None, description="Value from institution")


class HoldingUpdate(BaseModel):
    quantity: Optional[Decimal] = None
    cost_basis_per_share: Optional[Decimal] = None
    cost_basis_total: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    currency: Optional[str] = None
    as_of_date: Optional[date] = None
    institution_price: Optional[Decimal] = None
    institution_value: Optional[Decimal] = None


class Holding(HoldingBase):
    id: UUID4
    account_id: UUID4
    security_id: UUID4
    plaid_account_id: Optional[str]
    plaid_security_id: Optional[str]
    institution_price: Optional[Decimal]
    institution_value: Optional[Decimal]
    created_at: datetime
    updated_at: datetime
    
    # Nested relationships
    security: Optional[SecurityBasicInfo] = None
    
    class Config:
        from_attributes = True


class HoldingWithMetrics(Holding):
    """Holding with calculated performance metrics"""
    current_price: Optional[float] = Field(None, description="Current market price")
    unrealized_gain_loss: Optional[float] = Field(None, description="Unrealized P&L")
    unrealized_gain_loss_percent: Optional[float] = Field(None, description="Unrealized P&L percentage")
    portfolio_weight: Optional[float] = Field(None, description="Weight in portfolio percentage")
    market_value_base_currency: Optional[float] = Field(None, description="Market value in base currency")


# Position Schemas
class PositionBase(BaseModel):
    quantity: Decimal = Field(..., description="Current position quantity")
    average_cost: Optional[Decimal] = Field(None, description="Average cost basis")
    unrealized_gain_loss: Optional[Decimal] = Field(None, description="Unrealized P&L")
    lot_method: str = Field("fifo", description="Lot accounting method")


class PositionCreate(PositionBase):
    account_id: UUID4
    security_id: UUID4


class PositionUpdate(BaseModel):
    quantity: Optional[Decimal] = None
    average_cost: Optional[Decimal] = None
    unrealized_gain_loss: Optional[Decimal] = None
    lot_method: Optional[str] = None


class Position(PositionBase):
    id: UUID4
    account_id: UUID4
    security_id: UUID4
    updated_at: datetime
    
    # Nested relationships
    security: Optional[SecurityBasicInfo] = None
    
    class Config:
        from_attributes = True


# Bulk Operations
class BulkHoldingCreate(BaseModel):
    """Schema for bulk holding creation"""
    holdings: List[HoldingCreate] = Field(..., description="List of holdings to create")
    replace_existing: bool = Field(False, description="Replace existing holdings for the same date")


class BulkHoldingResponse(BaseModel):
    """Response for bulk holding operations"""
    created_count: int
    updated_count: int
    error_count: int
    errors: List[str] = []
    holdings: List[Holding] = []


# Holdings Summary
class HoldingsSummary(BaseModel):
    """Summary of holdings for an account or portfolio"""
    total_holdings: int
    total_market_value: float
    total_cost_basis: float
    total_unrealized_gain_loss: float
    total_unrealized_gain_loss_percent: float
    base_currency: str
    as_of_date: date
    
    by_asset_type: dict = Field(default_factory=dict, description="Breakdown by asset type")
    by_sector: dict = Field(default_factory=dict, description="Breakdown by sector")
    by_currency: dict = Field(default_factory=dict, description="Breakdown by currency")
    
    top_holdings: List[HoldingWithMetrics] = Field(default_factory=list, description="Top holdings by value")


# Search and Filter
class HoldingsFilter(BaseModel):
    """Filter parameters for holdings queries"""
    account_ids: Optional[List[UUID4]] = None
    security_types: Optional[List[str]] = None
    sectors: Optional[List[str]] = None
    currencies: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    as_of_date: Optional[date] = None


class HoldingsList(BaseModel):
    """Paginated holdings list response"""
    holdings: List[HoldingWithMetrics]
    total: int
    skip: int
    limit: int
    summary: HoldingsSummary
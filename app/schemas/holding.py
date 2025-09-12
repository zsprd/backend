from typing import Optional
from pydantic import BaseModel, Field, UUID4
from datetime import datetime, date
from decimal import Decimal

from app.schemas.security import SecurityBasicInfo



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
    plaid_account_id: Optional[str] = Field(None, max_length=255)
    plaid_security_id: Optional[str] = Field(None, max_length=255)
    institution_price: Optional[Decimal] = Field(None, description="Price from institution")
    institution_value: Optional[Decimal] = Field(None, description="Value from institution")


class HoldingUpdate(BaseModel):
    quantity: Optional[Decimal] = None
    cost_basis_per_share: Optional[Decimal] = None
    cost_basis_total: Optional[Decimal] = None
    market_value: Optional[Decimal] = None
    currency: Optional[str] = Field(None, max_length=3)
    as_of_date: Optional[date] = None
    institution_price: Optional[Decimal] = None
    institution_value: Optional[Decimal] = None


class HoldingResponse(HoldingBase):
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


class HoldingSummaryResponse(BaseModel):
    account_id: UUID4
    total_holdings: int
    total_market_value: Decimal
    total_cost_basis: Decimal
    total_unrealized_gain_loss: Decimal
    total_unrealized_gain_loss_percent: Decimal
    base_currency: str
    by_asset_type: dict[str, Decimal]
    by_sector: dict
    by_geography: dict
    as_of_date: date

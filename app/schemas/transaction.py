from typing import Optional, List
from pydantic import BaseModel, Field, UUID4
from datetime import datetime, date
from decimal import Decimal

from app.schemas.security import SecurityBasicInfo
from app.models.enums import TransactionCategory, TransactionSideCategory


class TransactionBase(BaseModel):
    transaction_category: TransactionCategory = Field(..., description="Transaction category")
    transaction_side: Optional[TransactionSideCategory] = Field(None, description="Buy or sell side")
    quantity: Optional[Decimal] = Field(None, description="Quantity of securities")
    price: Optional[Decimal] = Field(None, description="Price per unit")
    amount: Decimal = Field(..., description="Total transaction amount")
    fees: Optional[Decimal] = Field(None, description="Transaction fees")
    tax: Optional[Decimal] = Field(None, description="Tax amount")
    trade_date: date = Field(..., description="Trade execution date")
    settlement_date: Optional[date] = Field(None, description="Settlement date")
    transaction_currency: str = Field(..., max_length=3, description="Transaction currency")
    fx_rate: Optional[Decimal] = Field(None, description="FX rate if currency conversion")
    description: Optional[str] = Field(None, description="Transaction description")
    memo: Optional[str] = Field(None, description="Additional notes")
    subcategory: Optional[str] = Field(None, max_length=100, description="Transaction subcategory")


class TransactionCreate(TransactionBase):
    account_id: UUID4 = Field(..., description="Account ID")
    security_id: Optional[UUID4] = Field(None, description="Security ID (if applicable)")
    plaid_transaction_id: Optional[str] = Field(None, max_length=255)
    data_provider: str = Field("manual", description="Data provider source")


class TransactionUpdate(BaseModel):
    transaction_category: Optional[TransactionCategory] = None
    transaction_side: Optional[TransactionSideCategory] = None
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    fees: Optional[Decimal] = None
    tax: Optional[Decimal] = None
    trade_date: Optional[date] = None
    settlement_date: Optional[date] = None
    description: Optional[str] = None
    memo: Optional[str] = None
    subcategory: Optional[str] = None


class TransactionResponse(TransactionBase):
    id: UUID4
    account_id: UUID4
    security_id: Optional[UUID4]
    plaid_transaction_id: Optional[str]
    data_provider: str
    created_at: datetime
    updated_at: datetime
    
    # Nested relationships
    security: Optional[SecurityBasicInfo] = None
    
    class Config:
        from_attributes = True


class TransactionSummaryResponse(BaseModel):
    account_id: Optional[UUID4]
    total_transactions: int
    total_invested: Decimal
    total_fees: Decimal
    total_dividends: Decimal
    date_range: dict
    by_category: dict
    recent_transactions: List[TransactionResponse]

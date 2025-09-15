from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TransactionBase(BaseModel):
    account_id: UUID
    security_id: Optional[UUID] = None
    plaid_transaction_id: Optional[str] = None
    plaid_account_id: Optional[str] = None
    cancel_transaction_id: Optional[str] = None
    transaction_type: str
    transaction_subtype: Optional[str] = None
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    amount: Decimal
    fees: Optional[Decimal] = 0
    currency: str = Field("USD", max_length=3)
    data_source: str = Field("manual")
    as_of_date: date
    trade_date: Optional[date] = None
    settlement_date: Optional[date] = None
    name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TransactionCreate(TransactionBase):
    pass


class TransactionUpdate(BaseModel):
    account_id: Optional[UUID] = None
    security_id: Optional[UUID] = None
    plaid_transaction_id: Optional[str] = None
    plaid_account_id: Optional[str] = None
    cancel_transaction_id: Optional[str] = None
    transaction_type: Optional[str] = None
    transaction_subtype: Optional[str] = None
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    amount: Optional[Decimal] = None
    fees: Optional[Decimal] = None
    currency: Optional[str] = None
    data_source: Optional[str] = None
    as_of_date: Optional[date] = None
    trade_date: Optional[date] = None
    settlement_date: Optional[date] = None
    name: Optional[str] = None


class TransactionResponse(TransactionBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class HoldingBase(BaseModel):
    account_id: UUID
    security_id: UUID
    quantity: Decimal
    data_source: str = Field("manual")
    as_of_date: date


class HoldingCreate(HoldingBase):
    cost_basis: Optional[Decimal] = None
    plaid_account_id: Optional[str] = None
    institution_price: Optional[Decimal] = None
    institution_value: Optional[Decimal] = None


class HoldingUpdate(BaseModel):
    quantity: Optional[Decimal] = None
    cost_basis: Optional[Decimal] = None
    institution_price: Optional[Decimal] = None
    institution_value: Optional[Decimal] = None
    data_source: Optional[str] = None
    as_of_date: Optional[date] = None
    plaid_account_id: Optional[str] = None
    account_id: Optional[UUID] = None
    security_id: Optional[UUID] = None


class HoldingRead(HoldingBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- DB-aligned Market Data Schemas ---
class MarketDataBase(BaseModel):
    security_id: UUID
    as_of_date: date
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    close_price: Decimal
    volume: Optional[int] = None
    adjusted_close: Optional[Decimal] = None
    data_source: str = Field("calculated")


class MarketDataCreate(MarketDataBase):
    pass


class MarketDataUpdate(BaseModel):
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    close_price: Optional[Decimal] = None
    volume: Optional[int] = None
    adjusted_close: Optional[Decimal] = None
    data_source: Optional[str] = None
    as_of_date: Optional[date] = None
    security_id: Optional[UUID] = None


class MarketDataResponse(MarketDataBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime

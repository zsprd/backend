from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class AnalyticsPerformanceBase(BaseModel):
    account_id: UUID
    as_of_date: date
    benchmark_symbol: str
    alpha: Optional[Decimal] = None
    beta: Optional[Decimal] = None
    correlation: Optional[Decimal] = None
    best_day: Optional[Decimal] = None
    worst_day: Optional[Decimal] = None
    positive_periods: Optional[int] = None
    negative_periods: Optional[int] = None
    win_rate: Optional[Decimal] = None
    time_series_data: Optional[dict] = None
    calculation_status: str
    error_message: Optional[str] = None


class AnalyticsPerformanceResponse(AnalyticsPerformanceBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

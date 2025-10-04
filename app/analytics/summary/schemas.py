from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AnalyticsSummaryBase(BaseModel):
    account_id: UUID
    as_of_date: date
    available_balance: Optional[Decimal] = None
    current_balance: Optional[Decimal] = None
    balance_limit: Optional[Decimal] = None
    market_value: Decimal
    cost_basis: Decimal
    cash_contributions: Decimal
    fees_paid: Optional[Decimal] = 0
    total_return: Optional[Decimal] = None
    annualized_return: Optional[Decimal] = None
    ytd_return: Optional[Decimal] = None
    daily_return: Optional[Decimal] = None
    equity_value: Optional[Decimal] = 0
    debt_value: Optional[Decimal] = 0
    cash_value: Optional[Decimal] = 0
    alternatives_value: Optional[Decimal] = 0
    domestic_value: Optional[Decimal] = 0
    international_value: Optional[Decimal] = 0
    currency: str
    holdings_count: Optional[int] = 0
    data_quality: Optional[str] = None
    last_price_date: Optional[date] = None


class AnalyticsSummaryResponse(AnalyticsSummaryBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime

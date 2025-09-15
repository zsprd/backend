from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class AnalyticsRiskBase(BaseModel):
    account_id: UUID
    as_of_date: date
    volatility: Decimal
    sharpe_ratio: Optional[Decimal] = None
    sortino_ratio: Optional[Decimal] = None
    calmar_ratio: Optional[Decimal] = None
    omega_ratio: Optional[Decimal] = None
    max_drawdown: Decimal
    current_drawdown: Decimal
    average_drawdown: Optional[Decimal] = None
    max_drawdown_duration: Optional[int] = None
    recovery_time: Optional[int] = None
    var_95: Decimal
    var_99: Decimal
    var_99_9: Optional[Decimal] = None
    cvar_95: Decimal
    cvar_99: Optional[Decimal] = None
    downside_deviation: Decimal
    skewness: Optional[Decimal] = None
    kurtosis: Optional[Decimal] = None
    gain_loss_ratio: Optional[Decimal] = None
    tail_ratio: Optional[Decimal] = None
    gross_leverage: Optional[Decimal] = None
    net_leverage: Optional[Decimal] = None
    long_exposure: Optional[Decimal] = None
    short_exposure: Optional[Decimal] = None
    margin_utilization: Optional[Decimal] = None
    up_capture_ratio: Optional[Decimal] = None
    down_capture_ratio: Optional[Decimal] = None
    time_series_data: Optional[dict] = None
    calculation_status: str
    error_message: Optional[str] = None


class AnalyticsRiskResponse(AnalyticsRiskBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

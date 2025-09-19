from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AnalyticsExposureBase(BaseModel):
    account_id: UUID
    as_of_date: date
    allocation_by_asset_class: dict
    allocation_by_security_type: dict
    allocation_by_security_subtype: dict
    allocation_by_sector: dict
    allocation_by_industry: dict
    allocation_by_region: dict
    allocation_by_country: dict
    allocation_by_currency: dict
    allocation_by_equity_style: Optional[dict] = None
    allocation_by_debt_style: Optional[dict] = None
    top_5_weight: Decimal
    top_10_weight: Decimal
    largest_position_weight: Decimal
    top_holdings: list
    calculation_status: str
    error_message: Optional[str] = None


class AnalyticsExposureResponse(AnalyticsExposureBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SystemHealthBase(BaseModel):
    """
    Shared fields for SystemHealth schemas.
    """

    metric_name: str = Field(
        ..., description="Metric identifier: api_response_time, db_connections, memory_usage"
    )
    metric_value: Decimal = Field(..., description="Numerical value of the metric")
    metric_unit: Optional[str] = Field(
        None, description="Unit of measurement: ms, count, percent, bytes"
    )
    component: Optional[str] = Field(
        None, description="System component: api, database, worker, cache"
    )
    environment: str = Field(
        "production", description="Environment: production, staging, development"
    )
    recorded_at: datetime = Field(..., description="When this metric was recorded")


class SystemHealthCreate(SystemHealthBase):
    """
    Schema for creating a new system health metric.
    """

    pass


class SystemHealthRead(SystemHealthBase):
    """
    Schema for reading system health metric data (API response).
    """

    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="Unique metric ID")

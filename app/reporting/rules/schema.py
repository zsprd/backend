from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class MonitoringAlertBase(BaseModel):
    user_id: UUID
    alert_type: str
    description: Optional[str] = None
    conditions: dict
    is_active: bool = True
    last_triggered_at: Optional[datetime] = None
    trigger_count: int = 0


class MonitoringAlertCreate(MonitoringAlertBase):
    pass


class MonitoringAlertUpdate(BaseModel):
    alert_type: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[dict] = None
    is_active: Optional[bool] = None
    last_triggered_at: Optional[datetime] = None
    trigger_count: Optional[int] = None


class MonitoringAlertResponse(MonitoringAlertBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime

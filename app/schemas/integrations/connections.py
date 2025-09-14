from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DataConnectionBase(BaseModel):
    name: str = Field(..., max_length=255, description="User-friendly connection name")
    data_source: str = Field(
        ...,
        description="Data source. Allowed: plaid, manual, bulk, calculated, yfinance, alphavantage",
    )
    status: str = Field("active", description="Connection status. Allowed: active, error, expired")
    error_message: Optional[str] = Field(None, description="Last error encountered")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Provider-specific data")
    last_sync_at: Optional[datetime] = Field(None, description="Last successful sync")
    plaid_item_id: Optional[str] = Field(None, max_length=255, description="Plaid item ID")
    plaid_access_token: Optional[str] = Field(
        None, max_length=500, description="Encrypted Plaid access token"
    )


class DataConnectionCreate(DataConnectionBase):
    user_id: UUID = Field(..., description="User ID")
    institution_id: Optional[UUID] = Field(None, description="Institution ID")


class DataConnectionUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    data_source: Optional[str] = Field(
        None,
        description="Data source. Allowed: plaid, manual, bulk, calculated, yfinance, alphavantage",
    )
    status: Optional[str] = Field(
        None, description="Connection status. Allowed: active, error, expired"
    )
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    last_sync_at: Optional[datetime] = None
    plaid_item_id: Optional[str] = None
    plaid_access_token: Optional[str] = None
    institution_id: Optional[UUID] = None


class DataConnectionResponse(DataConnectionBase):
    id: UUID
    user_id: UUID
    institution_id: Optional[UUID]
    created_at: datetime

from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class SystemLogBase(BaseModel):
    """
    Shared fields for SystemLog schemas.
    """

    log_level: str = Field(
        ..., max_length=10, description="Log severity: debug, info, warn, error, critical"
    )
    message: str = Field(..., description="Primary log message")
    context: Optional[Dict[str, Any]] = Field(
        None, description="Additional structured context data"
    )
    user_id: Optional[UUID] = Field(None, description="Associated user (if applicable)")
    source: Optional[str] = Field(
        None, max_length=100, description="Component/module that generated the log entry"
    )
    request_id: Optional[str] = Field(
        None, max_length=100, description="Request tracking ID for correlation"
    )


class SystemLogCreate(SystemLogBase):
    """
    Schema for creating a new system log entry.
    """

    pass


class SystemLogRead(SystemLogBase):
    """
    Schema for reading system log data (API response).
    """

    id: int = Field(..., description="Unique log entry ID")

    class Config:
        from_attributes = True


class SystemLogUpdate(BaseModel):
    """
    Schema for updating a system log entry (PATCH/PUT).
    All fields are optional to allow partial updates.
    """

    log_level: Optional[str] = Field(
        None, max_length=10, description="Log severity: debug, info, warn, error, critical"
    )
    message: Optional[str] = Field(None, description="Primary log message")
    context: Optional[Dict[str, Any]] = Field(
        None, description="Additional structured context data"
    )
    user_id: Optional[UUID] = Field(None, description="Associated user (if applicable)")
    source: Optional[str] = Field(
        None, max_length=100, description="Component/module that generated the log entry"
    )
    request_id: Optional[str] = Field(
        None, max_length=100, description="Request tracking ID for correlation"
    )

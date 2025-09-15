from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ImportJobBase(BaseModel):
    job_type: str = Field(..., description="Job type. Allowed: accounts, transactions, holdings")
    status: str = Field(
        "pending", description="Job status. Allowed: pending, running, completed, failed"
    )
    filename: Optional[str] = Field(None, max_length=255, description="File name")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    total_records: int = Field(0, description="Total records in import")
    processed_records: int = Field(0, description="Records processed")
    failed_records: int = Field(0, description="Records failed")
    error_message: Optional[str] = Field(None, description="Error message")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Job-specific metadata")
    started_at: Optional[datetime] = Field(None, description="Job start time")
    completed_at: Optional[datetime] = Field(None, description="Job completion time")


class ImportJobCreate(ImportJobBase):
    user_id: UUID = Field(..., description="UserProfile ID")
    data_connection_id: Optional[UUID] = Field(None, description="Data connection ID")


class ImportJobUpdate(BaseModel):
    status: Optional[str] = Field(
        None, description="Job status. Allowed: pending, running, completed, failed"
    )
    error_message: Optional[str] = None
    processed_records: Optional[int] = None
    failed_records: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    filename: Optional[str] = None
    file_size: Optional[int] = None


class ImportJobResponse(ImportJobBase):
    id: UUID
    user_id: UUID
    data_connection_id: Optional[UUID]
    created_at: datetime

    class Config:
        from_attributes = True

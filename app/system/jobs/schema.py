from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SystemJobBase(BaseModel):
    """
    Shared fields for SystemJob schemas.
    """

    user_id: Optional[UUID] = Field(
        None, description="Reference to user who initiated the job (if applicable)"
    )
    job_type: str = Field(
        ...,
        max_length=50,
        description="Job category: data_import, analytics_calc, report_gen, maintenance",
    )
    job_name: Optional[str] = Field(
        None, max_length=255, description="Human-readable job description"
    )
    status: str = Field(
        ..., max_length=20, description="Job status: pending, running, completed, failed, cancelled"
    )
    priority: int = Field(50, description="Job priority level (higher number = more urgent)")
    total_records: int = Field(0, description="Total number of records/items to process")
    processed_records: int = Field(0, description="Number of records successfully processed")
    failed_records: int = Field(0, description="Number of records that failed processing")
    error_message: Optional[str] = Field(None, description="Error message if job failed")
    job_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Job-specific configuration and runtime data"
    )
    started_at: Optional[datetime] = Field(None, description="When job execution started")
    completed_at: Optional[datetime] = Field(
        None, description="When job execution completed (success or failure)"
    )


class SystemJobCreate(SystemJobBase):
    """
    Schema for creating a new system job.
    """

    pass


class SystemJobRead(SystemJobBase):
    """
    Schema for reading system job data (API response).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Unique system job ID")


class SystemJobUpdate(BaseModel):
    """
    Schema for updating a system job (PATCH/PUT).
    All fields are optional to allow partial updates.
    """

    user_id: Optional[UUID] = Field(
        None, description="Reference to user who initiated the job (if applicable)"
    )
    job_type: Optional[str] = Field(
        None,
        max_length=50,
        description="Job category: data_import, analytics_calc, report_gen, maintenance",
    )
    job_name: Optional[str] = Field(
        None, max_length=255, description="Human-readable job description"
    )
    status: Optional[str] = Field(
        None,
        max_length=20,
        description="Job status: pending, running, completed, failed, cancelled",
    )
    priority: Optional[int] = Field(
        None, description="Job priority level (higher number = more urgent)"
    )
    total_records: Optional[int] = Field(
        None, description="Total number of records/items to process"
    )
    processed_records: Optional[int] = Field(
        None, description="Number of records successfully processed"
    )
    failed_records: Optional[int] = Field(
        None, description="Number of records that failed processing"
    )
    error_message: Optional[str] = Field(None, description="Error message if job failed")
    job_metadata: Optional[Dict[str, Any]] = Field(
        None, description="Job-specific configuration and runtime data"
    )
    started_at: Optional[datetime] = Field(None, description="When job execution started")
    completed_at: Optional[datetime] = Field(
        None, description="When job execution completed (success or failure)"
    )

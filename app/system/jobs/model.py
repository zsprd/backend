from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.user.accounts.model import UserAccount


class SystemJob(BaseModel):
    """
    Background job processing and status tracking.

    Manages asynchronous tasks including data imports, analytics calculations,
    report generation, and system maintenance. Provides detailed progress
    tracking and error handling for operational visibility.
    """

    __tablename__ = "system_jobs"

    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Reference to user who initiated the job (if applicable)",
    )

    job_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Job category: data_import, analytics_calc, report_gen, maintenance",
    )

    job_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Human-readable job description"
    )

    status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
        comment="Job status: pending, running, completed, failed, cancelled",
    )

    priority: Mapped[int] = mapped_column(
        Integer,
        default=50,
        nullable=False,
        comment="Job priority level (higher number = more urgent)",
    )

    # Progress tracking
    total_records: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Total number of records/items to process"
    )

    processed_records: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Number of records successfully processed"
    )

    failed_records: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Number of records that failed processing"
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Error message if job failed"
    )

    # Job-specific data and configuration
    job_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Job-specific configuration and runtime data"
    )

    # Timing information
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="When job execution started"
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When job execution completed (success or failure)",
    )

    # Relationships
    user_accounts: Mapped[Optional["UserAccount"]] = relationship(
        "UserAccount", back_populates="system_jobs"
    )

    @property
    def progress_percentage(self) -> float:
        """Calculate job completion percentage."""
        if self.total_records == 0:
            return 0.0
        return (self.processed_records / self.total_records) * 100.0

    @property
    def is_running(self) -> bool:
        """Check if job is currently running."""
        return self.status == "running"

    @property
    def is_completed(self) -> bool:
        """Check if job completed successfully."""
        return self.status == "completed"

    @property
    def has_failed(self) -> bool:
        """Check if job failed."""
        return self.status == "failed"

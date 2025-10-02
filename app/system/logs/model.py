from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model import BaseModel

if TYPE_CHECKING:
    pass


class SystemLog(BaseModel):
    """
    System logging for application errors, debugging, and monitoring.

    Centralized logging for application events, errors, performance metrics,
    and operational information. For debugging and system health monitoring.

    NOTE: This is different from UserLog which tracks user actions for audit purposes.
    """

    __tablename__ = "system_logs"

    # Log severity level
    log_level: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="Log severity: debug, info, warning, error, critical",
    )

    # Primary log message
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Primary log message or error description",
    )

    # Source of the log
    source: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Component/module that generated the log (e.g., 'auth.login', 'api.payments')",
    )

    # Log category for filtering
    category: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        comment="Log category: api, database, celery, external_service, etc.",
    )

    # Exception/error details
    exception_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Python exception class name if applicable",
    )

    stack_trace: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Full stack trace for errors",
    )

    # Structured context data
    context: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional structured context data (request data, variables, etc.)",
    )

    # Request tracking
    request_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Request tracking ID for correlation across logs",
    )

    request_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="API endpoint or request path if applicable",
    )

    request_method: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="HTTP method if applicable",
    )

    # Performance metrics
    duration_ms: Mapped[Optional[int]] = mapped_column(
        nullable=True,
        comment="Execution duration in milliseconds (for performance logging)",
    )

    environment: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        comment="Environment: development, staging, production",
    )

    def __repr__(self) -> str:
        return f"<SystemLog(level={self.log_level}, source={self.source}, message={self.message[:50]}...)>"

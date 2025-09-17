from typing import TYPE_CHECKING, Any, Dict, Optional
from uuid import UUID

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.user.accounts.model import UserAccount


class SystemLog(BaseModel):
    """
    System logging and error tracking for debugging and monitoring.

    Centralized logging system for application events, errors, and
    operational information. Supports structured logging with context
    data for effective debugging and system monitoring.
    """

    __tablename__ = "system_logs"

    log_level: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
        comment="Log severity: debug, info, warn, error, critical",
    )

    message: Mapped[str] = mapped_column(Text, nullable=False, comment="Primary log message")

    context: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True, comment="Additional structured context data"
    )

    user_id: Mapped[Optional[UUID]] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="Associated user (if applicable)",
    )

    source: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Component/module that generated the log entry"
    )

    request_id: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, index=True, comment="Request tracking ID for correlation"
    )

    # Relationships
    user_accounts: Mapped[Optional["UserAccount"]] = relationship(
        "UserAccount", back_populates="system_logs"
    )

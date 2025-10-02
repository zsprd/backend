import uuid
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.user.accounts.model import UserAccount


class UserLog(BaseModel):
    """
    User activity audit logging for compliance and security monitoring.

    Immutable audit trail of user actions for compliance, security,
    and forensic analysis. Tracks WHO did WHAT, WHEN, and WHERE.
    """

    __tablename__ = "user_logs"

    # Who performed the action
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who performed the action (SET NULL preserves audit trail if user deleted)",
    )

    # What action was performed
    action: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Action type: login, create, update, delete, view, etc.",
    )

    # What was the target of the action
    target_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Resource category: users, documents, projects, etc.",
    )

    target_id: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="Specific resource ID that was affected",
    )

    # Human-readable description
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable description of the action",
    )

    # Request context
    request_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="API endpoint or URL path",
    )

    request_method: Mapped[Optional[str]] = mapped_column(
        String(10),
        nullable=True,
        comment="HTTP method: GET, POST, PUT, DELETE, etc.",
    )

    request_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Additional request data, before/after values, etc.",
    )

    # Where did it come from
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        index=True,
        comment="IP address (IPv4 or IPv6)",
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="Browser/client user agent string",
    )

    # Status and result
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="success",
        comment="Action result: success, failure, error",
    )

    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Error details if action failed",
    )

    # Relationships
    user_accounts: Mapped[Optional["UserAccount"]] = relationship(
        "UserAccount",
        back_populates="user_logs",
        foreign_keys=[user_id],
    )

    def __repr__(self) -> str:
        return f"<UserLog(user_id={self.user_id}, action={self.action}, target={self.target_category}/{self.target_id})>"

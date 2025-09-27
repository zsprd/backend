import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import INET, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.user.accounts.model import UserAccount


class UserSession(BaseModel):
    """
    User authentication session management for secure token handling.

    Tracks active user sessions with refresh tokens for secure authentication.
    Includes session metadata for security monitoring and device management.

    Security Features:
    - Unique refresh tokens with proper indexing
    - Automatic expiration handling
    - IP and user agent tracking for security monitoring
    - Cascade deletion when user is deleted
    - Optimized queries with composite indexes
    """

    __tablename__ = "user_sessions"

    # Core session data
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the authenticated user",
    )

    refresh_token: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        nullable=False,
        index=True,
        comment="Secure refresh token for session renewal",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="When this session expires and requires re-authentication",
    )

    last_used_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,  # Index for session cleanup and monitoring
        comment="Last activity timestamp for session management",
    )

    # Session metadata for security monitoring
    ip_address: Mapped[Optional[str]] = mapped_column(
        INET,
        nullable=True,
        index=True,  # Index for security monitoring queries
        comment="IP address where the session was created",
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Browser/device user agent string"
    )

    # Session state management
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,  # Critical for active session queries
        comment="Whether this session is currently active",
    )

    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When this session was revoked (for audit trail)",
    )

    # Relationships
    user_accounts: Mapped["UserAccount"] = relationship(
        "UserAccount",
        back_populates="user_sessions",
        lazy="select",  # Explicit lazy loading for performance
    )

    # Table constraints for data integrity
    __table_args__ = (
        # Ensure expires_at is always in the future when created
        CheckConstraint("expires_at > created_at", name="ck_session_expires_after_creation"),
        # Ensure revoked_at is set when is_active is False (for manual revocations)
        CheckConstraint(
            "(is_active = true) OR (is_active = false AND revoked_at IS NOT NULL)",
            name="ck_session_revoked_when_inactive",
        ),
        # Ensure last_used_at is not in the future
        CheckConstraint("last_used_at <= expires_at", name="ck_session_last_used_before_expiry"),
        # Composite indexes for common query patterns
        Index(
            "idx_user_sessions_user_active",
            "user_id",
            "is_active",
            "expires_at",
            postgresql_where="is_active = true",
        ),
        Index(
            "idx_user_sessions_cleanup",
            "expires_at",
            "is_active",
            postgresql_where="expires_at < NOW()",
        ),
        Index("idx_user_sessions_security_monitoring", "ip_address", "created_at", "user_id"),
        Index("idx_user_sessions_token_lookup", "refresh_token", "is_active", "expires_at"),
        # Add table comment
        {"comment": "User authentication sessions with enhanced security and monitoring"},
    )

    def __repr__(self) -> str:
        """Secure representation without exposing sensitive data."""
        return (
            f"<UserSession(id={self.id!r}, "
            f"user_id={self.user_id!r}, "
            f"is_active={self.is_active!r}, "
            f"expires_at={self.expires_at!r})>"
        )

    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        from datetime import timezone

        return self.expires_at <= datetime.now(timezone.utc)

    @property
    def is_valid(self) -> bool:
        """Check if session is active and not expired."""
        return self.is_active and not self.is_expired

    def to_dict_safe(self) -> dict:
        """
        Convert to dictionary without sensitive data.
        Used for logging and monitoring.
        """
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "expires_at": self.expires_at.isoformat(),
            "last_used_at": self.last_used_at.isoformat(),
            "ip_address": self.ip_address,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            # Deliberately exclude refresh_token and user_agent for security
        }

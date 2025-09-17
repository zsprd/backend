from datetime import datetime
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import INET
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.user.accounts.model import UserAccount


class UserSession(BaseModel):
    """
    User authentication session management for secure token handling.

    Tracks active user sessions with refresh tokens for secure authentication.
    Includes session metadata for security monitoring and device management.
    """

    __tablename__ = "user_sessions"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
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
        comment="Last activity timestamp for session management",
    )

    # Session metadata for security monitoring
    ip_address: Mapped[Optional[str]] = mapped_column(
        INET, nullable=True, comment="IP address where the session was created"
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Browser/device user agent string"
    )

    # Relationships
    user_accounts: Mapped["UserAccount"] = relationship(
        "UserAccount", back_populates="user_sessions"
    )

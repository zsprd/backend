from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModelWithSoftDelete
from app.portfolio.accounts.model import PortfolioAccount
from app.system.logs.model import SystemLog
from app.user.notifications.model import UserNotification
from app.user.sessions.model import UserSession
from app.user.subscriptions.model import UserSubscription


class UserAccount(BaseModelWithSoftDelete):
    __tablename__ = "user_accounts"

    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(320),
        unique=True,
        nullable=False,
        index=True,
        comment="Primary email address for authentication and communication",
    )

    hashed_password: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Bcrypt hashed password (null for OAuth-only accounts)"
    )

    # Account status fields
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the account is active and can log in",
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether the email address has been verified",
    )

    # Profile fields
    full_name: Mapped[str] = mapped_column(String(100), nullable=False, comment="User's full name")

    language: Mapped[str] = mapped_column(
        String(2),
        default="en",
        nullable=False,
        comment="Preferred language for the user (ISO 639-1 code)",
    )

    country: Mapped[str] = mapped_column(
        String(2),
        default="US",
        nullable=False,
        comment="Country of residence (ISO 3166-1 alpha-2 code)",
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
        comment="Currency code (ISO 4217 format) for displaying monetary values",
    )

    # Security and tracking fields
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp of the user's last successful login",
    )

    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="Number of consecutive failed login attempts"
    )

    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Account locked until this timestamp due to failed login attempts",
    )

    # Relationships
    user_sessions: Mapped[List["UserSession"]] = relationship(
        "UserSession",
        back_populates="user_accounts",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    user_subscriptions: Mapped[List["UserSubscription"]] = relationship(
        "UserSubscription",
        back_populates="user_accounts",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    user_notifications: Mapped[List["UserNotification"]] = relationship(
        "UserNotification",
        back_populates="user_accounts",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    portfolio_accounts: Mapped[List["PortfolioAccount"]] = relationship(
        "PortfolioAccount", back_populates="user_accounts", passive_deletes=True
    )

    system_logs: Mapped[List["SystemLog"]] = relationship(
        "SystemLog", back_populates="user_accounts", passive_deletes=True
    )

    def __repr__(self) -> str:
        return f"<UserAccount {self.id}: {self.email}>"

    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if not self.locked_until:
            return False
        return self.locked_until > datetime.now(timezone.utc)

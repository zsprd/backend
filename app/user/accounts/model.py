from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel
from app.portfolio.master.model import PortfolioMaster

if TYPE_CHECKING:
    from app.user.logs.model import UserLog
    from app.user.notifications.model import UserNotification
    from app.user.sessions.model import UserSession
    from app.user.subscriptions.model import UserSubscription


class UserAccount(BaseModel):
    """
    User account model with enhanced security and audit capabilities.

    Handles authentication, authorization, and user profile management
    with comprehensive security features including account lockout,
    audit logging, and proper data validation.
    """

    __tablename__ = "user_accounts"

    # Core authentication fields
    email: Mapped[str] = mapped_column(
        String(320),  # RFC 5321 maximum
        unique=True,
        nullable=False,
        index=True,
        comment="Primary email address for authentication and communication",
    )

    hashed_password: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Bcrypt hashed password (null for OAuth-only master)"
    )

    # Account status and security fields
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,  # Index for filtering active users
        comment="Whether the account is active and can log in",
    )

    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,  # Index for filtering verified users
        comment="Whether the email address has been verified",
    )

    # Profile fields with validation
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

    # Security and audit fields
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,  # Index for security monitoring
        comment="Timestamp of the user's last successful login",
    )

    failed_login_attempts: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        index=True,  # Index for security monitoring
        comment="Number of consecutive failed login attempts",
    )

    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,  # Index for lockout cleanup queries
        comment="Account locked until this timestamp due to failed login attempts",
    )

    # Relationships (using singular names for better semantics)
    user_sessions: Mapped[List["UserSession"]] = relationship(
        "UserSession",
        back_populates="user_accounts",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select",
    )

    user_subscriptions: Mapped[List["UserSubscription"]] = relationship(
        "UserSubscription",
        back_populates="user_accounts",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select",
    )

    user_notifications: Mapped[List["UserNotification"]] = relationship(
        "UserNotification",
        back_populates="user_accounts",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="select",
    )

    portfolio_accounts: Mapped[List["PortfolioMaster"]] = relationship(
        "PortfolioMaster", back_populates="user_accounts", passive_deletes=True, lazy="select"
    )

    user_logs: Mapped[List["UserLog"]] = relationship(
        "UserLog", back_populates="user_accounts", passive_deletes=True, lazy="select"
    )

    # Database constraints and indexes for security and performance
    __table_args__ = (
        # Security constraints
        CheckConstraint(
            "failed_login_attempts >= 0", name="ck_user_account_failed_attempts_positive"
        ),
        CheckConstraint(
            "failed_login_attempts <= 10",  # Reasonable upper limit
            name="ck_user_account_failed_attempts_limit",
        ),
        CheckConstraint(
            "length(email) >= 5",  # Minimum reasonable email length
            name="ck_user_account_email_min_length",
        ),
        CheckConstraint("length(full_name) >= 2", name="ck_user_account_name_min_length"),
        CheckConstraint("length(language) = 2", name="ck_user_account_language_iso"),
        CheckConstraint("length(country) = 2", name="ck_user_account_country_iso"),
        CheckConstraint("length(currency) = 3", name="ck_user_account_currency_iso"),
        # Ensure locked_until is in the future when set
        CheckConstraint(
            "(locked_until IS NULL) OR (locked_until > created_at)",
            name="ck_user_account_lockout_future",
        ),
        # Performance and security indexes
        Index(
            "idx_user_account_email_active",
            "email",
            "is_active",
            postgresql_where="is_active = true",
        ),
        Index(
            "idx_user_account_security_monitoring",
            "failed_login_attempts",
            "locked_until",
            "last_login_at",
            postgresql_where="failed_login_attempts > 0 OR locked_until IS NOT NULL",
        ),
        Index(
            "idx_user_account_lockout_cleanup",
            "locked_until",
            postgresql_where="locked_until IS NOT NULL",
        ),
        Index(
            "idx_user_account_verification_status",
            "is_verified",
            postgresql_where="is_verified = false",
        ),
        Index(
            "idx_user_account_last_login",
            "last_login_at",
            postgresql_where="last_login_at IS NOT NULL",
        ),
        # Add table comment
        {"comment": "User master with comprehensive security and audit features"},
    )

    def __repr__(self) -> str:
        """Secure representation without exposing sensitive data."""
        return f"<UserAccount(id={self.id!r}, email={self.email!r}, active={self.is_active!r})>"

    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked."""
        if not self.locked_until:
            return False
        return self.locked_until > datetime.now(timezone.utc)

    @property
    def lockout_time_remaining(self) -> Optional[int]:
        """Get remaining lockout time in minutes."""
        if not self.is_locked:
            return None

        remaining = self.locked_until - datetime.now(timezone.utc)
        return max(0, int(remaining.total_seconds() / 60))

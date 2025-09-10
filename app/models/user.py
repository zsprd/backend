import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.models.base import Base

if TYPE_CHECKING:
    from app.models.user_session import UserSession
    from app.models.account import Account
    from app.models.notification import Notification
    from app.models.subscription import Subscription
    from app.models.audit_log import AuditLog
    from app.models.alert import Alert
    from app.models.import_job import ImportJob
    from app.models.report import Report
    from app.models.plaid_item import PlaidItem


class User(Base):
    """Simplified User model for MVP."""
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Core profile
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    base_currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    timezone: Mapped[str] = mapped_column(String(50), nullable=False, default="UTC")
    language: Mapped[str] = mapped_column(String(10), nullable=False, default="en")
    theme_preference: Mapped[str] = mapped_column(String(10), nullable=False, default="light")

    # OAuth providers
    google_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)
    apple_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, unique=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships (typed)
    sessions: Mapped[list["UserSession"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    accounts: Mapped[list["Account"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[list["Notification"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    subscription: Mapped[Optional["Subscription"]] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    import_jobs: Mapped[list["ImportJob"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    reports: Mapped[list["Report"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    plaid_items: Mapped[list["PlaidItem"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', verified={self.is_verified})>"

    def to_dict(self) -> dict:
        """Convert user to dictionary for API responses."""
        return {
            "id": str(self.id),
            "email": self.email,
            "full_name": self.full_name,
            "base_currency": self.base_currency,
            "timezone": self.timezone,
            "language": self.language,
            "theme_preference": self.theme_preference,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_premium": self.is_premium,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @property
    def display_name(self) -> str:
        """Get user's display name."""
        return self.full_name or self.email.split('@')[0]

    @property
    def is_oauth_user(self) -> bool:
        """Check if user registered via OAuth."""
        return self.google_id is not None or self.apple_id is not None

    def can_login(self) -> bool:
        """Check if user can login."""
        return self.is_active

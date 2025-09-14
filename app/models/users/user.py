"""
SQLAlchemy model for users (authentication, profile, etc.).
"""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.monitoring.alert import Alert
    from app.models.monitoring.audit import AuditLog
    from app.models.portfolios.account import PortfolioAccount
    from app.models.users.notification import UserNotification
    from app.models.users.session import UserSession
    from app.models.users.subscription import UserSubscription


class User(BaseModel):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now()
    )

    # Relationships
    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession", back_populates="users", cascade="all, delete-orphan"
    )
    accounts: Mapped[list["PortfolioAccount"]] = relationship(
        "PortfolioAccount", back_populates="users", cascade="all, delete-orphan"
    )
    notifications: Mapped[list["UserNotification"]] = relationship(
        "UserNotification", back_populates="users", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list["UserSubscription"]] = relationship(
        "UserSubscription", back_populates="users", cascade="all, delete-orphan"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="users", cascade="all, delete-orphan"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        back_populates="users", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', verified={self.is_verified})>"

    def to_dict(self) -> dict:
        """Convert users to dictionary for API responses."""
        return {
            "id": str(self.id),
            "email": self.email,
            "full_name": self.full_name,
            "base_currency": self.base_currency,
            "timezone": self.timezone,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "last_login_at": (self.last_login_at.isoformat() if self.last_login_at else None),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @property
    def display_name(self) -> str:
        """Get users's display name."""
        return self.full_name or self.email.split("@")[0]

    def can_login(self) -> bool:
        """Check if users can log in."""
        return self.is_active

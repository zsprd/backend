from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.portfolios.account.model import PortfolioAccount
    from app.system.audit.model import SystemAudit
    from app.users.notification.model import UserNotification
    from app.users.session.model import UserSession
    from app.users.subscription.model import UserSubscription


class UserProfile(BaseModel):
    __tablename__ = "users"

    # Core fields
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Preferences
    timezone: Mapped[str] = mapped_column(String(50), default="UTC", nullable=False)
    base_currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    language: Mapped[str] = mapped_column(String(5), default="en", nullable=False)
    theme_preference: Mapped[str] = mapped_column(String(20), default="system", nullable=False)

    # Status fields
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    sessions: Mapped[list["UserSession"]] = relationship(
        "UserSession", back_populates="user", cascade="all, delete-orphan"
    )
    accounts: Mapped[list["PortfolioAccount"]] = relationship(
        "PortfolioAccount", back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[list["UserNotification"]] = relationship(
        "UserNotification", back_populates="user", cascade="all, delete-orphan"
    )
    subscriptions: Mapped[list["UserSubscription"]] = relationship(
        "UserSubscription", back_populates="user", cascade="all, delete-orphan"
    )
    audits: Mapped[list["SystemAudit"]] = relationship(
        "SystemAudit", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<UserProfile(id={self.id}, email='{self.email}', verified={self.is_verified})>"

    def to_dict(self) -> dict:
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "email": self.email,
            "full_name": self.full_name,
            "timezone": self.timezone,
            "base_currency": self.base_currency,
            "language": self.language,
            "theme_preference": self.theme_preference,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

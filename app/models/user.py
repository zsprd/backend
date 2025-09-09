from sqlalchemy import Column, String, Boolean, DateTime, Date, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.models.base import Base


class User(Base):
    """
    User model that matches your existing database schema exactly.
    """
    __tablename__ = "users"

    # Primary key
    id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        comment="Unique user identifier"
    )
    
    # Authentication
    email = Column(String(255), unique=True, nullable=False, comment="User email address")
    email_verified = Column(Boolean, nullable=False, default=False, comment="Email verification status")
    password_hash = Column(String(255), nullable=True, comment="Hashed password")
    
    # Profile information
    full_name = Column(String(255), nullable=True, comment="User's full name")
    first_name = Column(String(255), nullable=True, comment="User's first name")
    last_name = Column(String(255), nullable=True, comment="User's last name")
    profile_image = Column(Text, nullable=True, comment="Profile image URL")
    phone = Column(String(20), nullable=True, comment="Phone number")
    date_of_birth = Column(Date, nullable=True, comment="Date of birth")
    country = Column(String(2), nullable=True, comment="Country code (ISO 2-letter)")
    
    # Preferences and settings
    timezone = Column(String(50), nullable=False, default='UTC', comment="User timezone")
    language = Column(String(10), nullable=False, default='en', comment="Language preference")
    base_currency = Column(String(3), nullable=False, default='USD', comment="Base currency (ISO 3-letter)")
    theme_preference = Column(String(10), nullable=False, default='light', comment="UI theme preference")
    
    # Status flags
    is_active = Column(Boolean, nullable=False, default=True, comment="Account active status")
    is_verified = Column(Boolean, nullable=False, default=False, comment="Account verification status")
    is_premium = Column(Boolean, nullable=False, default=False, comment="Premium subscription status")
    
    # Timestamps
    last_login_at = Column(DateTime(timezone=True), nullable=True, comment="Last login timestamp")
    created_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        comment="Account creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        comment="Last update timestamp"
    )

    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', active={self.is_active})>"

    def to_dict(self) -> dict:
        """Convert user to dictionary for API responses."""
        return {
            "id": str(self.id),
            "email": self.email,
            "email_verified": self.email_verified,
            "full_name": self.full_name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "profile_image": self.profile_image,
            "phone": self.phone,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "country": self.country,
            "timezone": self.timezone,
            "language": self.language,
            "base_currency": self.base_currency,
            "theme_preference": self.theme_preference,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_premium": self.is_premium,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    @property
    def display_name(self) -> str:
        """Get display name for the user."""
        if self.full_name:
            return self.full_name
        elif self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        else:
            return self.email.split('@')[0]

    @property
    def is_email_verified(self) -> bool:
        """Check if email is verified (alias for email_verified)."""
        return self.email_verified

    def update_last_login(self):
        """Update the last login timestamp."""
        from datetime import datetime
        self.last_login_at = datetime.utcnow()
        
from sqlalchemy import Column, String, Boolean, DateTime, Date, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.models.base import Base


class User(Base):
    """
    User model aligned with corrected database schema.
    Uses is_verified instead of email_verified.
    """
    __tablename__ = "users"

    # Primary key
    id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        comment="Unique user identifier"
    )
    
    # Authentication - REMOVED email_verified, only using is_verified
    email = Column(String(255), unique=True, nullable=False, comment="User email address")
    password_hash = Column(String(255), nullable=True, comment="Bcrypt hashed password")
    
    # Profile information
    full_name = Column(String(255), nullable=True, comment="User's full name")
    phone = Column(String(20), nullable=True, comment="Phone number")
    date_of_birth = Column(Date, nullable=True, comment="Date of birth")
    country = Column(String(2), nullable=True, comment="Country code (ISO 2-letter)")
    
    # Preferences and settings
    timezone = Column(String(50), nullable=False, default='UTC', comment="User timezone")
    language = Column(String(10), nullable=False, default='en', comment="Language preference")
    base_currency = Column(String(3), nullable=False, default='USD', comment="Base currency (ISO 3-letter)")
    theme_preference = Column(String(10), nullable=False, default='light', comment="UI theme preference")
    
    # Status flags - ONLY is_verified, removed email_verified
    is_active = Column(Boolean, nullable=False, default=True, comment="Account active status")
    is_verified = Column(Boolean, nullable=False, default=False, comment="Email verification status")
    is_premium = Column(Boolean, nullable=False, default=False, comment="Premium subscription status")
    
    # OAuth fields (for future social login)
    google_id = Column(String(255), nullable=True, comment="Google OAuth ID")
    apple_id = Column(String(255), nullable=True, comment="Apple OAuth ID")
    
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
        onupdate=func.now(),  # Auto-update on modifications
        comment="Last update timestamp"
    )

    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")
    import_jobs = relationship("ImportJob", back_populates="user", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="user", cascade="all, delete-orphan")
    plaid_items = relationship("PlaidItem", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email='{self.email}', verified={self.is_verified}, active={self.is_active})>"

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert user to dictionary for API responses.
        
        Args:
            include_sensitive: If True, includes sensitive fields like password_hash
        """
        data = {
            "id": str(self.id),
            "email": self.email,
            "full_name": self.full_name,
            "phone": self.phone,
            "date_of_birth": self.date_of_birth.isoformat() if bool(self.date_of_birth) else None,
            "country": self.country,
            "timezone": self.timezone,
            "language": self.language,
            "base_currency": self.base_currency,
            "theme_preference": self.theme_preference,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "is_premium": self.is_premium,
            "last_login_at": self.last_login_at.isoformat() if bool(self.last_login_at) else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
        
        if include_sensitive:
            data.update({
                "password_hash": self.password_hash,
                "google_id": self.google_id,
                "apple_id": self.apple_id
            })
            
        return data

    @property
    def display_name(self) -> str:
        """Get user's display name (full_name or email)."""
        if bool(self.full_name):
            return str(self.full_name)
        else:
            return self.email.split('@')[0]

    @property
    def is_oauth_user(self) -> bool:
        """Check if user registered via OAuth."""
        return self.google_id is not None or self.apple_id is not None

    def can_login(self) -> bool:
        """Check if user can login (active account)."""
        return bool(self.is_active)
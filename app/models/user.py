from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class User(BaseModel):
    __tablename__ = "users"
    
    # Personal Information
    email = Column(String(255), unique=True, index=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    full_name = Column(String(255))
    first_name = Column(String(100))
    last_name = Column(String(100))
    
    # Authentication (for NextAuth.js integration)
    password_hash = Column(String(255))  # Optional if using OAuth only
    
    # Profile
    profile_image = Column(Text)  # URL to profile image
    phone = Column(String(20))
    date_of_birth = Column(DateTime(timezone=True))
    country = Column(String(2))  # ISO country code
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")
    
    # Preferences
    base_currency = Column(String(3), default="USD", nullable=False)
    theme_preference = Column(String(20), default="light")  # light, dark, auto
    notification_preferences = Column(Text)  # JSON string
    
    # Account Status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_premium = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    last_login_at = Column(DateTime(timezone=True))
    password_changed_at = Column(DateTime(timezone=True))
    
    # OAuth Integration
    google_id = Column(String(255), unique=True)
    apple_id = Column(String(255), unique=True)
    
    # Relationships
    accounts = relationship("Account", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    import_jobs = relationship("ImportJob", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
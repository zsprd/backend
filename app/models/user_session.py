from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

from app.models.base import Base


class UserSession(Base):
    """
    User session model for managing refresh tokens and session tracking.
    
    This table stores active user sessions with refresh tokens, allowing for:
    - Secure refresh token management
    - Session tracking and analytics
    - Remote logout capability
    - Device/location tracking
    """
    __tablename__ = "user_sessions"

    id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        comment="Unique session identifier"
    )
    
    user_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the user who owns this session"
    )
    
    session_token = Column(
        String(500), 
        nullable=False,
        index=True,
        comment="Session identifier token"
    )
    
    refresh_token = Column(
        String(500),
        nullable=True,
        index=True,
        comment="JWT refresh token for obtaining new access tokens"
    )
    
    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        comment="When this session expires"
    )
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When this session was created"
    )
    
    last_accessed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="When this session was last used"
    )
    
    ip_address = Column(
        INET,
        nullable=True,
        comment="IP address of the client when session was created"
    )
    
    user_agent = Column(
        Text,
        nullable=True,
        comment="User agent string of the client"
    )

    # Relationship to User model
    user = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"

    @property
    def is_expired(self) -> bool:
        """Check if this session is expired."""
        from datetime import datetime
        return self.expires_at < datetime.utcnow()

    @property
    def is_active(self) -> bool:
        """Check if this session is active (not expired)."""
        return not self.is_expired

    def to_dict(self) -> dict:
        """Convert session to dictionary for API responses."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_accessed_at": self.last_accessed_at.isoformat() if self.last_accessed_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "ip_address": str(self.ip_address) if self.ip_address else None,
            "user_agent": self.user_agent,
            "is_active": self.is_active
        }
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import timezone
import uuid

from app.models.base import Base


class UserSession(Base):
    """Simplified user session model."""
    __tablename__ = "user_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    refresh_token = Column(String(500), nullable=False, index=True, unique=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    # Optional metadata (can be null for MVP)
    ip_address = Column(INET, nullable=True)
    user_agent = Column(String(500), nullable=True)
    device_type = Column(String(50), nullable=True)  # 'web', 'mobile', 'api'

    # Relationship
    user = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, expires_at={self.expires_at})>"

    @property
    def is_expired(self) -> bool:
        """Check if session is expired."""
        from datetime import datetime
        return self.expires_at < datetime.now(timezone.utc)

    @property
    def is_active(self) -> bool:
        """Check if session is active."""
        return not self.is_expired
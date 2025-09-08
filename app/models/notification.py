from sqlalchemy import Column, DateTime, String, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class Notification(BaseModel):
    __tablename__ = "notifications"
    
    # Foreign Keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_id = Column(UUID(as_uuid=True), ForeignKey("alerts.id", ondelete="SET NULL"), nullable=True)
    
    # Notification Details
    category = Column(String(50), nullable=False)  # alert, system, import, error, welcome
    channel = Column(String(20), nullable=False)  # in_app, email, push
    
    # Content
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=False)
    action_url = Column(Text)
    
    # Status
    is_read = Column(Boolean, default=False, nullable=False)
    is_sent = Column(Boolean, default=False, nullable=False)
    read_at = Column(DateTime(timezone=True))
    sent_at = Column(DateTime(timezone=True))

    # Priority
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    
    # Relationships
    user = relationship("User", back_populates="notifications")
    alert = relationship("Alert", back_populates="notifications")

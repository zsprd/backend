from sqlalchemy import Column, DateTime, Integer, String, Boolean, DECIMAL, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

# Note: Need to add these enums to enums.py
class Alert(BaseModel):
    __tablename__ = "alerts"
    
    # Foreign Key
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Alert Configuration
    category = Column(String(50), nullable=False)  # price_change, portfolio_value, etc.
    name = Column(String(255), nullable=False)
    description = Column(Text)
    
    # Target and Conditions
    target_type = Column(String(50))  # portfolio, security, account
    target_id = Column(UUID(as_uuid=True))
    metric = Column(String(100))  # price, value, allocation_percent, etc.
    
    # Threshold Configuration
    threshold_operator = Column(String(10))  # gt, lt, gte, lte, eq, ne
    threshold_value = Column(DECIMAL(15, 4))
    threshold_percent = Column(DECIMAL(5, 2))
    
    # Frequency and Status
    frequency = Column(String(20), default="real_time")  # real_time, hourly, daily, weekly
    status = Column(String(20), default="active")  # active, paused, triggered, disabled
    
    # Configuration
    conditions = Column(JSONB)
    notification_config = Column(JSONB)
    
    # Status Tracking
    is_active = Column(Boolean, default=True, nullable=False)
    last_triggered_at = Column(DateTime(timezone=True))
    trigger_count = Column(Integer, default=0)
    
    # Relationships
    user = relationship("User", back_populates="alerts")
    notifications = relationship("Notification", back_populates="alert", cascade="all, delete-orphan")

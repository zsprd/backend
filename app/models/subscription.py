# app/models/subscription.py
from sqlalchemy import Column, String, ForeignKey, Date, DECIMAL, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.enums import subscription_status_category


class Subscription(BaseModel):
    __tablename__ = "subscriptions"
    
    # Foreign Key
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True  # One subscription per user
    )
    
    # Stripe Integration
    stripe_subscription_id = Column(String(255), unique=True)
    stripe_customer_id = Column(String(255))
    stripe_product_id = Column(String(255))
    stripe_price_id = Column(String(255))
    
    # Plan Details
    plan = Column(String(50), nullable=False)  # e.g., 'basic', 'premium'
    billing_cycle = Column(String(20))  # 'monthly', 'yearly'
    status = Column(subscription_status_category, default='active', nullable=False)
    
    # Billing Periods
    current_period_start = Column(Date, nullable=False)
    current_period_end = Column(Date, nullable=False)
    trial_start = Column(Date)
    trial_end = Column(Date)
    canceled_at = Column(Date)
    ended_at = Column(Date)
    
    # Pricing
    amount = Column(DECIMAL(10, 2))  # Amount in cents
    currency = Column(String(3), default='USD', nullable=False)
    tax_percent = Column(DECIMAL(5, 2))
    
    # Features
    feature_flags = Column(Text)  # JSON stored as text
    
    # Relationships
    user = relationship("User", back_populates="subscription")
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan={self.plan}, status={self.status})>"
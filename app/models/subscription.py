from typing import TYPE_CHECKING, Optional

from sqlalchemy import DECIMAL, Date, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User


class Subscription(BaseModel):
    __tablename__ = "subscriptions"

    # Foreign Key
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One subscription per user
    )

    # Stripe Integration
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True
    )
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255))
    stripe_product_id: Mapped[Optional[str]] = mapped_column(String(255))
    stripe_price_id: Mapped[Optional[str]] = mapped_column(String(255))

    # Plan Details
    plan_name: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # e.g., 'basic', 'premium'
    billing_cycle: Mapped[Optional[str]] = mapped_column(
        String(20)
    )  # 'monthly', 'yearly'
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)

    # Billing Periods
    current_period_start: Mapped[Date] = mapped_column(Date, nullable=False)
    current_period_end: Mapped[Date] = mapped_column(Date, nullable=False)
    trial_start: Mapped[Optional[Date]] = mapped_column(Date)
    trial_end: Mapped[Optional[Date]] = mapped_column(Date)
    canceled_at: Mapped[Optional[Date]] = mapped_column(Date)
    ended_at: Mapped[Optional[Date]] = mapped_column(Date)

    # Pricing
    amount: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2))  # Amount in cents
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Features
    feature_flags: Mapped[Optional[str]] = mapped_column(Text)  # JSON stored as text

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="subscription")

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan={self.plan_name}, status={self.status})>"

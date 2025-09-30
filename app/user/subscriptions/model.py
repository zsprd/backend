from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import DECIMAL, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.user.accounts.model import UserAccount


class UserSubscription(BaseModel):
    """
    User subscription and billing management.

    Tracks subscription plans, billing cycles, and payment processing
    through Stripe integration. Supports plan upgrades/downgrades
    and cancellation handling.
    """

    __tablename__ = "user_subscriptions"

    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("user_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the subscribing user",
    )

    plan_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Current subscription plan tier",
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="Subscription status: active, cancelled, past_due, etc."
    )

    # Billing period management
    current_period_start: Mapped[date] = mapped_column(
        Date, nullable=False, comment="Start date of the current billing period"
    )

    current_period_end: Mapped[date] = mapped_column(
        Date, nullable=False, comment="End date of the current billing period"
    )

    cancelled_at: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True, comment="Date when the subscription was cancelled"
    )

    # Stripe integration (payment processor IDs)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        unique=True,
        nullable=True,
        comment="Stripe subscription identifier for payment processing",
    )

    stripe_customer_id: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Stripe customer identifier"
    )

    # Pricing information
    amount: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(10, 2), nullable=True, comment="Subscription amount per billing period"
    )

    currency: Mapped[str] = mapped_column(
        String(3), default="USD", nullable=False, comment="Billing currency"
    )

    # Relationships
    user_accounts: Mapped["UserAccount"] = relationship(
        "UserAccount", back_populates="user_subscriptions"
    )

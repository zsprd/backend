from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserSubscriptionBase(BaseModel):
    """
    Shared fields for UserSubscription schemas.
    """

    user_id: UUID = Field(..., description="Reference to the subscribing user")
    plan_name: str = Field(..., description="Current subscription plan tier")
    status: str = Field(
        ..., max_length=20, description="Subscription status: active, cancelled, past_due, etc."
    )
    current_period_start: date = Field(..., description="Start date of the current billing period")
    current_period_end: date = Field(..., description="End date of the current billing period")
    cancelled_at: Optional[date] = Field(
        None, description="Date when the subscription was cancelled"
    )
    stripe_subscription_id: Optional[str] = Field(
        None, max_length=255, description="Stripe subscription identifier for payment processing"
    )
    stripe_customer_id: Optional[str] = Field(
        None, max_length=255, description="Stripe customer identifier"
    )
    amount: Optional[Decimal] = Field(None, description="Subscription amount per billing period")
    currency: str = Field("USD", max_length=3, description="Billing currency")


class UserSubscriptionCreate(UserSubscriptionBase):
    """
    Schema for creating a new user subscription.
    """

    pass


class UserSubscriptionRead(BaseModel):
    """
    Schema for reading user subscription data (API response).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Unique subscription ID")
    plan_name: str = Field(..., description="Current subscription plan tier")


class UserSubscriptionUpdate(BaseModel):
    """
    Schema for updating a user subscription (PATCH/PUT).
    All fields are optional to allow partial updates.
    """

    user_id: Optional[UUID] = Field(None, description="Reference to the subscribing user")
    plan_name: Optional[str] = Field(None, description="Current subscription plan tier")
    status: Optional[str] = Field(
        None, max_length=20, description="Subscription status: active, cancelled, past_due, etc."
    )
    current_period_start: Optional[date] = Field(
        None, description="Start date of the current billing period"
    )
    current_period_end: Optional[date] = Field(
        None, description="End date of the current billing period"
    )
    cancelled_at: Optional[date] = Field(
        None, description="Date when the subscription was cancelled"
    )
    stripe_subscription_id: Optional[str] = Field(
        None, max_length=255, description="Stripe subscription identifier for payment processing"
    )
    stripe_customer_id: Optional[str] = Field(
        None, max_length=255, description="Stripe customer identifier"
    )
    amount: Optional[Decimal] = Field(None, description="Subscription amount per billing period")
    currency: Optional[str] = Field(None, max_length=3, description="Billing currency")

import enum

from sqlalchemy import Enum


class PlanTypeEnum(enum.Enum):
    """
    Subscription plan types with escalating feature sets.

    Controls access to platform features and API limits.
    """

    FREE = "free"  # Basic portfolio tracking
    PREMIUM = "premium"  # Advanced analytics & reporting
    PROFESSIONAL = "professional"  # Institution-grade features
    ENTERPRISE = "enterprise"  # White-label & API access


# SQLAlchemy Enum type mappings for use in model definitions
PLAN_TYPE_ENUM = Enum(PlanTypeEnum, name="plan_type_enum")

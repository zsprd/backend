from enum import Enum


class PlanTypeEnum(str, Enum):
    """
    Subscription plan types with escalating feature sets.

    Controls access to platform features and API limits.
    """

    FREE = "free"  # Basic portfolio tracking
    PREMIUM = "premium"  # Advanced analytics & reporting
    PROFESSIONAL = "professional"  # Institution-grade features
    ENTERPRISE = "enterprise"  # White-label & API access

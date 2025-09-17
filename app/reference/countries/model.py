from typing import Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model import BaseModel


class ReferenceCountry(BaseModel):
    """
    Country reference data for geographic analysis and compliance.

    Country master data supporting geographic allocation analysis,
    tax reporting, and regulatory compliance requirements.
    Includes developed/emerging market classifications.
    """

    __tablename__ = "reference_countries"

    country_code: Mapped[str] = mapped_column(
        String(2),
        unique=True,
        nullable=False,
        comment="ISO 3166-1 alpha-2 country code (US, UK, CA, JP)",
    )

    country_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Full country name (United States, United Kingdom)"
    )

    region: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Geographic region (North America, Europe, Asia Pacific)"
    )

    currency_code: Mapped[Optional[str]] = mapped_column(
        String(3), nullable=True, comment="Primary currency for this country"
    )

    is_developed: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Developed market classification for analytics",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this country is active in the system",
    )

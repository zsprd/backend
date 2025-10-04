from typing import Optional

from sqlalchemy import Boolean, Numeric, String, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model import BaseModel


class ReferenceCountry(BaseModel):
    """
    Country reference data for geographic analysis and compliance.

    Comprehensive country master data supporting geographic allocation analysis,
    tax reporting, regulatory compliance, and UI display requirements.
    """

    __tablename__ = "reference_countries"

    # ISO Codes
    country_code: Mapped[str] = mapped_column(
        String(2),
        unique=True,
        nullable=False,
        index=True,
        comment="ISO 3166-1 alpha-2 country code (US, UK, CA, JP)",
    )

    country_code_alpha3: Mapped[Optional[str]] = mapped_column(
        String(3),
        nullable=True,
        index=True,
        comment="ISO 3166-1 alpha-3 country code (USA, GBR, CAN, JPN)",
    )

    # Names
    country_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Common country name (United States, United Kingdom)"
    )

    official_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Official country name (United States of America)"
    )

    # Geographic Information
    capital: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Capital city (Washington, D.C.)"
    )

    region: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Major region (Americas, Europe, Asia, Africa, Oceania)"
    )

    subregion: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Subregion (North America, Western Europe, Southeast Asia)",
    )

    continent: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Continent (North America, Europe, Asia)"
    )

    latitude: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 8), nullable=True, comment="Country center latitude"
    )

    longitude: Mapped[Optional[float]] = mapped_column(
        Numeric(11, 8), nullable=True, comment="Country center longitude"
    )

    # Financial & Economic
    currency_code: Mapped[Optional[str]] = mapped_column(
        String(3),
        nullable=True,
        index=True,
        comment="Primary currency for this country (USD, EUR, GBP)",
    )

    is_developed: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Developed market classification for account analytics",
    )

    # Demographics & Statistics
    population: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Country population (for analytics context)"
    )

    area: Mapped[Optional[float]] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Land area in square kilometers"
    )

    # Political Status
    independent: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, comment="Whether country is independent"
    )

    un_member: Mapped[Optional[bool]] = mapped_column(
        Boolean, nullable=True, comment="United Nations membership status"
    )

    # UI & Display
    flag_emoji: Mapped[Optional[str]] = mapped_column(
        String(10), nullable=True, comment="Flag emoji for UI display (🇺🇸)"
    )

    flag_svg_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="SVG flag image URL"
    )

    # System
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this country is active in the system",
    )

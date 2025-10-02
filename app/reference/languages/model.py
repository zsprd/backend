from typing import Optional

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model import BaseModel


class ReferenceLanguage(BaseModel):
    """
    Language reference data for internationalization.

    Master list of languages for UI localization and user preferences.
    Supports both ISO 639-1 (2-char) and ISO 639-2 (3-char) codes.
    """

    __tablename__ = "reference_languages"

    language_code: Mapped[str] = mapped_column(
        String(2),
        unique=True,
        nullable=False,
        index=True,
        comment="ISO 639-1 two-letter language code (en, es, fr, de)",
    )

    language_code_iso3: Mapped[Optional[str]] = mapped_column(
        String(3),
        nullable=True,
        comment="ISO 639-2 three-letter language code (eng, spa, fra, deu)",
    )

    language_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="English name of the language (English, Spanish)"
    )

    native_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Native name of the language (English, Español)"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this language is supported in the application",
    )

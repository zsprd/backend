from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model import BaseModel


class ReferenceTimezone(BaseModel):
    """
    Timezone reference data for scheduling and user preferences.

    IANA timezone database for accurate time handling across different
    regions. Used for user preferences, scheduling, and market hours.
    """

    __tablename__ = "reference_timezones"

    timezone_name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="IANA timezone name (America/New_York, Europe/London, Asia/Tokyo)",
    )

    utc_offset: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="UTC offset string (UTC-05:00, UTC+00:00, UTC+09:00)"
    )

    utc_offset_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="UTC offset in minutes for calculations (-300, 0, 540)"
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether this timezone is active in the system",
    )

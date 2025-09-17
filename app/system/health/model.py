from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DECIMAL, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model import BaseModel


class SystemHealth(BaseModel):
    """
    System health and performance metrics for monitoring.

    Stores key performance indicators and health metrics for
    system monitoring, alerting, and capacity planning.
    Supports both real-time and historical analysis.
    """

    __tablename__ = "system_health"

    metric_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        comment="Metric identifier: api_response_time, db_connections, memory_usage",
    )

    metric_value: Mapped[Decimal] = mapped_column(
        DECIMAL(15, 4), nullable=False, comment="Numerical value of the metric"
    )

    metric_unit: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="Unit of measurement: ms, count, percent, bytes"
    )

    component: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="System component: api, database, worker, cache"
    )

    environment: Mapped[str] = mapped_column(
        String(20),
        default="production",
        nullable=False,
        comment="Environment: production, staging, development",
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True, comment="When this metric was recorded"
    )

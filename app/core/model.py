from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import DateTime, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models.

    Provides common database schema patterns including UUID primary keys,
    automatic timestamp management, and soft delete support.
    """

    pass


class TimestampMixin:
    """
    Mixin for models that need created_at and updated_at timestamps.

    Automatically sets created_at on insert and updates updated_at on modification.
    Uses server-side defaults to ensure consistency across different application instances.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the record was created",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when the record was last updated",
    )


class SoftDeleteMixin:
    """
    Mixin for models that support soft delete functionality.

    Records are not physically deleted but marked as deleted with a timestamp.
    This preserves referential integrity and audit trails.
    """

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the record was soft deleted (NULL if active)",
    )

    @property
    def is_deleted(self) -> bool:
        """Check if this record has been soft deleted."""
        return self.deleted_at is not None

    def soft_delete(self) -> None:
        """Mark this record as deleted."""
        self.deleted_at = func.now()

    def restore(self) -> None:
        """Restore a soft deleted record."""
        self.deleted_at = None


class BaseModel(Base, TimestampMixin):
    """
    Abstract base model with UUID primary key and timestamps.

    This is the standard base class for most models in the system.
    Provides UUID primary keys for better security and scalability.
    """

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        comment="Unique identifier for the record",
    )


class BaseModelWithSoftDelete(BaseModel, SoftDeleteMixin):
    """
    Abstract base model with UUID primary key, timestamps, and soft delete.

    Used for models that need to preserve historical data and maintain
    referential integrity even after logical deletion.
    """

    __abstract__ = True

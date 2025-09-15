import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Declarative base for all models."""

    pass


class BaseModel(Base):
    """
    Abstract base model that provides common fields for all models.
    """

    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()"),
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id={self.id})>"

    def __str__(self) -> str:
        return self.__repr__()

    def to_dict(self) -> Dict[str, Any]:
        """Quick dict serialization for debugging (not for API output)."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

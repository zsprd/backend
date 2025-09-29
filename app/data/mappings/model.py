import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.data.connections.model import DataConnection


class DataMapping(BaseModel):
    __tablename__ = "data_mappings"

    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("data_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    internal_id: Mapped[str] = mapped_column(nullable=False, index=True)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)

    # Relationships
    data_connections: Mapped["DataConnection"] = relationship(
        "DataConnection", back_populates="data_mappings"
    )

    __table_args__ = (
        # Ensure unique mapping per connection, entity type, and internal ID
        # This prevents duplicate mappings for the same internal entity
        # within a single data connection.
        # Example: (connection_id, entity_type, internal_id) must be unique
        # to avoid conflicts.
        # Note: external_id can be non-unique as multiple internal entities
        # might map to the same external ID in some cases.
        # Adjust constraints as needed based on application requirements.
        # UniqueConstraint('connection_id', 'entity_type', 'internal_id', name='uq_data_mapping'),
    )

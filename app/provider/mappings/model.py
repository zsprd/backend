from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.provider.connections.model import ProviderConnection


class ProviderMapping(BaseModel):
    """
    External identifier mapping for provider-agnostic data integration.

    Maps external provider IDs to internal system IDs, enabling
    consistent data updates and preventing duplicate records.
    Critical for maintaining data integrity across provider changes.
    """

    __tablename__ = "provider_mappings"

    connection_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("provider_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the provider connection",
    )

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Type of entity being mapped: account, security, transaction",
    )

    internal_id: Mapped[UUID] = mapped_column(
        nullable=False, index=True, comment="Our internal UUID for this entity"
    )

    external_id: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Provider's unique identifier for this entity"
    )

    # Relationships
    provider_connections: Mapped["ProviderConnection"] = relationship(
        "ProviderConnection", back_populates="provider_mappings"
    )

    # Composite unique constraint on connection + entity_type + external_id
    __table_args__ = ({"comment": "Maps external provider IDs to internal system entities"},)

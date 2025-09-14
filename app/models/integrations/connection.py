import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

if TYPE_CHECKING:
    from app.models.users.user import User
    from app.models.integrations.institution import FinancialInstitution

from app.models.base import Base


class DataConnection(Base):
    __tablename__ = "data_connections"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    institution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("financial_institutions.id", ondelete="SET NULL"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    data_source: Mapped[str] = mapped_column(String(50), nullable=False)
    plaid_item_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    plaid_access_token: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    connection_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="data_connections")
    institution: Mapped[Optional["FinancialInstitution"]] = relationship(
        "FinancialInstitution", back_populates="data_connections"
    )
    job = relationship("ImportJob", back_populates="data_connection", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<DataConnection(id={self.id}, name={self.name}, data_source={self.data_source})>"

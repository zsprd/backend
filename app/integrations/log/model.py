import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

if TYPE_CHECKING:
    from app.users.profile.model import UserProfile
    from app.integrations.provider.model import DataConnection

from app.core.model import Base


class ImportJob(Base):
    __tablename__ = "import_jobs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    data_connection_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("data_connections.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    job_type: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="accounts, transactions, holdings"
    )
    status: Mapped[str] = mapped_column(
        String(20), default="pending", nullable=False, comment="pending, running, completed, failed"
    )
    filename: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    import_metadata: Mapped[Optional[dict]] = mapped_column("metadata", JSON, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=func.now(), nullable=False
    )
    user: Mapped["UserProfile"] = relationship("UserProfile", back_populates="import_jobs")
    data_connection: Mapped[Optional["DataConnection"]] = relationship(
        "DataConnection", back_populates="import_jobs"
    )

    def __repr__(self) -> str:
        return f"<ImportJob(id={self.id}, job_type={self.job_type}, status={self.status})>"

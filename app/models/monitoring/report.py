from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, BigInteger, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.core.user import User


class Report(BaseModel):
    __tablename__ = "reports"

    # Foreign Key
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Report Details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    report_category: Mapped[str] = mapped_column(String(50), nullable=False)
    file_format: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)

    # Configuration
    parameters: Mapped[Optional[dict]] = mapped_column(JSON)
    filters: Mapped[Optional[dict]] = mapped_column(JSON)

    # File Information
    file_url: Mapped[Optional[str]] = mapped_column(String(500))
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger)

    # Status Information
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    user: Mapped["User"] = relationship("User")

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, name={self.title}, category={self.report_category}, status={self.status})>"

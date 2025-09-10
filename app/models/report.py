from sqlalchemy import String, ForeignKey, BigInteger, Text, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import BaseModel
from app.models.enums import ReportCategory, ReportFormatCategory, ReportStatusCategory
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User


class Report(BaseModel):
    __tablename__ = "reports"

    # Foreign Key
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Report Details
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    report_category: Mapped[ReportCategory] = mapped_column(
        Enum(ReportCategory, native_enum=False, length=50),
        nullable=False
    )
    file_format: Mapped[ReportFormatCategory] = mapped_column(
        Enum(ReportFormatCategory, native_enum=False, length=20),
        nullable=False
    )
    status: Mapped[ReportStatusCategory] = mapped_column(
        Enum(ReportStatusCategory, native_enum=False, length=20),
        default=ReportStatusCategory.PENDING,
        nullable=False
    )

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
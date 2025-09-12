from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, ForeignKey, Integer, BigInteger, Text, JSON, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.account import Account


class ImportJob(BaseModel):
    __tablename__ = "import_jobs"

    # Foreign Keys
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    account_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True
    )

    # Job Details
    import_category: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default='pending', nullable=False)
    import_provider: Mapped[str] = mapped_column(String(50), nullable=False)

    # File Information
    filename: Mapped[Optional[str]] = mapped_column(String(255))
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger)
    file_url: Mapped[Optional[str]] = mapped_column(String(500))

    # Processing Information
    total_records: Mapped[Optional[int]] = mapped_column(Integer)
    processed_records: Mapped[Optional[int]] = mapped_column(Integer)
    failed_records: Mapped[Optional[int]] = mapped_column(Integer)

    # Results
    results: Mapped[Optional[dict]] = mapped_column(JSON)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    user: Mapped["User"] = relationship("User")
    account: Mapped[Optional["Account"]] = relationship("Account")

    def __repr__(self) -> str:
        return f"<ImportJob(id={self.id}, category={self.import_category}, status={self.status})>"
    
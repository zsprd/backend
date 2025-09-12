from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.account import Institution
    from app.models.user import User


class PlaidItem(BaseModel):
    __tablename__ = "plaid_items"

    # Foreign Keys
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    institution_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Plaid Details
    plaid_item_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    plaid_access_token: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="good", nullable=False)

    # Connection Information
    available_products: Mapped[Optional[str]] = mapped_column(
        Text
    )  # JSON array as text
    billed_products: Mapped[Optional[str]] = mapped_column(Text)  # JSON array as text
    consent_expiration_time: Mapped[Optional[str]] = mapped_column(String(50))

    # Error Information
    error_code: Mapped[Optional[str]] = mapped_column(String(50))
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    user: Mapped["User"] = relationship("User")
    institution: Mapped[Optional["Institution"]] = relationship("Institution")

    def __repr__(self) -> str:
        return f"<PlaidItem(id={self.id}, plaid_item_id={self.plaid_item_id}, status={self.status})>"

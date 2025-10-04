import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import Date, DECIMAL, ForeignKey, Index, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.security.master.model import Security


class CorporateAction(BaseModel):
    """
    Corporate actions and events affecting securities.

    Records all corporate actions including dividends, stock splits, mergers, spin-offs,
    and other events that impact security holdings. Essential for accurate position
    tracking and account analytics.

    Uses a flexible design with common fields for all action types and a JSON field
    for action-specific details. This keeps the model simple while supporting diverse
    corporate action types.
    """

    __tablename__ = "security_actions"

    security_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("security_master.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the affected security",
    )

    # Action classification
    action_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of corporate action: dividend, split, reverse_split, merger, spinoff, etc.",
    )

    action_subtype: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="Specific subtype: cash_dividend, stock_dividend, special_dividend, etc.",
    )

    # Key dates
    announcement_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date the action was announced",
    )

    ex_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
        comment="Ex-dividend/ex-date - date when security trades without the action benefit",
    )

    record_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date to be on record to receive the benefit",
    )

    payment_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
        comment="Date when payment/action is executed (for dividends, this is payment date)",
    )

    # Common financial fields (primarily for dividends)
    amount: Mapped[Optional[Decimal]] = mapped_column(
        DECIMAL(15, 4),
        nullable=True,
        comment="Cash amount per share (for dividends) or ratio (for splits)",
    )

    currency: Mapped[str] = mapped_column(
        String(3),
        default="USD",
        nullable=False,
        comment="Currency of the amount",
    )

    # Action-specific details stored as JSON
    action_details: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="Action-specific data: split_ratio, merger_terms, spinoff_details, etc.",
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Human-readable description of the corporate action",
    )

    # Data provenance
    data_provider: Mapped[str] = mapped_column(
        String(50),
        default="manual",
        nullable=False,
        comment="Source of this corporate action data",
    )

    # Relationships
    security_master: Mapped["Security"] = relationship(
        "Security",
        back_populates="security_actions",
    )

    __table_args__ = (
        Index("idx_security_action_ex_date", "security_id", "ex_date"),
        Index("idx_security_action_type", "action_type", "ex_date"),
        {"comment": "Corporate actions and events affecting securities"},
    )

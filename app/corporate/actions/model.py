from datetime import date
from typing import TYPE_CHECKING, Any, Dict
from uuid import UUID

from sqlalchemy import JSON, Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.security.master.model import SecurityMaster


class CorporateAction(BaseModel):
    """
    Corporate actions affecting securities and portfolio holdings.

    Tracks stock splits, mergers, spinoffs, and other corporate events
    that impact portfolio holdings and require position adjustments.
    Stores action-specific details in JSON for flexibility.
    """

    __tablename__ = "corporate_actions"

    security_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("security_master.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the affected security",
    )

    action_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="Type of action: split, dividend, merger, spinoff, delisting",
    )

    ex_date: Mapped[date] = mapped_column(
        Date, nullable=False, comment="Ex-dividend/action date when holders are determined"
    )

    effective_date: Mapped[date] = mapped_column(
        Date, nullable=False, comment="Date when the corporate action takes effect"
    )

    details: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="Action-specific details: ratio, new_symbol, cash_amount, etc.",
    )

    # Relationships
    security_master: Mapped["SecurityMaster"] = relationship(
        "SecurityMaster", back_populates="corporate_actions"
    )

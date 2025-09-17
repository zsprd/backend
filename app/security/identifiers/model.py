from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.security.master.model import SecurityMaster


class SecurityIdentifier(BaseModel):
    """
    Multiple identifier mappings for securities across different systems.

    Maps various security identification systems (CUSIP, ISIN, provider IDs)
    to enable cross-system data integration and prevent duplicate securities
    in the master database.
    """

    __tablename__ = "security_identifiers"

    security_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("security_master.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Reference to the security in our master database",
    )

    identifier_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Type of identifier: cusip, isin, plaid_id, bloomberg_id",
    )

    identifier_value: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="The actual identifier value"
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether this is the primary identifier of this type",
    )

    # Relationships
    security_master: Mapped["SecurityMaster"] = relationship(
        "SecurityMaster", back_populates="security_identifiers"
    )

    # Composite unique constraint on identifier_type + identifier_value
    __table_args__ = ({"comment": "Alternative identifiers for securities across systems"},)

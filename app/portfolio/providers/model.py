import uuid
from typing import TYPE_CHECKING

from sqlalchemy import String, UUID, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel

if TYPE_CHECKING:
    from app.portfolio.accounts.model import PortfolioAccount


class PortfolioProvider(BaseModel):
    __tablename__ = "portfolio_providers"

    account_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("portfolio_accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_role: Mapped[str] = mapped_column(String(50), nullable=False)

    external_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    connection_status: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    portfolio_accounts: Mapped["PortfolioAccount"] = relationship(
        "PortfolioAccount", back_populates="portfolio_providers"
    )

from typing import Optional

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.model import BaseModel


class CounterpartyMaster(BaseModel):
    __tablename__ = "counterparty_master"

    counterparty_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    counterparty_name: Mapped[str] = mapped_column(String(255), nullable=False)
    counterparty_type: Mapped[str] = mapped_column(String(50), nullable=False)
    country: Mapped[str] = mapped_column(String(2), default="US", nullable=False)
    legal_entity_identifier: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    web_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    logo_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

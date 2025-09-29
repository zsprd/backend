from typing import List

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.model import BaseModel
from app.data.connections.model import DataConnection


class DataProvider(BaseModel):
    __tablename__ = "data_providers"

    provider_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    provider_name: Mapped[str] = mapped_column(String(255), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    data_connections: Mapped[List["DataConnection"]] = relationship(
        "DataConnection", back_populates="data_providers", passive_deletes=True
    )

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ProviderConnectionRead(BaseModel):
    """
    Schema for reading provider connection data (API response).
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Unique provider connection ID")

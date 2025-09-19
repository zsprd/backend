from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PortfolioAccountBase(BaseModel):
    """Base schema for PortfolioAccount (shared fields)."""

    name: str = Field(..., description="Account name", max_length=255)
    account_type: str = Field(
        ..., description="Primary account category", examples=["investment", "depository"]
    )
    account_subtype: Optional[str] = Field(None, description="Specific account subtype")
    currency: str = Field("USD", description="ISO currency code", min_length=3, max_length=3)
    is_active: bool = True
    data_source: str = Field("manual", description="Source of account data", max_length=50)
    institution_id: Optional[UUID] = None
    connection_id: Optional[UUID] = None


class PortfolioAccountCreate(PortfolioAccountBase):
    """Schema for creating a PortfolioAccount."""

    user_id: UUID


class PortfolioAccountUpdate(BaseModel):
    """Schema for updating a PortfolioAccount."""

    name: Optional[str] = Field(None, description="Account name", max_length=255)
    account_type: Optional[str] = None
    account_subtype: Optional[str] = None
    currency: Optional[str] = Field(
        None, description="ISO currency code", min_length=3, max_length=3
    )
    data_source: Optional[str] = Field(None, description="Source of account data", max_length=50)
    institution_id: Optional[UUID] = Field(None, description="Institution reference")
    connection_id: Optional[UUID] = Field(None, description="Connection reference")


class PortfolioAccountResponse(PortfolioAccountBase):
    model_config = ConfigDict(from_attributes=True)

    user_id: UUID
    id: UUID = Field(..., description="Account ID")

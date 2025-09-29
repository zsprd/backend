from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .enums import AccountSubtypeEnum, AccountTypeEnum


class PortfolioAccountBase(BaseModel):
    """Base schema for PortfolioAccount (shared fields)."""

    name: str = Field(..., description="Account name", max_length=255)
    account_type: AccountTypeEnum = Field(
        ..., description="Primary account category", examples=["investment", "depository"]
    )
    account_subtype: Optional[AccountSubtypeEnum] = Field(
        None, description="Specific account subtype"
    )
    currency: str = Field("USD", description="ISO currency code", min_length=3, max_length=3)
    is_active: bool = True
    data_source: str = Field("manual", description="Source of account data", max_length=50)
    connection_id: Optional[UUID] = None


class PortfolioAccountRead(PortfolioAccountBase):

    user_id: UUID
    id: UUID = Field(..., description="Account ID")


class PortfolioAccountCreate(PortfolioAccountBase):

    user_id: UUID


class PortfolioAccountUpdate(PortfolioAccountBase):

    pass

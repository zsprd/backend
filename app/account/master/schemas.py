from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .enums import AccountSubType, AccountType


class AccountBase(BaseModel):
    """Base schema for PortfolioAccount (shared fields)."""

    name: str = Field(..., description="Account name", max_length=255)
    account_type: AccountType = Field(
        ..., description="Primary account category", examples=["investment", "depository"]
    )
    account_subtype: Optional[AccountSubType] = Field(None, description="Specific account subtype")
    currency: str = Field("USD", description="ISO currency code", min_length=3, max_length=3)
    is_active: bool = True
    data_source: str = Field("manual", description="Source of account data", max_length=50)


class AccountRead(AccountBase):

    user_id: UUID
    id: UUID = Field(..., description="Account ID")


class AccountCreate(AccountBase):

    user_id: UUID


class AccountUpdate(AccountBase):

    pass

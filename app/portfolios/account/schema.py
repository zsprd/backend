from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class AccountBase(BaseModel):
    user_id: UUID
    institution_id: Optional[UUID] = None
    data_connection_id: Optional[UUID] = None
    plaid_account_id: Optional[str] = None
    name: str = Field(..., max_length=255)
    official_name: Optional[str] = None
    mask: Optional[str] = None
    account_type: str
    account_subtype: Optional[str] = None
    currency: str = Field("USD", max_length=3)
    is_active: bool = True
    data_source: str = Field("manual")


class AccountCreate(AccountBase):
    pass


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    official_name: Optional[str] = None
    mask: Optional[str] = None
    account_type: Optional[str] = None
    account_subtype: Optional[str] = None
    currency: Optional[str] = None
    is_active: Optional[bool] = None
    data_source: Optional[str] = None
    institution_id: Optional[UUID] = None
    data_connection_id: Optional[UUID] = None
    plaid_account_id: Optional[str] = None


class AccountResponse(AccountBase):
    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class FinancialInstitutionBase(BaseModel):
    name: str = Field(..., max_length=255, description="Institution name")
    country: str = Field("US", max_length=2, description="ISO country code")
    website_url: Optional[str] = Field(None, description="Institution website")
    logo_url: Optional[str] = Field(None, description="Logo URL")
    primary_color: Optional[str] = Field(None, max_length=7, description="Hex color code")


class FinancialInstitutionCreate(FinancialInstitutionBase):
    plaid_institution_id: Optional[str] = Field(None, max_length=255)


class FinancialInstitutionResponse(FinancialInstitutionBase):
    id: UUID
    plaid_institution_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

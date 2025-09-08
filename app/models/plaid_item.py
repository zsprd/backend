from sqlalchemy import Column, String, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.enums import plaid_item_status_category


class PlaidItem(BaseModel):
    __tablename__ = "plaid_items"
    
    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    institution_id = Column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Plaid Details
    plaid_item_id = Column(String(255), unique=True, nullable=False)
    plaid_access_token = Column(String(255), nullable=False)
    status = Column(plaid_item_status_category, default='good', nullable=False)
    
    # Connection Information
    available_products = Column(Text)  # JSON array as text
    billed_products = Column(Text)     # JSON array as text
    consent_expiration_time = Column(String(50))
    
    # Error Information
    error_code = Column(String(50))
    error_message = Column(Text)
    
    # Relationships
    user = relationship("User")
    institution = relationship("Institution")
    
    def __repr__(self):
        return f"<PlaidItem(id={self.id}, plaid_item_id={self.plaid_item_id}, status={self.status})>"
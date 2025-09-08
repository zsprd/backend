# app/models/audit_log.py
from sqlalchemy import Column, String, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.enums import audit_action_category


class AuditLog(BaseModel):
    __tablename__ = "audit_logs"
    
    # Foreign Key
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    
    # Action Details
    action = Column(audit_action_category, nullable=False)
    description = Column(Text)
    
    # Target Information
    target_category = Column(String(50), nullable=False)  # 'account', 'transaction', 'user'
    target_id = Column(String(255))
    
    # Request Information
    request_path = Column(String(500))
    request_method = Column(String(10))  # GET, POST, PUT, DELETE
    
    # Changed: metadata -> request_metadata (metadata is reserved in SQLAlchemy)
    request_metadata = Column(JSON)
    ip_address = Column(String(45))  # IPv6 support
    user_agent = Column(Text)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, target_category={self.target_category})>"
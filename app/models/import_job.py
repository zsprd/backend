from sqlalchemy import Column, String, ForeignKey, Integer, BigInteger, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.enums import import_category, import_status_category, import_provider_category


class ImportJob(BaseModel):
    __tablename__ = "import_jobs"
    
    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Job Details
    category = Column(import_category, nullable=False)
    status = Column(import_status_category, default='pending', nullable=False)
    provider = Column(import_provider_category, nullable=False)
    
    # File Information
    filename = Column(String(255))
    file_size = Column(BigInteger)
    file_url = Column(String(500))
    
    # Processing Information
    total_records = Column(Integer)
    processed_records = Column(Integer)
    failed_records = Column(Integer)
    
    # Results
    results = Column(JSON)
    error_message = Column(Text)
    
    # Relationships
    user = relationship("User")
    account = relationship("Account")
    
    def __repr__(self):
        return f"<ImportJob(id={self.id}, category={self.category}, status={self.status})>"
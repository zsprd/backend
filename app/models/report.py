from sqlalchemy import Column, String, ForeignKey, BigInteger, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Report(BaseModel):
    __tablename__ = "reports"
    
    # Foreign Key
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Report Details
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False)  # 'portfolio_summary', 'performance', 'tax'
    format = Column(String(20), nullable=False)    # 'pdf', 'csv', 'xlsx'
    status = Column(String(20), default='pending', nullable=False)
    
    # Configuration
    parameters = Column(JSON)
    filters = Column(JSON)
    
    # File Information
    file_url = Column(String(500))
    file_size = Column(BigInteger)
    
    # Status Information
    error_message = Column(Text)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f"<Report(id={self.id}, name={self.name}, category={self.category}, status={self.status})>"
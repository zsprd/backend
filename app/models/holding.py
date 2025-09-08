# app/models/holding.py
from sqlalchemy import Column, String, ForeignKey, DECIMAL, Date, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.enums import lot_method_category


class Holding(BaseModel):
    __tablename__ = "holdings"
    
    # Foreign Keys
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    security_id = Column(
        UUID(as_uuid=True),
        ForeignKey("securities.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Holding Details
    quantity = Column(DECIMAL(15, 6), nullable=False)
    cost_basis_per_share = Column(DECIMAL(15, 4))
    cost_basis_total = Column(DECIMAL(15, 2))
    market_value = Column(DECIMAL(15, 2))
    currency = Column(String(3), nullable=False)
    as_of_date = Column(Date, nullable=False)
    
    # External Integration
    plaid_account_id = Column(String(255))
    plaid_security_id = Column(String(255))
    institution_price = Column(DECIMAL(15, 4))
    institution_value = Column(DECIMAL(15, 2))
    
    # Relationships
    account = relationship("Account", back_populates="holdings")
    security = relationship("Security", back_populates="holdings")
    
    # Unique constraint to prevent duplicate holdings for same account/security/date
    __table_args__ = (
        UniqueConstraint('account_id', 'security_id', 'as_of_date', name='_account_security_date_uc'),
    )
    
    def __repr__(self):
        return f"<Holding(id={self.id}, account_id={self.account_id}, security_id={self.security_id})>"


class Position(BaseModel):
    __tablename__ = "positions"
    
    # Foreign Keys
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    security_id = Column(
        UUID(as_uuid=True),
        ForeignKey("securities.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Position Details
    quantity = Column(DECIMAL(15, 6), nullable=False)
    average_cost = Column(DECIMAL(15, 4))
    unrealized_gain_loss = Column(DECIMAL(15, 2))
    lot_method = Column(lot_method_category, default="fifo", nullable=False)  # Fixed: use lot_method_category
    
    # Relationships
    account = relationship("Account", back_populates="positions")
    security = relationship("Security", back_populates="positions")
    
    # Unique constraint - one position per account/security
    __table_args__ = (
        UniqueConstraint('account_id', 'security_id', name='_account_security_position_uc'),
    )
    
    def __repr__(self):
        return f"<Position(id={self.id}, account_id={self.account_id}, security_id={self.security_id})>"
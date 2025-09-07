from sqlalchemy import Column, String, ForeignKey, DECIMAL, Date, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.enums import (
    transaction_type_enum, 
    transaction_side_enum, 
    cash_transaction_type_enum,
    data_source_enum
)


class Transaction(BaseModel):
    __tablename__ = "transactions"
    
    # Foreign Keys
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    security_id = Column(
        UUID(as_uuid=True),
        ForeignKey("securities.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Transaction Details
    type = Column(transaction_type_enum, nullable=False)
    side = Column(transaction_side_enum)  # buy/sell - only for equity transactions
    quantity = Column(DECIMAL(15, 6))
    price = Column(DECIMAL(15, 4))
    amount = Column(DECIMAL(15, 2), nullable=False)  # Total transaction amount
    fees = Column(DECIMAL(15, 2))
    tax = Column(DECIMAL(15, 2))
    
    # Dates
    trade_date = Column(Date, nullable=False, index=True)
    settlement_date = Column(Date)
    
    # Currency and FX
    transaction_currency = Column(String(3), nullable=False)
    fx_rate = Column(DECIMAL(15, 6))  # FX rate if different from account currency
    
    # Description and Categorization
    description = Column(Text)
    memo = Column(Text)
    category = Column(String(100))
    subcategory = Column(String(100))
    
    # External Integration
    plaid_transaction_id = Column(String(255))
    source = Column(data_source_enum, nullable=False)
    
    # Relationships
    account = relationship("Account", back_populates="transactions")
    security = relationship("Security", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, type={self.type}, amount={self.amount})>"


class CashTransaction(BaseModel):
    __tablename__ = "cash_transactions"
    
    # Foreign Key
    account_id = Column(
        UUID(as_uuid=True),
        ForeignKey("accounts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Transaction Details
    type = Column(cash_transaction_type_enum, nullable=False)
    amount = Column(DECIMAL(15, 2), nullable=False)
    description = Column(Text)
    category = Column(String(100))
    merchant_name = Column(String(255))
    
    # Date and Status
    date = Column(Date, nullable=False, index=True)
    pending = Column(Boolean, default=False, nullable=False)
    
    # External Integration
    plaid_transaction_id = Column(String(255))
    plaid_category = Column(Text)  # Array stored as JSON text
    
    # Relationships
    account = relationship("Account", back_populates="cash_transactions")
    
    def __repr__(self):
        return f"<CashTransaction(id={self.id}, type={self.type}, amount={self.amount})>"
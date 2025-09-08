# app/models/security.py
from sqlalchemy import Column, String, Boolean, UniqueConstraint
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.enums import security_category, data_provider_category


class Security(BaseModel):
    __tablename__ = "securities"
    
    # Basic Information
    symbol = Column(String(20), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(security_category, nullable=False)  # Fixed: use security_category
    currency = Column(String(3), default="USD", nullable=False)
    
    # Market Information
    exchange = Column(String(10))  # e.g., NASDAQ, NYSE, LSE
    country = Column(String(2))    # ISO country code
    
    # Classification
    sector = Column(String(100))
    industry = Column(String(100))
    
    # Identifiers
    cusip = Column(String(9))      # US securities identifier
    isin = Column(String(12))      # International securities identifier
    sedol = Column(String(7))      # Stock Exchange Daily Official List
    
    # External Integration
    plaid_security_id = Column(String(255))
    alphavantage_symbol = Column(String(20))
    data_provider_category = Column(data_provider_category)  # Added: matches database schema
    is_delisted = Column(Boolean, default=False, nullable=False)  # Added: matches database schema
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    holdings = relationship("Holding", back_populates="security")
    transactions = relationship("Transaction", back_populates="security")
    positions = relationship("Position", back_populates="security")
    market_data = relationship("MarketData", back_populates="security", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Security(id={self.id}, symbol={self.symbol}, name={self.name})>"
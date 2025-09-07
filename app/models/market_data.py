from sqlalchemy import Column, String, ForeignKey, DECIMAL, Date, BigInteger, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.enums import data_source_enum


class MarketData(BaseModel):
    __tablename__ = "market_data"
    
    # Foreign Key
    security_id = Column(
        UUID(as_uuid=True),
        ForeignKey("securities.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Date
    date = Column(Date, nullable=False, index=True)
    
    # OHLCV Data
    open = Column(DECIMAL(15, 4))
    high = Column(DECIMAL(15, 4))
    low = Column(DECIMAL(15, 4))
    close = Column(DECIMAL(15, 4), nullable=False)
    volume = Column(BigInteger)
    adjusted_close = Column(DECIMAL(15, 4))
    
    # Metadata
    currency = Column(String(3), nullable=False)
    source = Column(data_source_enum, nullable=False)
    
    # Relationships
    security = relationship("Security", back_populates="market_data")
    
    # Unique constraint - one price per security per date
    __table_args__ = (
        UniqueConstraint('security_id', 'date', name='_security_date_uc'),
    )
    
    def __repr__(self):
        return f"<MarketData(security_id={self.security_id}, date={self.date}, close={self.close})>"


class ExchangeRate(BaseModel):
    __tablename__ = "exchange_rates"
    
    # Currency Pair
    base_currency = Column(String(3), nullable=False, index=True)
    quote_currency = Column(String(3), nullable=False, index=True)
    
    # Date and Rate
    date = Column(Date, nullable=False, index=True)
    rate = Column(DECIMAL(15, 6), nullable=False)
    
    # Source
    source = Column(data_source_enum, nullable=False)
    
    # Unique constraint - one rate per currency pair per date
    __table_args__ = (
        UniqueConstraint('base_currency', 'quote_currency', 'date', name='_currency_pair_date_uc'),
    )
    
    def __repr__(self):
        return f"<ExchangeRate({self.base_currency}/{self.quote_currency} = {self.rate} on {self.date})>"
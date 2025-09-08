# app/models/market_data.py
from sqlalchemy import Column, String, ForeignKey, DECIMAL, Date, BigInteger, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.base import BaseModel
from app.models.enums import data_provider_category


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
    price_date = Column(Date, nullable=False, index=True)  # Fixed: match database column name
    
    # OHLCV Data
    open_price = Column(DECIMAL(15, 4))  # Fixed: avoid using 'open' as column name
    high_price = Column(DECIMAL(15, 4))
    low_price = Column(DECIMAL(15, 4))
    close_price = Column(DECIMAL(15, 4), nullable=False)
    volume = Column(BigInteger)
    adjusted_close = Column(DECIMAL(15, 4))
    
    # Metadata
    currency = Column(String(3), nullable=False)
    data_provider = Column(data_provider_category, nullable=False)  # Fixed: use data_provider_category
    
    # Relationships
    security = relationship("Security", back_populates="market_data")
    
    # Unique constraint - one price per security per date
    __table_args__ = (
        UniqueConstraint('security_id', 'price_date', name='_security_price_date_uc'),
    )
    
    def __repr__(self):
        return f"<MarketData(security_id={self.security_id}, price_date={self.price_date}, close_price={self.close_price})>"


class ExchangeRate(BaseModel):
    __tablename__ = "exchange_rates"
    
    # Currency Pair
    base_currency = Column(String(3), nullable=False, index=True)
    quote_currency = Column(String(3), nullable=False, index=True)
    
    # Date and Rate
    rate_date = Column(Date, nullable=False, index=True)  # Fixed: match database column name
    rate = Column(DECIMAL(15, 6), nullable=False)
    
    # Source
    data_provider = Column(data_provider_category, nullable=False)  # Fixed: use data_provider_category
    
    # Unique constraint - one rate per currency pair per date
    __table_args__ = (
        UniqueConstraint('base_currency', 'quote_currency', 'rate_date', name='_currency_pair_rate_date_uc'),
    )
    
    def __repr__(self):
        return f"<ExchangeRate({self.base_currency}/{self.quote_currency} = {self.rate} on {self.rate_date})>"
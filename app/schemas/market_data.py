from typing import Optional, List
from pydantic import BaseModel, Field, UUID4
from datetime import datetime, date
from decimal import Decimal
from app.models.enums import DataSource


class MarketDataBase(BaseModel):
    date: date = Field(..., description="Market data date")
    open: Optional[Decimal] = Field(None, description="Opening price")
    high: Optional[Decimal] = Field(None, description="High price")
    low: Optional[Decimal] = Field(None, description="Low price")
    close: Decimal = Field(..., description="Closing price")
    volume: Optional[int] = Field(None, description="Trading volume")
    adjusted_close: Optional[Decimal] = Field(None, description="Adjusted closing price")
    currency: str = Field(..., max_length=3, description="Price currency")
    source: DataSource = Field(..., description="Data source")


class MarketDataCreate(MarketDataBase):
    security_id: UUID4 = Field(..., description="Security ID")


class MarketDataUpdate(BaseModel):
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Optional[Decimal] = None
    volume: Optional[int] = None
    adjusted_close: Optional[Decimal] = None
    currency: Optional[str] = None


class MarketData(MarketDataBase):
    id: UUID4
    security_id: UUID4
    created_at: datetime
    
    class Config:
        from_attributes = True


class PricePoint(BaseModel):
    """Single price point for charting"""
    date: date
    price: float
    volume: Optional[int] = None


class PriceHistory(BaseModel):
    """Historical price data for a security"""
    security_id: UUID4
    symbol: str
    name: str
    currency: str
    data_points: int
    start_date: date
    end_date: date
    prices: List[PricePoint]


class OHLCV(BaseModel):
    """OHLCV data point"""
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: Optional[int] = None


class CandlestickData(BaseModel):
    """Candlestick chart data"""
    security_id: UUID4
    symbol: str
    timeframe: str  # daily, weekly, monthly
    data: List[OHLCV]


class ExchangeRateBase(BaseModel):
    base_currency: str = Field(..., max_length=3, description="Base currency")
    quote_currency: str = Field(..., max_length=3, description="Quote currency")
    date: date = Field(..., description="Exchange rate date")
    rate: Decimal = Field(..., description="Exchange rate")
    source: DataSource = Field(..., description="Data source")


class ExchangeRateCreate(ExchangeRateBase):
    pass


class ExchangeRate(ExchangeRateBase):
    id: UUID4
    created_at: datetime
    
    class Config:
        from_attributes = True


class QuoteData(BaseModel):
    """Real-time quote data"""
    security_id: UUID4
    symbol: str
    price: float
    change: float
    change_percent: float
    volume: Optional[int] = None
    bid: Optional[float] = None
    ask: Optional[float] = None
    bid_size: Optional[int] = None
    ask_size: Optional[int] = None
    last_trade_time: Optional[datetime] = None
    market_status: str = "closed"  # open, closed, pre_market, after_hours


class MarketDataRefreshStatus(BaseModel):
    """Status of market data refresh operation"""
    security_id: UUID4
    symbol: str
    status: str  # pending, in_progress, completed, failed
    last_updated: Optional[datetime] = None
    error_message: Optional[str] = None
    data_points_added: Optional[int] = None


class BulkRefreshResult(BaseModel):
    """Result of bulk market data refresh"""
    total_securities: int
    successful_refreshes: int
    failed_refreshes: int
    errors: List[str] = []
    refresh_statuses: List[MarketDataRefreshStatus] = []


class MarketSummary(BaseModel):
    """Market summary statistics"""
    date: date
    total_securities: int
    securities_updated: int
    price_changes: dict = Field(default_factory=dict, description="Price change distribution")
    volume_stats: dict = Field(default_factory=dict, description="Volume statistics")
    top_gainers: List[dict] = Field(default_factory=list)
    top_losers: List[dict] = Field(default_factory=list)
    most_active: List[dict] = Field(default_factory=list)


class TechnicalIndicators(BaseModel):
    """Technical analysis indicators"""
    security_id: UUID4
    symbol: str
    date: date
    
    # Moving averages
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    sma_200: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    
    # Momentum indicators
    rsi_14: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_histogram: Optional[float] = None
    
    # Volatility indicators
    bollinger_upper: Optional[float] = None
    bollinger_middle: Optional[float] = None
    bollinger_lower: Optional[float] = None
    atr_14: Optional[float] = None


class MarketDataStats(BaseModel):
    """Market data coverage statistics"""
    total_securities: int
    securities_with_data: int
    coverage_percentage: float
    latest_update: Optional[datetime] = None
    data_points_total: int
    date_range: dict = Field(default_factory=dict)
    by_source: dict = Field(default_factory=dict)
    by_security_type: dict = Field(default_factory=dict)
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class PerformanceMetrics(BaseModel):
    """Portfolio performance metrics"""
    total_return: float = Field(..., description="Total return percentage")
    annualized_return: float = Field(..., description="Annualized return percentage")
    volatility: float = Field(..., description="Volatility (standard deviation) percentage")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown percentage")
    value_at_risk_95: float = Field(..., description="95% Value at Risk percentage")
    current_value: float = Field(..., description="Current portfolio value")
    start_value: float = Field(..., description="Starting portfolio value")
    data_points: int = Field(..., description="Number of data points used")
    start_date: Optional[str] = Field(None, description="Analysis start date")
    end_date: Optional[str] = Field(None, description="Analysis end date")


class ValueAtRisk(BaseModel):
    """Value at Risk at different confidence levels"""
    var_90: float = Field(..., description="90% Value at Risk percentage")
    var_95: float = Field(..., description="95% Value at Risk percentage")
    var_99: float = Field(..., description="99% Value at Risk percentage")


class RiskMetrics(BaseModel):
    """Portfolio risk analysis metrics"""
    beta: float = Field(..., description="Beta coefficient vs benchmark")
    correlation_with_benchmark: float = Field(..., description="Correlation with benchmark")
    downside_deviation: float = Field(..., description="Downside deviation percentage")
    sortino_ratio: float = Field(..., description="Sortino ratio")
    value_at_risk: ValueAtRisk = Field(..., description="Value at Risk metrics")
    benchmark_symbol: str = Field(..., description="Benchmark ticker symbol")


class TopHolding(BaseModel):
    """Top holding information"""
    symbol: str = Field(..., description="Security symbol")
    name: str = Field(..., description="Security name")
    market_value: float = Field(..., description="Market value")
    weight: float = Field(..., description="Portfolio weight percentage")


class ConcentrationMetrics(BaseModel):
    """Portfolio concentration metrics"""
    top_5_weight: float = Field(..., description="Weight of top 5 holdings percentage")
    top_10_weight: float = Field(..., description="Weight of top 10 holdings percentage")
    number_of_positions: int = Field(..., description="Total number of positions")


class AllocationBreakdown(BaseModel):
    """Portfolio allocation breakdown"""
    total_portfolio_value: float = Field(..., description="Total portfolio value")
    by_asset_type: Dict[str, float] = Field(..., description="Allocation by asset type")
    by_sector: Dict[str, float] = Field(..., description="Allocation by sector")
    by_geography: Dict[str, float] = Field(..., description="Allocation by geography")
    by_currency: Dict[str, float] = Field(..., description="Allocation by currency")
    by_account: Dict[str, float] = Field(..., description="Allocation by account")
    top_holdings: List[TopHolding] = Field(..., description="Top 10 holdings")
    concentration: ConcentrationMetrics = Field(..., description="Concentration metrics")


class AnalyticsRequest(BaseModel):
    """Request parameters for analytics calculations"""
    account_ids: Optional[List[str]] = Field(None, description="Specific account IDs to analyze")
    start_date: Optional[datetime] = Field(None, description="Analysis start date")
    end_date: Optional[datetime] = Field(None, description="Analysis end date")
    benchmark_symbol: str = Field("SPY", description="Benchmark ticker for comparisons")
    base_currency: str = Field("USD", description="Base currency for calculations")


class TimeSeriesPoint(BaseModel):
    """Single point in time series data"""
    date: datetime = Field(..., description="Date")
    value: float = Field(..., description="Value")


class PortfolioTimeSeries(BaseModel):
    """Portfolio value time series"""
    data: List[TimeSeriesPoint] = Field(..., description="Time series data points")
    start_date: datetime = Field(..., description="Series start date")
    end_date: datetime = Field(..., description="Series end date")
    total_points: int = Field(..., description="Total number of data points")


class BenchmarkComparison(BaseModel):
    """Portfolio vs benchmark comparison"""
    portfolio_return: float = Field(..., description="Portfolio return percentage")
    benchmark_return: float = Field(..., description="Benchmark return percentage")
    alpha: float = Field(..., description="Alpha vs benchmark")
    beta: float = Field(..., description="Beta vs benchmark")
    correlation: float = Field(..., description="Correlation with benchmark")
    tracking_error: float = Field(..., description="Tracking error percentage")
    information_ratio: float = Field(..., description="Information ratio")
    benchmark_symbol: str = Field(..., description="Benchmark symbol")


class ComprehensiveAnalytics(BaseModel):
    """Complete analytics response"""
    performance: PerformanceMetrics = Field(..., description="Performance metrics")
    risk: RiskMetrics = Field(..., description="Risk metrics")
    allocation: AllocationBreakdown = Field(..., description="Allocation analysis")
    benchmark_comparison: Optional[BenchmarkComparison] = Field(None, description="Benchmark comparison")
    generated_at: datetime = Field(..., description="Analysis generation timestamp")
    base_currency: str = Field(..., description="Base currency used")


class AnalyticsError(BaseModel):
    """Analytics calculation error response"""
    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    details: Optional[Dict] = Field(None, description="Additional error details")
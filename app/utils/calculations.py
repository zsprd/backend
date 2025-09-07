import pandas as pd
import numpy as np
from typing import Union, Optional
from scipy import stats


def calculate_returns(prices: Union[pd.Series, np.ndarray]) -> pd.Series:
    """
    Calculate daily returns from price series.
    
    Args:
        prices: Series of prices
        
    Returns:
        Series of daily returns
    """
    if isinstance(prices, np.ndarray):
        prices = pd.Series(prices)
    
    return prices.pct_change().dropna()


def calculate_volatility(returns: pd.Series, annualize: bool = True) -> float:
    """
    Calculate volatility (standard deviation of returns).
    
    Args:
        returns: Series of returns
        annualize: Whether to annualize the volatility (multiply by sqrt(252))
        
    Returns:
        Volatility as a decimal
    """
    vol = returns.std()
    if annualize:
        vol *= np.sqrt(252)  # Assuming 252 trading days per year
    return vol


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """
    Calculate Sharpe ratio.
    
    Args:
        returns: Series of returns
        risk_free_rate: Annual risk-free rate as decimal
        
    Returns:
        Sharpe ratio
    """
    if len(returns) == 0:
        return 0.0
    
    # Annualize returns
    annual_return = returns.mean() * 252
    
    # Annualize volatility
    annual_vol = calculate_volatility(returns, annualize=True)
    
    if annual_vol == 0:
        return 0.0
    
    return (annual_return - risk_free_rate) / annual_vol


def calculate_sortino_ratio(returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """
    Calculate Sortino ratio (similar to Sharpe but uses downside deviation).
    
    Args:
        returns: Series of returns
        risk_free_rate: Annual risk-free rate as decimal
        
    Returns:
        Sortino ratio
    """
    if len(returns) == 0:
        return 0.0
    
    # Annualize returns
    annual_return = returns.mean() * 252
    
    # Calculate downside deviation
    downside_returns = returns[returns < 0]
    if len(downside_returns) == 0:
        return float('inf') if annual_return > risk_free_rate else 0.0
    
    downside_deviation = downside_returns.std() * np.sqrt(252)
    
    if downside_deviation == 0:
        return 0.0
    
    return (annual_return - risk_free_rate) / downside_deviation


def calculate_max_drawdown(prices: Union[pd.Series, np.ndarray]) -> float:
    """
    Calculate maximum drawdown from price series.
    
    Args:
        prices: Series of prices
        
    Returns:
        Maximum drawdown as a decimal (negative value)
    """
    if isinstance(prices, np.ndarray):
        prices = pd.Series(prices)
    
    # Calculate running maximum
    running_max = prices.expanding().max()
    
    # Calculate drawdown
    drawdown = (prices - running_max) / running_max
    
    return drawdown.min()


def calculate_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """
    Calculate Value at Risk using historical method.
    
    Args:
        returns: Series of returns
        confidence: Confidence level (e.g., 0.95 for 95% VaR)
        
    Returns:
        VaR as a decimal (negative value indicates loss)
    """
    if len(returns) == 0:
        return 0.0
    
    return float(np.percentile(returns, (1 - confidence) * 100))


def calculate_cvar(returns: pd.Series, confidence: float = 0.95) -> float:
    """
    Calculate Conditional Value at Risk (Expected Shortfall).
    
    Args:
        returns: Series of returns
        confidence: Confidence level (e.g., 0.95 for 95% CVaR)
        
    Returns:
        CVaR as a decimal (negative value indicates loss)
    """
    if len(returns) == 0:
        return 0.0
    
    var = calculate_var(returns, confidence)
    return returns[returns <= var].mean()


def calculate_beta(asset_returns: pd.Series, market_returns: pd.Series) -> float:
    """
    Calculate beta coefficient against market benchmark.
    
    Args:
        asset_returns: Series of asset returns
        market_returns: Series of market/benchmark returns
        
    Returns:
        Beta coefficient
    """
    if len(asset_returns) == 0 or len(market_returns) == 0:
        return 0.0
    
    # Align the series
    aligned = pd.concat([asset_returns, market_returns], axis=1, join='inner')
    if len(aligned) < 2:
        return 0.0
    
    aligned.columns = ['asset', 'market']
    
    # Calculate covariance and variance
    covariance = aligned['asset'].cov(aligned['market'])
    market_variance = aligned['market'].var()
    
    if market_variance == 0:
        return 0.0
    
    return float(covariance) / float(market_variance)


def calculate_alpha(asset_returns: pd.Series, market_returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """
    Calculate alpha using CAPM model.
    
    Args:
        asset_returns: Series of asset returns
        market_returns: Series of market/benchmark returns
        risk_free_rate: Annual risk-free rate as decimal
        
    Returns:
        Alpha as annualized decimal
    """
    if len(asset_returns) == 0 or len(market_returns) == 0:
        return 0.0
    
    # Align the series
    aligned = pd.concat([asset_returns, market_returns], axis=1, join='inner')
    if len(aligned) < 2:
        return 0.0
    
    aligned.columns = ['asset', 'market']
    
    # Calculate beta
    beta = calculate_beta(aligned['asset'], aligned['market'])
    
    # Annualize returns
    asset_annual_return = aligned['asset'].mean() * 252
    market_annual_return = aligned['market'].mean() * 252
    
    # Calculate alpha
    expected_return = risk_free_rate + beta * (market_annual_return - risk_free_rate)
    alpha = asset_annual_return - expected_return
    
    return alpha


def calculate_information_ratio(asset_returns: pd.Series, benchmark_returns: pd.Series) -> float:
    """
    Calculate Information Ratio.
    
    Args:
        asset_returns: Series of asset returns
        benchmark_returns: Series of benchmark returns
        
    Returns:
        Information ratio
    """
    if len(asset_returns) == 0 or len(benchmark_returns) == 0:
        return 0.0
    
    # Align the series
    aligned = pd.concat([asset_returns, benchmark_returns], axis=1, join='inner')
    if len(aligned) < 2:
        return 0.0
    
    aligned.columns = ['asset', 'benchmark']
    
    # Calculate excess returns
    excess_returns = aligned['asset'] - aligned['benchmark']
    
    # Calculate tracking error (standard deviation of excess returns)
    tracking_error = excess_returns.std()
    
    if tracking_error == 0:
        return 0.0
    
    # Calculate active return (annualized)
    active_return = excess_returns.mean() * 252
    
    # Annualize tracking error
    tracking_error_annual = tracking_error * np.sqrt(252)
    
    return active_return / tracking_error_annual


def calculate_treynor_ratio(returns: pd.Series, market_returns: pd.Series, risk_free_rate: float = 0.0) -> float:
    """
    Calculate Treynor ratio.
    
    Args:
        returns: Series of returns
        market_returns: Series of market returns
        risk_free_rate: Annual risk-free rate as decimal
        
    Returns:
        Treynor ratio
    """
    beta = calculate_beta(returns, market_returns)
    
    if beta == 0:
        return 0.0
    
    # Annualize returns
    annual_return = returns.mean() * 252
    
    return (annual_return - risk_free_rate) / beta


def calculate_calmar_ratio(returns: pd.Series) -> float:
    """
    Calculate Calmar ratio (annual return / max drawdown).
    
    Args:
        returns: Series of returns
        
    Returns:
        Calmar ratio
    """
    if len(returns) == 0:
        return 0.0
    
    # Calculate annualized return
    annual_return = returns.mean() * 252
    
    # Calculate max drawdown from cumulative returns
    cumulative = (1 + returns).cumprod()
    max_dd = calculate_max_drawdown(cumulative)
    
    if max_dd == 0:
        return float('inf') if annual_return > 0 else 0.0
    
    return annual_return / abs(max_dd)


def rolling_volatility(returns: pd.Series, window: int = 30) -> pd.Series:
    """
    Calculate rolling volatility.
    
    Args:
        returns: Series of returns
        window: Rolling window size in days
        
    Returns:
        Series of rolling volatility
    """
    return returns.rolling(window=window).std() * np.sqrt(252)


def rolling_sharpe(returns: pd.Series, window: int = 30, risk_free_rate: float = 0.0) -> pd.Series:
    """
    Calculate rolling Sharpe ratio.
    
    Args:
        returns: Series of returns
        window: Rolling window size in days
        risk_free_rate: Annual risk-free rate as decimal
        
    Returns:
        Series of rolling Sharpe ratios
    """
    rolling_return = returns.rolling(window=window).mean() * 252
    rolling_vol = rolling_volatility(returns, window)
    
    return (rolling_return - risk_free_rate) / rolling_vol
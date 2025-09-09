# app/api/v1/market_data.py
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import date, datetime, timezone

from app.core.database import get_db
from app.core.user import get_current_user_id

router = APIRouter()


@router.get("/securities/search")
async def search_securities(
    *,
    query: str = Query(..., description="Search query (symbol or name)"),
    limit: int = Query(10, description="Maximum number of results")
):
    """
    Search for securities by symbol or name.
    """
    return {
        "results": [
            {
                "symbol": "AAPL",
                "name": "Apple Inc.",
                "security_type": "equity",
                "exchange": "NASDAQ",
                "currency": "USD",
                "sector": "Technology",
                "current_price": 175.50
            },
            {
                "symbol": "MSFT",
                "name": "Microsoft Corporation", 
                "security_type": "equity",
                "exchange": "NASDAQ",
                "currency": "USD",
                "sector": "Technology",
                "current_price": 412.30
            }
        ],
        "total": 2,
        "query": query,
        "limit": limit
    }


@router.get("/securities/{symbol}/price")
async def get_current_price(
    *,
    symbol: str,
    currency: str = Query("USD", description="Target currency")
):
    """
    Get current price for a security.
    """
    return {
        "symbol": symbol.upper(),
        "current_price": 175.50,
        "previous_close": 174.20,
        "price_change": 1.30,
        "price_change_percent": 0.75,
        "currency": currency,
        "last_updated": datetime.now(timezone.utc).isoformat(),
        "volume": 45123000,
        "market_status": "closed"
    }


@router.get("/securities/{symbol}/history")
async def get_price_history(
    *,
    symbol: str,
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    interval: str = Query("daily", description="Price interval (daily, weekly, monthly)")
):
    """
    Get historical price data for a security.
    """
    return {
        "symbol": symbol.upper(),
        "interval": interval,
        "start_date": start_date.isoformat() if start_date else "2024-01-01",
        "end_date": end_date.isoformat() if end_date else "2024-12-31",
        "data_points": 252,
        "prices": [
            {
                "date": "2024-01-02",
                "open": 185.64,
                "high": 186.95,
                "low": 185.00,
                "close": 185.64,
                "volume": 47471600,
                "adjusted_close": 185.64
            },
            {
                "date": "2024-01-03",
                "open": 184.35,
                "high": 185.40,
                "low": 182.13,
                "close": 184.25,
                "volume": 58414100,
                "adjusted_close": 184.25
            }
        ]
    }


@router.get("/exchange-rates")
async def get_exchange_rates(
    *,
    base_currency: str = Query("USD", description="Base currency"),
    target_currencies: Optional[List[str]] = Query(None, description="Target currencies")
):
    """
    Get current exchange rates.
    """
    if target_currencies is None:
        target_currencies = ["EUR", "GBP", "JPY", "CAD"]
    
    return {
        "base_currency": base_currency,
        "rates": {
            "EUR": 0.85,
            "GBP": 0.73,
            "JPY": 110.25,
            "CAD": 1.25
        },
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


@router.get("/exchange-rates/{base}/{quote}")
async def get_specific_exchange_rate(
    *,
    base: str,
    quote: str
):
    """
    Get exchange rate for a specific currency pair.
    """
    return {
        "base_currency": base.upper(),
        "quote_currency": quote.upper(), 
        "rate": 0.85,
        "inverse_rate": 1.18,
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


@router.get("/benchmarks")
async def get_benchmarks():
    """
    Get available benchmark indices.
    """
    return {
        "benchmarks": [
            {
                "symbol": "SPY",
                "name": "SPDR S&P 500 ETF Trust",
                "description": "S&P 500 Index",
                "currency": "USD",
                "category": "US Large Cap"
            },
            {
                "symbol": "VTI",
                "name": "Vanguard Total Stock Market ETF",
                "description": "Total US Stock Market",
                "currency": "USD",
                "category": "US Total Market"
            },
            {
                "symbol": "VXUS",
                "name": "Vanguard Total International Stock ETF",
                "description": "International Markets",
                "currency": "USD", 
                "category": "International"
            }
        ]
    }


@router.get("/market-status")
async def get_market_status():
    """
    Get current market status for major exchanges.
    """
    return {
        "markets": {
            "NYSE": {
                "status": "closed",
                "next_open": "2024-01-03T09:30:00-05:00",
                "next_close": "2024-01-03T16:00:00-05:00"
            },
            "NASDAQ": {
                "status": "closed",
                "next_open": "2024-01-03T09:30:00-05:00", 
                "next_close": "2024-01-03T16:00:00-05:00"
            },
            "LSE": {
                "status": "closed",
                "next_open": "2024-01-03T08:00:00+00:00",
                "next_close": "2024-01-03T16:30:00+00:00"
            }
        },
        "last_updated": datetime.now(timezone.utc).isoformat()
    }


@router.get("/health")
async def market_data_health():
    """
    Health check for market data service.
    """
    return {
        "status": "healthy",
        "service": "market_data",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "features": [
            "security_search",
            "price_data",
            "exchange_rates",
            "benchmarks"
        ]
    }
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/securities/search")
async def search_securities(
    *,
    query: str = Query(..., description="Search query (symbol or name)"),
    limit: int = Query(10, description="Maximum number of results"),
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
                "current_price": 175.50,
            },
            {
                "symbol": "MSFT",
                "name": "Microsoft Corporation",
                "security_type": "equity",
                "exchange": "NASDAQ",
                "currency": "USD",
                "sector": "Technology",
                "current_price": 412.30,
            },
        ],
        "total": 2,
        "query": query,
        "limit": limit,
    }


@router.get("/exchange-rates")
async def get_exchange_rates(
    *,
    base_currency: str = Query("USD", description="Base currency"),
    target_currencies: Optional[List[str]] = Query(None, description="Target currencies"),
):
    """
    Get current exchange rates.
    """
    if target_currencies is None:
        target_currencies = ["EUR", "GBP", "JPY", "CAD"]

    return {
        "base_currency": base_currency,
        "rates": {"EUR": 0.85, "GBP": 0.73, "JPY": 110.25, "CAD": 1.25},
        "last_updated": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/exchange-rates/{base}/{quote}")
async def get_specific_exchange_rate(*, base: str, quote: str):
    """
    Get exchange rate for a specific currency pair.
    """
    return {
        "base_currency": base.upper(),
        "quote_currency": quote.upper(),
        "rate": 0.85,
        "inverse_rate": 1.18,
        "last_updated": datetime.now(timezone.utc).isoformat(),
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
                "security_type": "US Large Cap",
            },
            {
                "symbol": "VTI",
                "name": "Vanguard Total Stock Market ETF",
                "description": "Total US Stock Market",
                "currency": "USD",
                "security_type": "US Total Market",
            },
            {
                "symbol": "VXUS",
                "name": "Vanguard Total International Stock ETF",
                "description": "International Markets",
                "currency": "USD",
                "security_type": "International",
            },
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
                "next_close": "2024-01-03T16:00:00-05:00",
            },
            "NASDAQ": {
                "status": "closed",
                "next_open": "2024-01-03T09:30:00-05:00",
                "next_close": "2024-01-03T16:00:00-05:00",
            },
            "LSE": {
                "status": "closed",
                "next_open": "2024-01-03T08:00:00+00:00",
                "next_close": "2024-01-03T16:30:00+00:00",
            },
        },
        "last_updated": datetime.now(timezone.utc).isoformat(),
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
        "features": ["security_search", "price_data", "exchange_rates", "benchmarks"],
    }

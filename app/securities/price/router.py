from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Query

router = APIRouter()


@router.get("/securities/{symbol}/price")
async def get_current_price(
    *, symbol: str, currency: str = Query("USD", description="Target currency")
):
    """
    Get current price for a securities.
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
        "market_status": "closed",
    }


@router.get("/securities/{symbol}/history")
async def get_price_history(
    *,
    symbol: str,
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    interval: str = Query("daily", description="Price interval (daily, weekly, monthly)"),
):
    """
    Get historical price data for a securities.
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
                "adjusted_close": 185.64,
            },
            {
                "date": "2024-01-03",
                "open": 184.35,
                "high": 185.40,
                "low": 182.13,
                "close": 184.25,
                "volume": 58414100,
                "adjusted_close": 184.25,
            },
        ],
    }

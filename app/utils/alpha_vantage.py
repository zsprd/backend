import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import aiohttp
from sqlalchemy.orm import Session

from app.core.config import settings
from app.crud.base import CRUDBase
from app.models.security.market_data import MarketData
from app.models.security.security import Security
from app.utils.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class AlphaVantageClient:
    """
    Alpha Vantage API client with rate limiting and caching.
    Handles stock, ETF, and cryptocurrency data fetching.
    """

    def __init__(self):
        self.api_key = settings.ALPHA_VANTAGE_API_KEY
        self.base_url = settings.ALPHA_VANTAGE_BASE_URL
        self.rate_limiter = RateLimiter(
            max_requests=settings.ALPHA_VANTAGE_RATE_LIMIT, time_window=60  # 1 minute
        )

    async def fetch_daily_data(
        self, symbol: str, outputsize: str = "compact"
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch daily time series data for a stock/ETF.

        Args:
            symbol: Stock symbol (e.g., 'AAPL', 'SPY')
            outputsize: 'compact' (last 100 days) or 'full' (20+ years)
        """
        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol,
            "outputsize": outputsize,
            "apikey": self.api_key,
        }

        return await self._make_request(params)

    async def fetch_intraday_data(
        self, symbol: str, interval: str = "5min"
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch intraday data for a stock/ETF.

        Args:
            symbol: Stock symbol
            interval: Time interval ('1min', '5min', '15min', '30min', '60min')
        """
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": interval,
            "apikey": self.api_key,
        }

        return await self._make_request(params)

    async def fetch_crypto_data(self, symbol: str, market: str = "USD") -> Optional[Dict[str, Any]]:
        """
        Fetch cryptocurrency data.

        Args:
            symbol: Crypto symbol (e.g., 'BTC', 'ETH')
            market: Market currency (default: 'USD')
        """
        params = {
            "function": "DIGITAL_CURRENCY_DAILY",
            "symbol": symbol,
            "market": market,
            "apikey": self.api_key,
        }

        return await self._make_request(params)

    async def fetch_fx_rate(self, from_currency: str, to_currency: str) -> Optional[Dict[str, Any]]:
        """
        Fetch foreign exchange rate.

        Args:
            from_currency: Base currency (e.g., 'USD')
            to_currency: Quote currency (e.g., 'EUR')
        """
        params = {
            "function": "FX_DAILY",
            "from_symbol": from_currency,
            "to_symbol": to_currency,
            "apikey": self.api_key,
        }

        return await self._make_request(params)

    async def search_symbol(self, keywords: str) -> Optional[Dict[str, Any]]:
        """
        Search for securities by keywords.

        Args:
            keywords: Search keywords
        """
        params = {
            "function": "SYMBOL_SEARCH",
            "keywords": keywords,
            "apikey": self.api_key,
        }

        return await self._make_request(params)

    async def fetch_company_overview(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Fetch company fundamental data and overview.

        Args:
            symbol: Stock symbol
        """
        params = {"function": "OVERVIEW", "symbol": symbol, "apikey": self.api_key}

        return await self._make_request(params)

    async def _make_request(self, params: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        Make HTTP request to Alpha Vantage API with rate limiting.

        Args:
            params: Query parameters for the API call
        """
        # Wait for rate limiter
        await self.rate_limiter.wait_if_needed()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.base_url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()

                        # Check for API errors
                        if "Error Message" in data:
                            logger.error(f"Alpha Vantage API error: {data['Error Message']}")
                            return None

                        if "Note" in data:
                            logger.warning(f"Alpha Vantage API note: {data['Note']}")
                            # This typically means we've hit the rate limit
                            return None

                        return data
                    else:
                        logger.error(f"HTTP error {response.status}: {await response.text()}")
                        return None

        except Exception as e:
            logger.error(f"Request failed: {str(e)}")
            return None


class MarketDataService:
    """
    Service for fetching and storing market data using Alpha Vantage.
    """

    def __init__(self, db: Session):
        self.db = db
        self.client = AlphaVantageClient()
        self.market_data_crud = CRUDBase(MarketData)

    async def update_security_data(self, security_id: str, force_refresh: bool = False) -> bool:
        """
        Update market data for a specific security.

        Args:
            security_id: Security ID to update
            force_refresh: Force refresh even if data exists
        """
        # Get security details
        security = self.db.query(Security).filter(Security.id == security_id).first()
        if not security:
            logger.error(f"Security {security_id} not found")
            return False

        # Check if we need to update data
        if not force_refresh:
            latest_data = (
                self.db.query(MarketData)
                .filter(MarketData.security_id == security_id)
                .order_by(MarketData.date.desc())
                .first()
            )

            if latest_data and latest_data.date >= datetime.now().date() - timedelta(days=1):
                logger.info(f"Market data for {security.symbol} is up to date")
                return True

        # Fetch new data based on security type
        try:
            if security.type == "cryptocurrency":
                data = await self.client.fetch_crypto_data(security.symbol)
                return await self._process_crypto_data(security, data)
            else:
                data = await self.client.fetch_daily_data(security.symbol)
                return await self._process_stock_data(security, data)

        except Exception as e:
            logger.error(f"Failed to update data for {security.symbol}: {str(e)}")
            return False

    async def _process_stock_data(self, security: Security, data: Optional[Dict[str, Any]]) -> bool:
        """Process and store stock/ETF market data."""
        if not data or "Time Series (Daily)" not in data:
            logger.error(f"Invalid stock data format for {security.symbol}")
            return False

        time_series = data["Time Series (Daily)"]

        for date_str, price_data in time_series.items():
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()

                # Check if data already exists
                existing = (
                    self.db.query(MarketData)
                    .filter(MarketData.security_id == security.id, MarketData.date == date)
                    .first()
                )

                if existing:
                    continue

                # Create new market data entry
                market_data = MarketData(
                    security_id=security.id,
                    date=date,
                    open=float(price_data["1. open"]),
                    high=float(price_data["2. high"]),
                    low=float(price_data["3. low"]),
                    close=float(price_data["4. close"]),
                    adjusted_close=float(price_data["5. adjusted close"]),
                    volume=int(price_data["6. volume"]),
                    currency=security.currency,
                    source="alphavantage",
                )

                self.db.add(market_data)

            except (ValueError, KeyError) as e:
                logger.error(f"Error processing data for {date_str}: {str(e)}")
                continue

        self.db.commit()
        logger.info(f"Updated market data for {security.symbol}")
        return True

    async def _process_crypto_data(
        self, security: Security, data: Optional[Dict[str, Any]]
    ) -> bool:
        """Process and store cryptocurrency market data."""
        if not data or "Time Series (Digital Currency Daily)" not in data:
            logger.error(f"Invalid crypto data format for {security.symbol}")
            return False

        time_series = data["Time Series (Digital Currency Daily)"]

        for date_str, price_data in time_series.items():
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()

                # Check if data already exists
                existing = (
                    self.db.query(MarketData)
                    .filter(MarketData.security_id == security.id, MarketData.date == date)
                    .first()
                )

                if existing:
                    continue

                # Create new market data entry
                market_data = MarketData(
                    security_id=security.id,
                    date=date,
                    open=float(price_data["1a. open (USD)"]),
                    high=float(price_data["2a. high (USD)"]),
                    low=float(price_data["3a. low (USD)"]),
                    close=float(price_data["4a. close (USD)"]),
                    volume=float(price_data["5. volume"]),
                    currency="USD",  # Crypto prices in USD
                    source="alphavantage",
                )

                self.db.add(market_data)

            except (ValueError, KeyError) as e:
                logger.error(f"Error processing crypto data for {date_str}: {str(e)}")
                continue

        self.db.commit()
        logger.info(f"Updated crypto data for {security.symbol}")
        return True

    async def bulk_update_securities(
        self, security_ids: List[str], max_concurrent: int = 3
    ) -> Dict[str, bool]:
        """
        Update multiple securities with concurrent requests (respecting rate limits).

        Args:
            security_ids: List of security IDs to update
            max_concurrent: Maximum concurrent requests
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def update_with_semaphore(security_id: str) -> tuple[str, bool]:
            async with semaphore:
                result = await self.update_security_data(security_id)
                return security_id, result

        # Execute updates with concurrency control
        tasks = [update_with_semaphore(sid) for sid in security_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        update_results = {}
        for result in results:
            if isinstance(result, tuple):
                security_id, success = result
                update_results[security_id] = success
            else:
                logger.error(f"Update task failed: {result}")

        return update_results


# Create convenience function for getting market data service
def get_market_data_service(db: Session) -> MarketDataService:
    """Get MarketDataService instance with database session."""
    return MarketDataService(db)

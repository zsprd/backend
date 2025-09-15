import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import yfinance as yf
from sqlalchemy.orm import Session

from app.integrations.alphavantage.service import MarketDataService as AlphaVantageService
from app.securities.price.model import SecurityPrice
from app.securities.reference.crud import security_crud
from app.securities.reference.model import SecurityReference
from app.securities.reference.schema import SecurityCreate, SecurityUpdate

logger = logging.getLogger(__name__)


class MarketDataService:
    """
    Unified market data service that uses yfinance as primary source
    and Alpha Vantage as fallback. Provides securities enrichment and market data updates.

    This service coordinates between multiple data providers to ensure
    the best possible data quality and availability.
    """

    def __init__(self, db: Session):
        self.db = db
        self.alpha_vantage_service = AlphaVantageService(db)

        # Cache for yfinance ticker objects to avoid recreating
        self._ticker_cache: Dict[str, yf.Ticker] = {}

        # Performance tracking
        self._stats = {
            "yfinance_success": 0,
            "yfinance_failed": 0,
            "alphavantage_success": 0,
            "alphavantage_failed": 0,
            "minimal_created": 0,
        }

    async def search_and_create_security(
        self, symbol: str
    ) -> Tuple[Optional[SecurityReference], str]:
        """
        Search for a securities by symbol and create it if found.

        Priority:
        1. yfinance lookup and creation
        2. Alpha Vantage lookup and creation
        3. Minimal securities creation

        Args:
            symbol: SecurityReference symbol to search for

        Returns:
            Tuple of (SecurityReference instance or None, source string)
        """

        symbol = symbol.strip().upper()
        logger.info(f"Creating securities for symbol: {symbol}")

        # Try yfinance first
        try:
            security, source = await self._create_security_from_yfinance(symbol)
            if security:
                self._stats["yfinance_success"] += 1
                logger.info(f"Successfully created {symbol} using yfinance")
                return security, source
            else:
                self._stats["yfinance_failed"] += 1
        except Exception as e:
            self._stats["yfinance_failed"] += 1
            logger.warning(f"yfinance creation failed for {symbol}: {str(e)}")

        # Fallback to Alpha Vantage
        try:
            logger.info(f"Trying Alpha Vantage for {symbol}")
            security, source = await self._create_security_from_alphavantage(symbol)
            if security:
                self._stats["alphavantage_success"] += 1
                logger.info(f"Successfully created {symbol} using Alpha Vantage")
                return security, source
            else:
                self._stats["alphavantage_failed"] += 1
        except Exception as e:
            self._stats["alphavantage_failed"] += 1
            logger.warning(f"Alpha Vantage creation failed for {symbol}: {str(e)}")

        # Last resort: create minimal securities
        try:
            security = await self._create_minimal_security(symbol)
            if security:
                self._stats["minimal_created"] += 1
                logger.info(f"Created minimal securities for {symbol}")
                return security, "minimal"
        except Exception as e:
            logger.error(f"Failed to create minimal securities for {symbol}: {str(e)}")

        return None, "failed"

    async def enrich_security_data(
        self, security: SecurityReference, force_refresh: bool = False
    ) -> Tuple[bool, str]:
        """
        Enrich an existing securities with additional data (name, sector, etc.).

        Args:
            security: SecurityReference model instance to enrich
            force_refresh: Force refresh even if data seems complete

        Returns:
            Tuple of (success: bool, source: str)
        """

        # Skip enrichment if data looks complete and not forcing refresh
        if not force_refresh and self._security_has_good_data(security):
            logger.debug(f"SecurityReference {security.symbol} already has good data")
            return True, "cached"

        # Try yfinance first
        try:
            success, source = await self._enrich_with_yfinance(security)
            if success:
                return True, source
        except Exception as e:
            logger.warning(f"yfinance enrichment failed for {security.symbol}: {e}")

        # Fallback to Alpha Vantage
        try:
            success, source = await self._enrich_with_alphavantage(security)
            if success:
                return True, source
        except Exception as e:
            logger.warning(f"Alpha Vantage enrichment failed for {security.symbol}: {e}")

        return False, "failed"

    async def update_market_data(
        self, security_id: str, force_refresh: bool = False
    ) -> Tuple[bool, str]:
        """
        Update market data (prices, volumes) for a securities.

        Args:
            security_id: SecurityReference ID to update
            force_refresh: Force refresh even if recent data exists

        Returns:
            Tuple of (success: bool, source: str)
        """

        # Get securities
        security = (
            self.db.query(SecurityReference).filter(SecurityReference.id == security_id).first()
        )
        if not security:
            logger.error(f"SecurityReference {security_id} not found")
            return False, "not_found"

        # Check if we need to update (skip if recent data exists)
        if not force_refresh and self._has_recent_market_data(security):
            logger.debug(f"Recent market data exists for {security.symbol}")
            return True, "cached"

        # Try yfinance first
        try:
            success, source = await self._update_market_data_yfinance(security)
            if success:
                return True, source
        except Exception as e:
            logger.warning(f"yfinance market data update failed for {security.symbol}: {e}")

        # Fallback to Alpha Vantage
        try:
            success = await self.alpha_vantage_service.update_security_data(
                str(security_id), force_refresh
            )
            return success, "alphavantage" if success else "failed"
        except Exception as e:
            logger.error(f"Alpha Vantage market data update failed for {security.symbol}: {e}")
            return False, "failed"

    async def bulk_enrich_securities(
        self, security_ids: List[str], max_concurrent: int = 5
    ) -> Dict[str, Tuple[bool, str]]:
        """
        Enrich multiple securities concurrently with rate limiting.

        Args:
            security_ids: List of securities IDs to enrich
            max_concurrent: Maximum concurrent operations

        Returns:
            Dict mapping security_id to (success, source) tuple
        """

        semaphore = asyncio.Semaphore(max_concurrent)

        async def enrich_with_semaphore(security_id: str) -> Tuple[str, Tuple[bool, str]]:
            async with semaphore:
                security = (
                    self.db.query(SecurityReference)
                    .filter(SecurityReference.id == security_id)
                    .first()
                )
                if security:
                    success, source = await self.enrich_security_data(security)
                    return security_id, (success, source)
                return security_id, (False, "not_found")

        # Execute enrichment with concurrency control
        tasks = [enrich_with_semaphore(sid) for sid in security_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        enrichment_results = {}
        for result in results:
            if isinstance(result, tuple):
                security_id, (success, source) = result
                enrichment_results[security_id] = (success, source)
            else:
                logger.error(f"Enrichment task failed: {result}")

        return enrichment_results

    # ===================================================================
    # yfinance Integration Methods
    # ===================================================================

    async def _create_security_from_yfinance(
        self, symbol: str
    ) -> Tuple[Optional[SecurityReference], str]:
        """Create a new securities using yfinance data."""

        try:
            ticker = self._get_ticker(symbol)

            # Get basic info
            info = ticker.info

            if not info or not info.get("symbol") or info.get("symbol") == symbol:
                # Sometimes yfinance returns the search symbol even when not found
                # Double-check by trying to get some price data
                hist = ticker.history(period="5d")
                if hist.empty:
                    logger.debug(f"No yfinance data available for {symbol}")
                    return None, "yfinance_no_data"

            # Extract securities details
            security_data = self._extract_security_create_data_from_yfinance(symbol, info)

            if security_data:
                security = security_crud.create(self.db, obj_in=security_data)
                self.db.commit()

                # Try to get some initial market data
                try:
                    await self._update_market_data_yfinance(security)
                except Exception as e:
                    logger.warning(f"Failed to get initial market data for {symbol}: {e}")

                return security, "yfinance"

            return None, "yfinance_no_useful_data"

        except Exception as e:
            logger.error(f"yfinance securities creation failed for {symbol}: {str(e)}")
            return None, "yfinance_error"

    async def _enrich_with_yfinance(self, security: SecurityReference) -> Tuple[bool, str]:
        """Enrich securities using yfinance data."""

        try:
            ticker = self._get_ticker(security.symbol)
            info = ticker.info

            if not info or not info.get("symbol"):
                logger.debug(f"No yfinance info available for {security.symbol}")
                return False, "yfinance_no_data"

            # Update securities with yfinance data
            update_data = self._extract_security_update_data_from_yfinance(info)

            if update_data:
                # Only update if we have meaningful new data
                update_dict = update_data.model_dump(exclude_unset=True)
                if update_dict:
                    security_crud.update(self.db, db_obj=security, obj_in=update_data)
                    self.db.commit()
                    logger.info(f"Enriched securities {security.symbol} with yfinance data")
                    return True, "yfinance"

            return False, "yfinance_no_useful_data"

        except Exception as e:
            logger.error(f"yfinance enrichment failed for {security.symbol}: {str(e)}")
            return False, "yfinance_error"

    async def _update_market_data_yfinance(self, security: SecurityReference) -> Tuple[bool, str]:
        """Update market data using yfinance."""

        try:
            ticker = self._get_ticker(security.symbol)

            # Get recent price data (last 30 days to ensure we get some data)
            hist = ticker.history(period="30d")

            if hist.empty:
                logger.debug(f"No yfinance price data for {security.symbol}")
                return False, "yfinance_no_data"

            records_added = 0

            # Process and store the price data
            for date_index, row in hist.iterrows():
                try:
                    market_date = date_index.date()

                    # Check if data already exists
                    existing = (
                        self.db.query(SecurityPrice)
                        .filter(
                            SecurityPrice.security_id == security.id,
                            SecurityPrice.date == market_date,
                        )
                        .first()
                    )

                    if existing:
                        continue

                    # Validate data quality
                    if pd.isna(row["Close"]) or row["Close"] <= 0:
                        continue

                    # Create new market data entry
                    market_data = SecurityPrice(
                        security_id=security.id,
                        date=market_date,
                        open=float(row["Open"]) if not pd.isna(row["Open"]) else None,
                        high=float(row["High"]) if not pd.isna(row["High"]) else None,
                        low=float(row["Low"]) if not pd.isna(row["Low"]) else None,
                        close=float(row["Close"]),
                        adjusted_close=float(
                            row["Close"]
                        ),  # yfinance already provides adjusted data
                        volume=int(row["Volume"]) if not pd.isna(row["Volume"]) else 0,
                        currency=security.currency or "USD",
                        source="yfinance",
                    )

                    self.db.add(market_data)
                    records_added += 1

                except Exception as e:
                    logger.warning(
                        f"Failed to process market data for {security.symbol} on {date_index}: {e}"
                    )
                    continue

            if records_added > 0:
                self.db.commit()
                logger.info(
                    f"Added {records_added} market data records for {security.symbol} using yfinance"
                )
                return True, "yfinance"
            else:
                logger.debug(f"No new market data to add for {security.symbol}")
                return True, "yfinance_no_new_data"

        except Exception as e:
            logger.error(f"yfinance market data update failed for {security.symbol}: {str(e)}")
            return False, "yfinance_error"

    def _extract_security_create_data_from_yfinance(
        self, symbol: str, yf_data: Dict[str, Any]
    ) -> Optional[SecurityCreate]:
        """Extract creation data from yfinance info."""

        try:
            # Determine securities security_type
            quote_type = yf_data.get("quoteType", "").lower()
            category_mapping = {
                "equity": "equity",
                "etf": "etf",
                "mutualfund": "mutual_fund",
                "cryptocurrency": "cryptocurrency",
                "currency": "currency",
                "future": "futures",
                "option": "options",
            }
            security_category = category_mapping.get(quote_type, "equity")

            # Get name with fallback chain
            name = (
                yf_data.get("longName")
                or yf_data.get("shortName")
                or yf_data.get("displayName")
                or symbol
            )

            return SecurityCreate(
                symbol=symbol.upper(),
                name=name[:255] if name else symbol,
                security_category=security_category,
                currency=yf_data.get("currency", "USD"),
                exchange=yf_data.get("exchange", "")[:10] if yf_data.get("exchange") else None,
                country=yf_data.get("country", "")[:2] if yf_data.get("country") else None,
                sector=yf_data.get("sector", "")[:100] if yf_data.get("sector") else None,
                industry=yf_data.get("industry", "")[:100] if yf_data.get("industry") else None,
                alphavantage_symbol=symbol.upper(),
                data_provider_category=security_category,
            )

        except Exception as e:
            logger.error(f"Failed to extract yfinance create data for {symbol}: {str(e)}")
            return None

    def _extract_security_update_data_from_yfinance(
        self, yf_data: Dict[str, Any]
    ) -> Optional[SecurityUpdate]:
        """Extract update data from yfinance info."""

        try:
            update_fields = {}

            # Basic info - only update if we have better data
            long_name = yf_data.get("longName")
            short_name = yf_data.get("shortName")
            if long_name:
                update_fields["name"] = long_name[:255]
            elif short_name:
                update_fields["name"] = short_name[:255]

            # Classification
            if yf_data.get("sector"):
                update_fields["sector"] = yf_data["sector"][:100]

            if yf_data.get("industry"):
                update_fields["industry"] = yf_data["industry"][:100]

            # Market info
            if yf_data.get("currency"):
                update_fields["currency"] = yf_data["currency"]

            if yf_data.get("exchange"):
                update_fields["exchange"] = yf_data["exchange"][:10]

            if yf_data.get("country"):
                update_fields["country"] = yf_data["country"][:2]

            return SecurityUpdate(**update_fields) if update_fields else None

        except Exception as e:
            logger.error(f"Failed to extract yfinance update data: {str(e)}")
            return None

    # ===================================================================
    # Alpha Vantage Integration Methods
    # ===================================================================

    async def _create_security_from_alphavantage(
        self, symbol: str
    ) -> Tuple[Optional[SecurityReference], str]:
        """Create a new securities using Alpha Vantage data."""

        try:
            client = self.alpha_vantage_service.client
            overview_data = await client.fetch_company_overview(symbol)

            if not overview_data or "Symbol" not in overview_data:
                logger.debug(f"No Alpha Vantage data for {symbol}")
                return None, "alphavantage_no_data"

            # Extract securities details
            security_data = self._extract_security_create_data_from_alphavantage(
                symbol, overview_data
            )

            if security_data:
                security = security_crud.create(self.db, obj_in=security_data)
                self.db.commit()

                # Try to get some initial market data using Alpha Vantage
                try:
                    await self.alpha_vantage_service.update_security_data(
                        str(security.id), force_refresh=True
                    )
                except Exception as e:
                    logger.warning(
                        f"Failed to get initial Alpha Vantage market data for {symbol}: {e}"
                    )

                return security, "alphavantage"

            return None, "alphavantage_no_useful_data"

        except Exception as e:
            logger.error(f"Alpha Vantage securities creation failed for {symbol}: {str(e)}")
            return None, "alphavantage_error"

    async def _enrich_with_alphavantage(self, security: SecurityReference) -> Tuple[bool, str]:
        """Enrich securities using Alpha Vantage data."""

        try:
            client = self.alpha_vantage_service.client
            overview_data = await client.fetch_company_overview(security.symbol)

            if not overview_data or "Symbol" not in overview_data:
                return False, "alphavantage_no_data"

            # Update securities with Alpha Vantage data
            update_data = self._extract_security_update_data_from_alphavantage(overview_data)

            if update_data:
                update_dict = update_data.model_dump(exclude_unset=True)
                if update_dict:
                    security_crud.update(self.db, db_obj=security, obj_in=update_data)
                    self.db.commit()
                    logger.info(f"Enriched securities {security.symbol} with Alpha Vantage data")
                    return True, "alphavantage"

            return False, "alphavantage_no_useful_data"

        except Exception as e:
            logger.error(f"Alpha Vantage enrichment failed for {security.symbol}: {str(e)}")
            return False, "alphavantage_error"

    def _extract_security_create_data_from_alphavantage(
        self, symbol: str, av_data: Dict[str, Any]
    ) -> Optional[SecurityCreate]:
        """Extract creation data from Alpha Vantage overview."""

        try:
            # Determine asset type
            asset_type = av_data.get("AssetType", "Common Stock")
            category_mapping = {
                "Common Stock": "equity",
                "ETF": "etf",
                "Mutual Fund": "mutual_fund",
                "REIT": "equity",
                "Preferred Stock": "equity",
            }
            security_category = category_mapping.get(asset_type, "equity")

            return SecurityCreate(
                symbol=symbol.upper(),
                name=(av_data.get("Name") or symbol)[:255],
                security_category=security_category,
                currency=av_data.get("Currency", "USD"),
                exchange=av_data.get("Exchange", "")[:10] if av_data.get("Exchange") else None,
                country=av_data.get("Country", "")[:2] if av_data.get("Country") else None,
                sector=av_data.get("Sector", "")[:100] if av_data.get("Sector") else None,
                industry=av_data.get("Industry", "")[:100] if av_data.get("Industry") else None,
                alphavantage_symbol=symbol.upper(),
                data_provider_category=security_category,
            )

        except Exception as e:
            logger.error(f"Failed to extract Alpha Vantage create data for {symbol}: {str(e)}")
            return None

    def _extract_security_update_data_from_alphavantage(
        self, av_data: Dict[str, Any]
    ) -> Optional[SecurityUpdate]:
        """Extract update data from Alpha Vantage overview."""

        try:
            update_fields = {}

            if av_data.get("Name"):
                update_fields["name"] = av_data["Name"][:255]

            if av_data.get("Sector"):
                update_fields["sector"] = av_data["Sector"][:100]

            if av_data.get("Industry"):
                update_fields["industry"] = av_data["Industry"][:100]

            if av_data.get("Currency"):
                update_fields["currency"] = av_data["Currency"]

            if av_data.get("Exchange"):
                update_fields["exchange"] = av_data["Exchange"][:10]

            if av_data.get("Country"):
                update_fields["country"] = av_data["Country"][:2]

            return SecurityUpdate(**update_fields) if update_fields else None

        except Exception as e:
            logger.error(f"Failed to extract Alpha Vantage update data: {str(e)}")
            return None

    # ===================================================================
    # Fallback and Utility Methods
    # ===================================================================

    async def _create_minimal_security(self, symbol: str) -> Optional[SecurityReference]:
        """Create minimal securities when all external sources fail."""

        try:
            # Infer basic details from symbol
            category = self._infer_category_from_symbol(symbol)
            currency = self._infer_currency_from_symbol(symbol)

            create_data = SecurityCreate(
                symbol=symbol.upper(),
                name=f"Unknown SecurityReference ({symbol})",
                security_category=category,
                currency=currency,
                alphavantage_symbol=symbol.upper(),
                data_provider_category=category,
            )

            security = security_crud.create(self.db, obj_in=create_data)
            self.db.commit()

            logger.info(f"Created minimal securities: {symbol}")
            return security

        except Exception as e:
            logger.error(f"Failed to create minimal securities for {symbol}: {str(e)}")
            return None

    def _get_ticker(self, symbol: str) -> yf.Ticker:
        """Get yfinance ticker with caching."""
        if symbol not in self._ticker_cache:
            self._ticker_cache[symbol] = yf.Ticker(symbol)
        return self._ticker_cache[symbol]

    def _security_has_good_data(self, security: SecurityReference) -> bool:
        """Check if securities already has comprehensive data."""
        return bool(
            security.name
            and security.name != security.symbol
            and security.name != f"Unknown SecurityReference ({security.symbol})"
            and security.sector
            and security.currency
            and len(security.name) > len(security.symbol)  # Name is more than just the symbol
        )

    def _has_recent_market_data(self, security: SecurityReference) -> bool:
        """Check if securities has market data from the last trading day."""

        # Check for data within the last 3 days to account for weekends
        recent_date = datetime.now().date() - timedelta(days=3)

        recent_data = (
            self.db.query(SecurityPrice)
            .filter(SecurityPrice.security_id == security.id, SecurityPrice.date >= recent_date)
            .first()
        )

        return recent_data is not None

    def _infer_category_from_symbol(self, symbol: str) -> str:
        """Infer securities security_type from symbol patterns."""

        symbol_upper = symbol.upper()

        # Cryptocurrency patterns
        crypto_patterns = ["BTC", "ETH", "ADA", "DOT", "DOGE", "LTC", "XRP", "SOL"]
        if any(crypto in symbol_upper for crypto in crypto_patterns):
            return "cryptocurrency"

        if "-USD" in symbol_upper or symbol_upper.endswith("USD"):
            return "cryptocurrency"

        # ETF patterns
        etf_patterns = ["ETF", "SPY", "QQQ", "VTI", "VOO", "IVV", "IWDA", "VEA", "IEMG"]
        if any(etf in symbol_upper for etf in etf_patterns):
            return "etf"

        # Mutual fund patterns
        if symbol_upper.endswith("X") and len(symbol_upper) == 5:
            return "mutual_fund"

        # Default to equity
        return "equity"

    def _infer_currency_from_symbol(self, symbol: str) -> str:
        """Infer currency from symbol patterns."""

        symbol_upper = symbol.upper()

        # Cryptocurrency usually traded in USD
        if self._infer_category_from_symbol(symbol) == "cryptocurrency":
            return "USD"

        # Common currency patterns
        if "-USD" in symbol_upper or symbol_upper.endswith("USD"):
            return "USD"
        elif "-GBP" in symbol_upper or symbol_upper.endswith("GBP"):
            return "GBP"
        elif "-EUR" in symbol_upper or symbol_upper.endswith("EUR"):
            return "EUR"

        # Default to USD
        return "USD"

    def get_stats(self) -> Dict[str, int]:
        """Get performance statistics."""
        return self._stats.copy()

    def clear_cache(self) -> None:
        """Clear internal caches."""
        self._ticker_cache.clear()
        logger.debug("Market data service cache cleared")


# Convenience function for getting market data service
def get_market_data_service(db: Session) -> MarketDataService:
    """Get MarketDataService instance with database session."""
    return MarketDataService(db)

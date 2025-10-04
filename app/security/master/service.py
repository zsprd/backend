import logging
import re
from typing import Any, Dict, Optional

import pandas as pd
import yfinance as yf
from rapidfuzz import fuzz, process
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.security.master.model import Security
from app.security.master.repository import security_crud
from app.security.master.schemas import SecurityCreate

logger = logging.getLogger(__name__)


class SecurityMatcher:
    """
    Advanced securities matching service using fuzzy matching and market data integration.
    Tries multiple strategies to identify securities and creates them if not found.
    """

    def __init__(self, db: Session):
        self.db = db
        self._security_cache: Dict[str, Security] = {}

        # Load existing securities for fuzzy matching
        self._load_securities_for_matching()

    def match_or_create_security(self, row: pd.Series, result) -> Optional[Security]:
        """
        Match CSV row to existing securities or create new one.
        Uses sophisticated matching including fuzzy search.

        Args:
            row: CSV row data containing securities identifier
            result: Processing result object to track created securities

        Returns:
            SecurityMaster instance or None if matching/creation fails
        """

        symbol = row.get("symbol", "").strip().upper()
        if not symbol:
            return None

        # Check cache first
        if symbol in self._security_cache:
            return self._security_cache[symbol]

        # Try multiple matching strategies
        security = (
            self._exact_match(symbol)
            or self._fuzzy_symbol_match(symbol)
            or self._pattern_based_match(symbol)
            or self._create_security_from_market_data(symbol, result)
        )

        # Cache the result
        if security:
            self._security_cache[symbol] = security

        return security

    def _load_securities_for_matching(self) -> None:
        """Load existing securities for fuzzy matching operations."""
        try:
            securities = self.db.query(Security).filter(Security.is_active == True).all()

            # Create searchable lists
            self.symbols = [(sec.symbol, sec.id) for sec in securities if sec.symbol]
            self.names = [(sec.name, sec.id) for sec in securities if sec.name]
            self.isins = [(sec.isin, sec.id) for sec in securities if sec.isin]
            self.cusips = [(sec.cusip, sec.id) for sec in securities if sec.cusip]

            logger.info(f"Loaded {len(securities)} securities for matching")

        except Exception as e:
            logger.error(f"Failed to load securities for matching: {e}")
            self.symbols = []
            self.names = []
            self.isins = []
            self.cusips = []

    def _exact_match(self, identifier: str) -> Optional[Security]:
        """Try exact matches against various identifier fields."""

        security = (
            self.db.query(Security)
            .filter(
                or_(
                    Security.symbol == identifier,
                    Security.isin == identifier,
                    Security.cusip == identifier,
                    Security.alphavantage_symbol == identifier,
                )
            )
            .first()
        )

        if security:
            logger.debug(f"Exact match found for {identifier}: {security.symbol}")
            return security

        return None

    def _fuzzy_symbol_match(self, identifier: str, threshold: int = 85) -> Optional[Security]:
        """Use fuzzy matching to find similar symbols."""

        if not self.symbols:
            return None

        # Extract just the symbol strings for fuzzy matching
        symbol_strings = [symbol for symbol, _ in self.symbols]

        # Find best fuzzy match
        match = process.extractOne(
            identifier, symbol_strings, scorer=fuzz.ratio, score_cutoff=threshold
        )

        if match:
            matched_symbol, score = match

            # Find the securities ID for this symbol
            security_id = next(
                sec_id for symbol, sec_id in self.symbols if symbol == matched_symbol
            )
            security = self.db.query(Security).filter(Security.id == security_id).first()

            if security:
                logger.info(
                    f"Fuzzy match found for {identifier}: {matched_symbol} (score: {score})"
                )
                return security

        return None

    def _pattern_based_match(self, identifier: str) -> Optional[Security]:
        """Match based on identifier patterns (ISIN, CUSIP, etc.)."""

        # ISIN pattern: 12 characters, starts with 2 letters
        if re.match(r"^[A-Z]{2}[A-Z0-9]{9}[0-9]$", identifier):
            return self._match_by_isin(identifier)

        # CUSIP pattern: 9 alphanumeric characters
        if re.match(r"^[A-Z0-9]{9}$", identifier):
            return self._match_by_cusip(identifier)

        # Extended symbol patterns (e.g., BTC-USD, AAPL.NASDAQ)
        return self._match_extended_symbol(identifier)

    def _match_by_isin(self, isin: str) -> Optional[Security]:
        """Match by ISIN with fuzzy fallback."""

        # Try exact ISIN match first
        security = self.db.query(Security).filter(Security.isin == isin).first()
        if security:
            return security

        # Try fuzzy ISIN matching
        if self.isins:
            isin_strings = [isin_val for isin_val, _ in self.isins]
            match = process.extractOne(isin, isin_strings, scorer=fuzz.ratio, score_cutoff=90)

            if match:
                matched_isin, _ = match
                security_id = next(
                    sec_id for isin_val, sec_id in self.isins if isin_val == matched_isin
                )
                return self.db.query(Security).filter(Security.id == security_id).first()

        return None

    def _match_by_cusip(self, cusip: str) -> Optional[Security]:
        """Match by CUSIP with fuzzy fallback."""

        # Try exact CUSIP match first
        security = self.db.query(Security).filter(Security.cusip == cusip).first()
        if security:
            return security

        # Try fuzzy CUSIP matching
        if self.cusips:
            cusip_strings = [cusip_val for cusip_val, _ in self.cusips]
            match = process.extractOne(cusip, cusip_strings, scorer=fuzz.ratio, score_cutoff=95)

            if match:
                matched_cusip, _ = match
                security_id = next(
                    sec_id for cusip_val, sec_id in self.cusips if cusip_val == matched_cusip
                )
                return self.db.query(Security).filter(Security.id == security_id).first()

        return None

    def _match_extended_symbol(self, identifier: str) -> Optional[Security]:
        """Handle extended symbol formats like BTC-USD, AAPL.NASDAQ."""

        # Try various symbol variations
        variations = [
            identifier,
            identifier.replace("-", ""),
            identifier.replace(".", ""),
            identifier.split("-")[0] if "-" in identifier else identifier,
            identifier.split(".")[0] if "." in identifier else identifier,
        ]

        for variation in variations:
            security = self._exact_match(variation)
            if security:
                return security

        return None

    def _create_security_from_market_data(self, identifier: str, result) -> Optional[Security]:
        """
        Create new securities by fetching data from yfinance.
        Falls back to creating minimal securities if market data unavailable.
        """

        try:
            # Try to fetch from yfinance first
            ticker = yf.Ticker(identifier)
            info = ticker.info

            if info and info.get("symbol"):
                security = self._create_security_from_yfinance_data(identifier, info, result)
                if security:
                    return security

        except Exception as e:
            logger.warning(f"yfinance lookup failed for {identifier}: {e}")

        # If yfinance fails, create minimal securities
        return self._create_minimal_security(identifier, result)

    def _create_security_from_yfinance_data(
        self, identifier: str, yf_data: Dict[str, Any], result
    ) -> Optional[Security]:
        """Create securities using yfinance data."""

        try:
            # Extract securities details from yfinance
            symbol = yf_data.get("symbol", identifier).upper()
            name = yf_data.get("longName") or yf_data.get("shortName", symbol)
            currency = yf_data.get("currency", "USD").upper()
            exchange = yf_data.get("exchange", "").upper()
            country = yf_data.get("country", "")
            sector = yf_data.get("sector")
            industry = yf_data.get("industry")

            # Determine securities security_type
            category = self._determine_security_category(yf_data, symbol)

            # Create securities data
            create_data = SecurityCreate(
                symbol=symbol,
                name=name[:255],  # Truncate to fit db constraint
                security_category=category,
                currency=currency,
                exchange=exchange[:10] if exchange else None,
                country=country[:2] if country else None,
                sector=sector[:100] if sector else None,
                industry=industry[:100] if industry else None,
                alphavantage_symbol=symbol,
                data_provider_category=category,
            )

            security = security_crud.create(self.db, obj_in=create_data)

            result.created_securities.append(
                {"symbol": symbol, "name": name, "source": "yfinance", "status": "success"}
            )

            logger.info(f"Created securities from yfinance: {symbol} - {name}")
            return security

        except Exception as e:
            error_msg = f"Failed to create securities from yfinance data for {identifier}: {str(e)}"
            logger.error(error_msg)

            result.failed_securities.append(
                {"symbol": identifier, "source": "yfinance", "error": error_msg}
            )

            return None

    def _create_minimal_security(self, identifier: str, result) -> Optional[Security]:
        """Create minimal securities when market data is unavailable."""

        try:
            # Infer basic details from identifier
            category = self._infer_category_from_symbol(identifier)
            currency = self._infer_currency_from_symbol(identifier)

            create_data = SecurityCreate(
                symbol=identifier,
                name=f"Unknown SecurityMaster ({identifier})",
                security_category=category,
                currency=currency,
                alphavantage_symbol=identifier,
                data_provider_category=category,
            )

            security = security_crud.create(self.db, obj_in=create_data)

            result.created_securities.append(
                {
                    "symbol": identifier,
                    "name": f"Unknown SecurityMaster ({identifier})",
                    "source": "manual",
                    "status": "minimal_data",
                }
            )

            result.warnings.append(
                f"Created minimal securities for '{identifier}' - market data unavailable. "
                f"Please review and update securities details manually."
            )

            logger.info(f"Created minimal securities: {identifier}")
            return security

        except Exception as e:
            error_msg = f"Failed to create minimal securities for {identifier}: {str(e)}"
            logger.error(error_msg)

            result.failed_securities.append(
                {"symbol": identifier, "source": "manual", "error": error_msg}
            )

            return None

    def _determine_security_category(self, yf_data: Dict[str, Any], symbol: str) -> str:
        """Determine securities security_type from yfinance data."""

        quote_type = yf_data.get("quoteType", "").lower()

        # Map yfinance quote types to our categories
        category_mapping = {
            "equity": "equity",
            "etf": "etf",
            "mutualfund": "mutual_fund",
            "cryptocurrency": "cryptocurrency",
            "currency": "currency",
            "future": "futures",
            "option": "options",
        }

        category = category_mapping.get(quote_type)
        if category:
            return category

        # Fallback inference from symbol
        return self._infer_category_from_symbol(symbol)

    def _infer_category_from_symbol(self, symbol: str) -> str:
        """Infer securities security_type from symbol patterns."""

        symbol_upper = symbol.upper()

        # Cryptocurrency patterns
        if any(crypto in symbol_upper for crypto in ["BTC", "ETH", "ADA", "DOT", "-USD", "-USDT"]):
            return "cryptocurrency"

        # ETF patterns
        if any(etf in symbol_upper for etf in ["ETF", "SPY", "QQQ", "VTI", "VOO", "IVV", "IWDA"]):
            return "etf"

        # Default to equity
        return "equity"

    def _infer_currency_from_symbol(self, symbol: str) -> str:
        """Infer currency from symbol patterns."""

        symbol_upper = symbol.upper()

        # Common patterns
        if "-USD" in symbol_upper or symbol_upper.endswith("USD"):
            return "USD"
        elif "-GBP" in symbol_upper or symbol_upper.endswith("GBP"):
            return "GBP"
        elif "-EUR" in symbol_upper or symbol_upper.endswith("EUR"):
            return "EUR"

        # Default to USD
        return "USD"

    def clear_cache(self) -> None:
        """Clear internal caches and reload securities."""
        self._security_cache.clear()
        self._load_securities_for_matching()
        logger.debug("SecurityMaster matcher cache cleared and reloaded")

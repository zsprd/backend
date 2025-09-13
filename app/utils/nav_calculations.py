from datetime import date
from typing import Any, Dict, List, Optional

import pandas as pd


class NAVCalculations:
    """
    Provides methods to compute Net Asset Value (NAV) for a portfolio/account on any given day using holdings or transactions.
    Handles cash flows so that NAV is correct and returns are not distorted by deposits/withdrawals.
    """

    @staticmethod
    def compute_nav_from_holdings(
        holdings: List[Dict[str, Any]], prices: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Compute NAV from a list of holdings and (optionally) a dict of prices.
        Each holding should have 'symbol', 'quantity', and either 'market_value' or 'price'.
        If prices are provided, they override holding['price'].
        """
        nav = 0.0
        for h in holdings:
            qty = h.get("quantity", 0)
            price = None
            if prices and h["symbol"] in prices:
                price = prices[h["symbol"]]
            elif "price" in h:
                price = h["price"]
            elif "market_value" in h and qty:
                price = h["market_value"] / qty if qty else 0
            if price is not None:
                nav += qty * price
            elif "market_value" in h:
                nav += h["market_value"]
        return float(nav)

    @staticmethod
    def compute_nav_from_transactions(
        transactions: List[Dict[str, Any]], prices: Dict[str, float], as_of_date: date
    ) -> float:
        """
        Compute NAV by reconstructing the portfolio from transactions up to as_of_date, then valuing using prices.
        Transactions should have 'date', 'symbol', 'quantity', 'amount', 'type' (buy, sell, deposit, withdrawal).
        Cash is tracked as a synthetic 'CASH' symbol.
        """
        positions = {}
        cash = 0.0
        for t in transactions:
            t_date = (
                pd.to_datetime(t["date"]).date() if not isinstance(t["date"], date) else t["date"]
            )
            if t_date > as_of_date:
                continue
            t_type = t.get("type", "").lower()
            symbol = t.get("symbol")
            qty = t.get("quantity", 0)
            amt = t.get("amount", 0)
            if t_type == "buy":
                positions[symbol] = positions.get(symbol, 0) + qty
                cash -= amt
            elif t_type == "sell":
                positions[symbol] = positions.get(symbol, 0) - qty
                cash += amt
            elif t_type == "deposit":
                cash += amt
            elif t_type == "withdrawal":
                cash -= amt
        nav = cash
        for symbol, qty in positions.items():
            if symbol == "CASH":
                nav += qty
            elif symbol in prices:
                nav += qty * prices[symbol]
        return float(nav)

    @staticmethod
    def compute_time_series_nav_from_holdings(
        holdings_by_date: Dict[date, List[Dict[str, Any]]],
        prices_by_date: Dict[date, Dict[str, float]],
    ) -> pd.Series:
        """
        Compute NAV time series from holdings and prices by date.
        Returns a pd.Series indexed by date.
        """
        navs = {}
        for d, holdings in holdings_by_date.items():
            navs[d] = NAVCalculations.compute_nav_from_holdings(holdings, prices_by_date.get(d, {}))
        return pd.Series(navs)

    @staticmethod
    def compute_time_series_nav_from_transactions(
        transactions: List[Dict[str, Any]],
        prices_by_date: Dict[date, Dict[str, float]],
        date_range: List[date],
    ) -> pd.Series:
        """
        Compute NAV time series from transactions and prices by date.
        Returns a pd.Series indexed by date.
        """
        navs = {}
        for d in date_range:
            navs[d] = NAVCalculations.compute_nav_from_transactions(
                transactions, prices_by_date.get(d, {}), d
            )
        return pd.Series(navs)

from datetime import datetime, timedelta
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.holding import Holding
from app.models.market_data import MarketData
from app.models.security import Security
from app.utils.calculations import (
    calculate_beta,
    calculate_max_drawdown,
    calculate_returns,
    calculate_sharpe_ratio,
    calculate_var,
    calculate_volatility,
)


class AnalyticsService:
    """
    Service for calculating portfolio analytics including performance, risk, and allocation metrics.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_portfolio_performance(
        self,
        user_id: str,
        account_ids: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict:
        """
        Calculate comprehensive portfolio performance metrics.
        """
        if not end_date:
            end_date = datetime.now()
        if not start_date:
            start_date = end_date - timedelta(days=365)  # Default to 1 year

        # Get portfolio data
        portfolio_data = self._get_portfolio_data(
            user_id, account_ids, start_date, end_date
        )

        if portfolio_data.empty:
            return self._empty_performance_response()

        # Calculate returns
        returns = calculate_returns(portfolio_data["total_value"])

        # Performance metrics
        total_return = (
            (
                portfolio_data["total_value"].iloc[-1]
                / portfolio_data["total_value"].iloc[0]
            )
            - 1
        ) * 100
        annualized_return = (
            (
                portfolio_data["total_value"].iloc[-1]
                / portfolio_data["total_value"].iloc[0]
            )
            ** (365 / len(portfolio_data))
            - 1
        ) * 100
        volatility = calculate_volatility(returns) * 100
        sharpe_ratio = calculate_sharpe_ratio(returns)
        max_drawdown = calculate_max_drawdown(portfolio_data["total_value"]) * 100

        # Value at Risk (95% confidence)
        var_95 = calculate_var(returns, confidence=0.95) * 100

        return {
            "total_return": round(total_return, 2),
            "annualized_return": round(annualized_return, 2),
            "volatility": round(volatility, 2),
            "sharpe_ratio": round(sharpe_ratio, 3),
            "max_drawdown": round(max_drawdown, 2),
            "value_at_risk_95": round(var_95, 2),
            "current_value": float(portfolio_data["total_value"].iloc[-1]),
            "start_value": float(portfolio_data["total_value"].iloc[0]),
            "data_points": len(portfolio_data),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

    def get_risk_metrics(
        self,
        user_id: str,
        account_ids: Optional[List[str]] = None,
        benchmark_symbol: str = "SPY",
    ) -> Dict:
        """
        Calculate risk metrics including beta, correlation, and various risk measures.
        """
        # Get portfolio returns
        portfolio_data = self._get_portfolio_data(user_id, account_ids)
        if portfolio_data.empty:
            return self._empty_risk_response()

        portfolio_returns = calculate_returns(portfolio_data["total_value"])

        # Get benchmark returns
        benchmark_returns = self._get_benchmark_returns(benchmark_symbol)

        # Align data
        aligned_data = pd.concat(
            [portfolio_returns, benchmark_returns], axis=1, join="inner"
        )
        aligned_data.columns = ["portfolio", "benchmark"]

        if len(aligned_data) < 30:  # Need at least 30 data points
            return self._empty_risk_response()

        # Risk calculations
        beta = calculate_beta(aligned_data["portfolio"], aligned_data["benchmark"])
        correlation = aligned_data["portfolio"].corr(aligned_data["benchmark"])

        # Downside risk metrics
        downside_returns = portfolio_returns[portfolio_returns < 0]
        downside_deviation = (
            downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        )

        # Sortino ratio (assuming 0% risk-free rate)
        sortino_ratio = (
            (portfolio_returns.mean() * 252) / downside_deviation
            if downside_deviation > 0
            else 0
        )

        # Value at Risk at different confidence levels
        var_90 = calculate_var(portfolio_returns, confidence=0.90) * 100
        var_95 = calculate_var(portfolio_returns, confidence=0.95) * 100
        var_99 = calculate_var(portfolio_returns, confidence=0.99) * 100

        return {
            "beta": round(beta, 3),
            "correlation_with_benchmark": round(correlation, 3),
            "downside_deviation": round(downside_deviation * 100, 2),
            "sortino_ratio": round(sortino_ratio, 3),
            "value_at_risk": {
                "var_90": round(var_90, 2),
                "var_95": round(var_95, 2),
                "var_99": round(var_99, 2),
            },
            "benchmark_symbol": benchmark_symbol,
        }

    def get_allocation_breakdown(
        self, user_id: str, account_ids: Optional[List[str]] = None
    ) -> Dict:
        """
        Calculate portfolio allocation breakdown by various dimensions.
        """
        # Get current holdings with security details
        holdings_query = (
            self.db.query(Holding, Security, Account)
            .join(Security, Holding.security_id == Security.id)
            .join(Account, Holding.account_id == Account.id)
            .filter(
                Account.user_id == user_id,
                Account.is_active,
                Holding.quantity > 0,
            )
        )

        if account_ids:
            holdings_query = holdings_query.filter(Account.id.in_(account_ids))

        holdings = holdings_query.all()

        if not holdings:
            return self._empty_allocation_response()

        # Create DataFrame for easier calculations
        data = []
        for holding, security, account in holdings:
            market_value = holding.market_value or (
                holding.quantity * (holding.cost_basis_per_share or 0)
            )
            data.append(
                {
                    "security_id": security.id,
                    "symbol": security.symbol,
                    "name": security.name,
                    "type": security.type,
                    "sector": security.sector,
                    "country": security.country,
                    "currency": security.currency,
                    "market_value": market_value,
                    "account_id": account.id,
                    "account_name": account.name,
                    "account_type": account.type,
                }
            )

        df = pd.DataFrame(data)
        total_value = df["market_value"].sum()

        if total_value == 0:
            return self._empty_allocation_response()

        # Asset type allocation
        by_asset_type = df.groupby("type")["market_value"].sum().to_dict()
        by_asset_type = {
            k: round((v / total_value) * 100, 2) for k, v in by_asset_type.items()
        }

        # Sector allocation (exclude cash and other non-equity types)
        equity_df = df[df["type"].isin(["equity", "etf"])]
        if not equity_df.empty:
            by_sector = equity_df.groupby("sector")["market_value"].sum().to_dict()
            by_sector = {
                k: round((v / total_value) * 100, 2) for k, v in by_sector.items() if k
            }
        else:
            by_sector = {}

        # Geographic allocation
        by_geography = df.groupby("country")["market_value"].sum().to_dict()
        by_geography = {
            k: round((v / total_value) * 100, 2) for k, v in by_geography.items() if k
        }

        # Currency allocation
        by_currency = df.groupby("currency")["market_value"].sum().to_dict()
        by_currency = {
            k: round((v / total_value) * 100, 2) for k, v in by_currency.items()
        }

        # Account allocation
        by_account = (
            df.groupby(["account_id", "account_name"])["market_value"].sum().to_dict()
        )
        by_account_formatted = {}
        for (account_id, account_name), value in by_account.items():
            by_account_formatted[account_name] = round((value / total_value) * 100, 2)

        # Top holdings
        top_holdings = df.nlargest(10, "market_value")[
            ["symbol", "name", "market_value"]
        ].to_dict("records")
        for holding in top_holdings:
            holding["weight"] = round((holding["market_value"] / total_value) * 100, 2)

        return {
            "total_portfolio_value": round(total_value, 2),
            "by_asset_type": by_asset_type,
            "by_sector": by_sector,
            "by_geography": by_geography,
            "by_currency": by_currency,
            "by_account": by_account_formatted,
            "top_holdings": top_holdings,
            "concentration": {
                "top_5_weight": sum([h["weight"] for h in top_holdings[:5]]),
                "top_10_weight": sum([h["weight"] for h in top_holdings]),
                "number_of_positions": len(df),
            },
        }

    def _get_portfolio_data(
        self,
        user_id: str,
        account_ids: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        Get historical portfolio data for calculations.
        """
        # This is a simplified version - in production, you'd want to store
        # daily portfolio snapshots for faster calculations

        # For now, we'll calculate from current holdings and assume static allocation
        # TODO: Implement proper historical portfolio value tracking

        holdings_query = (
            self.db.query(Holding, Account)
            .join(Account, Holding.account_id == Account.id)
            .filter(Account.user_id == user_id, Account.is_active)
        )

        if account_ids:
            holdings_query = holdings_query.filter(Account.id.in_(account_ids))

        holdings = holdings_query.all()

        # Create synthetic historical data (this should be replaced with real historical snapshots)
        dates = pd.date_range(
            start=start_date or datetime.now() - timedelta(days=365),
            end=end_date or datetime.now(),
            freq="D",
        )

        total_values = []
        for date in dates:
            total_value = sum([h.market_value or 0 for h, a in holdings])
            # Add some synthetic variation (remove this in production)
            variation = np.random.normal(0, 0.02)  # 2% daily volatility
            total_value *= 1 + variation
            total_values.append(total_value)

        return pd.DataFrame({"date": dates, "total_value": total_values}).set_index(
            "date"
        )

    def _get_benchmark_returns(self, symbol: str) -> pd.Series:
        """
        Get benchmark returns for comparison.
        """
        # Get benchmark security
        benchmark = self.db.query(Security).filter(Security.symbol == symbol).first()
        if not benchmark:
            # Return empty series if benchmark not found
            return pd.Series(dtype=float)

        # Get market data
        market_data = (
            self.db.query(MarketData)
            .filter(MarketData.security_id == benchmark.id)
            .order_by(MarketData.price_date)
            .all()
        )

        if not market_data:
            return pd.Series(dtype=float)

        # Convert to DataFrame and calculate returns
        df = pd.DataFrame(
            [(md.price_date, md.close_price) for md in market_data],
            columns=["date", "close"],
        ).set_index("date")

        return calculate_returns(df["close"])

    def _empty_performance_response(self) -> Dict:
        """Return empty performance response when no data is available."""
        return {
            "total_return": 0.0,
            "annualized_return": 0.0,
            "volatility": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "value_at_risk_95": 0.0,
            "current_value": 0.0,
            "start_value": 0.0,
            "data_points": 0,
            "start_date": None,
            "end_date": None,
        }

    def _empty_risk_response(self) -> Dict:
        """Return empty risk response when no data is available."""
        return {
            "beta": 0.0,
            "correlation_with_benchmark": 0.0,
            "downside_deviation": 0.0,
            "sortino_ratio": 0.0,
            "value_at_risk": {"var_90": 0.0, "var_95": 0.0, "var_99": 0.0},
            "benchmark_symbol": "SPY",
        }

    def _empty_allocation_response(self) -> Dict:
        """Return empty allocation response when no data is available."""
        return {
            "total_portfolio_value": 0.0,
            "by_asset_type": {},
            "by_sector": {},
            "by_geography": {},
            "by_currency": {},
            "by_account": {},
            "top_holdings": [],
            "concentration": {
                "top_5_weight": 0.0,
                "top_10_weight": 0.0,
                "number_of_positions": 0,
            },
        }

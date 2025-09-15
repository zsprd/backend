from typing import Any, Dict, Optional, Union

import empyrical as ep
import numpy as np
import pandas as pd


class PerformanceCalculations:
    """
    Provides performance analytics for a portfolios, focusing on return and risk-adjusted return metrics.
    Risk metrics (drawdown, volatility, beta, etc.) are handled in calculations.py.
    """

    def __init__(
        self,
        portfolio_returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None,
        risk_free: Union[float, pd.Series] = 0.0,
    ):
        self.portfolio_returns = portfolio_returns.dropna()
        self.benchmark_returns = (
            benchmark_returns.dropna() if benchmark_returns is not None else None
        )
        self.risk_free = risk_free

    def total_return(self) -> float:
        return float(ep.cum_returns_final(self.portfolio_returns) * 100)

    def annualized_return(self) -> float:
        return float(ep.annual_return(self.portfolio_returns) * 100)

    def sharpe_ratio(self) -> float:
        return float(ep.sharpe_ratio(self.portfolio_returns, risk_free=self.risk_free))

    def sortino_ratio(self) -> float:
        return float(ep.sortino_ratio(self.portfolio_returns))

    def calmar_ratio(self) -> float:
        return float(ep.calmar_ratio(self.portfolio_returns))

    def omega_ratio(self) -> float:
        return float(ep.omega_ratio(self.portfolio_returns))

    def best_day(self) -> float:
        return float(self.portfolio_returns.max() * 100)

    def worst_day(self) -> float:
        return float(self.portfolio_returns.min() * 100)

    def alpha(self) -> Optional[float]:
        if self.benchmark_returns is not None and len(self.benchmark_returns) > 0:
            aligned = pd.concat(
                [self.portfolio_returns, self.benchmark_returns], axis=1, join="inner"
            ).dropna()
            return float(
                ep.alpha(aligned.iloc[:, 0], aligned.iloc[:, 1], risk_free=self.risk_free) * 100
            )
        return None

    def information_ratio(self) -> Optional[float]:
        if self.benchmark_returns is not None and len(self.benchmark_returns) > 0:
            aligned = pd.concat(
                [self.portfolio_returns, self.benchmark_returns], axis=1, join="inner"
            ).dropna()
            return float(ep.excess_sharpe(aligned.iloc[:, 0], aligned.iloc[:, 1]))
        return None

    def cumulative_returns(self) -> pd.Series:
        return self._cumulative_returns(self.portfolio_returns)

    def rolling_sharpe(self, window: int = 30) -> pd.Series:
        return self.portfolio_returns.rolling(window).apply(
            lambda x: ep.sharpe_ratio(x) if len(x) == window else np.nan
        )

    def rolling_annualized_return(self, window: int = 30) -> pd.Series:
        return self.portfolio_returns.rolling(window).apply(
            lambda x: ep.annual_return(x) if len(x) == window else np.nan
        )

    def monthly_returns_table(self) -> pd.DataFrame:
        """
        Returns a DataFrame of monthly returns, indexed by year and month.
        """
        monthly = (1 + self.portfolio_returns).resample("M").prod() - 1
        monthly.index = monthly.index.to_period("M")
        return monthly.to_frame("monthly_return")

    def time_series_data(self) -> Dict[str, Any]:
        return {
            "portfolio_returns": self.portfolio_returns.to_dict(),
            "cumulative_returns": self.cumulative_returns().to_dict(),
            "rolling_sharpe_30d": self.rolling_sharpe(30).to_dict(),
            "rolling_annualized_return_30d": self.rolling_annualized_return(30).to_dict(),
        }

    def benchmark_total_return(self) -> Optional[float]:
        if self.benchmark_returns is not None:
            return float(ep.cum_returns_final(self.benchmark_returns) * 100)
        return None

    def benchmark_annualized_return(self) -> Optional[float]:
        if self.benchmark_returns is not None:
            return float(ep.annual_return(self.benchmark_returns) * 100)
        return None

    def benchmark_cumulative_returns(self) -> Optional[pd.Series]:
        if self.benchmark_returns is not None:
            return self._cumulative_returns(self.benchmark_returns)
        return None

    def benchmark_monthly_returns_table(self) -> Optional[pd.DataFrame]:
        if self.benchmark_returns is not None:
            monthly = (1 + self.benchmark_returns).resample("M").prod() - 1
            monthly.index = monthly.index.to_period("M")
            return monthly.to_frame("monthly_return")
        return None

    def benchmark_best_day(self) -> Optional[float]:
        if self.benchmark_returns is not None:
            return float(self.benchmark_returns.max() * 100)
        return None

    def benchmark_worst_day(self) -> Optional[float]:
        if self.benchmark_returns is not None:
            return float(self.benchmark_returns.min() * 100)
        return None

    def outperformance_table(self) -> Optional[pd.DataFrame]:
        if self.benchmark_returns is not None:
            df = pd.DataFrame(
                {"portfolios": self.portfolio_returns, "benchmark": self.benchmark_returns}
            ).dropna()
            df["excess"] = df["portfolios"] - df["benchmark"]
            return df
        return None

    def percent_months_outperformed(self) -> Optional[float]:
        if self.benchmark_returns is not None:
            port_monthly = (1 + self.portfolio_returns).resample("M").prod() - 1
            bench_monthly = (1 + self.benchmark_returns).resample("M").prod() - 1
            df = pd.DataFrame({"portfolios": port_monthly, "benchmark": bench_monthly}).dropna()
            if len(df) == 0:
                return None
            outperf = ((df["portfolios"] > df["benchmark"]).to_numpy().astype(int)).sum()
            return float(outperf / len(df) * 100)
        return None

    def rolling_excess_return(self, window: int = 30) -> Optional[pd.Series]:
        if self.benchmark_returns is not None:
            aligned = pd.concat(
                [self.portfolio_returns, self.benchmark_returns], axis=1, join="inner"
            ).dropna()
            excess = aligned.iloc[:, 0] - aligned.iloc[:, 1]
            return excess.rolling(window).mean()
        return None

    def all_performance_analytics(self) -> Dict[str, Any]:
        analytics = {
            "total_return": self.total_return(),
            "annualized_return": self.annualized_return(),
            "sharpe_ratio": self.sharpe_ratio(),
            "sortino_ratio": self.sortino_ratio(),
            "calmar_ratio": self.calmar_ratio(),
            "omega_ratio": self.omega_ratio(),
            "best_day": self.best_day(),
            "worst_day": self.worst_day(),
            "alpha": self.alpha(),
            "information_ratio": self.information_ratio(),
            "monthly_returns_table": self.monthly_returns_table().to_dict(),
            "time_series_data": self.time_series_data(),
        }
        if self.benchmark_returns is not None:
            analytics.update(
                {
                    "benchmark_total_return": self.benchmark_total_return(),
                    "benchmark_annualized_return": self.benchmark_annualized_return(),
                    "benchmark_best_day": self.benchmark_best_day(),
                    "benchmark_worst_day": self.benchmark_worst_day(),
                    "benchmark_monthly_returns_table": (
                        self.benchmark_monthly_returns_table().to_dict()
                        if self.benchmark_monthly_returns_table() is not None
                        else {}
                    ),
                    "percent_months_outperformed": self.percent_months_outperformed(),
                    "outperformance_table": (
                        self.outperformance_table().to_dict()
                        if self.outperformance_table() is not None
                        else {}
                    ),
                    "rolling_excess_return": (
                        self.rolling_excess_return().to_dict()
                        if self.rolling_excess_return() is not None
                        else {}
                    ),
                }
            )
        return analytics

    @staticmethod
    def _cumulative_returns(returns: pd.Series) -> pd.Series:
        """Compute cumulative returns series."""
        return (1 + returns).cumprod() - 1

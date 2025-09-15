from typing import Any, Dict, Optional, Union

import empyrical as ep
import numpy as np
import pandas as pd
import pyfolio as pf


class RiskCalculations:
    """
    Provides risk analytics for a portfolios, focusing on drawdown, volatility, downside risk, tail risk, beta, tracking error, and stress tests.
    Performance metrics (returns, Sharpe, Sortino, etc.) are handled in performance_calculations.py.
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

    # --- Drawdown Analytics ---
    def max_drawdown(self) -> float:
        return float(ep.max_drawdown(self.portfolio_returns) * 100)

    def current_drawdown(self) -> float:
        dd_series = self._drawdown_series(self.portfolio_returns)
        return float(dd_series.iloc[-1] * 100) if not dd_series.empty else 0.0

    def avg_drawdown(self) -> float:
        dd_series = self._drawdown_series(self.portfolio_returns)
        return float(dd_series.mean() * 100) if not dd_series.empty else 0.0

    def max_drawdown_duration(self) -> int:
        dd_series = self._drawdown_series(self.portfolio_returns)
        if dd_series.empty:
            return 0
        in_drawdown = dd_series < 0
        max_duration = 0
        current_duration = 0
        for is_dd in in_drawdown.to_numpy():
            if is_dd:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                current_duration = 0
        return max_duration

    def drawdown_table(self) -> pd.DataFrame:
        return pf.timeseries.gen_drawdown_table(self.portfolio_returns, top=5)

    def drawdown_periods(self) -> Any:
        return pf.timeseries.get_top_drawdowns(self.portfolio_returns, top=5)

    # --- Volatility & Beta ---
    def volatility(self, annualization: int = 252) -> float:
        return float(
            ep.annual_volatility(self.portfolio_returns, annualization=annualization) * 100
        )

    def rolling_volatility(self, window: int = 63) -> pd.Series:
        return self.portfolio_returns.rolling(window).std() * (252**0.5)

    def beta(self) -> Optional[float]:
        if self.benchmark_returns is not None and len(self.benchmark_returns) > 0:
            aligned = pd.concat(
                [self.portfolio_returns, self.benchmark_returns], axis=1, join="inner"
            ).dropna()
            return float(ep.beta(aligned.iloc[:, 0], aligned.iloc[:, 1]))
        return None

    def rolling_beta(self, window: int = 63) -> Optional[pd.Series]:
        if self.benchmark_returns is None:
            return None
        aligned = pd.concat(
            [self.portfolio_returns, self.benchmark_returns], axis=1, join="inner"
        ).dropna()
        aligned.columns = ["portfolios", "benchmark"]
        return (
            aligned["portfolios"].rolling(window).cov(aligned["benchmark"])
            / aligned["benchmark"].rolling(window).var()
        )

    def correlation(self) -> Optional[float]:
        if self.benchmark_returns is not None and len(self.benchmark_returns) > 0:
            aligned = pd.concat(
                [self.portfolio_returns, self.benchmark_returns], axis=1, join="inner"
            ).dropna()
            return float(aligned.iloc[:, 0].corr(aligned.iloc[:, 1]))
        return None

    def tracking_error(self) -> Optional[float]:
        if self.benchmark_returns is not None and len(self.benchmark_returns) > 0:
            aligned = pd.concat(
                [self.portfolio_returns, self.benchmark_returns], axis=1, join="inner"
            ).dropna()
            return float(self._tracking_error(aligned.iloc[:, 0], aligned.iloc[:, 1]) * 100)
        return None

    # --- Downside & Tail Risk ---
    def downside_risk(self) -> float:
        return float(ep.downside_risk(self.portfolio_returns) * 100)

    def value_at_risk(self, level: float = 0.95) -> float:
        return float(ep.value_at_risk(self.portfolio_returns, cutoff=1 - level) * 100)

    def conditional_value_at_risk(self, level: float = 0.95) -> float:
        return float(ep.conditional_value_at_risk(self.portfolio_returns, cutoff=1 - level) * 100)

    def distribution_metrics(self) -> Dict[str, Optional[float]]:
        return {
            "skewness": float(self.portfolio_returns.skew()),
            "kurtosis": float(self.portfolio_returns.kurtosis()),
            "tail_ratio": (
                float(ep.tail_ratio(self.portfolio_returns))
                if len(self.portfolio_returns) > 252
                else None
            ),
        }

    # --- Capture Ratios ---
    def capture_ratios(self) -> Dict[str, float]:
        if self.benchmark_returns is None or len(self.benchmark_returns) == 0:
            return {"up_capture": 0.0, "downside_capture": 0.0}
        aligned = pd.concat([self.portfolio_returns, self.benchmark_returns], axis=1, join="inner")
        if len(aligned) < 30:
            return {"up_capture": 0.0, "downside_capture": 0.0}
        aligned.columns = ["portfolios", "benchmark"]
        return {
            "up_capture": float(ep.up_capture(aligned["portfolios"], aligned["benchmark"]) * 100),
            "downside_capture": float(
                ep.down_capture(aligned["portfolios"], aligned["benchmark"]) * 100
            ),
        }

    # --- Market Stress Tests ---
    def historical_stress_test(self, stress_periods: Dict[str, tuple]) -> Dict[str, Any]:
        results = {}
        for label, (start, end) in stress_periods.items():
            period_returns = self.portfolio_returns.loc[start:end]
            results[label] = {
                "max_drawdown": float(ep.max_drawdown(period_returns) * 100),
                "volatility": float(ep.annual_volatility(period_returns) * 100),
                "return": float(period_returns.sum() * 100),
            }
        return results

    def shock_scenario(self, shock_pct: float) -> float:
        shocked = self.portfolio_returns.copy()
        shocked.iloc[-1] += shock_pct
        return float(shocked.sum() * 100)

    # --- Aggregate ---
    def all_risk_analytics(self) -> Dict[str, Any]:
        analytics = {
            "drawdown": {
                "max_drawdown": self.max_drawdown(),
                "current_drawdown": self.current_drawdown(),
                "avg_drawdown": self.avg_drawdown(),
                "max_drawdown_duration": self.max_drawdown_duration(),
                "drawdown_table": self.drawdown_table().to_dict(),
                "drawdown_periods": self.drawdown_periods(),
            },
            "volatility": self.volatility(),
            "rolling_volatility": self.rolling_volatility().to_dict(),
            "beta": self.beta(),
            "rolling_beta": (
                self.rolling_beta().to_dict() if self.benchmark_returns is not None else {}
            ),
            "correlation": self.correlation(),
            "tracking_error": self.tracking_error(),
            "downside_risk": self.downside_risk(),
            "value_at_risk": self.value_at_risk(),
            "conditional_value_at_risk": self.conditional_value_at_risk(),
            "distribution": self.distribution_metrics(),
            "capture_ratios": self.capture_ratios(),
        }
        return analytics

    @staticmethod
    def _drawdown_series(returns: pd.Series) -> pd.Series:
        """Compute drawdown series as cumulative max minus current value."""
        cumulative = (1 + returns).cumprod()
        peak = cumulative.cummax()
        dd = (cumulative - peak) / peak
        return dd

    @staticmethod
    def _tracking_error(portfolio: pd.Series, benchmark: pd.Series) -> float:
        diff = portfolio - benchmark
        return np.std(diff) * np.sqrt(252)

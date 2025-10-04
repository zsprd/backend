from typing import Any, Dict

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.exposure.model import AnalyticsExposure
from app.analytics.performance.model import AnalyticsPerformance
from app.analytics.risk.model import AnalyticsRisk


class AnalyticsSummaryRepository:
    """Repository for managing analytics summary data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def get_account_analytics_summary(
        self,
        account_id: str,
    ) -> Dict[str, Any]:
        if not account_id:
            return None
        latest_performance = self.db.execute(
            select(AnalyticsPerformance)
            .where(AnalyticsPerformance.account_id == account_id)
            .order_by(desc(AnalyticsPerformance.calculation_date))
            .limit(1)
        ).scalar_one_or_none()
        latest_risk = self.db.execute(
            select(AnalyticsRisk)
            .where(AnalyticsRisk.account_id == account_id)
            .order_by(desc(AnalyticsRisk.calculation_date))
            .limit(1)
        ).scalar_one_or_none()
        latest_exposure = self.db.execute(
            select(AnalyticsExposure)
            .where(AnalyticsExposure.account_id == account_id)
            .order_by(desc(AnalyticsExposure.calculation_date))
            .limit(1)
        ).scalar_one_or_none()
        summary = {
            "key_metrics": {},
            "data_availability": {
                "has_performance_data": latest_performance is not None,
                "has_risk_data": latest_risk is not None,
                "has_exposure_data": latest_exposure is not None,
            },
        }
        if latest_performance:
            summary["key_metrics"]["performance"] = {
                "total_return": float(latest_performance.total_return),
                "annualized_return": float(latest_performance.annualized_return),
                "sharpe_ratio": float(latest_performance.sharpe_ratio or 0),
                "max_drawdown": float(latest_performance.max_drawdown),
                "last_updated": latest_performance.calculation_date.isoformat(),
            }
        if latest_risk:
            summary["key_metrics"]["risk"] = {
                "var_95": float(latest_risk.var_95),
                "downside_deviation": float(latest_risk.downside_deviation),
                "last_updated": latest_risk.calculation_date.isoformat(),
            }
        if latest_exposure:
            summary["key_metrics"]["exposure"] = {
                "total_value": float(latest_exposure.total_market_value),
                "holdings_count": latest_exposure.holdings_count,
                "top_10_weight": float(latest_exposure.top_10_weight),
                "largest_country": (
                    max(latest_exposure.allocation_by_country.items(), key=lambda x: x[1])[0]
                    if latest_exposure.allocation_by_country
                    else None
                ),
                "last_updated": latest_exposure.calculation_date.isoformat(),
            }
        return summary

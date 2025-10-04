from datetime import date, timedelta
from typing import Any, Dict, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.performance.model import AnalyticsPerformance


class AnalyticsPerformanceRepository:
    """Repository for managing analytics performance data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def get_account_performance_analytics(
        self,
        account_id: str,
        start_date: Optional[date],
        end_date: Optional[date],
        page: int,
        limit: int,
        benchmark: str,
    ) -> Dict[str, Any]:
        if not account_id:
            return None
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=730)
        query = (
            select(AnalyticsPerformance)
            .where(
                and_(
                    AnalyticsPerformance.account_id == account_id,
                    AnalyticsPerformance.calculation_date >= start_date,
                    AnalyticsPerformance.calculation_date <= end_date,
                    AnalyticsPerformance.calculation_status == "completed",
                )
            )
            .order_by(desc(AnalyticsPerformance.calculation_date))
        )
        count_query = select(func.count(AnalyticsPerformance.id)).where(
            and_(
                AnalyticsPerformance.account_id == account_id,
                AnalyticsPerformance.calculation_date >= start_date,
                AnalyticsPerformance.calculation_date <= end_date,
                AnalyticsPerformance.calculation_status == "completed",
            )
        )
        total_count = self.db.execute(count_query).scalar()
        offset = (page - 1) * limit
        paginated_query = query.offset(offset).limit(limit)
        result = self.db.execute(paginated_query)
        performance_records = list(result.scalars().all())
        if not performance_records:
            return {
                "account_id": account_id,
                "message": "No performance data available for the selected period",
                "total_records": 0,
                "page": page,
                "limit": limit,
                "total_pages": 0,
            }
        latest_record = performance_records[0]
        performance_data = {
            "current_metrics": {
                "total_return": float(latest_record.total_return),
                "annualized_return": float(latest_record.annualized_return),
                "volatility": float(latest_record.volatility),
                "sharpe_ratio": float(latest_record.sharpe_ratio or 0),
                "sortino_ratio": float(latest_record.sortino_ratio or 0),
                "calmar_ratio": float(latest_record.calmar_ratio or 0),
                "max_drawdown": float(latest_record.max_drawdown),
                "current_drawdown": float(latest_record.current_drawdown),
                "best_day": float(latest_record.best_day or 0),
                "worst_day": float(latest_record.worst_day or 0),
            },
            "benchmark_comparison": {
                "benchmark_symbol": latest_record.benchmark_symbol,
                "alpha": float(latest_record.alpha or 0),
                "beta": float(latest_record.beta or 0),
                "correlation": float(latest_record.correlation or 0),
                "tracking_error": float(latest_record.tracking_error or 0),
                "information_ratio": float(latest_record.information_ratio or 0),
            },
            "time_series": {
                "performance_history": [
                    {
                        "date": record.calculation_date.isoformat(),
                        "total_return": float(record.total_return),
                        "annualized_return": float(record.annualized_return),
                        "volatility": float(record.volatility),
                        "sharpe_ratio": float(record.sharpe_ratio or 0),
                        "max_drawdown": float(record.max_drawdown),
                        "alpha": float(record.alpha or 0),
                        "beta": float(record.beta or 0),
                    }
                    for record in performance_records
                ],
                "chart_data": (
                    latest_record.time_series_data if latest_record.time_series_data else {}
                ),
            },
            "pagination": {
                "total_records": total_count,
                "page": page,
                "limit": limit,
                "total_pages": (total_count + limit - 1) // limit,
                "has_next": page < ((total_count + limit - 1) // limit),
                "has_previous": page > 1,
            },
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "benchmark_symbol": benchmark,
            },
            "data_quality": {
                "last_updated": latest_record.updated_at.isoformat(),
                "calculation_status": latest_record.calculation_status,
                "period_days": latest_record.period_days,
            },
        }
        return performance_data

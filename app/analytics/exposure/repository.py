from datetime import date, timedelta
from typing import Any, Dict, Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.exposure.model import AnalyticsExposure


class AnalyticsExposureRepository:
    """Repository for managing analytics exposure data."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def get_account_exposure_analytics(
        self,
        account_id: str,
        start_date: Optional[date],
        end_date: Optional[date],
        page: int,
        limit: int,
    ) -> Dict[str, Any]:
        if not account_id:
            return None
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=730)
        query = (
            select(AnalyticsExposure)
            .where(
                and_(
                    AnalyticsExposure.account_id == account_id,
                    AnalyticsExposure.calculation_date >= start_date,
                    AnalyticsExposure.calculation_date <= end_date,
                    AnalyticsExposure.calculation_status == "completed",
                )
            )
            .order_by(desc(AnalyticsExposure.calculation_date))
        )
        count_query = select(func.count(AnalyticsExposure.id)).where(
            and_(
                AnalyticsExposure.account_id == account_id,
                AnalyticsExposure.calculation_date >= start_date,
                AnalyticsExposure.calculation_date <= end_date,
                AnalyticsExposure.calculation_status == "completed",
            )
        )
        total_count = self.db.execute(count_query).scalar()
        offset = (page - 1) * limit
        paginated_query = query.offset(offset).limit(limit)
        result = self.db.execute(paginated_query)
        exposure_records = list(result.scalars().all())
        if not exposure_records:
            return {
                "account_id": account_id,
                "message": "No exposure data available for the selected period",
                "total_records": 0,
            }
        latest_record = exposure_records[0]
        exposure_data = {
            "current_allocation": {
                "by_asset_class": latest_record.allocation_by_asset_class,
                "by_sector": latest_record.allocation_by_sector,
                "by_country": latest_record.allocation_by_country,
                "by_region": latest_record.allocation_by_region,
                "by_currency": latest_record.allocation_by_currency,
            },
            "concentration_metrics": {
                "top_5_weight": float(latest_record.top_5_weight),
                "top_10_weight": float(latest_record.top_10_weight),
                "largest_position_weight": float(latest_record.largest_position_weight),
                "herfindahl_index": float(latest_record.herfindahl_index),
            },
            "top_holdings": latest_record.top_holdings,
            "visualization_data": {
                "asset_class_donut": [
                    {
                        "name": asset_class,
                        "value": percentage,
                        "tooltip": f"{asset_class}: {percentage:.1f}%",
                    }
                    for asset_class, percentage in latest_record.allocation_by_asset_class.items()
                ],
                "sector_bar_chart": [
                    {
                        "sector": sector,
                        "percentage": percentage,
                        "value": (percentage / 100) * float(latest_record.total_market_value),
                    }
                    for sector, percentage in latest_record.allocation_by_sector.items()
                ],
                "geographic_map": [
                    {
                        "country": country,
                        "percentage": percentage,
                        "value": (percentage / 100) * float(latest_record.total_market_value),
                    }
                    for country, percentage in latest_record.allocation_by_country.items()
                ],
                "holdings_treemap": latest_record.top_holdings.get("holdings", [])[:15],
            },
            "time_series": {
                "allocation_history": [
                    {
                        "date": record.calculation_date.isoformat(),
                        "total_value": float(record.total_market_value),
                        "holdings_count": record.holdings_count,
                        "top_10_weight": float(record.top_10_weight),
                        "herfindahl_index": float(record.herfindahl_index),
                        "by_asset_class": record.allocation_by_asset_class,
                        "by_sector": record.allocation_by_sector,
                    }
                    for record in exposure_records
                ]
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
            },
        }
        return exposure_data

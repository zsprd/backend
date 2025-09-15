from datetime import date

from sqlalchemy import and_, desc, func, select
from sqlalchemy.orm import Session

from app.analytics.risk.model import AnalyticsRisk


def get_account_risk_analytics(
    db: Session,
    account_id: str,
    start_date: date,
    end_date: date,
    page: int,
    limit: int,
):
    query = (
        select(AnalyticsRisk)
        .where(
            and_(
                AnalyticsRisk.account_id == account_id,
                AnalyticsRisk.calculation_date >= start_date,
                AnalyticsRisk.calculation_date <= end_date,
                AnalyticsRisk.calculation_status == "completed",
            )
        )
        .order_by(desc(AnalyticsRisk.calculation_date))
    )
    count_query = select(func.count(AnalyticsRisk.id)).where(
        and_(
            AnalyticsRisk.account_id == account_id,
            AnalyticsRisk.calculation_date >= start_date,
            AnalyticsRisk.calculation_date <= end_date,
            AnalyticsRisk.calculation_status == "completed",
        )
    )
    total_count = db.execute(count_query).scalar()
    offset = (page - 1) * limit
    paginated_query = query.offset(offset).limit(limit)
    result = db.execute(paginated_query)
    risk_records = list(result.scalars().all())
    return risk_records, total_count

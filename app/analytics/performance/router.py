from datetime import date
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.analytics.performance.crud import get_account_performance_analytics
from app.core.database import get_db

router = APIRouter()


@router.get("/performance/accounts/{account_id}")
async def get_performance_analytics(
    *,
    db: Session = Depends(get_db),
    account_id: str = Path(..., description="PortfolioAccount ID for performance analysis"),
    start_date: Optional[date] = Query(None, description="Start date for analysis period"),
    end_date: Optional[date] = Query(None, description="End date for analysis period"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=500, description="Records per page"),
    benchmark: str = Query("SPY", description="Benchmark symbol for comparison"),
) -> Dict[str, Any]:
    """
    📊 PERFORMANCE ANALYTICS ENDPOINT
    Returns paginated historical performance analytics for visualization.
    """
    try:
        result = get_account_performance_analytics(
            db=db,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            limit=limit,
            benchmark=benchmark,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="PortfolioAccount not found")
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving performance analytics: {str(e)}"
        )

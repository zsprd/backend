from datetime import date
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.analytics.risk.repository import get_account_risk_analytics
from app.core.database import get_db

router = APIRouter()


@router.get("/risk/accounts/{account_id}")
async def get_risk_analytics(
    *,
    db: Session = Depends(get_db),
    account_id: str = Path(..., description="PortfolioAccount ID for risk analysis"),
    start_date: Optional[date] = Query(None, description="Start date for analysis period"),
    end_date: Optional[date] = Query(None, description="End date for analysis period"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=500, description="Records per page"),
    confidence_level: float = Query(95.0, description="VaR confidence level (90, 95, 99)"),
) -> Dict[str, Any]:
    """
    ⚠️ RISK ANALYTICS ENDPOINT
    Returns paginated historical risk analytics for visualization.
    """
    try:
        result = get_account_risk_analytics(
            db=db,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            limit=limit,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving risk analytics: {str(e)}")

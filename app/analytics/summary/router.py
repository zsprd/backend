from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session

from app.analytics.summary.repository import get_account_analytics_summary
from app.core.database import get_db

router = APIRouter()


@router.get("/summary/accounts/{account_id}")
async def get_analytics_summary(
    *,
    db: Session = Depends(get_db),
    account_id: str = Path(..., description="PortfolioAccount ID for summary"),
) -> Dict[str, Any]:
    """
    📊 ANALYTICS SUMMARY ENDPOINT
    Returns high-level analytics summary for dashboard overview cards.
    """
    try:
        result = get_account_analytics_summary(
            db=db,
            account_id=account_id,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="PortfolioAccount not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving analytics summary: {str(e)}")

from datetime import date
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.analytics_exposure import get_account_exposure_analytics
from app.crud.analytics_performance import get_account_performance_analytics
from app.crud.analytics_risk import get_account_risk_analytics
from app.crud.analytics_summary import get_account_analytics_summary

router = APIRouter()


@router.get("/summary/accounts/{account_id}")
async def get_analytics_summary(
    *,
    db: Session = Depends(get_db),
    account_id: str = Path(..., description="Account ID for summary"),
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
            raise HTTPException(status_code=404, detail="Account not found")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving analytics summary: {str(e)}")


@router.get("/exposure/accounts/{account_id}")
async def get_exposure_analytics(
    *,
    db: Session = Depends(get_db),
    account_id: str = Path(..., description="Account ID for exposure analysis"),
    start_date: Optional[date] = Query(None, description="Start date for analysis period"),
    end_date: Optional[date] = Query(None, description="End date for analysis period"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=500, description="Records per page"),
) -> Dict[str, Any]:
    """
    🌍 EXPOSURE ANALYTICS ENDPOINT
    Returns paginated historical exposure analytics for visualization.
    """
    try:
        result = get_account_exposure_analytics(
            db=db,
            account_id=account_id,
            start_date=start_date,
            end_date=end_date,
            page=page,
            limit=limit,
        )
        if result is None:
            raise HTTPException(status_code=404, detail="Account not found")
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving exposure analytics: {str(e)}"
        )


@router.get("/performance/accounts/{account_id}")
async def get_performance_analytics(
    *,
    db: Session = Depends(get_db),
    account_id: str = Path(..., description="Account ID for performance analysis"),
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
            raise HTTPException(status_code=404, detail="Account not found")
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error retrieving performance analytics: {str(e)}"
        )


@router.get("/risk/accounts/{account_id}")
async def get_risk_analytics(
    *,
    db: Session = Depends(get_db),
    account_id: str = Path(..., description="Account ID for risk analysis"),
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

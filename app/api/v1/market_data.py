from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.auth import get_current_user_id
from app.models.market_data import MarketData
from app.models.security import Security
from app.utils.alpha_vantage import get_market_data_service
from app.crud.base import CRUDBase

router = APIRouter()


@router.get("/securities/{security_id}/prices")
async def get_security_prices(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    security_id: str,
    start_date: Optional[datetime] = Query(None, description="Start date for price data"),
    end_date: Optional[datetime] = Query(None, description="End date for price data"),
    limit: int = Query(100, description="Maximum number of data points")
):
    """
    Get historical price data for a specific security.
    """
    # Verify security exists
    security = db.query(Security).filter(Security.id == security_id).first()
    if not security:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security not found"
        )
    
    # Build query for market data
    query = db.query(MarketData).filter(MarketData.security_id == security_id)
    
    if start_date:
        query = query.filter(MarketData.date >= start_date.date())
    
    if end_date:
        query = query.filter(MarketData.date <= end_date.date())
    
    # Get data ordered by date (most recent first)
    market_data = query.order_by(MarketData.date.desc()).limit(limit).all()
    
    # Format response
    price_data = []
    for data_point in market_data:
        price_data.append({
            "date": data_point.date.isoformat(),
            "open": float(data_point.open) if data_point.open else None,
            "high": float(data_point.high) if data_point.high else None,
            "low": float(data_point.low) if data_point.low else None,
            "close": float(data_point.close),
            "adjusted_close": float(data_point.adjusted_close) if data_point.adjusted_close else None,
            "volume": data_point.volume,
            "currency": data_point.currency
        })
    
    return {
        "security_id": security_id,
        "symbol": security.symbol,
        "name": security.name,
        "currency": security.currency,
        "data_points": len(price_data),
        "prices": price_data
    }


@router.get("/securities/{security_id}/latest-price")
async def get_latest_price(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    security_id: str
):
    """
    Get the latest price for a specific security.
    """
    # Verify security exists
    security = db.query(Security).filter(Security.id == security_id).first()
    if not security:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security not found"
        )
    
    # Get latest price
    latest_data = db.query(MarketData).filter(
        MarketData.security_id == security_id
    ).order_by(MarketData.date.desc()).first()
    
    if not latest_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No price data available for this security"
        )
    
    return {
        "security_id": security_id,
        "symbol": security.symbol,
        "name": security.name,
        "date": latest_data.date.isoformat(),
        "price": float(latest_data.close),
        "adjusted_price": float(latest_data.adjusted_close) if latest_data.adjusted_close else None,
        "currency": latest_data.currency,
        "volume": latest_data.volume,
        "source": latest_data.source
    }


@router.post("/securities/{security_id}/refresh")
async def refresh_security_data(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    security_id: str,
    background_tasks: BackgroundTasks,
    force: bool = Query(False, description="Force refresh even if data is recent")
):
    """
    Refresh market data for a specific security from Alpha Vantage.
    This runs in the background to avoid blocking the request.
    """
    # Verify security exists
    security = db.query(Security).filter(Security.id == security_id).first()
    if not security:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Security not found"
        )
    
    # Add background task to refresh data
    market_data_service = get_market_data_service(db)
    background_tasks.add_task(
        market_data_service.update_security_data,
        security_id,
        force
    )
    
    return {
        "message": f"Market data refresh initiated for {security.symbol}",
        "security_id": security_id,
        "symbol": security.symbol,
        "status": "pending"
    }


@router.post("/refresh-all")
async def refresh_all_securities(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    background_tasks: BackgroundTasks,
    max_age_days: int = Query(1, description="Refresh securities with data older than N days")
):
    """
    Refresh market data for all securities that need updating.
    This is useful for batch updates and maintenance.
    """
    # Find securities that need updating
    cutoff_date = datetime.now().date() - timedelta(days=max_age_days)
    
    # Get securities with old or missing data
    securities_to_update = db.query(Security).outerjoin(MarketData).filter(
        Security.is_active == True
    ).filter(
        (MarketData.date < cutoff_date) | (MarketData.date.is_(None))
    ).distinct().all()
    
    security_ids = [str(s.id) for s in securities_to_update]
    
    # Add background task for bulk update
    market_data_service = get_market_data_service(db)
    background_tasks.add_task(
        market_data_service.bulk_update_securities,
        security_ids
    )
    
    return {
        "message": f"Initiated refresh for {len(security_ids)} securities",
        "securities_count": len(security_ids),
        "max_age_days": max_age_days,
        "status": "pending"
    }


@router.get("/search/{query}")
async def search_securities(
    *,
    db: Session = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    query: str,
    limit: int = Query(10, description="Maximum number of results")
):
    """
    Search for securities by symbol or name.
    """
    # Search in local database first
    securities = db.query(Security).filter(
        (Security.symbol.ilike(f"%{query}%")) |
        (Security.name.ilike(f"%{query}%"))
    ).filter(Security.is_active == True).limit(limit).all()
    
    results = []
    for security in securities:
        # Get latest price if available
        latest_price = db.query(MarketData).filter(
            MarketData.security_id == security.id
        ).order_by(MarketData.date.desc()).first()
        
        results.append({
            "id": str(security.id),
            "symbol": security.symbol,
            "name": security.name,
            "type": security.type,
            "currency": security.currency,
            "exchange": security.exchange,
            "sector": security.sector,
            "latest_price": float(latest_price.close) if latest_price else None,
            "latest_date": latest_price.date.isoformat() if latest_price else None
        })
    
    return {
        "query": query,
        "results_count": len(results),
        "results": results
    }


@router.get("/health")
async def market_data_health():
    """
    Health check for market data service.
    """
    return {
        "status": "healthy",
        "service": "market_data",
        "timestamp": datetime.utcnow(),
        "features": [
            "price_history",
            "latest_prices", 
            "alpha_vantage_integration",
            "background_refresh",
            "security_search"
        ]
    }
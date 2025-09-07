from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc, asc
from datetime import date, datetime, timedelta

from app.crud.base import CRUDBase
from app.models.market_data import MarketData, ExchangeRate
from app.models.security import Security
from app.schemas.market_data import MarketDataCreate, MarketDataUpdate, ExchangeRateCreate


class CRUDMarketData(CRUDBase[MarketData, MarketDataCreate, MarketDataUpdate]):
    def get_by_security(
        self,
        db: Session,
        *,
        security_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None
    ) -> List[MarketData]:
        """Get market data for a specific security."""
        query = db.query(MarketData).filter(MarketData.security_id == security_id)
        
        if start_date:
            query = query.filter(MarketData.date >= start_date)
        if end_date:
            query = query.filter(MarketData.date <= end_date)
        
        query = query.order_by(desc(MarketData.date))
        
        if limit:
            query = query.limit(limit)
        
        return query.all()

    def get_latest_price(
        self,
        db: Session,
        *,
        security_id: str
    ) -> Optional[MarketData]:
        """Get the latest price for a security."""
        return db.query(MarketData).filter(
            MarketData.security_id == security_id
        ).order_by(desc(MarketData.date)).first()

    def get_latest_prices_bulk(
        self,
        db: Session,
        *,
        security_ids: List[str]
    ) -> List[MarketData]:
        """Get latest prices for multiple securities."""
        # Get the latest date for each security
        subquery = db.query(
            MarketData.security_id,
            func.max(MarketData.date).label('max_date')
        ).filter(
            MarketData.security_id.in_(security_ids)
        ).group_by(MarketData.security_id).subquery()
        
        # Join to get the actual records
        return db.query(MarketData).join(
            subquery,
            and_(
                MarketData.security_id == subquery.c.security_id,
                MarketData.date == subquery.c.max_date
            )
        ).all()

    def get_price_on_date(
        self,
        db: Session,
        *,
        security_id: str,
        target_date: date
    ) -> Optional[MarketData]:
        """Get price for a security on a specific date, or closest available."""
        # Try exact date first
        exact_match = db.query(MarketData).filter(
            and_(
                MarketData.security_id == security_id,
                MarketData.date == target_date
            )
        ).first()
        
        if exact_match:
            return exact_match
        
        # If no exact match, get the closest date before
        return db.query(MarketData).filter(
            and_(
                MarketData.security_id == security_id,
                MarketData.date <= target_date
            )
        ).order_by(desc(MarketData.date)).first()

    def get_price_history(
        self,
        db: Session,
        *,
        security_id: str,
        days: int = 365
    ) -> List[MarketData]:
        """Get price history for the last N days."""
        start_date = date.today() - timedelta(days=days)
        return self.get_by_security(
            db,
            security_id=security_id,
            start_date=start_date
        )

    def calculate_returns(
        self,
        db: Session,
        *,
        security_id: str,
        periods: List[int] = [1, 7, 30, 90, 365]
    ) -> Dict[str, Optional[float]]:
        """Calculate returns for various periods."""
        current_price = self.get_latest_price(db, security_id=security_id)
        if not current_price:
            return {f"return_{p}d": None for p in periods}
        
        returns = {}
        current_close = float(current_price.close)
        
        for period in periods:
            historical_date = date.today() - timedelta(days=period)
            historical_price = self.get_price_on_date(
                db, security_id=security_id, target_date=historical_date
            )
            
            if historical_price:
                historical_close = float(historical_price.close)
                if historical_close > 0:
                    return_pct = ((current_close - historical_close) / historical_close) * 100
                    returns[f"return_{period}d"] = return_pct
                else:
                    returns[f"return_{period}d"] = None
            else:
                returns[f"return_{period}d"] = None
        
        return returns

    def get_volatility(
        self,
        db: Session,
        *,
        security_id: str,
        days: int = 30
    ) -> Optional[float]:
        """Calculate volatility over the specified period."""
        price_data = self.get_price_history(db, security_id=security_id, days=days)
        
        if len(price_data) < 2:
            return None
        
        # Calculate daily returns
        returns = []
        for i in range(1, len(price_data)):
            prev_price = float(price_data[i].close)
            curr_price = float(price_data[i-1].close)  # Note: data is in desc order
            
            if prev_price > 0:
                daily_return = (curr_price - prev_price) / prev_price
                returns.append(daily_return)
        
        if not returns:
            return None
        
        # Calculate standard deviation and annualize
        import statistics
        import math
        
        volatility = statistics.stdev(returns) * math.sqrt(252)  # Annualized
        return volatility * 100  # Convert to percentage

    def get_securities_needing_update(
        self,
        db: Session,
        *,
        max_age_days: int = 1,
        limit: int = 100
    ) -> List[str]:
        """Get security IDs that need market data updates."""
        cutoff_date = date.today() - timedelta(days=max_age_days)
        
        # Get securities with old or missing data
        subquery = db.query(MarketData.security_id).filter(
            MarketData.date >= cutoff_date
        ).subquery()
        
        securities_needing_update = db.query(Security.id).filter(
            and_(
                Security.is_active == True,
                ~Security.id.in_(subquery)
            )
        ).limit(limit).all()
        
        return [str(s.id) for s in securities_needing_update]

    def bulk_create_or_update(
        self,
        db: Session,
        *,
        market_data_list: List[Dict[str, Any]]
    ) -> List[MarketData]:
        """Bulk create or update market data records."""
        created_records = []
        
        for data in market_data_list:
            try:
                # Check if record exists
                existing = db.query(MarketData).filter(
                    and_(
                        MarketData.security_id == data["security_id"],
                        MarketData.date == data["date"]
                    )
                ).first()
                
                if existing:
                    # Update existing record
                    for key, value in data.items():
                        if key not in ["id", "security_id", "date", "created_at"]:
                            setattr(existing, key, value)
                    db.add(existing)
                    created_records.append(existing)
                else:
                    # Create new record
                    record = self.create_from_dict(db, obj_in=data)
                    created_records.append(record)
                    
            except Exception as e:
                print(f"Error processing market data: {e}")
                continue
        
        return created_records

    def get_market_summary(
        self,
        db: Session,
        *,
        target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get market summary for a specific date."""
        if not target_date:
            target_date = date.today()
        
        # Get all market data for the date
        market_data = db.query(MarketData).filter(
            MarketData.date == target_date
        ).all()
        
        if not market_data:
            return {"date": target_date, "message": "No market data available"}
        
        total_securities = len(market_data)
        
        # Calculate price changes (vs previous day)
        previous_date = target_date - timedelta(days=1)
        price_changes = []
        
        for data in market_data:
            prev_data = self.get_price_on_date(
                db, security_id=data.security_id, target_date=previous_date
            )
            
            if prev_data:
                current_price = float(data.close)
                prev_price = float(prev_data.close)
                
                if prev_price > 0:
                    change_pct = ((current_price - prev_price) / prev_price) * 100
                    price_changes.append(change_pct)
        
        # Summary statistics
        gainers = [c for c in price_changes if c > 0]
        losers = [c for c in price_changes if c < 0]
        
        return {
            "date": target_date,
            "total_securities": total_securities,
            "securities_with_changes": len(price_changes),
            "gainers": len(gainers),
            "losers": len(losers),
            "unchanged": total_securities - len(price_changes),
            "avg_change": sum(price_changes) / len(price_changes) if price_changes else 0
        }

    def delete_old_data(
        self,
        db: Session,
        *,
        older_than_days: int = 730  # 2 years
    ) -> int:
        """Delete market data older than specified days."""
        cutoff_date = date.today() - timedelta(days=older_than_days)
        
        deleted_count = db.query(MarketData).filter(
            MarketData.date < cutoff_date
        ).delete()
        
        db.commit()
        return deleted_count


class CRUDExchangeRate(CRUDBase[ExchangeRate, ExchangeRateCreate, None]):
    def get_rate(
        self,
        db: Session,
        *,
        base_currency: str,
        quote_currency: str,
        target_date: Optional[date] = None
    ) -> Optional[ExchangeRate]:
        """Get exchange rate for a currency pair on a specific date."""
        if not target_date:
            target_date = date.today()
        
        # Try exact date first
        exact_match = db.query(ExchangeRate).filter(
            and_(
                ExchangeRate.base_currency == base_currency,
                ExchangeRate.quote_currency == quote_currency,
                ExchangeRate.date == target_date
            )
        ).first()
        
        if exact_match:
            return exact_match
        
        # Get closest date before
        return db.query(ExchangeRate).filter(
            and_(
                ExchangeRate.base_currency == base_currency,
                ExchangeRate.quote_currency == quote_currency,
                ExchangeRate.date <= target_date
            )
        ).order_by(desc(ExchangeRate.date)).first()

    def get_latest_rates(
        self,
        db: Session,
        *,
        base_currency: str
    ) -> List[ExchangeRate]:
        """Get latest exchange rates for a base currency."""
        subquery = db.query(
            ExchangeRate.quote_currency,
            func.max(ExchangeRate.date).label('max_date')
        ).filter(
            ExchangeRate.base_currency == base_currency
        ).group_by(ExchangeRate.quote_currency).subquery()
        
        return db.query(ExchangeRate).join(
            subquery,
            and_(
                ExchangeRate.quote_currency == subquery.c.quote_currency,
                ExchangeRate.date == subquery.c.max_date
            )
        ).filter(ExchangeRate.base_currency == base_currency).all()


# Create instances
market_data_crud = CRUDMarketData(MarketData)
exchange_rate_crud = CRUDExchangeRate(ExchangeRate)
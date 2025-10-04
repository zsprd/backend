from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from app.core.repository import BaseRepository
from app.security.master.model import Security
from app.security.prices.model import SecurityPrice
from app.security.prices.schemas import (
    MarketDataCreate,
    MarketDataUpdate,
)


class MarketDataRepository(BaseRepository[SecurityPrice, MarketDataCreate, MarketDataUpdate]):

    def get_by_security(
        self,
        db: Session,
        *,
        security_id: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: Optional[int] = None,
    ) -> List[SecurityPrice]:
        """Get market data for a specific securities."""
        query = db.query(SecurityPrice).filter(SecurityPrice.security_id == security_id)

        if start_date:
            query = query.filter(SecurityPrice.price_date >= start_date)
        if end_date:
            query = query.filter(SecurityPrice.price_date <= end_date)

        query = query.order_by(desc(SecurityPrice.price_date))

        if limit:
            query = query.limit(limit)
        return query.scalars().all()

    def get_latest_price(self, db: Session, *, security_id: str) -> Optional[MarketData]:
        """Get the latest price for a securities."""
        return (
            db.query(SecurityPrice)
            .filter(SecurityPrice.security_id == security_id)
            .order_by(desc(SecurityPrice.price_date))
            .first()
        )

    def get_latest_prices_bulk(
        self, db: Session, *, security_ids: List[str]
    ) -> List[SecurityPrice]:
        """Get latest prices for multiple securities."""
        # Get the latest date for each securities
        subquery = (
            db.query(
                SecurityPrice.security_id,
                func.max(SecurityPrice.price_date).label("max_date"),
            )
            .filter(SecurityPrice.security_id.in_(security_ids))
            .group_by(SecurityPrice.security_id)
            .subquery()
        )

        # Join to get the actual records
        return (
            db.query(SecurityPrice)
            .join(
                subquery,
                and_(
                    SecurityPrice.security_id == subquery.c.security_id,
                    SecurityPrice.price_date == subquery.c.max_date,
                ),
            )
            .scalars()
            .all()
        )

    def get_price_on_date(
        self, db: Session, *, security_id: str, target_date: date
    ) -> Optional[SecurityPrice]:
        """Get price for a securities on a specific date, or closest available."""
        # Try exact date first
        exact_match = (
            db.query(SecurityPrice)
            .filter(
                and_(
                    SecurityPrice.security_id == security_id,
                    SecurityPrice.price_date == target_date,
                )
            )
            .first()
        )

        if exact_match:
            return exact_match

        # If no exact match, get the closest date before
        return (
            db.query(SecurityPrice)
            .filter(
                and_(
                    SecurityPrice.security_id == security_id,
                    SecurityPrice.price_date <= target_date,
                )
            )
            .order_by(desc(SecurityPrice.price_date))
            .first()
        )

    def get_price_history(
        self, db: Session, *, security_id: str, days: int = 365
    ) -> List[SecurityPrice]:
        """Get price history for the last N days."""
        start_date = date.today() - timedelta(days=days)
        return self.get_by_security(db, security_id=security_id, start_date=start_date)

    def calculate_returns(
        self, db: Session, *, security_id: str, periods: Optional[List[int]] = None
    ) -> Dict[str, Optional[float]]:
        """Calculate returns for various periods."""
        if periods is None:
            periods = [1, 7, 30, 90, 365]
        current_price = self.get_latest_price(db, security_id=security_id)
        if not current_price:
            return {f"return_{p}d": None for p in periods}

        returns = {}
        current_close = float(current_price.close_price)

        for period in periods:
            historical_date = date.today() - timedelta(days=period)
            historical_price = self.get_price_on_date(
                db, security_id=security_id, target_date=historical_date
            )

            if historical_price:
                historical_close = float(historical_price.close_price)
                if historical_close > 0:
                    return_pct = ((current_close - historical_close) / historical_close) * 100
                    returns[f"return_{period}d"] = return_pct
                else:
                    returns[f"return_{period}d"] = None
            else:
                returns[f"return_{period}d"] = None

        return returns

    def get_volatility(self, db: Session, *, security_id: str, days: int = 30) -> Optional[float]:
        """Calculate volatility over the specified period."""
        price_data = self.get_price_history(db, security_id=security_id, days=days)

        if len(price_data) < 2:
            return None

        # Calculate daily returns
        returns = []
        for i in range(1, len(price_data)):
            prev_price = float(price_data[i].close_price)
            curr_price = float(price_data[i - 1].close_price)  # Note: data is in desc order

            if prev_price > 0:
                daily_return = (curr_price - prev_price) / prev_price
                returns.append(daily_return)

        if not returns:
            return None

        # Calculate standard deviation and annualize
        import math
        import statistics

        volatility = statistics.stdev(returns) * math.sqrt(252)  # Annualized
        return volatility * 100  # Convert to percentage

    def get_securities_needing_update(
        self, db: Session, *, max_age_days: int = 1, limit: int = 100
    ) -> List[str]:
        """Get securities IDs that need market data updates."""
        cutoff_date = date.today() - timedelta(days=max_age_days)

        # Get securities with old or missing data
        subquery = (
            db.query(SecurityPrice.security_id)
            .filter(SecurityPrice.price_date >= cutoff_date)
            .subquery()
        )

        securities_needing_update = (
            db.query(Security.id)
            .filter(and_(Security.is_active, ~Security.id.in_(subquery)))
            .limit(limit)
            .all()
        )

        return [str(s.id) for s in securities_needing_update]

    def bulk_create_or_update(
        self, db: Session, *, market_data_list: List[Dict[str, Any]]
    ) -> List[SecurityPrice]:
        """Bulk create or update market data records."""
        created_records = []

        for data in market_data_list:
            try:
                # Check if record exists
                existing = (
                    db.query(SecurityPrice)
                    .filter(
                        and_(
                            SecurityPrice.security_id == data["security_id"],
                            SecurityPrice.price_date == data["price_date"],
                        )
                    )
                    .first()
                )

                if existing:
                    # Update existing record
                    for key, value in data.items():
                        if key not in ["id", "security_id", "price_date", "created_at"]:
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
        self, db: Session, *, target_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get market summary for a specific date."""
        if not target_date:
            target_date = date.today()

        # Get all market data for the date
        market_data = db.query(SecurityPrice).filter(SecurityPrice.price_date == target_date).all()

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
                current_price = float(data.close_price)
                prev_price = float(prev_data.close_price)

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
            "avg_change": (sum(price_changes) / len(price_changes) if price_changes else 0),
        }

    def delete_old_data(self, db: Session, *, older_than_days: int = 730) -> int:  # 2 years
        """Delete market data older than specified days."""
        cutoff_date = date.today() - timedelta(days=older_than_days)

        deleted_count = (
            db.query(SecurityPrice).filter(SecurityPrice.price_date < cutoff_date).delete()
        )

        db.commit()
        return deleted_count

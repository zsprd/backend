from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from app.crud.base import CRUDBase
from app.models.security import Security
from app.models.market_data import MarketData
from app.schemas.security import SecurityCreate, SecurityUpdate


class CRUDSecurity(CRUDBase[Security, SecurityCreate, SecurityUpdate]):
    def get_by_symbol(
        self, 
        db: Session, 
        *, 
        symbol: str, 
        currency: str = "USD"
    ) -> Optional[Security]:
        """Get security by symbol and currency."""
        return db.query(Security).filter(
            and_(
                Security.symbol == symbol.upper(),
                Security.currency == currency,
                Security.is_active == True
            )
        ).first()

    def get_by_symbol_any_currency(
        self, 
        db: Session, 
        *, 
        symbol: str
    ) -> List[Security]:
        """Get securities by symbol across all currencies."""
        return db.query(Security).filter(
            and_(
                Security.symbol == symbol.upper(),
                Security.is_active == True
            )
        ).all()

    def search_securities(
        self,
        db: Session,
        *,
        query: str,
        security_types: Optional[List[str]] = None,
        currencies: Optional[List[str]] = None,
        exchanges: Optional[List[str]] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Security]:
        """Search securities by symbol, name, or other criteria."""
        db_query = db.query(Security).filter(Security.is_active == True)
        
        # Text search on symbol and name
        if query:
            search_term = f"%{query.upper()}%"
            db_query = db_query.filter(
                or_(
                    Security.symbol.ilike(search_term),
                    Security.name.ilike(search_term)
                )
            )
        
        # Filter by security types
        if security_types:
            db_query = db_query.filter(Security.type.in_(security_types))
        
        # Filter by currencies
        if currencies:
            db_query = db_query.filter(Security.currency.in_(currencies))
        
        # Filter by exchanges
        if exchanges:
            db_query = db_query.filter(Security.exchange.in_(exchanges))
        
        # Order by relevance (exact symbol match first, then alphabetical)
        if query:
            db_query = db_query.order_by(
                Security.symbol == query.upper(),
                Security.symbol
            )
        else:
            db_query = db_query.order_by(Security.symbol)
        
        return db_query.offset(skip).limit(limit).all()

    def get_by_sector(
        self,
        db: Session,
        *,
        sector: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Security]:
        """Get securities by sector."""
        return db.query(Security).filter(
            and_(
                Security.sector == sector,
                Security.is_active == True
            )
        ).offset(skip).limit(limit).all()

    def get_by_exchange(
        self,
        db: Session,
        *,
        exchange: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Security]:
        """Get securities by exchange."""
        return db.query(Security).filter(
            and_(
                Security.exchange == exchange,
                Security.is_active == True
            )
        ).offset(skip).limit(limit).all()

    def get_by_type(
        self,
        db: Session,
        *,
        security_type: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Security]:
        """Get securities by type."""
        return db.query(Security).filter(
            and_(
                Security.type == security_type,
                Security.is_active == True
            )
        ).offset(skip).limit(limit).all()

    def get_with_recent_data(
        self,
        db: Session,
        *,
        days: int = 30,
        skip: int = 0,
        limit: int = 100
    ) -> List[Security]:
        """Get securities that have recent market data."""
        from datetime import date, timedelta
        cutoff_date = date.today() - timedelta(days=days)
        
        return db.query(Security).join(MarketData).filter(
            and_(
                Security.is_active == True,
                MarketData.date >= cutoff_date
            )
        ).distinct().offset(skip).limit(limit).all()

    def get_without_recent_data(
        self,
        db: Session,
        *,
        days: int = 7,
        skip: int = 0,
        limit: int = 100
    ) -> List[Security]:
        """Get securities that lack recent market data."""
        from datetime import date, timedelta
        cutoff_date = date.today() - timedelta(days=days)
        
        # Get securities without any recent data
        subquery = db.query(MarketData.security_id).filter(
            MarketData.date >= cutoff_date
        ).subquery()
        
        return db.query(Security).filter(
            and_(
                Security.is_active == True,
                ~Security.id.in_(subquery)
            )
        ).offset(skip).limit(limit).all()

    def get_by_plaid_id(
        self, 
        db: Session, 
        *, 
        plaid_security_id: str
    ) -> Optional[Security]:
        """Get security by Plaid security ID."""
        return db.query(Security).filter(
            Security.plaid_security_id == plaid_security_id
        ).first()

    def get_by_identifier(
        self,
        db: Session,
        *,
        identifier_type: str,
        identifier_value: str
    ) -> Optional[Security]:
        """Get security by various identifiers (CUSIP, ISIN, SEDOL)."""
        if identifier_type.upper() == "CUSIP":
            return db.query(Security).filter(Security.cusip == identifier_value).first()
        elif identifier_type.upper() == "ISIN":
            return db.query(Security).filter(Security.isin == identifier_value).first()
        elif identifier_type.upper() == "SEDOL":
            return db.query(Security).filter(Security.sedol == identifier_value).first()
        else:
            return None

    def get_securities_stats(self, db: Session) -> Dict[str, Any]:
        """Get statistics about securities in the database."""
        total_securities = db.query(Security).filter(Security.is_active == True).count()
        
        # Count by type
        by_type = {}
        type_counts = db.query(
            Security.type, 
            func.count(Security.id)
        ).filter(Security.is_active == True).group_by(Security.type).all()
        
        for sec_type, count in type_counts:
            by_type[sec_type] = count
        
        # Count by currency
        by_currency = {}
        currency_counts = db.query(
            Security.currency,
            func.count(Security.id)
        ).filter(Security.is_active == True).group_by(Security.currency).all()
        
        for currency, count in currency_counts:
            by_currency[currency] = count
        
        # Count by exchange
        by_exchange = {}
        exchange_counts = db.query(
            Security.exchange,
            func.count(Security.id)
        ).filter(
            and_(Security.is_active == True, Security.exchange.isnot(None))
        ).group_by(Security.exchange).all()
        
        for exchange, count in exchange_counts:
            if exchange:
                by_exchange[exchange] = count
        
        return {
            "total_securities": total_securities,
            "by_type": by_type,
            "by_currency": by_currency,
            "by_exchange": by_exchange
        }

    def create_or_update_by_symbol(
        self,
        db: Session,
        *,
        symbol: str,
        security_data: Dict[str, Any]
    ) -> Security:
        """Create a new security or update existing one by symbol."""
        existing = self.get_by_symbol(
            db, 
            symbol=symbol, 
            currency=security_data.get("currency", "USD")
        )
        
        if existing:
            # Update existing security
            return self.update(db, db_obj=existing, obj_in=security_data)
        else:
            # Create new security
            security_data["symbol"] = symbol.upper()
            return self.create_from_dict(db, obj_in=security_data)

    def bulk_create_or_update(
        self,
        db: Session,
        *,
        securities_data: List[Dict[str, Any]]
    ) -> List[Security]:
        """Bulk create or update securities."""
        created_securities = []
        
        for security_data in securities_data:
            try:
                symbol = security_data.get("symbol")
                if symbol:
                    security = self.create_or_update_by_symbol(
                        db, symbol=symbol, security_data=security_data
                    )
                    created_securities.append(security)
            except Exception as e:
                # Log error but continue with other securities
                print(f"Error processing security {security_data.get('symbol', 'unknown')}: {e}")
                continue
        
        return created_securities

    def deactivate_security(
        self, 
        db: Session, 
        *, 
        security_id: str
    ) -> Optional[Security]:
        """Deactivate a security (soft delete)."""
        security = self.get(db, id=security_id)
        if security:
            security.is_active = False
            db.add(security)
            db.commit()
            db.refresh(security)
        return security

    def get_popular_securities(
        self,
        db: Session,
        *,
        limit: int = 50
    ) -> List[Security]:
        """Get popular securities based on usage in portfolios."""
        # This would typically join with holdings to find most held securities
        # For now, return securities with recent market data
        from datetime import date, timedelta
        recent_date = date.today() - timedelta(days=30)
        
        return db.query(Security).join(MarketData).filter(
            and_(
                Security.is_active == True,
                MarketData.date >= recent_date
            )
        ).distinct().limit(limit).all()


# Create instance
security_crud = CRUDSecurity(Security)
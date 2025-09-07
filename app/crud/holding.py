from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, desc
from datetime import date

from app.crud.base import CRUDBase
from app.models.holding import Holding, Position
from app.models.security import Security
from app.models.account import Account
from app.schemas.holding import HoldingCreate, HoldingUpdate, PositionCreate, PositionUpdate


class CRUDHolding(CRUDBase[Holding, HoldingCreate, HoldingUpdate]):
    def get_by_account(
        self,
        db: Session,
        *,
        account_id: str,
        as_of_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Holding]:
        """Get holdings for a specific account."""
        query = db.query(Holding).options(
            joinedload(Holding.security)
        ).filter(Holding.account_id == account_id)
        
        if as_of_date:
            query = query.filter(Holding.as_of_date == as_of_date)
        else:
            # Get latest holdings for each security
            subquery = db.query(
                Holding.security_id,
                func.max(Holding.as_of_date).label('max_date')
            ).filter(
                Holding.account_id == account_id
            ).group_by(Holding.security_id).subquery()
            
            query = query.join(
                subquery,
                and_(
                    Holding.security_id == subquery.c.security_id,
                    Holding.as_of_date == subquery.c.max_date
                )
            )
        
        return query.offset(skip).limit(limit).all()

    def get_by_user_accounts(
        self,
        db: Session,
        *,
        user_id: str,
        account_ids: Optional[List[str]] = None,
        as_of_date: Optional[date] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Holding]:
        """Get holdings across multiple accounts for a user."""
        query = db.query(Holding).options(
            joinedload(Holding.security)
        ).join(Account).filter(Account.user_id == user_id)
        
        if account_ids:
            query = query.filter(Holding.account_id.in_(account_ids))
        
        if as_of_date:
            query = query.filter(Holding.as_of_date == as_of_date)
        else:
            # Get latest holdings for each account/security combination
            subquery = db.query(
                Holding.account_id,
                Holding.security_id,
                func.max(Holding.as_of_date).label('max_date')
            ).join(Account).filter(Account.user_id == user_id)
            
            if account_ids:
                subquery = subquery.filter(Holding.account_id.in_(account_ids))
            
            subquery = subquery.group_by(
                Holding.account_id, Holding.security_id
            ).subquery()
            
            query = query.join(
                subquery,
                and_(
                    Holding.account_id == subquery.c.account_id,
                    Holding.security_id == subquery.c.security_id,
                    Holding.as_of_date == subquery.c.max_date
                )
            )
        
        return query.offset(skip).limit(limit).all()

    def get_by_security(
        self,
        db: Session,
        *,
        security_id: str,
        user_id: str,
        as_of_date: Optional[date] = None
    ) -> List[Holding]:
        """Get all holdings of a specific security for a user."""
        query = db.query(Holding).join(Account).filter(
            and_(
                Holding.security_id == security_id,
                Account.user_id == user_id
            )
        )
        
        if as_of_date:
            query = query.filter(Holding.as_of_date == as_of_date)
        
        return query.all()

    def get_portfolio_summary(
        self,
        db: Session,
        *,
        user_id: str,
        account_ids: Optional[List[str]] = None,
        base_currency: str = "USD"
    ) -> Dict[str, Any]:
        """Get portfolio summary with totals and breakdowns."""
        holdings = self.get_by_user_accounts(
            db, user_id=user_id, account_ids=account_ids
        )
        
        if not holdings:
            return {
                "total_holdings": 0,
                "total_market_value": 0.0,
                "total_cost_basis": 0.0,
                "by_asset_type": {},
                "by_sector": {},
                "by_currency": {}
            }
        
        total_market_value = sum([
            float(h.market_value or 0) for h in holdings
        ])
        total_cost_basis = sum([
            float(h.cost_basis_total or 0) for h in holdings
        ])
        
        # Asset type breakdown
        by_asset_type = {}
        by_sector = {}
        by_currency = {}
        
        for holding in holdings:
            if holding.security:
                # Asset type
                asset_type = holding.security.type
                market_val = float(holding.market_value or 0)
                by_asset_type[asset_type] = by_asset_type.get(asset_type, 0) + market_val
                
                # Sector (if applicable)
                if holding.security.sector:
                    sector = holding.security.sector
                    by_sector[sector] = by_sector.get(sector, 0) + market_val
                
                # Currency
                currency = holding.currency
                by_currency[currency] = by_currency.get(currency, 0) + market_val
        
        return {
            "total_holdings": len(holdings),
            "total_market_value": total_market_value,
            "total_cost_basis": total_cost_basis,
            "total_unrealized_gain_loss": total_market_value - total_cost_basis,
            "by_asset_type": by_asset_type,
            "by_sector": by_sector,
            "by_currency": by_currency
        }

    def update_market_values(
        self,
        db: Session,
        *,
        holding_id: str,
        market_value: float,
        current_price: float
    ) -> Optional[Holding]:
        """Update market value and price for a holding."""
        holding = self.get(db, id=holding_id)
        if holding:
            holding.market_value = market_value
            # You might want to store current price in a separate field
            db.add(holding)
            db.commit()
            db.refresh(holding)
        return holding

    def create_bulk(
        self,
        db: Session,
        *,
        holdings_data: List[Dict[str, Any]],
        replace_existing: bool = False
    ) -> List[Holding]:
        """Create multiple holdings in bulk."""
        created_holdings = []
        
        for holding_data in holdings_data:
            if replace_existing:
                # Check if holding exists for same account/security/date
                existing = db.query(Holding).filter(
                    and_(
                        Holding.account_id == holding_data["account_id"],
                        Holding.security_id == holding_data["security_id"],
                        Holding.as_of_date == holding_data["as_of_date"]
                    )
                ).first()
                
                if existing:
                    # Update existing
                    for key, value in holding_data.items():
                        if key != "id":
                            setattr(existing, key, value)
                    db.add(existing)
                    created_holdings.append(existing)
                    continue
            
            # Create new holding
            holding = self.create_from_dict(db, obj_in=holding_data)
            created_holdings.append(holding)
        
        return created_holdings


class CRUDPosition(CRUDBase[Position, PositionCreate, PositionUpdate]):
    def get_by_account(
        self,
        db: Session,
        *,
        account_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Position]:
        """Get all positions for an account."""
        return db.query(Position).options(
            joinedload(Position.security)
        ).filter(
            Position.account_id == account_id
        ).offset(skip).limit(limit).all()

    def get_by_user_accounts(
        self,
        db: Session,
        *,
        user_id: str,
        account_ids: Optional[List[str]] = None
    ) -> List[Position]:
        """Get positions across user's accounts."""
        query = db.query(Position).options(
            joinedload(Position.security)
        ).join(Account).filter(Account.user_id == user_id)
        
        if account_ids:
            query = query.filter(Position.account_id.in_(account_ids))
        
        return query.all()

    def get_by_security(
        self,
        db: Session,
        *,
        account_id: str,
        security_id: str
    ) -> Optional[Position]:
        """Get position for specific account and security."""
        return db.query(Position).filter(
            and_(
                Position.account_id == account_id,
                Position.security_id == security_id
            )
        ).first()

    def update_position(
        self,
        db: Session,
        *,
        account_id: str,
        security_id: str,
        quantity_change: float,
        price: float,
        transaction_type: str
    ) -> Position:
        """Update position based on transaction."""
        position = self.get_by_security(
            db, account_id=account_id, security_id=security_id
        )
        
        if not position:
            # Create new position
            position_data = {
                "account_id": account_id,
                "security_id": security_id,
                "quantity": quantity_change,
                "average_cost": price,
                "unrealized_gain_loss": 0.0
            }
            position = self.create_from_dict(db, obj_in=position_data)
        else:
            # Update existing position
            if transaction_type in ["buy", "transfer_in"]:
                # Calculate new average cost
                total_cost = (float(position.quantity) * float(position.average_cost or 0) + 
                             quantity_change * price)
                new_quantity = float(position.quantity) + quantity_change
                
                if new_quantity > 0:
                    position.average_cost = total_cost / new_quantity
                    position.quantity = new_quantity
                else:
                    # Position closed
                    position.quantity = 0
                    position.average_cost = 0
                    
            elif transaction_type in ["sell", "transfer_out"]:
                position.quantity = float(position.quantity) - quantity_change
                
                if position.quantity <= 0:
                    # Position closed or negative
                    position.quantity = 0
                    position.average_cost = 0
            
            db.add(position)
            db.commit()
            db.refresh(position)
        
        return position


# Create instances
holding_crud = CRUDHolding(Holding)
position_crud = CRUDPosition(Position)
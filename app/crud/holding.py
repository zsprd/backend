from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, func, desc
from datetime import date, datetime
from decimal import Decimal

from app.crud.base import CRUDBase
from app.models.holding import Holding
from app.schemas.holding import HoldingCreate, HoldingUpdate


class CRUDHolding(CRUDBase[Holding, HoldingCreate, HoldingUpdate]):
    def get_by_account(
        self,
        db: Session,
        *,
        account_id: str,
        as_of_date: Optional[date] = None
    ) -> List[Holding]:
        """Get holdings for a specific account."""
        query = db.query(Holding).options(joinedload(Holding.security)).filter(
            Holding.account_id == account_id
        )
        
        if as_of_date:
            query = query.filter(Holding.as_of_date <= as_of_date)
        
        return query.order_by(desc(Holding.as_of_date)).all()

    def get_by_user_accounts(
        self,
        db: Session,
        *,
        user_id: str,
        account_ids: Optional[List[str]] = None,
        as_of_date: Optional[date] = None
    ) -> List[Holding]:
        """Get holdings across multiple accounts for a user."""
        from app.models.account import Account
        
        query = db.query(Holding).options(joinedload(Holding.security)).join(Account).filter(
            Account.user_id == user_id
        )
        
        if account_ids:
            query = query.filter(Holding.account_id.in_(account_ids))
        
        if as_of_date:
            query = query.filter(Holding.as_of_date <= as_of_date)
        
        return query.order_by(desc(Holding.as_of_date)).all()

    def get_by_security(
        self,
        db: Session,
        *,
        security_id: str,
        user_id: str
    ) -> List[Holding]:
        """Get all holdings for a specific security owned by user."""
        from app.models.account import Account
        
        return db.query(Holding).options(joinedload(Holding.security)).join(Account).filter(
            and_(
                Holding.security_id == security_id,
                Account.user_id == user_id
            )
        ).all()

    def get_latest_by_account_and_security(
        self,
        db: Session,
        *,
        account_id: str,
        security_id: str
    ) -> Optional[Holding]:
        """Get the most recent holding for an account/security combination."""
        return db.query(Holding).filter(
            and_(
                Holding.account_id == account_id,
                Holding.security_id == security_id
            )
        ).order_by(desc(Holding.as_of_date)).first()

    def get_holdings_summary(
        self,
        db: Session,
        *,
        account_id: str,
        base_currency: str = "USD"
    ) -> Dict[str, Any]:
        """Get holdings summary for an account."""
        holdings = self.get_by_account(db, account_id=account_id)
        
        total_market_value = sum(h.market_value or Decimal('0') for h in holdings)
        total_cost_basis = sum(h.cost_basis_total or Decimal('0') for h in holdings)
        unrealized_gain_loss = total_market_value - total_cost_basis
        unrealized_gain_loss_percent = (unrealized_gain_loss / total_cost_basis * 100) if total_cost_basis > 0 else Decimal('0')
        
        # Group by asset type
        by_asset_type = {}
        by_sector = {}
        
        for holding in holdings:
            if holding.security:
                # By asset type
                asset_type = holding.security.security_category
                if asset_type not in by_asset_type:
                    by_asset_type[asset_type] = Decimal('0')
                by_asset_type[asset_type] += (holding.market_value or Decimal('0'))
                
                # By sector
                sector = holding.security.sector or "Other"
                if sector not in by_sector:
                    by_sector[sector] = Decimal('0')
                by_sector[sector] += (holding.market_value or Decimal('0'))
        
        # Convert to percentages
        if total_market_value > 0:
            by_asset_type = {k: float(v / total_market_value * 100) for k, v in by_asset_type.items()}
            by_sector = {k: float(v / total_market_value * 100) for k, v in by_sector.items()}
        
        return {
            "account_id": account_id,
            "total_holdings": len(holdings),
            "total_market_value": total_market_value,
            "total_cost_basis": total_cost_basis,
            "total_unrealized_gain_loss": unrealized_gain_loss,
            "total_unrealized_gain_loss_percent": unrealized_gain_loss_percent,
            "base_currency": base_currency,
            "by_asset_type": by_asset_type,
            "by_sector": by_sector,
            "by_geography": {"US": 100.0},  # Simplified for now
            "as_of_date": date.today()
        }


# Create instance
holding_crud = CRUDHolding(Holding)
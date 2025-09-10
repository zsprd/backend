from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, ilike

from app.crud.base import CRUDBase
from app.models.security import Security
from app.schemas.security import SecurityCreate, SecurityUpdate


class CRUDSecurity(CRUDBase[Security, SecurityCreate, SecurityUpdate]):
    def search_securities(
        self,
        db: Session,
        *,
        query: str,
        limit: int = 50
    ) -> List[Security]:
        """Search securities by symbol or name."""
        return db.query(Security).filter(
            and_(
                Security.is_active == True,
                or_(
                    Security.symbol.ilike(f"%{query}%"),
                    Security.name.ilike(f"%{query}%")
                )
            )
        ).limit(limit).all()

    def get_by_symbol(self, db: Session, *, symbol: str) -> Optional[Security]:
        """Get security by symbol."""
        return db.query(Security).filter(
            and_(Security.symbol == symbol.upper(), Security.is_active == True)
        ).first()

    def get_by_category(self, db: Session, *, category: str) -> List[Security]:
        """Get securities by category."""
        return db.query(Security).filter(
            and_(Security.security_category == category, Security.is_active == True)
        ).all()


# Create instance
security_crud = CRUDSecurity(Security)
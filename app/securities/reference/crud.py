from typing import List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.crud import CRUDBase
from app.securities.reference.model import SecurityReference
from app.securities.reference.schema import SecurityCreate, SecurityUpdate


class CRUDSecurity(CRUDBase[SecurityReference, SecurityCreate, SecurityUpdate]):

    def search_securities(
        self, db: Session, *, query: str, limit: int = 50
    ) -> List[SecurityReference]:
        """Search securities by symbol or name."""
        stmt = (
            select(SecurityReference)
            .where(
                and_(
                    SecurityReference.is_active,
                    or_(
                        SecurityReference.symbol.ilike(f"%{query}%"),
                        SecurityReference.name.ilike(f"%{query}%"),
                    ),
                )
            )
            .limit(limit)
        )

        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_by_symbol(self, db: Session, *, symbol: str) -> Optional[SecurityReference]:
        """Get securities by symbol."""
        stmt = select(SecurityReference).where(
            and_(SecurityReference.symbol == symbol.upper(), SecurityReference.is_active)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_category(self, db: Session, *, category: str) -> List[SecurityReference]:
        """Get securities by security_type."""
        stmt = select(SecurityReference).where(
            and_(SecurityReference.security_type == category, SecurityReference.is_active)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())


# Create instance
security_crud = CRUDSecurity(SecurityReference)

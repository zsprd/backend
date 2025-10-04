from typing import List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.repository import BaseRepository
from app.security.master.model import Security
from app.security.master.schemas import SecurityCreate, SecurityUpdate


class SecurityRepository(BaseRepository[Security, SecurityCreate, SecurityUpdate]):

    def search_securities(self, db: Session, *, query: str, limit: int = 50) -> List[Security]:
        """Search securities by symbol or name."""
        stmt = (
            select(Security)
            .where(
                and_(
                    Security.is_active,
                    or_(
                        Security.symbol.ilike(f"%{query}%"),
                        Security.name.ilike(f"%{query}%"),
                    ),
                )
            )
            .limit(limit)
        )

        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_by_symbol(self, db: Session, *, symbol: str) -> Optional[Security]:
        """Get securities by symbol."""
        stmt = select(Security).where(and_(Security.symbol == symbol.upper(), Security.is_active))
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_category(self, db: Session, *, category: str) -> List[Security]:
        """Get securities by security_type."""
        stmt = select(Security).where(and_(Security.security_type == category, Security.is_active))
        result = db.execute(stmt)
        return list(result.scalars().all())


# Create instance
security_crud = SecurityRepository(Security)

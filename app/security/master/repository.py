from typing import List, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.core.repository import BaseRepository
from app.security.master.model import SecurityMaster
from app.security.master.schemas import SecurityCreate, SecurityUpdate


class SecurityRepository(BaseRepository[SecurityMaster, SecurityCreate, SecurityUpdate]):

    def search_securities(
        self, db: Session, *, query: str, limit: int = 50
    ) -> List[SecurityMaster]:
        """Search securities by symbol or name."""
        stmt = (
            select(SecurityMaster)
            .where(
                and_(
                    SecurityMaster.is_active,
                    or_(
                        SecurityMaster.symbol.ilike(f"%{query}%"),
                        SecurityMaster.name.ilike(f"%{query}%"),
                    ),
                )
            )
            .limit(limit)
        )

        result = db.execute(stmt)
        return list(result.scalars().all())

    def get_by_symbol(self, db: Session, *, symbol: str) -> Optional[SecurityMaster]:
        """Get securities by symbol."""
        stmt = select(SecurityMaster).where(
            and_(SecurityMaster.symbol == symbol.upper(), SecurityMaster.is_active)
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_by_category(self, db: Session, *, category: str) -> List[SecurityMaster]:
        """Get securities by security_type."""
        stmt = select(SecurityMaster).where(
            and_(SecurityMaster.security_type == category, SecurityMaster.is_active)
        )
        result = db.execute(stmt)
        return list(result.scalars().all())


# Create instance
security_crud = SecurityRepository(SecurityMaster)

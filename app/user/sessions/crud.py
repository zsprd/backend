from datetime import datetime, timezone
from typing import Optional, Union
from uuid import UUID as UUIDType

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.crud import CRUDBase
from app.user.sessions.model import UserSession
from app.user.sessions.schema import UserSessionCreate, UserSessionUpdate


class CRUDUserSession(CRUDBase[UserSession, UserSessionCreate, UserSessionUpdate]):
    """CRUD operations for UserSession model with proper typing."""

    @staticmethod
    def _to_uuid(value: Union[str, UUIDType]) -> UUIDType:
        if isinstance(value, UUIDType):
            return value
        return UUIDType(str(value))

    async def create_session(
        self,
        db: AsyncSession,
        user_id: str,
        refresh_token: str,
        expires_at: datetime,
        ip_address: str,
        user_agent: str,
    ) -> UserSession:
        session = UserSession(
            user_id=user_id,
            refresh_token=refresh_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            created_at=datetime.now(timezone.utc),
        )
        db.add(session)
        await db.commit()
        await db.refresh(session)
        return session

    async def get_active_session_by_token(
        self, db: AsyncSession, refresh_token: str
    ) -> Optional[UserSession]:
        result = await db.execute(
            select(UserSession).where(
                UserSession.refresh_token == refresh_token,
                UserSession.expires_at > datetime.now(timezone.utc),
                UserSession.is_revoked == False,
            )
        )
        return result.scalar_one_or_none()

    async def revoke_session_by_token(self, db: AsyncSession, refresh_token: str):
        result = await db.execute(
            select(UserSession).where(UserSession.refresh_token == refresh_token)
        )
        session = result.scalar_one_or_none()
        if session:
            session.is_revoked = True
            session.revoked_at = datetime.now(timezone.utc)
            db.add(session)
            await db.commit()

    async def revoke_all_user_sessions(self, db: AsyncSession, user_id: str):
        result = await db.execute(
            select(UserSession).where(
                UserSession.user_id == user_id, UserSession.is_revoked == False
            )
        )
        sessions = result.scalars().all()
        for session in sessions:
            session.is_revoked = True
            session.revoked_at = datetime.now(timezone.utc)
            db.add(session)
        await db.commit()


# Create instance
user_session_crud = CRUDUserSession(UserSession)

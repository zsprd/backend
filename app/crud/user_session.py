from datetime import datetime, timezone
from typing import List, Optional, Union
from uuid import UUID as UUIDType

from sqlalchemy import and_, delete, func, select
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.users.session import UserSession
from app.schemas.users import UserSessionCreate, UserSessionUpdate


class CRUDUserSession(CRUDBase[UserSession, UserSessionCreate, UserSessionUpdate]):
    """CRUD operations for UserSession model with proper typing."""

    @staticmethod
    def _to_uuid(value: Union[str, UUIDType]) -> UUIDType:
        if isinstance(value, UUIDType):
            return value
        return UUIDType(str(value))

    def create_session(
        self,
        db: Session,
        *,
        user_id: Union[str, UUIDType],
        refresh_token: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_type: Optional[str] = "web",
    ) -> UserSession:
        """Create new users session."""
        session = UserSession(
            user_id=self._to_uuid(user_id),
            refresh_token=refresh_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=device_type,
            last_used_at=datetime.now(timezone.utc),
        )

        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def get_active_session_by_token(
        self, db: Session, *, refresh_token: str
    ) -> Optional[UserSession]:
        """Get active session by refresh token using SQLAlchemy 2.0 syntax."""
        stmt = select(UserSession).where(
            and_(
                UserSession.refresh_token == refresh_token,
                UserSession.expires_at > datetime.now(timezone.utc),
            )
        )
        result = db.execute(stmt)
        return result.scalar_one_or_none()

    def get_user_sessions(
        self,
        db: Session,
        *,
        user_id: Union[str, UUIDType],
        active_only: bool = True,
        limit: int = 10,
    ) -> List[UserSession]:
        """Get users sessions with optional filtering."""
        user_uuid = self._to_uuid(user_id)
        stmt = select(UserSession).where(UserSession.user_id == user_uuid)

        if active_only:
            stmt = stmt.where(UserSession.expires_at > datetime.now(timezone.utc))

        stmt = stmt.order_by(UserSession.last_used_at.desc()).limit(limit)
        result = db.execute(stmt)
        return list(result.scalars().all())

    def update_last_used(self, db: Session, *, session: UserSession) -> UserSession:
        """Update session last used timestamp."""
        session.last_used_at = datetime.now(timezone.utc)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def update_last_used_by_token(
        self, db: Session, *, refresh_token: str
    ) -> Optional[UserSession]:
        """Update session last used timestamp by token."""
        session = self.get_active_session_by_token(db, refresh_token=refresh_token)
        if session:
            return self.update_last_used(db, session=session)
        return None

    def revoke_session(self, db: Session, *, session_id: Union[str, UUIDType]) -> bool:
        """Revoke specific session using SQLAlchemy 2.0 syntax."""
        session_uuid = self._to_uuid(session_id)
        stmt = delete(UserSession).where(UserSession.id == session_uuid)
        result = db.execute(stmt)
        db.commit()
        return result.rowcount > 0

    def revoke_session_by_token(self, db: Session, *, refresh_token: str) -> bool:
        """Revoke session by refresh token using SQLAlchemy 2.0 syntax."""
        stmt = delete(UserSession).where(UserSession.refresh_token == refresh_token)
        result = db.execute(stmt)
        db.commit()
        return result.rowcount > 0

    def revoke_all_user_sessions(self, db: Session, *, user_id: Union[str, UUIDType]) -> int:
        """Revoke all sessions for a users using SQLAlchemy 2.0 syntax."""
        user_uuid = self._to_uuid(user_id)
        # First count the sessions
        count_stmt = select(func.count(UserSession.id)).where(UserSession.user_id == user_uuid)
        count_result = db.execute(count_stmt)
        count = count_result.scalar() or 0

        # Delete all sessions
        delete_stmt = delete(UserSession).where(UserSession.user_id == user_uuid)
        db.execute(delete_stmt)
        db.commit()

        return count

    def revoke_other_sessions(
        self, db: Session, *, user_id: Union[str, UUIDType], current_refresh_token: str
    ) -> int:
        """Revoke all users sessions except current one."""
        user_uuid = self._to_uuid(user_id)
        count_stmt = select(func.count(UserSession.id)).where(
            and_(
                UserSession.user_id == user_uuid,
                UserSession.refresh_token != current_refresh_token,
            )
        )
        count_result = db.execute(count_stmt)
        count = count_result.scalar() or 0

        delete_stmt = delete(UserSession).where(
            and_(
                UserSession.user_id == user_uuid,
                UserSession.refresh_token != current_refresh_token,
            )
        )
        db.execute(delete_stmt)
        db.commit()

        return count

    def cleanup_expired_sessions(self, db: Session) -> int:
        """Clean up expired sessions using SQLAlchemy 2.0 syntax."""
        # Count expired sessions
        now = datetime.now(timezone.utc)
        count_stmt = select(func.count(UserSession.id)).where(UserSession.expires_at <= now)
        count_result = db.execute(count_stmt)
        count = count_result.scalar() or 0

        # Delete expired sessions
        delete_stmt = delete(UserSession).where(UserSession.expires_at <= now)
        db.execute(delete_stmt)
        db.commit()

        return count

    def get_session_stats(self, db: Session, *, user_id: Union[str, UUIDType]) -> dict:
        """Get session statistics for a users."""
        user_uuid = self._to_uuid(user_id)
        total_stmt = select(func.count(UserSession.id)).where(UserSession.user_id == user_uuid)
        total_result = db.execute(total_stmt)
        total_sessions = total_result.scalar() or 0

        active_stmt = select(func.count(UserSession.id)).where(
            and_(
                UserSession.user_id == user_uuid,
                UserSession.expires_at > datetime.now(timezone.utc),
            )
        )
        active_result = db.execute(active_stmt)
        active_sessions = active_result.scalar() or 0

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "expired_sessions": total_sessions - active_sessions,
        }

    def get_all_session_stats(self, db: Session) -> dict:
        """Get global session statistics."""
        total_stmt = select(func.count(UserSession.id))
        total_result = db.execute(total_stmt)
        total_sessions = total_result.scalar() or 0

        active_stmt = select(func.count(UserSession.id)).where(
            UserSession.expires_at > datetime.now(timezone.utc)
        )
        active_result = db.execute(active_stmt)
        active_sessions = active_result.scalar() or 0

        # Get unique active users
        unique_users_stmt = select(func.count(func.distinct(UserSession.user_id))).where(
            UserSession.expires_at > datetime.now(timezone.utc)
        )
        unique_users_result = db.execute(unique_users_stmt)
        unique_active_users = unique_users_result.scalar() or 0

        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "expired_sessions": total_sessions - active_sessions,
            "unique_active_users": unique_active_users,
        }

    def get_sessions_by_device_type(
        self, db: Session, *, user_id: Union[str, UUIDType], device_type: str
    ) -> List[UserSession]:
        """Get sessions filtered by device type."""
        user_uuid = self._to_uuid(user_id)
        stmt = (
            select(UserSession)
            .where(
                and_(
                    UserSession.user_id == user_uuid,
                    UserSession.device_type == device_type,
                    UserSession.expires_at > datetime.now(timezone.utc),
                )
            )
            .order_by(UserSession.last_used_at.desc())
        )

        result = db.execute(stmt)
        return list(result.scalars().all())


# Create instance
user_session_crud = CRUDUserSession(UserSession)

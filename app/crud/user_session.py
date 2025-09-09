from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.crud.base import CRUDBase
from app.models.user_session import UserSession


class CRUDUserSession(CRUDBase[UserSession, None, None]):
    """CRUD operations for UserSession model."""

    def create_session(
        self,
        db: Session,
        *,
        user_id: str,
        refresh_token: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        device_type: Optional[str] = "web"
    ) -> UserSession:
        """Create new user session."""
        session = UserSession(
            user_id=user_id,
            refresh_token=refresh_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=device_type,
            last_used_at=datetime.now(timezone.utc)
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def get_active_session_by_token(
        self, 
        db: Session, 
        *, 
        refresh_token: str
    ) -> Optional[UserSession]:
        """Get active session by refresh token."""
        return db.query(UserSession).filter(
            and_(
                UserSession.refresh_token == refresh_token,
                UserSession.expires_at > datetime.now(timezone.utc)
            )
        ).first()

    def update_last_used(
        self,
        db: Session,
        *,
        session: UserSession
    ) -> UserSession:
        """Update session last used timestamp."""
        session.last_used_at = datetime.now(timezone.utc)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def revoke_session(self, db: Session, *, session_id: str) -> bool:
        """Revoke specific session."""
        session = self.get(db, id=session_id)
        if session:
            db.delete(session)
            db.commit()
            return True
        return False

    def revoke_session_by_token(self, db: Session, *, refresh_token: str) -> bool:
        """Revoke session by refresh token."""
        session = db.query(UserSession).filter(
            UserSession.refresh_token == refresh_token
        ).first()
        
        if session:
            db.delete(session)
            db.commit()
            return True
        return False

    def revoke_all_user_sessions(self, db: Session, *, user_id: str) -> int:
        """Revoke all sessions for a user."""
        count = db.query(UserSession).filter(
            UserSession.user_id == user_id
        ).count()
        
        db.query(UserSession).filter(
            UserSession.user_id == user_id
        ).delete()
        
        db.commit()
        return count

    def cleanup_expired_sessions(self, db: Session) -> int:
        """Clean up expired sessions."""
        count = db.query(UserSession).filter(
            UserSession.expires_at < datetime.now(timezone.utc)
        ).count()
        
        db.query(UserSession).filter(
            UserSession.expires_at < datetime.now(timezone.utc)
        ).delete()
        
        db.commit()
        return count


user_session_crud = CRUDUserSession(UserSession)
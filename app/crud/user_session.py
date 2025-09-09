from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.crud.base import CRUDBase
from app.models.user_session import UserSession


class CRUDUserSession(CRUDBase[UserSession, None, None]):
    """
    CRUD operations for UserSession model.
    Manages refresh tokens and user session tracking.
    """

    def create_session(
        self,
        db: Session,
        *,
        user_id: str,
        refresh_token: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserSession:
        """
        Create a new user session with refresh token.
        
        Args:
            user_id: User's ID
            refresh_token: Refresh token string
            expires_at: When the refresh token expires
            ip_address: Client IP address
            user_agent: Client user agent string
        """
        # Generate a session token for additional security
        session_token = f"session_{refresh_token[:16]}"
        
        session = UserSession(
            user_id=user_id,
            session_token=session_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            last_accessed_at=datetime.utcnow()
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
        """
        Get active session by refresh token.
        Returns None if token is invalid or expired.
        """
        return db.query(UserSession).filter(
            and_(
                UserSession.refresh_token == refresh_token,
                UserSession.expires_at > datetime.utcnow()
            )
        ).first()

    def get_session_by_token(
        self, 
        db: Session, 
        *, 
        session_token: str
    ) -> Optional[UserSession]:
        """Get session by session token."""
        return db.query(UserSession).filter(
            UserSession.session_token == session_token
        ).first()

    def get_user_sessions(
        self, 
        db: Session, 
        *, 
        user_id: str,
        active_only: bool = True
    ) -> List[UserSession]:
        """
        Get all sessions for a user.
        
        Args:
            user_id: User's ID
            active_only: Only return non-expired sessions
        """
        query = db.query(UserSession).filter(UserSession.user_id == user_id)
        
        if active_only:
            query = query.filter(UserSession.expires_at > datetime.utcnow())
        
        return query.order_by(UserSession.last_accessed_at.desc()).all()

    def update_session(
        self,
        db: Session,
        *,
        session: UserSession,
        refresh_token: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        update_last_accessed: bool = True
    ) -> UserSession:
        """
        Update session with new refresh token and/or expiration.
        """
        if refresh_token:
            session.refresh_token = refresh_token
        
        if expires_at:
            session.expires_at = expires_at
        
        if update_last_accessed:
            session.last_accessed_at = datetime.utcnow()
        
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def revoke_session(self, db: Session, *, session: UserSession) -> bool:
        """
        Revoke a specific session by setting expiration to past.
        """
        session.expires_at = datetime.utcnow() - timedelta(seconds=1)
        db.add(session)
        db.commit()
        return True

    def revoke_session_by_token(
        self, 
        db: Session, 
        *, 
        refresh_token: str
    ) -> bool:
        """
        Revoke session by refresh token.
        """
        session = db.query(UserSession).filter(
            UserSession.refresh_token == refresh_token
        ).first()
        
        if session:
            return self.revoke_session(db, session=session)
        return False

    def revoke_all_user_sessions(
        self, 
        db: Session, 
        *, 
        user_id: str
    ) -> int:
        """
        Revoke all active sessions for a user.
        Returns the number of sessions revoked.
        """
        expired_time = datetime.utcnow() - timedelta(seconds=1)
        
        result = db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.expires_at > datetime.utcnow()
            )
        ).update(
            {"expires_at": expired_time},
            synchronize_session=False
        )
        
        db.commit()
        return result

    def revoke_other_sessions(
        self, 
        db: Session, 
        *, 
        user_id: str, 
        keep_session_id: str
    ) -> int:
        """
        Revoke all sessions for a user except the specified one.
        Useful for "sign out other devices" functionality.
        """
        expired_time = datetime.utcnow() - timedelta(seconds=1)
        
        result = db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.id != keep_session_id,
                UserSession.expires_at > datetime.utcnow()
            )
        ).update(
            {"expires_at": expired_time},
            synchronize_session=False
        )
        
        db.commit()
        return result

    def cleanup_expired_sessions(self, db: Session) -> int:
        """
        Clean up expired sessions from the database.
        Returns the number of sessions deleted.
        """
        cutoff_time = datetime.utcnow() - timedelta(days=30)  # Keep for 30 days for audit
        
        result = db.query(UserSession).filter(
            UserSession.expires_at < cutoff_time
        ).delete(synchronize_session=False)
        
        db.commit()
        return result

    def get_session_stats(self, db: Session, *, user_id: str) -> dict:
        """
        Get session statistics for a user.
        """
        total_sessions = db.query(UserSession).filter(
            UserSession.user_id == user_id
        ).count()
        
        active_sessions = db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.expires_at > datetime.utcnow()
            )
        ).count()
        
        # Get most recent session
        recent_session = db.query(UserSession).filter(
            UserSession.user_id == user_id
        ).order_by(UserSession.last_accessed_at.desc()).first()
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "last_session_at": recent_session.last_accessed_at.isoformat() if recent_session else None,
            "last_ip_address": recent_session.ip_address if recent_session else None
        }

    def get_sessions_by_ip(
        self, 
        db: Session, 
        *, 
        ip_address: str, 
        hours: int = 24
    ) -> List[UserSession]:
        """
        Get all sessions from a specific IP in the last N hours.
        Useful for detecting suspicious activity.
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        return db.query(UserSession).filter(
            and_(
                UserSession.ip_address == ip_address,
                UserSession.created_at >= cutoff_time
            )
        ).order_by(UserSession.created_at.desc()).all()

    def get_concurrent_sessions(
        self, 
        db: Session, 
        *, 
        user_id: str,
        max_allowed: int = 5
    ) -> dict:
        """
        Check if user has too many concurrent sessions.
        Returns info about concurrent sessions and whether limit is exceeded.
        """
        active_sessions = self.get_user_sessions(db, user_id=user_id, active_only=True)
        
        return {
            "active_count": len(active_sessions),
            "max_allowed": max_allowed,
            "limit_exceeded": len(active_sessions) > max_allowed,
            "sessions": [
                {
                    "id": str(session.id),
                    "created_at": session.created_at.isoformat(),
                    "last_accessed_at": session.last_accessed_at.isoformat(),
                    "ip_address": session.ip_address,
                    "user_agent": session.user_agent[:100] if session.user_agent else None
                }
                for session in active_sessions
            ]
        }

    def track_session_activity(
        self, 
        db: Session, 
        *, 
        session: UserSession
    ) -> UserSession:
        """
        Update last accessed time for session tracking.
        """
        session.last_accessed_at = datetime.utcnow()
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def get_global_session_stats(self, db: Session) -> dict:
        """
        Get global session statistics for admin dashboard.
        """
        total_sessions = db.query(UserSession).count()
        
        active_sessions = db.query(UserSession).filter(
            UserSession.expires_at > datetime.utcnow()
        ).count()
        
        # Sessions created in last 24 hours
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_sessions = db.query(UserSession).filter(
            UserSession.created_at >= recent_cutoff
        ).count()
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "recent_sessions_24h": recent_sessions,
            "inactive_sessions": total_sessions - active_sessions
        }


# Create instance
user_session_crud = CRUDUserSession(UserSession)
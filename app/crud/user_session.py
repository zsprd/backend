from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import secrets

from app.crud.base import CRUDBase
from app.models.user_session import UserSession


class CRUDUserSession(CRUDBase[UserSession, None, None]):
    """
    CRUD operations for UserSession model.
    Manages refresh tokens, session tracking, and token rotation for enhanced security.
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
            refresh_token: JWT refresh token string
            expires_at: When the refresh token expires
            ip_address: Client IP address
            user_agent: Client user agent string
            
        Returns:
            Created UserSession object
        """
        # Generate a unique session token
        session_token = f"sess_{secrets.token_urlsafe(24)}"
        
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
        """Get session by session token (not refresh token)."""
        return db.query(UserSession).filter(
            UserSession.session_token == session_token
        ).first()

    def get_user_sessions(
        self, 
        db: Session, 
        *, 
        user_id: str,
        active_only: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[UserSession]:
        """
        Get all sessions for a user.
        
        Args:
            user_id: User's ID
            active_only: Only return non-expired sessions
            limit: Maximum sessions to return
            offset: Number of sessions to skip
        """
        query = db.query(UserSession).filter(UserSession.user_id == user_id)
        
        if active_only:
            query = query.filter(UserSession.expires_at > datetime.utcnow())
        
        return query.order_by(
            UserSession.last_accessed_at.desc()
        ).offset(offset).limit(limit).all()

    def update_session_token(
        self,
        db: Session,
        *,
        session: UserSession,
        new_refresh_token: str,
        new_expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> UserSession:
        """
        Update session with new refresh token (token rotation).
        
        Args:
            session: Existing session to update
            new_refresh_token: New JWT refresh token
            new_expires_at: New expiration time
            ip_address: Updated IP address
            user_agent: Updated user agent
        """
        session.refresh_token = new_refresh_token
        session.expires_at = new_expires_at
        session.last_accessed_at = datetime.utcnow()
        
        if ip_address:
            session.ip_address = ip_address
        if user_agent:
            session.user_agent = user_agent
        
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def update_last_accessed(
        self,
        db: Session,
        *,
        session: UserSession
    ) -> UserSession:
        """Update session's last accessed timestamp."""
        session.last_accessed_at = datetime.utcnow()
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def revoke_session(
        self, 
        db: Session, 
        *, 
        session_id: str
    ) -> bool:
        """
        Revoke (delete) a specific session.
        
        Args:
            session_id: Session UUID to revoke
            
        Returns:
            True if session was found and revoked, False otherwise
        """
        session = self.get(db, id=session_id)
        if session:
            db.delete(session)
            db.commit()
            return True
        return False

    def revoke_session_by_token(
        self, 
        db: Session, 
        *, 
        refresh_token: str
    ) -> bool:
        """
        Revoke session by refresh token.
        
        Args:
            refresh_token: Refresh token to revoke
            
        Returns:
            True if session was found and revoked, False otherwise
        """
        session = db.query(UserSession).filter(
            UserSession.refresh_token == refresh_token
        ).first()
        
        if session:
            db.delete(session)
            db.commit()
            return True
        return False

    def revoke_all_user_sessions(
        self, 
        db: Session, 
        *, 
        user_id: str,
        except_current: bool = False,
        current_refresh_token: Optional[str] = None
    ) -> int:
        """
        Revoke all sessions for a user.
        
        Args:
            user_id: User's ID
            except_current: Keep current session active
            current_refresh_token: Current session's refresh token to preserve
            
        Returns:
            Number of sessions revoked
        """
        query = db.query(UserSession).filter(UserSession.user_id == user_id)
        
        if except_current and current_refresh_token:
            query = query.filter(UserSession.refresh_token != current_refresh_token)
        
        sessions = query.all()
        count = len(sessions)
        
        for session in sessions:
            db.delete(session)
        
        db.commit()
        return count

    def cleanup_expired_sessions(self, db: Session) -> int:
        """
        Remove all expired sessions from the database.
        This should be run periodically as a cleanup task.
        
        Returns:
            Number of sessions cleaned up
        """
        expired_sessions = db.query(UserSession).filter(
            UserSession.expires_at <= datetime.utcnow()
        ).all()
        
        count = len(expired_sessions)
        
        for session in expired_sessions:
            db.delete(session)
        
        db.commit()
        return count

    def get_sessions_by_ip(
        self,
        db: Session,
        *,
        ip_address: str,
        active_only: bool = True,
        limit: int = 100
    ) -> List[UserSession]:
        """
        Get sessions by IP address.
        Useful for security monitoring and rate limiting.
        """
        query = db.query(UserSession).filter(UserSession.ip_address == ip_address)
        
        if active_only:
            query = query.filter(UserSession.expires_at > datetime.utcnow())
        
        return query.order_by(
            UserSession.created_at.desc()
        ).limit(limit).all()

    def get_recent_sessions(
        self,
        db: Session,
        *,
        user_id: str,
        hours: int = 24,
        limit: int = 10
    ) -> List[UserSession]:
        """
        Get recent sessions for a user within specified hours.
        Useful for security dashboards and alerts.
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        
        return db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.created_at >= since
            )
        ).order_by(
            UserSession.created_at.desc()
        ).limit(limit).all()

    def count_active_sessions_by_user(
        self,
        db: Session,
        *,
        user_id: str
    ) -> int:
        """
        Count active sessions for a user.
        """
        return db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.expires_at > datetime.utcnow()
            )
        ).count()

    def get_session_stats(
        self,
        db: Session,
        *,
        user_id: Optional[str] = None
    ) -> dict:
        """
        Get session statistics for analytics.
        
        Args:
            user_id: Specific user ID, or None for system-wide stats
        """
        base_query = db.query(UserSession)
        
        if user_id:
            base_query = base_query.filter(UserSession.user_id == user_id)
        
        now = datetime.utcnow()
        
        total_sessions = base_query.count()
        active_sessions = base_query.filter(UserSession.expires_at > now).count()
        expired_sessions = total_sessions - active_sessions
        
        # Sessions created in last 24 hours
        last_24h = now - timedelta(hours=24)
        recent_sessions = base_query.filter(UserSession.created_at >= last_24h).count()
        
        # Sessions accessed in last hour
        last_hour = now - timedelta(hours=1)
        recent_activity = base_query.filter(UserSession.last_accessed_at >= last_hour).count()
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "expired_sessions": expired_sessions,
            "sessions_last_24h": recent_sessions,
            "active_last_hour": recent_activity
        }

    def extend_session(
        self,
        db: Session,
        *,
        session: UserSession,
        extend_by_days: int = 30
    ) -> UserSession:
        """
        Extend session expiration time.
        Useful for "Remember me" functionality.
        """
        session.expires_at = session.expires_at + timedelta(days=extend_by_days)
        session.last_accessed_at = datetime.utcnow()
        
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    def is_session_from_new_device(
        self,
        db: Session,
        *,
        user_id: str,
        user_agent: str,
        ip_address: str,
        days_lookback: int = 30
    ) -> bool:
        """
        Check if this appears to be a new device/location for the user.
        Useful for security alerts.
        """
        since = datetime.utcnow() - timedelta(days=days_lookback)
        
        # Check for similar user agent or IP in recent sessions
        existing_session = db.query(UserSession).filter(
            and_(
                UserSession.user_id == user_id,
                UserSession.created_at >= since,
                or_(
                    UserSession.user_agent == user_agent,
                    UserSession.ip_address == ip_address
                )
            )
        ).first()
        
        return existing_session is None


# Create global instance
user_session_crud = CRUDUserSession(UserSession)
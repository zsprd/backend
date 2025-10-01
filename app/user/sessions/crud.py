import logging
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Union
from uuid import UUID

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.repository import BaseRepository
from app.user.accounts.model import UserAccount
from app.user.sessions.model import UserSession
from app.user.sessions.schema import UserSessionCreate, UserSessionUpdate

logger = logging.getLogger(__name__)


class UserSessionRepository(BaseRepository[UserSession, UserSessionCreate, UserSessionUpdate]):
    """CRUD operations for user sessions."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        super().__init__(UserSession)
        self.db = db

    async def create_user_session(
        self,
        user: UserAccount,
        refresh_token: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> Optional[UserSession]:
        """Create a new user session."""
        try:
            # Enforce session limit per user
            await self._enforce_session_limit(user.id)

            # Calculate expiration
            expires_at = datetime.now(timezone.utc) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )

            # Create session
            session = UserSession(
                user_id=user.id,
                refresh_token=refresh_token,
                expires_at=expires_at,
                ip_address=ip_address,
                user_agent=user_agent,
                last_used_at=datetime.now(timezone.utc),
                is_active=True,
            )

            self.db.add(session)
            await self.db.commit()
            await self.db.refresh(session)

            logger.info(f"Session created for user: {user.id}")
            return session

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Unexpected error creating session: {type(e).__name__}")
            return None

    async def get_user_session_by_token(self, refresh_token: str) -> Optional[UserSession]:
        """Get user session by refresh token with validation."""
        if not refresh_token or len(refresh_token.strip()) < 32:
            return None

        try:
            now = datetime.now(timezone.utc)

            result = await self.db.execute(
                select(UserSession).where(
                    and_(
                        UserSession.refresh_token == refresh_token.strip(),
                        UserSession.is_active == True,
                        UserSession.expires_at > now,
                    )
                )
            )
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Database error retrieving session: {type(e).__name__}")
            return None

    async def get_active_user_sessions(self, user_id: Union[str, UUID]) -> List[UserSession]:
        """Get all active sessions for a user."""
        try:
            # Convert to UUID if string
            if isinstance(user_id, str):
                try:
                    user_uuid = UUID(user_id)
                except ValueError:
                    logger.warning(f"Invalid UUID format: {user_id}")
                    return []
            else:
                user_uuid = user_id

            now = datetime.now(timezone.utc)

            result = await self.db.execute(
                select(UserSession)
                .where(
                    and_(
                        UserSession.user_id == user_uuid,
                        UserSession.is_active == True,
                        UserSession.expires_at > now,
                    )
                )
                .order_by(UserSession.last_used_at.desc())
            )

            return list(result.scalars().all())

        except Exception as e:
            logger.error(f"Error retrieving user sessions: {type(e).__name__}")
            return []

    async def update_user_session(
        self, old_refresh_token: str, new_refresh_token: str
    ) -> Optional[UserSession]:
        """Update session with new refresh token."""
        try:
            # Get current session
            session = await self.get_user_session_by_token(old_refresh_token)
            if not session:
                logger.warning("Session not found or expired for token update")
                return None

            # Update session
            session.refresh_token = new_refresh_token
            session.last_used_at = datetime.now(timezone.utc)
            session.expires_at = datetime.now(timezone.utc) + timedelta(
                days=settings.REFRESH_TOKEN_EXPIRE_DAYS
            )
            session.updated_at = datetime.now(timezone.utc)

            await self.db.commit()
            await self.db.refresh(session)

            logger.info(f"Session token refreshed for user: {session.user_id}")
            return session

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Unexpected error updating session: {type(e).__name__}")
            return None

    async def update_session_activity(self, session: UserSession) -> Optional[UserSession]:
        """Update session last activity timestamp."""
        try:
            session.last_used_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(session)
            return session
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error updating session activity: {type(e).__name__}")
            return None

    async def revoke_user_session(self, session_id: Union[str, UUID]) -> bool:
        """Revoke a specific user session."""
        try:
            # Convert to UUID if string
            if isinstance(session_id, str):
                try:
                    session_uuid = UUID(session_id)
                except ValueError:
                    logger.warning(f"Invalid session ID format: {session_id}")
                    return False
            else:
                session_uuid = session_id

            now = datetime.now(timezone.utc)

            result = await self.db.execute(
                update(UserSession)
                .where(UserSession.id == session_uuid)
                .values(
                    is_active=False,
                    revoked_at=now,
                    updated_at=now,
                )
            )

            await self.db.commit()
            revoked = result.rowcount > 0

            if revoked:
                logger.info(f"Session revoked: {session_id}")

            return revoked

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error revoking session: {type(e).__name__}")
            return False

    async def revoke_all_user_sessions(self, user_id: Union[str, UUID]) -> int:
        """Revoke all sessions for a user."""
        try:
            # Convert to UUID if string
            if isinstance(user_id, str):
                try:
                    user_uuid = UUID(user_id)
                except ValueError:
                    logger.warning(f"Invalid user ID format: {user_id}")
                    return 0
            else:
                user_uuid = user_id

            now = datetime.now(timezone.utc)

            result = await self.db.execute(
                update(UserSession)
                .where(
                    and_(
                        UserSession.user_id == user_uuid,
                        UserSession.is_active == True,
                    )
                )
                .values(
                    is_active=False,
                    revoked_at=now,
                    updated_at=now,
                )
            )

            await self.db.commit()
            revoked_count = result.rowcount

            if revoked_count > 0:
                logger.info(f"Revoked {revoked_count} sessions for user: {user_id}")

            return revoked_count

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error revoking user sessions: {type(e).__name__}")
            return 0

    async def is_session_valid(self, refresh_token: str) -> bool:
        """Check if a session is valid."""
        session = await self.get_user_session_by_token(refresh_token)
        return (
            session is not None and session.is_active and not getattr(session, "is_expired", False)
        )

    async def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions from database."""
        try:
            now = datetime.now(timezone.utc)

            # Delete expired sessions
            result = await self.db.execute(
                delete(UserSession)
                .where(UserSession.expires_at <= now)
                .execution_options(synchronize_session=False)
            )

            await self.db.commit()
            cleaned_count = result.rowcount

            if cleaned_count > 0:
                logger.info(f"Deleted {cleaned_count} expired sessions")

            return cleaned_count

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error during session cleanup: {type(e).__name__}")
            return 0

    async def cleanup_inactive_sessions(
        self, days_old: int = settings.SESSION_INACTIVE_DAYS
    ) -> int:
        """Clean up old inactive sessions."""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)

            result = await self.db.execute(
                delete(UserSession)
                .where(
                    and_(
                        UserSession.is_active == False,
                        UserSession.revoked_at <= cutoff_date,
                    )
                )
                .execution_options(synchronize_session=False)
            )

            await self.db.commit()
            cleaned_count = result.rowcount

            if cleaned_count > 0:
                logger.info(f"Deleted {cleaned_count} old inactive sessions")

            return cleaned_count

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error cleaning inactive sessions: {type(e).__name__}")
            return 0

    async def _enforce_session_limit(self, user_id: UUID) -> None:
        """Enforce maximum active sessions per user."""
        try:
            # Count active sessions
            active_count = await self.db.execute(
                select(func.count(UserSession.id)).where(
                    and_(
                        UserSession.user_id == user_id,
                        UserSession.is_active == True,
                        UserSession.expires_at > datetime.now(timezone.utc),
                    )
                )
            )
            count = active_count.scalar()

            # Auto-revoke oldest if at limit
            if count >= settings.MAX_ACTIVE_SESSIONS:
                oldest_session = await self.db.execute(
                    select(UserSession)
                    .where(
                        and_(
                            UserSession.user_id == user_id,
                            UserSession.is_active == True,
                        )
                    )
                    .order_by(UserSession.last_used_at.asc())
                    .limit(1)
                )

                session_to_revoke = oldest_session.scalar_one_or_none()
                if session_to_revoke:
                    await self.revoke_user_session(session_to_revoke.id)
                    logger.info(f"Auto-revoked oldest session for user: {user_id}")

        except Exception as e:
            logger.error(f"Error enforcing session limit: {type(e).__name__}")

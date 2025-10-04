import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from uuid import UUID

from passlib.context import CryptContext
from sqlalchemy import and_, func, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.user.accounts.model import UserAccount

logger = logging.getLogger(__name__)


class UserRepository:
    """Repository for user account data access operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    async def create_user_with_password(
        self, email: str, full_name: str, password: str
    ) -> Optional[UserAccount]:
        """Create a new user account with password."""
        try:
            if await self.is_email_taken(email):
                logger.warning(f"Duplicate email attempted: {email}")
                return None

            hashed_password = self._hash_password(password)

            user = UserAccount(
                email=email.lower().strip(),
                full_name=full_name.strip(),
                hashed_password=hashed_password,
                language="en",
                country="US",
                currency="USD",
                is_verified=False,
                is_active=True,
                failed_login_attempts=0,
            )

            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            logger.info(f"User account created: {user.id}")
            return user

        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error creating user {email}: {str(e)}")
            return None
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error creating user {email}: {str(e)}")
            return None

    async def create_oauth_user(
        self, email: str, full_name: str, provider: str
    ) -> Optional[UserAccount]:
        """Create a new OAuth user account."""
        try:
            existing_user = await self.get_user_by_email(email)
            if existing_user:
                logger.info(f"OAuth user already exists: {existing_user.id}")
                return existing_user

            user = UserAccount(
                email=email.lower().strip(),
                full_name=full_name.strip(),
                hashed_password=None,
                language="en",
                country="US",
                currency="USD",
                is_verified=True,
                is_active=True,
                failed_login_attempts=0,
            )

            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            logger.info(f"OAuth user created: {user.id} via {provider}")
            return user

        except (IntegrityError, SQLAlchemyError) as e:
            await self.db.rollback()
            logger.error(f"Error creating OAuth user {email}: {str(e)}")
            return None

    async def get_user_by_id(self, user_id: Union[str, UUID]) -> Optional[UserAccount]:
        """Get user account by ID."""
        try:
            if isinstance(user_id, str):
                try:
                    user_uuid = UUID(user_id)
                except ValueError:
                    logger.warning(f"Invalid UUID format: {user_id}")
                    return None
            else:
                user_uuid = user_id

            query = select(UserAccount).where(
                and_(UserAccount.id == user_uuid, UserAccount.is_active == True)
            )

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving user by ID {user_id}: {str(e)}")
            return None

    async def get_user_by_email(self, email: str) -> Optional[UserAccount]:
        """Get user account by email address."""
        try:
            query = select(UserAccount).where(
                and_(UserAccount.email == email.lower().strip(), UserAccount.is_active == True)
            )

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except SQLAlchemyError as e:
            logger.error(f"Error retrieving user by email: {str(e)}")
            return None

    async def authenticate_user(self, user: UserAccount, password: str) -> bool:
        """Authenticate user with password."""
        try:
            # Check if account is locked using database field
            now = datetime.now(timezone.utc)
            if user.locked_until and user.locked_until > now:
                logger.warning(f"Authentication attempt on locked account: {user.id}")
                return False

            if not user.is_active:
                logger.debug(f"Authentication attempt on inactive account: {user.id}")
                return False

            if not user.hashed_password:
                logger.debug(f"Password auth attempted for OAuth user: {user.id}")
                return False

            if not self._verify_password(password, user.hashed_password):
                await self._handle_failed_login(user)
                logger.debug(f"Invalid password for user: {user.id}")
                return False

            # Success - reset failed attempts
            if user.failed_login_attempts > 0 or user.locked_until:
                await self._reset_failed_attempts(user)
                await self.db.commit()

            # Check if password needs rehashing
            if self._needs_rehash(user.hashed_password):
                logger.info(f"Rehashing password for user: {user.id}")
                user.hashed_password = self._hash_password(password)
                user.updated_at = datetime.now(timezone.utc)
                self.db.add(user)
                await self.db.commit()

            logger.info(f"Authentication successful for user: {user.id}")
            return True

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error during authentication for user {user.id}: {str(e)}")
            return False

    async def update_last_login(self, user: UserAccount) -> None:
        """Update user's last login timestamp."""
        try:
            user.last_login_at = datetime.now(timezone.utc)
            user.updated_at = datetime.now(timezone.utc)
            self.db.add(user)
            await self.db.commit()

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error updating last login for user {user.id}: {str(e)}")

    async def update_password(
        self, user: UserAccount, current_password: str, new_password: str
    ) -> Optional[UserAccount]:
        """Update user password with current password verification."""
        try:
            if user.hashed_password and not self._verify_password(
                current_password, user.hashed_password
            ):
                await self._handle_failed_login(user)
                logger.warning(f"Current password is incorrect for user: {user.id}")
                return None

            user.hashed_password = self._hash_password(new_password)
            user.updated_at = datetime.now(timezone.utc)
            user.failed_login_attempts = 0
            user.locked_until = None

            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            logger.info(f"Password updated for user: {user.id}")
            return user

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error updating password for user {user.id}: {str(e)}")
            return None

    async def reset_password(self, user: UserAccount, new_password: str) -> Optional[UserAccount]:
        """Reset user password (no current password required)."""
        try:
            user.hashed_password = self._hash_password(new_password)
            user.updated_at = datetime.now(timezone.utc)
            user.failed_login_attempts = 0
            user.locked_until = None

            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            logger.info(f"Password reset for user: {user.id}")
            return user

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error resetting password for user {user.id}: {str(e)}")
            return None

    async def update_profile(
        self, user: UserAccount, profile_update: dict
    ) -> Optional[UserAccount]:
        """Update user profile information."""
        try:
            if not profile_update:
                logger.debug(f"No fields to update for user: {user.id}")
                return user

            updated = False

            if "full_name" in profile_update:
                user.full_name = profile_update["full_name"]
                logger.debug(f"Updated full_name for user {user.id}")
                updated = True

            if "language" in profile_update:
                user.language = profile_update["language"]
                logger.debug(f"Updated language for user {user.id}")
                updated = True

            if "country" in profile_update:
                user.country = profile_update["country"]
                logger.debug(f"Updated country for user {user.id}")
                updated = True

            if "currency" in profile_update:
                user.currency = profile_update["currency"]
                logger.debug(f"Updated currency for user {user.id}")
                updated = True

            if not updated:
                logger.debug(f"No valid fields to update for user: {user.id}")
                return user

            user.updated_at = datetime.now(timezone.utc)

            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            logger.info(f"Profile updated successfully for user: {user.id}")
            return user

        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Integrity error updating profile for user {user.id}: {str(e)}")
            raise  # Let service layer handle
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Database error updating profile for user {user.id}: {str(e)}")
            raise

    async def mark_email_verified(self, user: UserAccount) -> Optional[UserAccount]:
        """Mark user's email as verified."""
        try:
            user.is_verified = True
            user.updated_at = datetime.now(timezone.utc)

            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            logger.info(f"Email verified for user: {user.id}")
            return user

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error marking email verified for user {user.id}: {str(e)}")
            return None

    async def deactivate_account(self, user: UserAccount) -> Optional[UserAccount]:
        """Deactivate user account."""
        try:
            user.is_active = False
            user.updated_at = datetime.now(timezone.utc)

            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            logger.info(f"Account deactivated: {user.id}")
            return user

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error deactivating account for user {user.id}: {str(e)}")
            return None

    async def delete_account(self, user: UserAccount) -> bool:
        """Delete user account."""
        try:
            await self.db.delete(user)
            await self.db.commit()
            logger.info(f"User account deleted: {user.id}")
            return True

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error deleting user {user.id}: {str(e)}")
            return False

    async def is_email_taken(self, email: str) -> bool:
        """Check if email address is already in use."""
        try:
            result = await self.db.execute(
                select(func.count(UserAccount.id)).where(UserAccount.email == email.lower().strip())
            )
            return result.scalar() > 0

        except SQLAlchemyError as e:
            logger.error(f"Error checking email availability: {str(e)}")
            return True

    async def cleanup_locked_accounts(self) -> int:
        """Clean up master whose lockout period has expired."""
        try:
            now = datetime.now(timezone.utc)

            result = await self.db.execute(
                update(UserAccount)
                .where(
                    and_(
                        UserAccount.locked_until.isnot(None),
                        UserAccount.locked_until <= now,
                    )
                )
                .values(
                    locked_until=None,
                    failed_login_attempts=0,
                    updated_at=now,
                )
            )

            await self.db.commit()
            unlocked_count = result.rowcount

            if unlocked_count > 0:
                logger.info(f"Unlocked {unlocked_count} expired account lockouts")
            return unlocked_count

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error during lockout cleanup: {str(e)}")
            return 0

    async def _handle_failed_login(self, user: UserAccount) -> None:
        """Handle failed login attempt and potential account lockout."""
        try:
            user.failed_login_attempts += 1
            now = datetime.now(timezone.utc)

            if user.failed_login_attempts >= settings.MAX_FAILED_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=settings.ACCOUNT_LOCKOUT_MINUTES)
                logger.warning(
                    f"Account locked after {settings.MAX_FAILED_ATTEMPTS} failed attempts: {user.id}"
                )

            user.updated_at = now
            self.db.add(user)
            await self.db.commit()

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Error handling failed login for user {user.id}: {str(e)}")

    async def _reset_failed_attempts(self, user: UserAccount) -> None:
        """Reset failed login attempts and unlock account."""
        try:
            user.failed_login_attempts = 0
            user.locked_until = None
            user.updated_at = datetime.now(timezone.utc)
            self.db.add(user)
            # Caller commits

        except Exception as e:
            logger.error(f"Error resetting failed attempts for user {user.id}: {str(e)}")

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return self.pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        try:
            return self.pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Error verifying password: {str(e)}")
            return False

    def _needs_rehash(self, hashed_password: str) -> bool:
        """Check if password hash needs updating."""
        try:
            return self.pwd_context.needs_update(hashed_password)
        except Exception as e:
            logger.error(f"Error checking password rehash: {str(e)}")
            return False

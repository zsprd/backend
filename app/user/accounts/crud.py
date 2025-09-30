import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
from uuid import UUID

from passlib.context import CryptContext
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.crud import CRUDBase
from app.user.accounts.model import UserAccount
from app.user.accounts.schema import UserAccountCreate, UserAccountUpdate

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)


class CRUDUserAccount(CRUDBase[UserAccount, UserAccountCreate, UserAccountUpdate]):
    """CRUD operations for user accounts."""

    def __init__(self, db: AsyncSession):
        """Initialize repository with database session."""
        super().__init__(UserAccount)
        self.db = db

    async def create_user_with_password(
        self, email: str, full_name: str, password: str
    ) -> Optional[UserAccount]:
        """Create a new user account with password."""
        try:
            # Check if email already exists
            if await self.is_email_taken(email):
                logger.warning(f"Duplicate email attempted: {email}")
                return None

            # Hash password securely
            hashed_password = self._hash_password(password)

            # Create user account
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

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Unexpected error creating user: {email} - {type(e).__name__} - {str(e)}")
            return None

    async def create_oauth_user(
        self, email: str, full_name: str, provider: str
    ) -> Optional[UserAccount]:
        """Create a new OAuth user account."""
        try:
            # Check if user already exists
            existing_user = await self.get_user_by_email(email)
            if existing_user:
                # TODO: Link OAuth provider to existing account
                logger.info(f"OAuth user already exists: {existing_user.id}")
                return existing_user

            # Create OAuth user (no password)
            user = UserAccount(
                email=email.lower().strip(),
                full_name=full_name.strip(),
                hashed_password=None,  # OAuth users don't have passwords
                language="en",
                country="US",
                currency="USD",
                is_verified=True,  # OAuth emails are pre-verified
                is_active=True,
                failed_login_attempts=0,
            )

            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            logger.info(f"OAuth user created: {user.id} via {provider}")
            return user

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Unexpected error creating OAuth user: {email} - {type(e).__name__} - {str(e)}"
            )
            return None

    async def get_user_by_id(
        self, user_id: Union[str, UUID], include_inactive: bool = False
    ) -> Optional[UserAccount]:
        """Get user account by ID."""
        try:
            # Convert to UUID if string
            if isinstance(user_id, str):
                try:
                    user_uuid = UUID(user_id)
                except ValueError:
                    logger.warning(f"Invalid UUID format: {user_id}")
                    return None
            else:
                user_uuid = user_id

            # Build query
            query = select(UserAccount).where(UserAccount.id == user_uuid)

            if not include_inactive:
                query = query.where(UserAccount.is_active == True)

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error retrieving user by ID {user_id}: {type(e).__name__} - {str(e)}")
            return None

    async def delete_account(self, user: UserAccount) -> bool:
        """Delete user account."""
        try:
            await self.db.delete(user)
            await self.db.commit()
            logger.info(f"User account deleted: {user.id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error deleting user {user.id}: {type(e).__name__} - {str(e)}")
            return False

    async def get_user_by_email(
        self, email: str, include_inactive: bool = False
    ) -> Optional[UserAccount]:
        """Get user account by email address."""
        try:
            query = select(UserAccount).where(UserAccount.email == email.lower().strip())

            if not include_inactive:
                query = query.where(UserAccount.is_active == True)

            result = await self.db.execute(query)
            return result.scalar_one_or_none()

        except Exception as e:
            logger.error(f"Error retrieving user by email: {type(e).__name__} - {str(e)}")
            return None

    async def authenticate_user(self, user: UserAccount, password: str) -> bool:
        """Authenticate user with password."""
        try:
            # Check if account is locked
            if user.is_locked:
                logger.warning(f"Authentication attempt on locked account: {user.id}")
                return False

            # Check if account is active
            if not user.is_active:
                logger.debug(f"Authentication attempt on inactive account: {user.id}")
                return False

            # OAuth users can't authenticate with password
            if not user.hashed_password:
                logger.debug(f"Password auth attempted for OAuth user: {user.id}")
                return False

            # Verify password
            if not self._verify_password(password, user.hashed_password):
                await self._handle_failed_login(user)
                logger.debug(f"Invalid password for user: {user.id}")
                return False

            # Success - reset failed attempts
            if user.failed_login_attempts > 0 or user.locked_until:
                await self._reset_failed_attempts(user)

            # Check if password needs rehashing
            if self._needs_rehash(user.hashed_password):
                logger.info(f"Rehashing password for user: {user.id}")
                user.hashed_password = self._hash_password(password)
                user.updated_at = datetime.now(timezone.utc)
                self.db.add(user)
                await self.db.commit()

            logger.info(f"Authentication successful for user: {user.id}")
            return True

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Error during authentication for user {user.id}: {type(e).__name__} - {str(e)}"
            )
            return False

    async def update_last_login(self, user: UserAccount) -> None:
        """Update user's last login timestamp."""
        try:
            user.last_login_at = datetime.now(timezone.utc)
            user.updated_at = datetime.now(timezone.utc)
            self.db.add(user)
            await self.db.commit()

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Error updating last login for user {user.id}: {type(e).__name__} - {str(e)}"
            )

    async def update_password(
        self, user: UserAccount, current_password: str, new_password: str
    ) -> Optional[UserAccount]:
        """Update user password with current password verification."""
        try:
            # Verify current password
            if user.hashed_password and not self._verify_password(
                current_password, user.hashed_password
            ):
                await self._handle_failed_login(user)
                logger.warning(f"Current password is incorrect for user: {user.id}")
                return None

            # Update password
            user.hashed_password = self._hash_password(new_password)
            user.updated_at = datetime.now(timezone.utc)

            # Reset security flags
            user.failed_login_attempts = 0
            user.locked_until = None

            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            logger.info(f"Password updated for user: {user.id}")
            return user

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Unexpected error updating password for user {user.id}: {type(e).__name__} - {str(e)}"
            )
            return None

    async def reset_password(self, user: UserAccount, new_password: str) -> Optional[UserAccount]:
        """Reset user password (no current password required)."""
        try:
            user.hashed_password = self._hash_password(new_password)
            user.updated_at = datetime.now(timezone.utc)

            # Reset security state
            user.failed_login_attempts = 0
            user.locked_until = None

            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            logger.info(f"Password reset for user: {user.id}")
            return user

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Unexpected error resetting password for user {user.id}: {type(e).__name__} - {str(e)}"
            )
            return None

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

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Unexpected error marking email verified for user {user.id}: {type(e).__name__} - {str(e)}"
            )
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

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Unexpected error deactivating account for user {user.id}: {type(e).__name__} - {str(e)}"
            )
            return None

    async def is_email_taken(self, email: str) -> bool:
        """Check if email address is already in use."""
        try:
            result = await self.db.execute(
                select(func.count(UserAccount.id)).where(UserAccount.email == email.lower().strip())
            )
            return result.scalar() > 0

        except Exception as e:
            logger.error(f"Error checking email availability: {type(e).__name__} - {str(e)}")
            return True  # Err on the side of caution

    async def cleanup_locked_accounts(self) -> int:
        """Clean up accounts whose lockout period has expired."""
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

        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error during lockout cleanup: {type(e).__name__} - {str(e)}")
            return 0

    async def update_profile(
        self, user: UserAccount, profile_update: Union[dict, UserAccountUpdate]
    ) -> Optional[UserAccount]:
        """Update user profile information."""
        try:
            # Get only the fields that were actually provided
            if hasattr(profile_update, "model_dump"):
                update_data = profile_update.model_dump(exclude_unset=True)
            else:
                update_data = dict(profile_update) if profile_update else {}

            if not update_data:
                logger.debug(f"No fields to update for user: {user.id}")
                return user

            # Apply updates
            for field, value in update_data.items():
                if hasattr(user, field) and field not in ["id", "created_at", "hashed_password"]:
                    old_value = getattr(user, field)
                    setattr(user, field, value)
                    logger.debug(f"Updated {field} for user {user.id}: {old_value} -> {value}")

            # Update timestamp
            user.updated_at = datetime.now(timezone.utc)

            # Save to database
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)

            logger.info(f"Profile updated successfully for user: {user.id}")
            return user

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Unexpected error updating profile for user {user.id}: {type(e).__name__} - {str(e)}"
            )
            return None

    async def _handle_failed_login(self, user: UserAccount) -> None:
        """Handle failed login attempt and potential account lockout."""
        try:
            user.failed_login_attempts += 1
            now = datetime.now(timezone.utc)

            # Lock account if max attempts reached
            if user.failed_login_attempts >= settings.MAX_FAILED_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=settings.ACCOUNT_LOCKOUT_MINUTES)
                logger.warning(
                    f"Account locked after {settings.MAX_FAILED_ATTEMPTS} failed attempts: {user.id}"
                )

            user.updated_at = now
            self.db.add(user)
            await self.db.commit()

        except Exception as e:
            await self.db.rollback()
            logger.error(
                f"Error handling failed login for user {user.id}: {type(e).__name__} - {str(e)}"
            )

    async def _reset_failed_attempts(self, user: UserAccount) -> None:
        """Reset failed login attempts and unlock account."""
        try:
            user.failed_login_attempts = 0
            user.locked_until = None
            user.updated_at = datetime.now(timezone.utc)
            self.db.add(user)
            # Note: Caller should commit

        except Exception as e:
            logger.error(
                f"Error resetting failed attempts for user {user.id}: {type(e).__name__} - {str(e)}"
            )

    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        try:
            return pwd_context.hash(password)
        except Exception as e:
            logger.error(f"Error hashing password: {type(e).__name__} - {str(e)}")
            raise

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Error verifying password: {type(e).__name__} - {str(e)}")
            return False

    def _needs_rehash(self, hashed_password: str) -> bool:
        """Check if password hash needs updating."""
        try:
            return pwd_context.needs_update(hashed_password)
        except Exception as e:
            logger.error(f"Error checking password rehash: {type(e).__name__} - {str(e)}")
            return False

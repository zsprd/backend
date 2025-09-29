import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Set

from jose import JWTError, jwt

from app.core.config import settings
from app.core.redis import redis_client

logger = logging.getLogger(__name__)

# Token type constants
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"
TOKEN_TYPE_VERIFICATION = "verification"
TOKEN_TYPE_RESET = "reset"


class TokenError(Exception):
    """Base exception for token-related errors."""

    pass


class TokenBlacklist:
    """
    Token blacklist with Redis backend and in-memory fallback.

    Uses Redis with TTL for automatic expiration of blacklisted tokens.
    Falls back to in-memory set when Redis is unavailable.
    """

    def __init__(self):
        self._memory_blacklist: Set[str] = set()
        self._use_redis = redis_client.is_available()

        if self._use_redis:
            logger.info("✅ Token blacklist using Redis backend")
        else:
            logger.warning("⚠️ Token blacklist using in-memory - NOT suitable for production.")

    def add(self, jti: str, ttl_seconds: int = None) -> bool:
        """Add token JTI to blacklist with optional TTL."""
        if not ttl_seconds:
            # Default to maximum possible token lifetime
            ttl_seconds = max(
                settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
                settings.RESET_TOKEN_EXPIRE_MINUTES * 60,
                settings.VERIFICATION_TOKEN_EXPIRE_HOURS * 3600,
            )

        if redis_client.is_available():
            try:
                key = f"blacklist:token:{jti}"
                redis_client.setex(key, ttl_seconds, "1")
                return True
            except Exception as e:
                logger.error(f"Failed to add token to Redis blacklist: {e}")
                # Fallback to memory
                self._memory_blacklist.add(jti)
                return True
        else:
            self._memory_blacklist.add(jti)
            return True

    def contains(self, jti: str) -> bool:
        """Check if token JTI is blacklisted."""
        if redis_client.is_available():
            try:
                key = f"blacklist:token:{jti}"
                return redis_client.exists(key) > 0
            except Exception as e:
                logger.error(f"Failed to check Redis blacklist: {e}")
                # Fallback to memory
                return jti in self._memory_blacklist
        else:
            return jti in self._memory_blacklist

    def remove(self, jti: str) -> bool:
        """Remove token JTI from blacklist (rarely needed)."""
        if redis_client.is_available():
            try:
                key = f"blacklist:token:{jti}"
                return redis_client.delete(key) > 0
            except Exception as e:
                logger.error(f"Failed to remove from Redis blacklist: {e}")
                self._memory_blacklist.discard(jti)
                return False
        else:
            self._memory_blacklist.discard(jti)
            return True

    def blacklist_all_user_tokens(self, user_id: str, ttl_seconds: int = None) -> bool:
        """Blacklist all tokens for a specific user."""
        if not ttl_seconds:
            ttl_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400

        if redis_client.is_available():
            try:
                key = f"blacklist:user:{user_id}"
                timestamp = datetime.now(timezone.utc).isoformat()
                redis_client.setex(key, ttl_seconds, timestamp)
                logger.info(f"All tokens blacklisted for user {user_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to blacklist user tokens: {e}")
                return False
        else:
            logger.warning(f"Cannot blacklist all user tokens without Redis (user: {user_id}).")
            return False

    def is_user_blacklisted(self, user_id: str, token_issued_at: datetime) -> bool:
        """Check if a user's tokens issued before a certain time are blacklisted."""
        if redis_client.is_available():
            try:
                key = f"blacklist:user:{user_id}"
                blacklist_timestamp = redis_client.get(key)

                if blacklist_timestamp:
                    blacklist_dt = datetime.fromisoformat(blacklist_timestamp)
                    return token_issued_at < blacklist_dt
                return False
            except Exception as e:
                logger.error(f"Failed to check user blacklist: {e}")
                return False
        return False

    def remove_expired(self) -> None:
        """Remove expired tokens from blacklist."""
        if redis_client.is_available():
            # Redis handles expiration automatically via TTL
            logger.debug("Redis TTL handles automatic blacklist cleanup")
        else:
            # With in-memory storage, we can't know when tokens expire
            # without storing the full token or expiration time
            logger.debug("In-memory blacklist cannot auto-cleanup without token metadata")


# Initialize token blacklist (uses Redis if available, falls back to in-memory)
token_blacklist = TokenBlacklist()


def create_access_token(user_id: str) -> str:
    return _create_token(
        subject=user_id,
        token_type=TOKEN_TYPE_ACCESS,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: str) -> str:
    return _create_token(
        subject=user_id,
        token_type=TOKEN_TYPE_REFRESH,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def create_verification_token(user_id: str) -> str:
    return _create_token(
        subject=user_id,
        token_type=TOKEN_TYPE_VERIFICATION,
        expires_delta=timedelta(hours=settings.VERIFICATION_TOKEN_EXPIRE_HOURS),
    )


def create_reset_token(user_id: str) -> str:
    return _create_token(
        subject=user_id,
        token_type=TOKEN_TYPE_RESET,
        expires_delta=timedelta(minutes=settings.RESET_TOKEN_EXPIRE_MINUTES),
    )


def verify_token(token: str, expected_type: str) -> Optional[Dict[str, Any]]:
    if not token or not token.strip():
        logger.warning("Empty token provided for verification")
        return None

    try:
        # Decode and verify token
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Verify token type
        if payload.get("type") != expected_type:
            logger.warning(
                f"Token type mismatch: expected {expected_type}, got {payload.get('type')}"
            )
            return None

        # Check if specific token is blacklisted
        jti = payload.get("jti")
        if jti and token_blacklist.contains(jti):
            logger.warning(f"Blacklisted token used: {jti}")
            return None

        # Check if all user tokens are blacklisted
        user_id = payload.get("sub")
        iat = payload.get("iat")
        if user_id and iat:
            issued_at = datetime.fromtimestamp(iat, tz=timezone.utc)
            if token_blacklist.is_user_blacklisted(user_id, issued_at):
                logger.warning(f"User token blacklisted: {user_id} (issued at {issued_at})")
                return None

        # JWT library handles expiration, but we can double-check
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            logger.warning(f"Token expired for subject: {payload.get('sub')}")
            return None

        return payload

    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        return None


def revoke_token(token: str) -> bool:
    """Revoke a specific token by adding its JTI to the blacklist."""
    try:
        # Get JTI and expiration without full verification
        unverified_payload = jwt.get_unverified_claims(token)
        jti = unverified_payload.get("jti")
        exp = unverified_payload.get("exp")

        if jti:
            # Calculate TTL based on token expiration
            ttl_seconds = None
            if exp:
                now = datetime.now(timezone.utc)
                exp_dt = datetime.fromtimestamp(exp, tz=timezone.utc)
                if exp_dt > now:
                    ttl_seconds = int((exp_dt - now).total_seconds())

            token_blacklist.add(jti, ttl_seconds)
            logger.info(f"Token revoked: {jti}")
            return True
        else:
            logger.warning("Token missing JTI, cannot revoke")
            return False

    except Exception as e:
        logger.error(f"Failed to revoke token: {e}")
        return False


def revoke_all_user_tokens(user_id: str) -> bool:
    """Revoke all tokens for a specific user."""
    try:
        success = token_blacklist.blacklist_all_user_tokens(user_id)
        if success:
            logger.info(f"All tokens revoked for user {user_id}")
        else:
            logger.warning(f"Failed to revoke all tokens for user {user_id}")
        return success
    except Exception as e:
        logger.error(f"Error revoking all user tokens: {e}")
        return False


def is_token_expired(token: str) -> bool:
    try:
        payload = jwt.get_unverified_claims(token)
        exp = payload.get("exp")
        if exp:
            return datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc)
        return True
    except Exception:
        return True


def extract_token_claims(token: str) -> Optional[Dict[str, Any]]:
    try:
        return jwt.get_unverified_claims(token)
    except Exception:
        return None


def _create_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
) -> str:
    now = datetime.now(timezone.utc)

    # Build token payload
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
        "jti": _generate_jti(),  # Unique token ID for revocation
    }

    try:
        # Encode token
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        logger.debug(f"{token_type} token created for subject {subject} with jti {payload['jti']}")
        return token

    except Exception as e:
        logger.error(f"Failed to create {token_type} token: {e}")
        raise TokenError(f"Token creation failed: {e}")


def _generate_jti() -> str:
    return secrets.token_urlsafe(16)


async def cleanup_expired_blacklist() -> None:
    """Cleanup expired tokens from blacklist."""
    if redis_client.is_available():
        logger.info("Redis TTL automatically handles token blacklist cleanup")
    else:
        logger.info("In-memory token blacklist - manual cleanup not available")

    token_blacklist.remove_expired()

import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Set

from jose import JWTError, jwt

from app.core.config import settings

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
    # TODO: Replace with Redis implementation for production.

    def __init__(self):
        self._blacklist: Set[str] = set()
        logger.warning("Using in-memory token blacklist - not suitable for production")

    def add(self, jti: str) -> None:
        """Add token JTI to blacklist."""
        self._blacklist.add(jti)

    def contains(self, jti: str) -> bool:
        """Check if token JTI is blacklisted."""
        return jti in self._blacklist

    def remove_expired(self) -> None:
        # TODO: Implement when using Redis with TTL.
        pass


# Initialize token blacklist (replace with Redis in production)
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

        # Check if token is blacklisted
        jti = payload.get("jti")
        if jti and token_blacklist.contains(jti):
            logger.warning(f"Blacklisted token used: {jti}")
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
    try:
        # Get JTI without full verification (token might be expired)
        unverified_payload = jwt.get_unverified_claims(token)
        jti = unverified_payload.get("jti")

        if jti:
            token_blacklist.add(jti)
            logger.info(f"Token revoked: {jti}")
            return True
        else:
            logger.warning("Token missing JTI, cannot revoke")
            return False

    except Exception as e:
        logger.error(f"Failed to revoke token: {e}")
        return False


def revoke_all_user_tokens(user_id: str) -> None:
    # TODO: Implement when using Redis or database storage.
    logger.info(f"Token revocation requested for user {user_id}")


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
    # TODO: Implement when using Redis with TTL or database storage.
    token_blacklist.remove_expired()
    logger.info("Token blacklist cleanup completed")

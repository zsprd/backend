import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import Request
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ----------------------
# Password Utilities
# ----------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def needs_rehash(hashed_password: str) -> bool:
    """Check if password hash needs to be updated."""
    return pwd_context.needs_update(hashed_password)


# ----------------------
# JWT & Tokens
# ----------------------
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"
TOKEN_TYPE_EMAIL_VERIFICATION = "email_verification"
TOKEN_TYPE_PASSWORD_RESET = "password_reset"


def _create_token(
    sub: str, token_type: str, expires: timedelta, extra_data: Optional[Dict[str, Any]] = None
) -> str:
    """Create a JWT token with specified type and expiration."""
    data = extra_data.copy() if extra_data else {}
    data.update(
        {
            "sub": sub,
            "type": token_type,
            "iat": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + expires,
            "jti": secrets.token_urlsafe(16),
        }
    )

    token = jwt.encode(data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.debug(f"{token_type} token created for {sub} with jti {data['jti']}")
    return token


def create_access_token(user_id: str, data: Optional[dict] = None) -> str:
    """Create an access token for a user."""
    return _create_token(
        user_id, TOKEN_TYPE_ACCESS, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), data
    )


def create_refresh_token(user_id: str) -> str:
    """Create a refresh token for a user."""
    return _create_token(
        user_id, TOKEN_TYPE_REFRESH, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )


def create_email_verification_token(email: str) -> str:
    """Create an email verification token."""
    return _create_token(
        email,
        TOKEN_TYPE_EMAIL_VERIFICATION,
        timedelta(hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS),
    )


def create_password_reset_token(email: str) -> str:
    """Create a password reset token."""
    return _create_token(
        email, TOKEN_TYPE_PASSWORD_RESET, timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)
    )


# ----------------------
# Token Verification
# ----------------------
def verify_token(token: str, token_type: str) -> Optional[Dict[str, Any]]:
    """Verify a JWT token and return its payload."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        # Check token type
        if payload.get("type") != token_type:
            logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
            return None

        # Check expiration
        exp = payload.get("exp")
        if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
            logger.warning(f"Token expired for subject: {payload.get('sub')}")
            return None

        # Note: JTI blacklist checking would be done here when Redis is implemented
        # For now, just return the payload

        return payload

    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {e}")
        return None


def verify_email_token(token: str) -> Optional[str]:
    """Verify an email verification token and return the email."""
    payload = verify_token(token, TOKEN_TYPE_EMAIL_VERIFICATION)
    return payload.get("sub") if payload else None


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify a password reset token and return the email."""
    payload = verify_token(token, TOKEN_TYPE_PASSWORD_RESET)
    return payload.get("sub") if payload else None


def get_user_id_from_token(token: str) -> Optional[str]:
    """Extract user ID from an access or refresh token."""
    # Try access token first
    payload = verify_token(token, TOKEN_TYPE_ACCESS)
    if not payload:
        # Try refresh token
        payload = verify_token(token, TOKEN_TYPE_REFRESH)

    return payload.get("sub") if payload else None


# ----------------------
# Client Info & Misc
# ----------------------
def get_client_ip(request: Request) -> str:
    """Extract client IP address from request."""
    # Check for proxy headers first
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        return forwarded_for.split(",")[0].strip()

    # Check for other proxy headers
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()

    # Fall back to direct client connection
    if request.client:
        return request.client.host

    return "unknown"


def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID."""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def sanitize_user_agent(user_agent: Optional[str]) -> str:
    """Sanitize and truncate user agent string."""
    if not user_agent:
        return "unknown"

    # Remove any control characters and limit length
    sanitized = "".join(char for char in user_agent if char.isprintable())
    return sanitized.strip()[:500]


def generate_secure_random_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def is_strong_password(password: str) -> bool:
    """Check if a password meets strength requirements."""
    import re

    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False

    return True

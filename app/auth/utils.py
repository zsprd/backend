import logging
import re
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Set

from fastapi import Request
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ----------------------
# Password Utilities
# ----------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def needs_rehash(hashed_password: str) -> bool:
    return pwd_context.needs_update(hashed_password)


def validate_strong_password(value: str) -> str:
    if not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", value):
        raise ValueError("Password must contain at least one lowercase letter")
    if not re.search(r"\d", value):
        raise ValueError("Password must contain at least one number")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
        raise ValueError("Password must contain at least one special character")
    return value


# ----------------------
# JWT & Tokens
# ----------------------
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"
TOKEN_TYPE_EMAIL_VERIFICATION = "email_verification"
TOKEN_TYPE_PASSWORD_RESET = "password_reset"

BLACKLISTED_JTIS: Set[str] = set()
logger = logging.getLogger("auth.utils")


def _create_token(
    sub: str, token_type: str, expires: timedelta, extra_data: Optional[Dict[str, Any]] = None
) -> str:
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
    return _create_token(
        user_id, TOKEN_TYPE_ACCESS, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES), data
    )


def create_refresh_token(user_id: str) -> str:
    return _create_token(
        user_id, TOKEN_TYPE_REFRESH, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )


def create_email_verification_token(email: str) -> str:
    return _create_token(
        email,
        TOKEN_TYPE_EMAIL_VERIFICATION,
        timedelta(hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS),
    )


def create_password_reset_token(email: str) -> str:
    return _create_token(
        email, TOKEN_TYPE_PASSWORD_RESET, timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES)
    )


# ----------------------
# Token Verification
# ----------------------
def verify_token(token: str, token_type: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != token_type:
            logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
            return None
        jti = payload.get("jti")
        if jti and is_token_blacklisted(jti):
            logger.warning(f"Token with jti {jti} is blacklisted.")
            return None
        return payload
    except JWTError as e:
        logger.error(f"JWT verification failed: {e}")
        return None


def verify_email_token(token: str) -> Optional[str]:
    payload = verify_token(token, TOKEN_TYPE_EMAIL_VERIFICATION)
    return payload.get("sub") if payload else None


def verify_password_reset_token(token: str) -> Optional[str]:
    payload = verify_token(token, TOKEN_TYPE_PASSWORD_RESET)
    return payload.get("sub") if payload else None


def is_token_blacklisted(jti: str) -> bool:
    return jti in BLACKLISTED_JTIS


def blacklist_token(jti: str) -> None:
    BLACKLISTED_JTIS.add(jti)
    logger.info(f"Token with jti {jti} has been blacklisted.")


def get_user_id_from_token(token: str) -> Optional[str]:
    payload = verify_token(token, TOKEN_TYPE_ACCESS) or verify_token(token, TOKEN_TYPE_REFRESH)
    return payload.get("sub") if payload else None


# ----------------------
# Client Info & Misc
# ----------------------
def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


def is_valid_uuid(value: str) -> bool:
    try:
        uuid.UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def sanitize_user_agent(user_agent: Optional[str]) -> str:
    if not user_agent:
        return "unknown"
    return user_agent.strip()[:500]

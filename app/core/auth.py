import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import Request
from jose import jwt
from jose.exceptions import JWTError
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token types
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"
TOKEN_TYPE_EMAIL_VERIFICATION = "email_verification"
TOKEN_TYPE_PASSWORD_RESET = "password_reset"


def hash_password(password: str) -> str:
    """Hash password with bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update(
        {
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": TOKEN_TYPE_ACCESS,
            "jti": secrets.token_urlsafe(16),
        }
    )

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create JWT refresh token."""
    to_encode = {
        "sub": user_id,
        "type": TOKEN_TYPE_REFRESH,
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        "iat": datetime.now(timezone.utc),
        "jti": secrets.token_urlsafe(16),
    }

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_email_verification_token(email: str) -> str:
    """Create email verification token."""
    to_encode = {
        "sub": email,
        "type": TOKEN_TYPE_EMAIL_VERIFICATION,
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=settings.EMAIL_VERIFICATION_EXPIRE_HOURS),
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_password_reset_token(email: str) -> str:
    """Create password reset token."""
    to_encode = {
        "sub": email,
        "type": TOKEN_TYPE_PASSWORD_RESET,
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES),
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str, token_type: str) -> Optional[Dict[str, Any]]:
    """Verify JWT token and return payload."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])

        if payload.get("type") != token_type:
            return None

        return payload
    except JWTError:
        return None


def verify_email_token(token: str) -> Optional[str]:
    """Verify email verification token and return email."""
    payload = verify_token(token, TOKEN_TYPE_EMAIL_VERIFICATION)
    return payload.get("sub") if payload else None


def verify_password_reset_token(token: str) -> Optional[str]:
    """Verify password reset token and return email."""
    payload = verify_token(token, TOKEN_TYPE_PASSWORD_RESET)
    return payload.get("sub") if payload else None


def get_client_ip(request: Request) -> str:
    """Get client IP from request headers."""
    # Check for forwarded headers (behind proxy)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    return request.client.host if request.client else "unknown"


def check_password_strength(password: str) -> dict:
    """Enhanced password strength checking for fintech security."""
    checks = {
        "min_length": len(password) >= 8,
        "has_uppercase": any(c.isupper() for c in password),
        "has_lowercase": any(c.islower() for c in password),
        "has_digit": any(c.isdigit() for c in password),
        "has_special": any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password),
        "no_common_sequences": not _has_common_sequences(password),
    }

    score = sum(checks.values())

    if score < 4:
        strength = "weak"
    elif score < 6:
        strength = "medium"
    else:
        strength = "strong"

    return {
        "score": score,
        "max_score": len(checks),
        "checks": checks,
        "strength": strength,
        "is_valid": score >= 5,  # Require 5/6 criteria
    }


def _has_common_sequences(password: str) -> bool:
    """Check for common sequential patterns."""
    common_sequences = [
        "123456",
        "654321",
        "abcdef",
        "qwerty",
        "password",
        "admin",
        "letmein",
        "welcome",
        "monkey",
        "dragon",
    ]

    password_lower = password.lower()
    return any(seq in password_lower for seq in common_sequences)

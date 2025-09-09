from datetime import datetime, timedelta
from typing import Optional
import secrets
import uuid
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

# Initialize bcrypt context for secure password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token security
security = HTTPBearer()

# Token types
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"
TOKEN_TYPE_EMAIL_VERIFICATION = "email_verification"
TOKEN_TYPE_PASSWORD_RESET = "password_reset"

# Fintech-appropriate token expiration times
ACCESS_TOKEN_EXPIRE_MINUTES = 30      # 30 minutes for security
REFRESH_TOKEN_EXPIRE_DAYS = 90        # 90 days for user convenience
EMAIL_VERIFICATION_EXPIRE_HOURS = 24  # 24 hours
PASSWORD_RESET_EXPIRE_HOURS = 1       # 1 hour for security

# Import user_crud (will be defined later)
from app.crud.user import user_crud


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt with salt.
    This is called when user registers or changes password.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plaintext password against its bcrypt hash.
    Used during login to validate user credentials.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Token payload (should include 'sub' with user_id)
        expires_delta: Custom expiration time (optional)
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": TOKEN_TYPE_ACCESS,
        "jti": secrets.token_urlsafe(16)  # Unique token ID
    })
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """
    Create a JWT refresh token with longer expiration.
    Used to obtain new access tokens without re-authentication.
    """
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {
        "sub": user_id,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": TOKEN_TYPE_REFRESH,
        "jti": secrets.token_urlsafe(16)
    }
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_email_verification_token(email: str) -> str:
    """
    Create a token for email verification.
    Token expires in 24 hours.
    """
    expire = datetime.utcnow() + timedelta(hours=EMAIL_VERIFICATION_EXPIRE_HOURS)
    to_encode = {
        "sub": email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": TOKEN_TYPE_EMAIL_VERIFICATION,
        "jti": secrets.token_urlsafe(16)
    }
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_password_reset_token(email: str) -> str:
    """
    Create a token for password reset.
    Token expires in 1 hour for security.
    """
    expire = datetime.utcnow() + timedelta(hours=PASSWORD_RESET_EXPIRE_HOURS)
    to_encode = {
        "sub": email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": TOKEN_TYPE_PASSWORD_RESET,
        "jti": secrets.token_urlsafe(16)
    }
    
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str, expected_type: str = TOKEN_TYPE_ACCESS) -> Optional[dict]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        expected_type: Expected token type for validation
        
    Returns:
        Token payload if valid, None if invalid
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Verify token type
        if payload.get("type") != expected_type:
            return None
            
        # Check expiration (jwt.decode already handles this, but explicit check)
        exp = payload.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            return None
            
        return payload
        
    except JWTError:
        return None


def verify_email_token(token: str) -> Optional[str]:
    """
    Verify email verification token and return email if valid.
    """
    payload = verify_token(token, TOKEN_TYPE_EMAIL_VERIFICATION)
    if payload:
        return payload.get("sub")  # Email is stored in 'sub'
    return None


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify password reset token and return email if valid.
    """
    payload = verify_token(token, TOKEN_TYPE_PASSWORD_RESET)
    if payload:
        return payload.get("sub")  # Email is stored in 'sub'
    return None


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extract and validate the current user ID from JWT access token.
    Raises HTTP 401 if token is invalid or expired.
    """
    token = credentials.credentials
    payload = verify_token(token, TOKEN_TYPE_ACCESS)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token missing user ID",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate UUID format
    try:
        uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user_id


def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user object from database.
    Raises HTTP 404 if user not found, HTTP 400 if user inactive.
    """
    user = user_crud.get(db, id=user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account is disabled"
        )
    
    return user


def get_optional_current_user_id(request: Request) -> Optional[str]:
    """
    Optional authentication - returns user ID if valid token provided.
    Returns None if no token or invalid token (doesn't raise exception).
    Useful for endpoints that work for both authenticated and anonymous users.
    """
    authorization = request.headers.get("Authorization")
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.split(" ")[1]
    payload = verify_token(token, TOKEN_TYPE_ACCESS)
    
    if payload is None:
        return None
    
    user_id = payload.get("sub")
    if user_id is None:
        return None
    
    try:
        uuid.UUID(user_id)
        return user_id
    except ValueError:
        return None


def get_optional_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise.
    Used for endpoints that enhance functionality when user is logged in.
    """
    user_id = get_optional_current_user_id(request)
    if not user_id:
        return None
    
    user = user_crud.get(db, id=user_id)
    if not user or not user.is_active:
        return None
    
    return user


# Session management helpers
def generate_session_token() -> str:
    """Generate a secure random session token."""
    return secrets.token_urlsafe(32)


def generate_api_key() -> str:
    """Generate a secure API key for future external integrations."""
    return f"zsprd_{secrets.token_urlsafe(32)}"


# Security utilities
def check_password_strength(password: str) -> dict:
    """
    Check password strength and return detailed analysis.
    Useful for frontend password strength indicators.
    """
    checks = {
        "min_length": len(password) >= 8,
        "has_uppercase": any(c.isupper() for c in password),
        "has_lowercase": any(c.islower() for c in password),
        "has_digit": any(c.isdigit() for c in password),
        "has_special": any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    }
    
    score = sum(checks.values())
    
    # Determine strength level
    if score < 3:
        strength = "weak"
    elif score < 5:
        strength = "medium" 
    else:
        strength = "strong"
    
    return {
        "score": score,
        "max_score": len(checks),
        "checks": checks,
        "strength": strength,
        "is_valid": score >= 4  # Require at least 4/5 criteria
    }


def validate_token_payload(payload: dict, required_fields: list = None) -> bool:
    """
    Validate JWT token payload has required fields.
    """
    if not payload:
        return False
    
    required_fields = required_fields or ["sub", "exp", "iat", "type"]
    
    for field in required_fields:
        if field not in payload:
            return False
    
    return True


# Rate limiting helpers (for future Redis implementation)
def get_client_ip(request: Request) -> str:
    """Get client IP address from request headers."""
    # Check for forwarded headers first (common in production)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    return request.client.host if request.client else "unknown"


def create_rate_limit_key(identifier: str, action: str) -> str:
    """Create Redis key for rate limiting."""
    return f"rate_limit:{action}:{identifier}"


def create_login_attempt_key(email: str, ip: str) -> str:
    """Create Redis key for failed login attempt tracking."""
    return f"login_attempts:{email}:{ip}"


# Constants for easy configuration
FINTECH_SECURITY_SETTINGS = {
    "access_token_expire_minutes": ACCESS_TOKEN_EXPIRE_MINUTES,
    "refresh_token_expire_days": REFRESH_TOKEN_EXPIRE_DAYS,
    "email_verification_expire_hours": EMAIL_VERIFICATION_EXPIRE_HOURS,
    "password_reset_expire_hours": PASSWORD_RESET_EXPIRE_HOURS,
    "max_login_attempts": 5,
    "login_lockout_minutes": 15,
    "password_reset_per_hour": 3,
    "auth_requests_per_minute": 20
}
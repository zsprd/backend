from datetime import datetime, timedelta
from typing import Optional, Union
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from app.core.config import settings
from app.core.database import get_db
from app.crud.user import user_crud
from app.models.user import User
from sqlalchemy.orm import Session
import uuid
import secrets

# Security scheme for Bearer token
security = HTTPBearer()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Token types for different purposes
TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_EMAIL_VERIFICATION = "email_verification"
TOKEN_TYPE_PASSWORD_RESET = "password_reset"


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token with the given data and expiration time.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)  # 15 minutes for financial app
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": TOKEN_TYPE_ACCESS
    })
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_email_verification_token(email: str) -> str:
    """
    Create a JWT token for email verification.
    Token expires in 24 hours.
    """
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode = {
        "sub": email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": TOKEN_TYPE_EMAIL_VERIFICATION,
        "jti": secrets.token_urlsafe(16)  # Unique token ID
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_password_reset_token(email: str) -> str:
    """
    Create a JWT token for password reset.
    Token expires in 1 hour for security.
    """
    expire = datetime.utcnow() + timedelta(hours=1)
    to_encode = {
        "sub": email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": TOKEN_TYPE_PASSWORD_RESET,
        "jti": secrets.token_urlsafe(16)  # Unique token ID
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str, token_type: str = TOKEN_TYPE_ACCESS) -> Optional[dict]:
    """
    Verify and decode a JWT token.
    Returns the payload if valid, None if invalid.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        # Check token type
        if payload.get("type") != token_type:
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


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    Note: In this app, passwords are hashed on frontend,
    so this is used for double-hashing if needed.
    """
    return pwd_context.hash(password)


def verify_password_hash(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    Since frontend sends hashed passwords, this compares:
    frontend_hash == stored_hash
    """
    # For frontend-hashed passwords, we do direct comparison
    # If you want double-hashing, use: pwd_context.verify(plain_password, hashed_password)
    return plain_password == hashed_password


def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extract and validate the current user ID from JWT token.
    This dependency can be used in route handlers to get the authenticated user ID.
    """
    token = credentials.credentials
    payload = verify_token(token, TOKEN_TYPE_ACCESS)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate that user_id is a valid UUID
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
    Get the current user object from the database.
    This dependency can be used when you need the full user object.
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
            detail="Inactive user"
        )
    
    return user


def get_optional_current_user_id(
    request: Request
) -> Optional[str]:
    """
    Optional authentication - returns user ID if valid token is provided,
    None if no token or invalid token.
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
    Useful for endpoints that work for both authenticated and anonymous users.
    """
    user_id = get_optional_current_user_id(request)
    if not user_id:
        return None
    
    user = user_crud.get(db, id=user_id)
    if not user or not user.is_active:
        return None
    
    return user


# Helper functions for session management
def generate_session_token() -> str:
    """Generate a secure random session token."""
    return secrets.token_urlsafe(32)


def generate_api_key() -> str:
    """Generate a secure API key for external integrations."""
    return f"zsprd_{secrets.token_urlsafe(32)}"


# Security utilities
def check_password_strength(password: str) -> dict:
    """
    Check password strength and return requirements.
    This is mainly for frontend guidance.
    """
    checks = {
        "length": len(password) >= 8,
        "uppercase": any(c.isupper() for c in password),
        "lowercase": any(c.islower() for c in password),
        "digit": any(c.isdigit() for c in password),
        "special": any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password)
    }
    
    score = sum(checks.values())
    
    return {
        "score": score,
        "max_score": len(checks),
        "checks": checks,
        "strength": "weak" if score < 3 else "medium" if score < 5 else "strong"
    }


def validate_token_payload(payload: dict, required_fields: list = None) -> bool:
    """
    Validate JWT token payload has required fields.
    """
    if not payload:
        return False
    
    required_fields = required_fields or ["sub", "exp", "iat"]
    
    for field in required_fields:
        if field not in payload:
            return False
    
    # Check if token is expired
    exp = payload.get("exp")
    if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
        return False
    
    return True


# Rate limiting helpers (for future implementation)
def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def create_login_attempt_key(email: str, ip: str) -> str:
    """Create Redis key for login attempt tracking."""
    return f"login_attempts:{email}:{ip}"


# NextAuth.js compatibility (if needed)
def verify_nextauth_token(token: str) -> Optional[dict]:
    """
    Verify NextAuth.js JWT tokens.
    You might need to adjust this based on your NextAuth.js configuration.
    """
    try:
        # If using NextAuth.js with a different secret, use that secret here
        # For now, using the same secret as defined in settings
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


# Constants for token validation
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
EMAIL_VERIFICATION_EXPIRE_HOURS = 24
PASSWORD_RESET_EXPIRE_HOURS = 1
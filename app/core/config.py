import sys
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import EmailStr, ValidationError
from pydantic_settings import BaseSettings

env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)


class Settings(BaseSettings):
    # Basic App Settings
    APP_NAME: str = "ZSPRD Portfolio Analytics"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "Portfolio analytics and insights platform"
    API_PREFIX: str = "v1"
    ENVIRONMENT: str = "development"  # Set to "production" in prod
    DEBUG: bool = True  # Set to False in production

    # Security Settings
    SECRET_KEY: str  # Must be set in .env
    ALGORITHM: str = "HS256"

    # JWT Token Expiration
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30  # 30 minutes for balance of securities/UX
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30  # 30 days for less frequent logins
    VERIFICATION_TOKEN_EXPIRE_HOURS: int = 24  # 24 hours
    RESET_TOKEN_EXPIRE_MINUTES: int = 60  # 1 hour for securities

    # OAuth Configuration
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    APPLE_CLIENT_ID: Optional[str] = None
    APPLE_CLIENT_SECRET: Optional[str] = None
    APPLE_KEY_ID: Optional[str] = None
    APPLE_TEAM_ID: Optional[str] = None
    APPLE_PRIVATE_KEY_PATH: Optional[str] = None

    # Auth URLs
    FRONTEND_URL: str = "http://localhost:3000"
    OAUTH_REDIRECT_URI: str = "http://localhost:3000/auth/callback"

    # Password Security Requirements
    MIN_PASSWORD_LENGTH: int = 8
    MAX_PASSWORD_LENGTH: int = 128
    REQUIRE_PASSWORD_UPPERCASE: bool = True
    REQUIRE_PASSWORD_LOWERCASE: bool = True
    REQUIRE_PASSWORD_DIGIT: bool = True
    REQUIRE_PASSWORD_SPECIAL: bool = False

    # Rate Limiting (requests per time window)
    RATE_LIMIT_REGISTER: str = "3/hour"  # Limit signups to prevent abuse
    RATE_LIMIT_LOGIN: str = "5/15minutes"  # Limit login attempts to prevent brute force
    RATE_LIMIT_REFRESH: str = "100/hour"  # Allow frequent token refreshes
    RATE_LIMIT_PASSWORD: str = "5/hour"  # Limit password reset attempts
    RATE_LIMIT_VERIFY: str = "10/hour"  # Limit email verification attempts
    RATE_LIMIT_UPDATE: str = "20/hour"  # Limit profile updates

    # Session Management
    MAX_FAILED_ATTEMPTS: int = 5  # Max failed login attempts
    ACCOUNT_LOCKOUT_MINUTES: int = 15  # Lockout duration after max attempts
    MAX_ACTIVE_SESSIONS: int = 5  # Limit concurrent sessions
    SESSION_INACTIVE_DAYS: int = 30  # Extend session by 30 days
    REMEMBER_ME_DAYS: int = 30  # Remember me duration

    # Security Headers
    CORS_ORIGINS: list = [
        "http://localhost:3000",  # Next.js dev
        "https://app.zsprd.com",  # Production frontend
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    CORS_ALLOW_HEADERS: list = ["*"]

    # Database Settings
    POSTGRES_HOST: str  # e.g. "localhost" or a remote host
    POSTGRES_PORT: int = 5432  # Default PostgreSQL port
    POSTGRES_USER: str  # e.g. "myuser"
    POSTGRES_PASSWORD: str  # e.g. "mypassword"
    POSTGRES_DB: str  # e.g. "mydatabase"
    DATABASE_URL: str  # Constructed below if not set directly
    DATABASE_ECHO: bool = True  # Log SQL queries for debugging
    POOL_SIZE: int = 10  # Adjust based on expected load
    MAX_OVERFLOW: int = 20  # Allow some overflow connections
    POOL_TIMEOUT: int = 30  # Seconds to wait for a connection
    POOL_RECYCLE: int = 1800  # Recycle connections every 30 minutes
    ALEMBIC_URL: Optional[str] = None  # If different from DATABASE_URL

    # Redis Settings (for caching and rate limiting)
    REDIS_URL: Optional[str] = None
    REDIS_PASSWORD: Optional[str] = None
    CACHE_EXPIRE_SECONDS: int = 0

    # Email Settings (for verification and password reset)
    MAIL_SERVER: str
    MAIL_PORT: int = 587
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_FROM: EmailStr
    MAIL_FROM_NAME: str

    # External API Keys
    ALPHA_VANTAGE_API_KEY: str = ""

    # Logging and Monitoring
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: Optional[str] = None
    SENTRY_DSN: Optional[str] = None

    # Security Monitoring
    ENABLE_AUDIT_LOGS: bool = True
    TRACK_LOGIN_ATTEMPTS: bool = True
    ALERT_ON_SUSPICIOUS_LOGIN: bool = True
    NEW_DEVICE_NOTIFICATION: bool = True

    # API Documentation
    DOCS_URL: str = "/api/v1/docs"
    REDOC_URL: str = "/api/v1/redoc"
    OPENAPI_URL: str = "/api/v1/openapi.json"

    # Production Security Settings
    REQUIRE_HTTPS: bool = False  # Set to True in production
    SECURE_COOKIES: bool = False  # Set to True in production
    HSTS_MAX_AGE: int = 31536000  # 1 year

    class Config:
        env_file = ".env"
        extra = "ignore"
        case_sensitive = True

    @property
    def security_config(self) -> dict:
        """Get all securities settings in one dict."""
        return {
            "access_token_expire_minutes": self.ACCESS_TOKEN_EXPIRE_MINUTES,
            "refresh_token_expire_days": self.REFRESH_TOKEN_EXPIRE_DAYS,
            "email_verification_expire_hours": self.VERIFICATION_TOKEN_EXPIRE_HOURS,
            "password_reset_expire_minutes": self.RESET_TOKEN_EXPIRE_MINUTES,
            "max_login_attempts": self.RATE_LIMIT_PASSWORD,
            "account_lockout_minutes": self.ACCOUNT_LOCKOUT_MINUTES,
            "max_active_sessions": self.MAX_ACTIVE_SESSIONS,
            "require_strong_passwords": True,
            "enable_token_rotation": True,
            "track_session_security": True,
        }

    @property
    def password_requirements(self) -> dict:
        """Get password requirements for frontend validation."""
        return {
            "min_length": self.MIN_PASSWORD_LENGTH,
            "require_uppercase": self.REQUIRE_PASSWORD_UPPERCASE,
            "require_lowercase": self.REQUIRE_PASSWORD_LOWERCASE,
            "require_digits": self.REQUIRE_PASSWORD_DIGIT,
            "require_special_chars": self.REQUIRE_PASSWORD_SPECIAL,
        }


# Create global settings instance
settings = Settings()

# --- Startup check for missing required environment variables ---


def _check_required_env(settings_obj):
    missing = []
    for name, field in settings_obj.model_fields.items():
        required = field.is_required()
        value = getattr(settings_obj, name, None)
        # If required and value is None or empty string
        if required and (value is None or (isinstance(value, str) and value.strip() == "")):
            missing.append(name)
    if missing:
        print(
            f"\n[ERROR] The following required environment variables are missing or empty: {', '.join(missing)}\n",
            file=sys.stderr,
        )
        sys.exit(1)


try:
    _check_required_env(settings)
except ValidationError as e:
    print(f"\n[ERROR] Settings validation error: {e}\n", file=sys.stderr)
    sys.exit(1)

# Security middleware configuration
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": f"max-age={settings.HSTS_MAX_AGE}; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}

# Rate limiting configuration for different endpoints
RATE_LIMIT_CONFIG = {
    "auth_signin": "5/15minutes",  # 5 attempts per 15 minutes
    "auth_signup": "3/hour",  # 3 signups per hour
    "auth_refresh": "10/5minutes",  # 10 refreshes per 5 minutes
    "auth_forgot_password": "3/hour",  # 3 password resets per hour
    "auth_general": "20/minute",  # 20 general auth requests per minute
    "api_general": "100/minute",  # 100 general API requests per minute
}

# JWT Token blacklist for enhanced securities (optional Redis implementation)
TOKEN_BLACKLIST_ENABLED = True

# Audit log events to track
AUDIT_EVENTS = [
    "user_signin",
    "user_signup",
    "user_signout",
    "password_change",
    "password_reset",
    "email_verify",
    "profile_update",
    "session_revoke",
    "suspicious_activity",
]

from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class Settings(BaseSettings):
    # Basic App Settings
    APP_NAME: str = "ZSPRD Portfolio Analytics"
    VERSION: str = "1.0.0"
    API_VERSION: str = "v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True  # Set to False in production
    
    # Security Settings
    SECRET_KEY: str = secrets.token_urlsafe(32)  # Generate secure key
    ALGORITHM: str = "HS256"
    
    # JWT Token Expiration
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30      # 30 minutes for balance of security/UX
    REFRESH_TOKEN_EXPIRE_DAYS: int = 90        # 90 days for less frequent logins
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24  # 24 hours
    PASSWORD_RESET_EXPIRE_MINUTES: int = 60    # 1 hour for security

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
    REQUIRE_UPPERCASE: bool = True
    REQUIRE_LOWERCASE: bool = True
    REQUIRE_DIGITS: bool = True
    REQUIRE_SPECIAL_CHARS: bool = False  # Optional for better UX
    
    # Rate Limiting (requests per time window)
    LOGIN_RATE_LIMIT: str = "5/15minutes"      # 5 attempts per 15 minutes
    SIGNUP_RATE_LIMIT: str = "3/hour"          # 3 signups per hour per IP
    PASSWORD_RESET_RATE_LIMIT: str = "3/hour"  # 3 reset requests per hour
    AUTH_GENERAL_RATE_LIMIT: str = "20/minute" # 20 auth requests per minute
    
    # Session Management
    MAX_ACTIVE_SESSIONS_PER_USER: int = 5      # Limit concurrent sessions
    SESSION_CLEANUP_INTERVAL_HOURS: int = 24   # Clean expired sessions daily
    REMEMBER_ME_EXTEND_DAYS: int = 30          # Extend session by 30 days
    
    # Security Headers
    CORS_ORIGINS: list = [
        "http://localhost:3000",  # Next.js dev
        "https://app.zsprd.com",  # Production frontend
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list = ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]
    CORS_ALLOW_HEADERS: list = ["*"]
    
    # Database Settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    DATABASE_URL: Optional[str] = None
    DATABASE_ECHO: bool = True  # Set to True for SQL debugging
    
    # Redis Settings (for caching and rate limiting)
    REDIS_URL: Optional[str] = None
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    
    # Email Settings (for verification and password reset)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    FROM_EMAIL: str = "noreply@zsprd.com"
    FROM_NAME: str = "ZSPRD Portfolio Analytics"
    
    # External API Keys
    ALPHA_VANTAGE_API_KEY: Optional[str] = None
    
    # Logging and Monitoring
    LOG_LEVEL: str = "INFO"
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
        case_sensitive = True

    @property
    def security_config(self) -> dict:
        """Get all security settings in one dict."""
        return {
            "access_token_expire_minutes": self.ACCESS_TOKEN_EXPIRE_MINUTES,
            "refresh_token_expire_days": self.REFRESH_TOKEN_EXPIRE_DAYS,
            "email_verification_expire_hours": self.EMAIL_VERIFICATION_EXPIRE_HOURS,
            "password_reset_expire_minutes": self.PASSWORD_RESET_EXPIRE_MINUTES,
            "max_login_attempts": 5,
            "login_lockout_minutes": 15,
            "password_reset_per_hour": 3,
            "auth_requests_per_minute": 20,
            "max_active_sessions": self.MAX_ACTIVE_SESSIONS_PER_USER,
            "require_strong_passwords": True,
            "enable_token_rotation": True,
            "track_session_security": True
        }

    @property
    def password_requirements(self) -> dict:
        """Get password requirements for frontend validation."""
        return {
            "min_length": self.MIN_PASSWORD_LENGTH,
            "require_uppercase": self.REQUIRE_UPPERCASE,
            "require_lowercase": self.REQUIRE_LOWERCASE,
            "require_digits": self.REQUIRE_DIGITS,
            "require_special_chars": self.REQUIRE_SPECIAL_CHARS
        }


# Create global settings instance
settings = Settings()


# Security middleware configuration
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "X-XSS-Protection": "1; mode=block",
    "Strict-Transport-Security": f"max-age={settings.HSTS_MAX_AGE}; includeSubDomains",
    "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
}

# Rate limiting configuration for different endpoints
RATE_LIMIT_CONFIG = {
    "auth_signin": "5/15minutes",      # 5 attempts per 15 minutes
    "auth_signup": "3/hour",           # 3 signups per hour
    "auth_refresh": "10/5minutes",     # 10 refreshes per 5 minutes
    "auth_forgot_password": "3/hour",  # 3 password resets per hour
    "auth_general": "20/minute",       # 20 general auth requests per minute
    "api_general": "100/minute"        # 100 general API requests per minute
}

# JWT Token blacklist for enhanced security (optional Redis implementation)
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
    "suspicious_activity"
]
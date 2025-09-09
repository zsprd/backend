from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
import os
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "ZSPRD Portfolio Analytics API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # API Configuration
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Reduced for financial app security
    
    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "zsprd_dev"
    POSTGRES_USER: str = "zsprd_dev"
    POSTGRES_PASSWORD: str = "secure"
    DATABASE_URL: Optional[str] = None
    
    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        return (
            f"postgresql://{values.get('POSTGRES_USER')}:"
            f"{values.get('POSTGRES_PASSWORD')}@"
            f"{values.get('POSTGRES_HOST')}:"
            f"{values.get('POSTGRES_PORT')}/"
            f"{values.get('POSTGRES_DB')}"
        )
    
    # Email Configuration
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""  # Your Gmail address
    SMTP_PASSWORD: str = ""  # Your Gmail app password
    FROM_EMAIL: Optional[str] = None
    FROM_NAME: str = "ZSPRD Portfolio Analytics"
    
    @field_validator("FROM_EMAIL", mode="before")
    def assemble_from_email(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        return values.get('SMTP_USERNAME', '')
    
    # Frontend Configuration
    FRONTEND_URL: str = "http://localhost:3000"
    
    # External APIs
    ALPHA_VANTAGE_API_KEY: str
    ALPHA_VANTAGE_BASE_URL: str = "https://www.alphavantage.co/query"
    ALPHA_VANTAGE_RATE_LIMIT: int = 5  # requests per minute for free tier
    
    # Redis (optional)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None
    
    # @field_validator("REDIS_URL", mode="before")
    # def assemble_redis_connection(cls, v: Optional[str], values: dict) -> str:
    #     if isinstance(v, str):
    #         return v
    #     return (
    #         f"redis://{values.get('REDIS_HOST')}:"
    #         f"{values.get('REDIS_PORT')}/"
    #         f"{values.get('REDIS_DB')}"
    #     )
    
    # CORS
    BACKEND_CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Security Settings
    PASSWORD_MIN_LENGTH: int = 8
    MAX_LOGIN_ATTEMPTS: int = 5
    LOGIN_ATTEMPT_TIMEOUT_MINUTES: int = 15
    
    # Session Management
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MAX_CONCURRENT_SESSIONS: int = 5
    SESSION_CLEANUP_INTERVAL_HOURS: int = 24
    
    # Email Token Expiration
    EMAIL_VERIFICATION_EXPIRE_HOURS: int = 24
    PASSWORD_RESET_EXPIRE_HOURS: int = 1
    
    # Cache and Performance
    CACHE_TTL_SECONDS: int = 3600  # 1 hour
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW_MINUTES: int = 15
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 10
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    # Feature Flags
    ENABLE_EMAIL_VERIFICATION: bool = True
    ENABLE_PASSWORD_RESET: bool = True
    ENABLE_SOCIAL_LOGIN: bool = True
    ENABLE_RATE_LIMITING: bool = True
    
    # Development Settings
    SEND_REAL_EMAILS: bool = False  # Set to True in production
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Database connection string for SQLAlchemy
DATABASE_URL = settings.DATABASE_URL

# JWT Configuration
JWT_SECRET_KEY = settings.SECRET_KEY
JWT_ALGORITHM = settings.ALGORITHM
JWT_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

# Email Configuration
EMAIL_CONFIG = {
    "smtp_server": settings.SMTP_SERVER,
    "smtp_port": settings.SMTP_PORT,
    "smtp_username": settings.SMTP_USERNAME,
    "smtp_password": settings.SMTP_PASSWORD,
    "from_email": settings.FROM_EMAIL,
    "from_name": settings.FROM_NAME,
    "frontend_url": settings.FRONTEND_URL
}

# Security Configuration
SECURITY_CONFIG = {
    "password_min_length": settings.PASSWORD_MIN_LENGTH,
    "max_login_attempts": settings.MAX_LOGIN_ATTEMPTS,
    "login_attempt_timeout": settings.LOGIN_ATTEMPT_TIMEOUT_MINUTES,
    "refresh_token_expire_days": settings.REFRESH_TOKEN_EXPIRE_DAYS,
    "max_concurrent_sessions": settings.MAX_CONCURRENT_SESSIONS
}
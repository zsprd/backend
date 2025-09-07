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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
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
    
    # External APIs
    ALPHA_VANTAGE_API_KEY: str
    ALPHA_VANTAGE_BASE_URL: str = "https://www.alphavantage.co/query"
    ALPHA_VANTAGE_RATE_LIMIT: int = 5  # requests per minute for free tier
    
    # Redis (optional)
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None
    
    @field_validator("REDIS_URL", mode="before")
    def assemble_redis_connection(cls, v: Optional[str], values: dict) -> str:
        if isinstance(v, str):
            return v
        return (
            f"redis://{values.get('REDIS_HOST')}:"
            f"{values.get('REDIS_PORT')}/"
            f"{values.get('REDIS_DB')}"
        )
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Cache and Performance
    CACHE_TTL_SECONDS: int = 3600  # 1 hour
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
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
from typing import AsyncGenerator

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in settings.")

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # Log SQL queries if in debug mode
    pool_pre_ping=True,  # Check connections before using
    pool_size=settings.POOL_SIZE,  # Maintain a pool of 5 connections
    max_overflow=settings.MAX_OVERFLOW,  # Allow up to 10 overflow connections
    pool_timeout=settings.POOL_TIMEOUT,  # 30 seconds timeout for getting connections from the pool
    pool_recycle=settings.POOL_RECYCLE,  # Recycle connections after 1800 seconds
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,  # Use AsyncSession for async operations
    expire_on_commit=False,  # Prevent attribute expiration on commit
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI routes to get database sessions."""
    async with AsyncSessionLocal() as session:
        try:
            yield session  # Provide the session to the route
        except SQLAlchemyError:
            await session.rollback()  # Rollback on error
            raise


__all__ = [
    "Base",
    "get_db",
    "engine",
    "AsyncSessionLocal",
]

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

# Create SQLAlchemy engine
if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in settings.")

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=300,  # Recycle connections every 5 minutes
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Database dependency that creates a new database session for each request,
    closes it when the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Optional: Create async database setup if needed in the future
# from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
# from sqlalchemy.orm import sessionmaker as async_sessionmaker

# Async engine (uncomment if you want to use async operations)
# async_engine = create_async_engine(
#     settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
#     echo=settings.DEBUG
# )
#
# AsyncSessionLocal = async_sessionmaker(
#     async_engine, class_=AsyncSession, expire_on_commit=False
# )
#
# async def get_async_db() -> AsyncSession:
#     async with AsyncSessionLocal() as session:
#         yield session

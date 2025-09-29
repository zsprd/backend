from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import settings

Base = declarative_base()

if not settings.DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in settings.")

async_engine = create_async_engine(
    settings.DATABASE_URL,
    # echo=settings.DEBUG,
)

async_session_maker = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


__all__ = [
    "get_async_db",
]

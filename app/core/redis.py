"""
Redis client configuration and connection management.

Provides a singleton Redis client with connection pooling, error handling,
and graceful degradation when Redis is unavailable.
"""

import logging
from typing import Any, Optional

import redis
from redis.connection import ConnectionPool

from app.core.config import settings

logger = logging.getLogger(__name__)


class RedisClient:
    """Singleton Redis client with connection pooling."""

    _instance: Optional["RedisClient"] = None
    _client: Optional[redis.Redis] = None
    _pool: Optional[ConnectionPool] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Redis connection pool if not already initialized."""
        if self._client is None:
            self._initialize_connection()

    def _initialize_connection(self) -> None:
        """Initialize Redis connection with connection pooling."""
        if not settings.REDIS_URL:
            logger.warning(
                "Redis URL not configured. Redis features will be disabled. "
                "Set REDIS_URL in environment variables to enable caching and token blacklist."
            )
            return

        try:
            # Create connection pool
            self._pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                max_connections=20,
                socket_timeout=5,
                socket_connect_timeout=5,
                decode_responses=True,  # Automatically decode responses to strings
                encoding="utf-8",
            )

            # Create Redis client
            self._client = redis.Redis(connection_pool=self._pool)

            # Test connection
            self._client.ping()
            logger.info("✅ Redis connection established successfully")

        except redis.ConnectionError as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            logger.warning("Redis features disabled - using in-memory fallback")
            self._client = None
        except Exception as e:
            logger.error(f"❌ Unexpected error initializing Redis: {e}")
            self._client = None

    def get_client(self) -> Optional[redis.Redis]:
        """Get Redis client instance."""
        return self._client

    def is_available(self) -> bool:
        """Check if Redis is available and connected."""
        if self._client is None:
            return False
        try:
            self._client.ping()
            return True
        except (redis.ConnectionError, redis.TimeoutError):
            logger.warning("Redis connection lost, attempting reconnect...")
            self._initialize_connection()
            return self._client is not None
        except Exception as e:
            logger.error(f"Error checking Redis availability: {e}")
            return False

    def close(self) -> None:
        """Close Redis connection and cleanup."""
        if self._client:
            try:
                self._client.close()
                logger.info("Redis connection closed")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                self._client = None
                self._pool = None

    # Convenience methods with error handling
    def get(self, key: str) -> Optional[str]:
        """Get value from Redis with error handling."""
        if not self.is_available():
            return None
        try:
            return self._client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error for key '{key}': {e}")
            return None

    def set(
        self,
        key: str,
        value: Any,
        ex: Optional[int] = None,
        px: Optional[int] = None,
        nx: bool = False,
        xx: bool = False,
    ) -> bool:
        """Set value in Redis with error handling."""
        if not self.is_available():
            return False
        try:
            return bool(self._client.set(key, value, ex=ex, px=px, nx=nx, xx=xx))
        except Exception as e:
            logger.error(f"Redis SET error for key '{key}': {e}")
            return False

    def delete(self, *keys: str) -> int:
        """Delete keys from Redis with error handling."""
        if not self.is_available():
            return 0
        try:
            return self._client.delete(*keys)
        except Exception as e:
            logger.error(f"Redis DELETE error for keys {keys}: {e}")
            return 0

    def exists(self, *keys: str) -> int:
        """Check if keys exist in Redis."""
        if not self.is_available():
            return 0
        try:
            return self._client.exists(*keys)
        except Exception as e:
            logger.error(f"Redis EXISTS error for keys {keys}: {e}")
            return 0

    def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time for a key."""
        if not self.is_available():
            return False
        try:
            return bool(self._client.expire(key, seconds))
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key '{key}': {e}")
            return False

    def setex(self, key: str, seconds: int, value: Any) -> bool:
        """Set value with expiration time."""
        if not self.is_available():
            return False
        try:
            return bool(self._client.setex(key, seconds, value))
        except Exception as e:
            logger.error(f"Redis SETEX error for key '{key}': {e}")
            return False


# Global Redis client instance
redis_client = RedisClient()


def get_redis() -> RedisClient:
    """Dependency injection for Redis client."""
    return redis_client

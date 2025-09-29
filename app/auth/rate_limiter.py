"""
Redis-based rate limiting with in-memory fallback.

Provides distributed rate limiting across multiple application instances
using Redis. Falls back to in-memory rate limiting when Redis is unavailable.
"""

import logging
import time
from collections import defaultdict, deque
from functools import wraps
from typing import Dict, Tuple

from fastapi import HTTPException, Request, status

from app.core.redis import redis_client

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter with Redis backend and in-memory fallback."""

    def __init__(self):
        self._memory_store: Dict[str, deque] = defaultdict(deque)
        self._use_redis = redis_client.is_available()

        if self._use_redis:
            logger.info("✅ Rate limiter using Redis backend")
        else:
            logger.warning("⚠️ Rate limiter using in-memory - not shared across instances")

    def _parse_rate_limit(self, rate_limit: str) -> Tuple[int, int]:
        """Parse rate limit string like '5/15minutes' or '100/hour'."""
        parts = rate_limit.split("/")
        if len(parts) != 2:
            raise ValueError(f"Invalid rate limit format: {rate_limit}")

        max_requests = int(parts[0])
        period_str = parts[1].lower().strip()

        # Parse time period - check longer strings first to avoid partial matches
        time_units = [
            ("seconds", 1),
            ("second", 1),
            ("minutes", 60),
            ("minute", 60),
            ("hours", 3600),
            ("hour", 3600),
            ("days", 86400),
            ("day", 86400),
        ]

        # Try to match a time unit using endswith
        for unit, multiplier in time_units:
            if period_str.endswith(unit):
                # Extract number before unit
                number_str = period_str[: -len(unit)].strip()
                if number_str:
                    period_value = int(number_str)
                else:
                    period_value = 1  # Default to 1 if no number
                window_seconds = period_value * multiplier
                return max_requests, window_seconds

        # If no match found
        raise ValueError(f"Unknown time unit in rate limit: {period_str}")

    def _build_key(self, identifier: str, endpoint: str) -> str:
        """Build rate limit key."""
        return f"ratelimit:{endpoint}:{identifier}"

    def check_rate_limit(
        self,
        identifier: str,
        endpoint: str,
        rate_limit: str,
    ) -> Tuple[bool, int, int]:
        """Check if request is within rate limit."""
        max_requests, window_seconds = self._parse_rate_limit(rate_limit)

        if self._use_redis:
            return self._redis_check_rate_limit(identifier, endpoint, max_requests, window_seconds)
        else:
            return self._memory_check_rate_limit(identifier, endpoint, max_requests, window_seconds)

    def _redis_check_rate_limit(
        self,
        identifier: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        """Check rate limit using Redis sliding window."""
        try:
            client = redis_client.get_client()
            if not client:
                return self._memory_check_rate_limit(
                    identifier, endpoint, max_requests, window_seconds
                )

            key = self._build_key(identifier, endpoint)
            now = time.time()
            window_start = now - window_seconds

            pipe = client.pipeline()

            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)

            # Count requests in current window
            pipe.zcard(key)

            # Add current request
            pipe.zadd(key, {str(now): now})

            # Set expiration
            pipe.expire(key, window_seconds)

            results = pipe.execute()
            current_count = results[1]

            # Check if limit exceeded
            is_allowed = current_count < max_requests
            remaining = max(0, max_requests - current_count - 1)

            # Calculate reset time (when oldest request expires)
            if current_count > 0:
                oldest = client.zrange(key, 0, 0, withscores=True)
                if oldest:
                    reset_time = int(oldest[0][1] + window_seconds)
                else:
                    reset_time = int(now + window_seconds)
            else:
                reset_time = int(now + window_seconds)

            return is_allowed, remaining, reset_time

        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            return self._memory_check_rate_limit(identifier, endpoint, max_requests, window_seconds)

    def _memory_check_rate_limit(
        self,
        identifier: str,
        endpoint: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        """Check rate limit using in-memory sliding window."""
        key = self._build_key(identifier, endpoint)
        now = time.time()
        window_start = now - window_seconds

        # Get or create request queue for this key
        requests = self._memory_store[key]

        # Remove old requests outside the window
        while requests and requests[0] < window_start:
            requests.popleft()

        # Check if limit exceeded
        current_count = len(requests)
        is_allowed = current_count < max_requests

        if is_allowed:
            requests.append(now)

        remaining = max(0, max_requests - current_count - 1)

        # Calculate reset time
        if requests:
            reset_time = int(requests[0] + window_seconds)
        else:
            reset_time = int(now + window_seconds)

        return is_allowed, remaining, reset_time

    def reset(self, identifier: str, endpoint: str) -> bool:
        """Reset rate limit for identifier and endpoint."""
        key = self._build_key(identifier, endpoint)

        if self._use_redis:
            try:
                return redis_client.delete(key) > 0
            except Exception as e:
                logger.error(f"Failed to reset rate limit in Redis: {e}")

        # Also reset memory cache
        if key in self._memory_store:
            del self._memory_store[key]
            return True

        return False


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(rate_limit_str: str, identifier_func=None):
    """
    Decorator for rate limiting endpoints.

    Args:
        rate_limit_str: Rate limit string from settings (e.g., settings.RATE_LIMIT_LOGIN)
        identifier_func: Optional function to extract identifier from request

    Example:
        @router.post("/login")
        @rate_limit(settings.RATE_LIMIT_LOGIN)
        async def login(request: Request, ...):
            ...
    """

    def decorator(func):
        @wraps(func)  # Preserve function signature for FastAPI
        async def wrapper(*args, **kwargs):
            # Extract request object
            request = None
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    break

            if not request:
                # Look in kwargs
                request = kwargs.get("request")

            if not request:
                logger.warning("Rate limit decorator: Request object not found")
                return await func(*args, **kwargs)

            # Get identifier
            if identifier_func:
                identifier = identifier_func(request)
            else:
                # Default to IP address
                identifier = request.client.host if request.client else "unknown"

            # Get endpoint
            endpoint = request.url.path

            # Check rate limit
            is_allowed, remaining, reset_time = rate_limiter.check_rate_limit(
                identifier, endpoint, rate_limit_str
            )

            # Add rate limit headers
            if hasattr(request, "state"):
                request.state.rate_limit_remaining = remaining
                request.state.rate_limit_reset = reset_time

            if not is_allowed:
                retry_after = reset_time - int(time.time())
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail={
                        "error": "rate_limit_exceeded",
                        "message": f"Rate limit exceeded. Try again in {retry_after} seconds.",
                        "retry_after": retry_after,
                        "limit": rate_limit_str,
                    },
                    headers={"Retry-After": str(retry_after)},
                )

            return await func(*args, **kwargs)

        return wrapper

    return decorator


# Export for convenience
__all__ = ["rate_limit"]

import asyncio
import time
from typing import List
from collections import deque


class RateLimiter:
    """
    Async rate limiter for API requests.
    Ensures we don't exceed the specified number of requests per time window.
    """
    
    def __init__(self, max_requests: int, time_window: int):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: deque = deque()
        self._lock = asyncio.Lock()
    
    async def wait_if_needed(self) -> None:
        """
        Wait if necessary to respect rate limits.
        Should be called before making each API request.
        """
        async with self._lock:
            now = time.time()
            
            # Remove old requests outside the time window
            while self.requests and self.requests[0] <= now - self.time_window:
                self.requests.popleft()
            
            # If we're at the limit, wait until we can make another request
            if len(self.requests) >= self.max_requests:
                # Calculate how long to wait
                oldest_request = self.requests[0]
                wait_time = self.time_window - (now - oldest_request)
                
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Remove the old request after waiting
                    self.requests.popleft()
            
            # Record this request
            self.requests.append(now)
    
    def can_make_request(self) -> bool:
        """
        Check if we can make a request without waiting.
        
        Returns:
            True if request can be made immediately, False otherwise
        """
        now = time.time()
        
        # Remove old requests
        while self.requests and self.requests[0] <= now - self.time_window:
            self.requests.popleft()
        
        return len(self.requests) < self.max_requests
    
    def requests_remaining(self) -> int:
        """
        Get the number of requests remaining in the current window.
        
        Returns:
            Number of requests that can be made without waiting
        """
        now = time.time()
        
        # Remove old requests
        while self.requests and self.requests[0] <= now - self.time_window:
            self.requests.popleft()
        
        return max(0, self.max_requests - len(self.requests))
    
    def time_until_next_request(self) -> float:
        """
        Get the time (in seconds) until the next request can be made.
        
        Returns:
            Seconds to wait, or 0 if request can be made immediately
        """
        if self.can_make_request():
            return 0.0
        
        now = time.time()
        oldest_request = self.requests[0]
        return max(0.0, self.time_window - (now - oldest_request))
    
    def reset(self) -> None:
        """
        Reset the rate limiter, clearing all recorded requests.
        """
        self.requests.clear()


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter implementation.
    More flexible than the simple time window approach.
    """
    
    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket rate limiter.
        
        Args:
            capacity: Maximum number of tokens in the bucket
            refill_rate: Number of tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = float(capacity)
        self.last_refill = time.time()
        self._lock = asyncio.Lock()
    
    async def wait_for_token(self) -> None:
        """
        Wait for a token to become available.
        """
        async with self._lock:
            await self._refill_tokens()
            
            if self.tokens >= 1.0:
                self.tokens -= 1.0
                return
            
            # Calculate wait time for next token
            wait_time = (1.0 - self.tokens) / self.refill_rate
            await asyncio.sleep(wait_time)
            
            # Refill again after waiting
            await self._refill_tokens()
            self.tokens -= 1.0
    
    async def _refill_tokens(self) -> None:
        """
        Refill tokens based on time elapsed.
        """
        now = time.time()
        time_passed = now - self.last_refill
        
        # Add tokens based on time passed
        tokens_to_add = time_passed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def tokens_available(self) -> float:
        """
        Get the number of tokens currently available.
        
        Returns:
            Number of available tokens
        """
        now = time.time()
        time_passed = now - self.last_refill
        tokens_to_add = time_passed * self.refill_rate
        
        return min(self.capacity, self.tokens + tokens_to_add)


# Global rate limiter instances for common use cases
alpha_vantage_limiter = RateLimiter(max_requests=5, time_window=60)  # 5 requests per minute
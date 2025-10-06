"""
Rate Limiter for API Calls
Prevents hitting API rate limits for LLM providers
"""

import asyncio
import time
from collections import deque
from typing import Optional
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter to prevent API quota exhaustion"""
    
    def __init__(
        self, 
        max_requests: int = 60, 
        time_window: int = 60,
        name: str = "RateLimiter"
    ):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum number of requests allowed in time window
            time_window: Time window in seconds
            name: Name for logging purposes
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.name = name
        self.requests = deque()
        self._lock = asyncio.Lock()
        logger.info(
            f"{self.name} initialized: "
            f"{max_requests} requests per {time_window}s"
        )
    
    async def acquire(self):
        """
        Acquire permission to make an API call
        Will wait if rate limit is reached
        """
        if not settings.ENABLE_RATE_LIMITING:
            return
        
        async with self._lock:
            now = time.time()
            
            # Remove old requests outside the time window
            while self.requests and self.requests[0] < now - self.time_window:
                self.requests.popleft()
            
            # Check if we're at the limit
            if len(self.requests) >= self.max_requests:
                # Calculate wait time
                oldest_request = self.requests[0]
                wait_time = self.time_window - (now - oldest_request) + 1
                
                logger.warning(
                    f"{self.name}: Rate limit reached "
                    f"({len(self.requests)}/{self.max_requests}). "
                    f"Waiting {wait_time:.2f}s..."
                )
                
                await asyncio.sleep(wait_time)
                
                # Clean up again after waiting
                now = time.time()
                while self.requests and self.requests[0] < now - self.time_window:
                    self.requests.popleft()
            
            # Record this request
            self.requests.append(time.time())
            logger.debug(
                f"{self.name}: Request allowed "
                f"({len(self.requests)}/{self.max_requests})"
            )
    
    def get_current_usage(self) -> dict:
        """Get current rate limit usage"""
        now = time.time()
        
        # Clean up old requests
        while self.requests and self.requests[0] < now - self.time_window:
            self.requests.popleft()
        
        return {
            "current_requests": len(self.requests),
            "max_requests": self.max_requests,
            "time_window": self.time_window,
            "usage_percentage": (len(self.requests) / self.max_requests) * 100
        }
    
    def reset(self):
        """Reset the rate limiter"""
        self.requests.clear()
        logger.info(f"{self.name}: Reset")


# Global rate limiter instances for different providers
_rate_limiters = {}


def get_rate_limiter(provider: str = "default") -> RateLimiter:
    """
    Get or create a rate limiter for a specific provider
    
    Args:
        provider: Provider name (openai, anthropic, gemini, default)
    
    Returns:
        RateLimiter instance
    """
    if provider not in _rate_limiters:
        # Provider-specific rate limits
        limits = {
            "openai": {"max_requests": 60, "time_window": 60},  # 60 req/min
            "anthropic": {"max_requests": 50, "time_window": 60},  # 50 req/min
            "gemini": {"max_requests": 60, "time_window": 60},  # 60 req/min
            "default": {
                "max_requests": settings.MAX_REQUESTS_PER_MINUTE,
                "time_window": 60
            }
        }
        
        config = limits.get(provider, limits["default"])
        _rate_limiters[provider] = RateLimiter(
            max_requests=config["max_requests"],
            time_window=config["time_window"],
            name=f"RateLimiter[{provider}]"
        )
    
    return _rate_limiters[provider]

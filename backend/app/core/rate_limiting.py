"""
Rate limiting implementation using Redis.

This module provides:
- Redis-based rate limiting
- Per-user request tracking
- Configurable limits and time windows
- FastAPI dependency for rate limit checking
"""

import time
from typing import Optional
from fastapi import HTTPException, status, Request
from redis import Redis
import asyncio
import redis.asyncio as aioredis
from .config import settings


class RateLimiter:
    """
    Redis-based rate limiter implementation.
    """
    
    def __init__(self, redis_url: str = None):
        """
        Initialize the rate limiter.
        
        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url or settings.redis_url
        self._redis: Optional[aioredis.Redis] = None
    
    async def get_redis(self) -> aioredis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.redis_max_connections
            )
        return self._redis
    
    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
    
    async def is_allowed(
        self, 
        key: str, 
        limit: int = 100, 
        window: int = 60,
        identifier: str = None
    ) -> tuple[bool, dict]:
        """
        Check if request is allowed based on rate limit.
        
        Uses sliding window counter algorithm.
        
        Args:
            key: Unique identifier for rate limiting (e.g., user_id, ip_address)
            limit: Maximum number of requests allowed
            window: Time window in seconds
            identifier: Additional identifier for logging
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        redis = await self.get_redis()
        current_time = int(time.time())
        
        # Create Redis key with prefix
        redis_key = f"rate_limit:{key}"
        
        # Use Redis pipeline for atomic operations
        pipe = redis.pipeline()
        
        # Remove expired entries (outside the time window)
        window_start = current_time - window
        pipe.zremrangebyscore(redis_key, 0, window_start)
        
        # Count current requests in the window
        pipe.zcard(redis_key)
        
        # Add current request
        pipe.zadd(redis_key, {str(current_time): current_time})
        
        # Set expiration for the key
        pipe.expire(redis_key, window + 10)  # Add buffer for cleanup
        
        # Execute pipeline
        results = await pipe.execute()
        current_requests = results[1]
        
        # Check if limit is exceeded
        is_allowed = current_requests < limit
        remaining = max(0, limit - current_requests - 1)
        
        # Calculate reset time (when the window resets)
        reset_time = current_time + window
        
        rate_limit_info = {
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time,
            "retry_after": window if not is_allowed else None,
            "current_requests": current_requests + 1,
            "window": window
        }
        
        return is_allowed, rate_limit_info
    
    async def get_rate_limit_status(
        self, 
        key: str, 
        limit: int = 100, 
        window: int = 60
    ) -> dict:
        """
        Get current rate limit status without incrementing counter.
        
        Args:
            key: Unique identifier for rate limiting
            limit: Maximum number of requests allowed
            window: Time window in seconds
            
        Returns:
            Rate limit status information
        """
        redis = await self.get_redis()
        current_time = int(time.time())
        
        # Create Redis key with prefix
        redis_key = f"rate_limit:{key}"
        
        # Count current requests in the window
        window_start = current_time - window
        current_requests = await redis.zcount(redis_key, window_start, current_time)
        
        remaining = max(0, limit - current_requests)
        reset_time = current_time + window
        
        return {
            "limit": limit,
            "remaining": remaining,
            "reset": reset_time,
            "current_requests": current_requests,
            "window": window
        }


# Global rate limiter instance
rate_limiter = RateLimiter()


async def check_rate_limit(
    request: Request,
    user_id: str = None,
    limit: int = 100,
    window: int = 60
) -> dict:
    """
    FastAPI dependency for rate limiting.
    
    Args:
        request: FastAPI request object
        user_id: User ID for authenticated requests
        limit: Rate limit (requests per window)
        window: Time window in seconds
        
    Returns:
        Rate limit information
        
    Raises:
        HTTPException: If rate limit is exceeded
    """
    # Determine rate limit key
    if user_id:
        key = f"user:{user_id}"
    else:
        # Fall back to IP address for unauthenticated requests
        client_ip = request.client.host if request.client else "unknown"
        key = f"ip:{client_ip}"
    
    # Check rate limit
    is_allowed, rate_limit_info = await rate_limiter.is_allowed(
        key=key,
        limit=limit,
        window=window,
        identifier=user_id or client_ip
    )
    
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Limit: {limit} requests per {window} seconds",
                "rate_limit": rate_limit_info
            },
            headers={
                "X-RateLimit-Limit": str(limit),
                "X-RateLimit-Remaining": str(rate_limit_info["remaining"]),
                "X-RateLimit-Reset": str(rate_limit_info["reset"]),
                "Retry-After": str(rate_limit_info["retry_after"]) if rate_limit_info["retry_after"] else "60"
            }
        )
    
    return rate_limit_info


async def add_rate_limit_headers(response, rate_limit_info: dict):
    """
    Add rate limit headers to response.
    
    Args:
        response: FastAPI response object
        rate_limit_info: Rate limit information dictionary
    """
    response.headers["X-RateLimit-Limit"] = str(rate_limit_info["limit"])
    response.headers["X-RateLimit-Remaining"] = str(rate_limit_info["remaining"])
    response.headers["X-RateLimit-Reset"] = str(rate_limit_info["reset"])
    
    if rate_limit_info.get("retry_after"):
        response.headers["Retry-After"] = str(rate_limit_info["retry_after"])
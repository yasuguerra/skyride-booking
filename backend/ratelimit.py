"""
Rate limiting middleware for SkyRide API
Simple Redis-based rate limiting (5 req/min)
"""

import time
import logging
from typing import Callable
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import redis.asyncio as aioredis
import os

logger = logging.getLogger(__name__)

class RateLimiter:
    """Simple rate limiter using Redis sliding window."""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.redis = None
    
    async def init_redis(self):
        """Initialize Redis connection."""
        if not self.redis:
            self.redis = aioredis.from_url(self.redis_url, decode_responses=True)
    
    async def is_rate_limited(self, key: str, limit: int = 5, window: int = 60) -> bool:
        """
        Check if key is rate limited.
        Args:
            key: Unique identifier (IP, user_id, etc.)
            limit: Max requests allowed (default: 5)
            window: Time window in seconds (default: 60)
        """
        await self.init_redis()
        
        current_time = int(time.time())
        window_start = current_time - window
        
        # Use Redis pipeline for atomic operations
        pipe = self.redis.pipeline()
        
        # Remove old entries
        pipe.zremrangebyscore(f"rate_limit:{key}", 0, window_start)
        
        # Count current requests
        pipe.zcard(f"rate_limit:{key}")
        
        # Add current request
        pipe.zadd(f"rate_limit:{key}", {str(current_time): current_time})
        
        # Set TTL
        pipe.expire(f"rate_limit:{key}", window + 10)
        
        results = await pipe.execute()
        current_count = results[1]  # Count result
        
        return current_count >= limit
    
    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()

# Global rate limiter instance
rate_limiter = RateLimiter()

def rate_limit(limit: int = 5, window: int = 60):
    """
    Rate limiting decorator for FastAPI routes.
    
    Args:
        limit: Max requests per window (default: 5)
        window: Window size in seconds (default: 60)
    """
    def decorator(func: Callable):
        async def wrapper(request: Request, *args, **kwargs):
            # Get client IP
            client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            if not client_ip:
                client_ip = request.headers.get("X-Real-IP", "")
            if not client_ip:
                client_ip = getattr(request.client, "host", "unknown")
            
            # Create rate limit key
            endpoint = request.url.path
            rate_key = f"{client_ip}:{endpoint}"
            
            # Check rate limit
            try:
                is_limited = await rate_limiter.is_rate_limited(rate_key, limit, window)
                
                if is_limited:
                    logger.warning(f"Rate limit exceeded for {client_ip} on {endpoint}")
                    raise HTTPException(
                        status_code=429,
                        detail={
                            "error": "Rate limit exceeded",
                            "limit": limit,
                            "window": window,
                            "message": f"Too many requests. Limit: {limit} requests per {window} seconds."
                        }
                    )
                
                # Call the original function
                return await func(request, *args, **kwargs)
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Rate limiting error: {e}")
                # Continue without rate limiting if Redis fails
                return await func(request, *args, **kwargs)
        
        return wrapper
    return decorator

async def get_rate_limit_status(key: str, window: int = 60) -> dict:
    """Get current rate limit status for a key."""
    await rate_limiter.init_redis()
    
    current_time = int(time.time())
    window_start = current_time - window
    
    # Clean and count
    await rate_limiter.redis.zremrangebyscore(f"rate_limit:{key}", 0, window_start)
    count = await rate_limiter.redis.zcard(f"rate_limit:{key}")
    
    return {
        "current_requests": count,
        "window_seconds": window,
        "reset_time": window_start + window
    }

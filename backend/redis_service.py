"""
Redis Service for SkyRide Platform
Handles caching, locks, and temporary data storage
"""

import redis.asyncio as aioredis
import json
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Optional, Dict, List
import logging
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class RedisService:
    def __init__(self):
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.redis_client: Optional[aioredis.Redis] = None
        
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            # Test connection
            await self.redis_client.ping()
            logger.info("✅ Connected to Redis")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            raise
            
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("📴 Disconnected from Redis")
            
    async def get(self, key: str) -> Optional[str]:
        """Get value from Redis"""
        try:
            return await self.redis_client.get(key)
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
            return None
            
    async def set(self, key: str, value: str, expire: Optional[int] = None) -> bool:
        """Set value in Redis with optional expiration"""
        try:
            if expire:
                return await self.redis_client.setex(key, expire, value)
            else:
                return await self.redis_client.set(key, value)
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
            return False
            
    async def delete(self, key: str) -> bool:
        """Delete key from Redis"""
        try:
            result = await self.redis_client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting key {key}: {e}")
            return False
            
    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis"""
        try:
            return await self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking existence of key {key}: {e}")
            return False
            
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration for existing key"""
        try:
            return await self.redis_client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Error setting expiration for key {key}: {e}")
            return False
            
    async def ttl(self, key: str) -> int:
        """Get time to live for key"""
        try:
            return await self.redis_client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key {key}: {e}")
            return -1
            
    # JSON helpers
    async def set_json(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set JSON value in Redis"""
        try:
            json_str = json.dumps(value)
            return await self.set(key, json_str, expire)
        except Exception as e:
            logger.error(f"Error setting JSON key {key}: {e}")
            return False
            
    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value from Redis"""
        try:
            value = await self.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Error getting JSON key {key}: {e}")
            return None
            
    # Lock operations for holds
    async def acquire_lock(self, resource: str, timeout: int = 300, retry_interval: float = 0.1) -> bool:
        """
        Acquire distributed lock for resource (e.g., aircraft slot)
        Returns True if lock acquired, False otherwise
        """
        lock_key = f"lock:{resource}"
        lock_value = "locked"
        
        try:
            # Try to set lock with NX (only if not exists) and EX (expiration)
            result = await self.redis_client.set(lock_key, lock_value, nx=True, ex=timeout)
            
            if result:
                logger.info(f"🔒 Acquired lock for {resource}")
                return True
            else:
                logger.info(f"⏰ Lock already exists for {resource}")
                return False
                
        except Exception as e:
            logger.error(f"Error acquiring lock for {resource}: {e}")
            return False
            
    async def release_lock(self, resource: str) -> bool:
        """Release distributed lock for resource"""
        lock_key = f"lock:{resource}"
        
        try:
            result = await self.delete(lock_key)
            if result:
                logger.info(f"🔓 Released lock for {resource}")
            return result
        except Exception as e:
            logger.error(f"Error releasing lock for {resource}: {e}")
            return False
            
    async def is_locked(self, resource: str) -> bool:
        """Check if resource is locked"""
        lock_key = f"lock:{resource}"
        return await self.exists(lock_key)
        
    # Hold-specific operations
    async def create_hold_lock(self, listing_id: str, hold_duration_minutes: int = 1440) -> bool:
        """
        Create hold lock for a listing (default 24 hours)
        Returns True if hold created, False if already held
        """
        hold_key = f"hold:{listing_id}"
        hold_data = {
            "listing_id": listing_id,
            "created_at": int(datetime.now(timezone.utc).timestamp()),
            "expires_in_seconds": hold_duration_minutes * 60
        }
        
        try:
            # Use SET with NX and EX for atomic operation
            json_data = json.dumps(hold_data)
            result = await self.redis_client.set(
                hold_key, 
                json_data, 
                nx=True,  # Only set if key doesn't exist
                ex=hold_duration_minutes * 60  # Expire after duration
            )
            
            if result:
                logger.info(f"⏰ Created hold for listing {listing_id} (expires in {hold_duration_minutes} minutes)")
                return True
            else:
                logger.info(f"❌ Listing {listing_id} already on hold")
                return False
                
        except Exception as e:
            logger.error(f"Error creating hold for listing {listing_id}: {e}")
            return False
            
    async def release_hold_lock(self, listing_id: str) -> bool:
        """Release hold lock for listing"""
        hold_key = f"hold:{listing_id}"
        
        try:
            result = await self.delete(hold_key)
            if result:
                logger.info(f"✅ Released hold for listing {listing_id}")
            return result
        except Exception as e:
            logger.error(f"Error releasing hold for listing {listing_id}: {e}")
            return False
            
    async def get_hold_info(self, listing_id: str) -> Optional[Dict[str, Any]]:
        """Get hold information for listing"""
        hold_key = f"hold:{listing_id}"
        
        try:
            hold_data = await self.get_json(hold_key)
            if hold_data:
                # Add TTL information
                ttl = await self.ttl(hold_key)
                hold_data['remaining_seconds'] = ttl
                
            return hold_data
        except Exception as e:
            logger.error(f"Error getting hold info for listing {listing_id}: {e}")
            return None
            
    async def is_on_hold(self, listing_id: str) -> bool:
        """Check if listing is currently on hold"""
        hold_key = f"hold:{listing_id}"
        return await self.exists(hold_key)
        
    # Cache operations
    async def cache_availability(self, aircraft_id: str, date_range: str, availability_data: List[Dict]) -> bool:
        """Cache availability data for aircraft"""
        cache_key = f"availability:{aircraft_id}:{date_range}"
        
        try:
            # Cache for 5 minutes
            return await self.set_json(cache_key, availability_data, expire=300)
        except Exception as e:
            logger.error(f"Error caching availability for {aircraft_id}: {e}")
            return False
            
    async def get_cached_availability(self, aircraft_id: str, date_range: str) -> Optional[List[Dict]]:
        """Get cached availability data"""
        cache_key = f"availability:{aircraft_id}:{date_range}"
        return await self.get_json(cache_key)
        
    async def invalidate_availability_cache(self, aircraft_id: str) -> bool:
        """Invalidate all availability cache for aircraft"""
        try:
            pattern = f"availability:{aircraft_id}:*"
            keys = await self.redis_client.keys(pattern)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                logger.info(f"🗑️ Invalidated {deleted} availability cache entries for aircraft {aircraft_id}")
                return deleted > 0
                
            return True
        except Exception as e:
            logger.error(f"Error invalidating availability cache for {aircraft_id}: {e}")
            return False

# Global Redis service instance
redis_service = RedisService()

# FastAPI dependency
async def get_redis():
    """Dependency for FastAPI to get Redis service"""
    if not redis_service.redis_client:
        await redis_service.connect()
    return redis_service
import redis
import json
from typing import Optional
from app.config.settings import settings
from app.infrastructure.security_logger import SecurityLogger

logger = SecurityLogger(__name__)

class CacheService:
    """Service for caching using Redis"""
    
    def __init__(self):
        try:
            if not settings.REDIS_ENABLED:
                logger.info("Redis caching is disabled")
                self.client = None
                return
            
            self.client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
                health_check_interval=30
            )
            # Verificar conexión
            self.client.ping()
            logger.info("Redis cache initialized successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed, running without cache: {str(e)}")
            self.client = None
    
    def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if not self.client:
            return None
        try:
            return self.client.get(key)
        except Exception as e:
            logger.warning(f"Cache get error: {str(e)}")
            return None
    
    def set(self, key: str, value: str, ttl: int = None) -> bool:
        """Set value in cache with TTL"""
        if not self.client:
            return False
        
        if ttl is None:
            ttl = settings.SCHEMA_CACHE_TTL
        
        try:
            self.client.setex(key, ttl, value)
            return True
        except Exception as e:
            logger.warning(f"Cache set error: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        if not self.client:
            return False
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error: {str(e)}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Clear all keys matching a pattern"""
        if not self.client:
            return 0
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache clear pattern error: {str(e)}")
            return 0

    def incr(self, key: str, amount: int = 1, ttl: int = None) -> int:
        """Increment a numeric key and optionally set TTL for first time"""
        if not self.client:
            return 0
        try:
            val = self.client.incr(key, amount)
            # If ttl specified and key was just created, set expiry
            if ttl is not None:
                self.client.expire(key, ttl)
            return int(val)
        except Exception as e:
            logger.warning(f"Cache incr error: {str(e)}")
            return 0

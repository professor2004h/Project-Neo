import redis.asyncio as redis
import os
from dotenv import load_dotenv
import asyncio
from utils.logger import logger
from typing import List, Any, Optional

# Redis connection manager
class RedisConnectionManager:
    """Singleton Redis connection manager with connection pooling."""
    
    _instance: Optional['RedisConnectionManager'] = None
    _initialized = False
    _client: Optional[redis.Redis] = None
    _connection_pool: Optional[redis.ConnectionPool] = None
    _init_lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """No initialization needed in __init__ as it's handled in __new__"""
        pass

    def _create_connection_pool(self):
        """Create Redis connection pool with production-grade settings."""
        # Load environment variables if not already loaded
        load_dotenv()

        # Get Redis configuration
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_password = os.getenv('REDIS_PASSWORD', '') or None
        redis_ssl_str = os.getenv('REDIS_SSL', 'False')
        redis_ssl = redis_ssl_str.lower() == 'true'
        
        # Connection pool configuration
        max_connections = int(os.getenv('REDIS_MAX_CONNECTIONS', '100'))
        
        logger.info(f"Creating Redis connection pool to {redis_host}:{redis_port} with max_connections={max_connections}, SSL={redis_ssl}")
        

        # Create connection pool arguments
        pool_kwargs = {
            'host': redis_host,
            'port': redis_port,
            'password': redis_password,
            'decode_responses': True,
            'max_connections': max_connections,
            'socket_timeout': 10.0,
            'socket_connect_timeout': 10.0,
            'socket_keepalive': True,
            'socket_keepalive_options': {},
            'retry_on_timeout': True,
            'health_check_interval': 30,
        }
        
        # Only add SSL parameter if it's actually True
        # redis.asyncio doesn't accept ssl=False, but works fine without the parameter
        if redis_ssl:
            pool_kwargs['ssl'] = True
        
        self._connection_pool = redis.ConnectionPool(**pool_kwargs)


    def _create_client(self):
        """Create Redis client using the connection pool."""
        if self._connection_pool is None:
            self._create_connection_pool()
            
        self._client = redis.Redis(
            connection_pool=self._connection_pool,
            socket_timeout=10.0,
            socket_connect_timeout=10.0,
        )

    async def initialize(self):
        """Initialize the Redis connection and pool."""
        if self._initialized:
            return
                
        async with self._init_lock:
            if not self._initialized:
                try:
                    logger.info("Initializing Redis connection manager")
                    self._create_client()
                    
                    # Test the connection
                    await self._client.ping()
                    logger.info("Successfully connected to Redis with connection pooling")
                    self._initialized = True
                    
                    # Log pool configuration
                    logger.info(f"Redis connection pool configured: max_connections={self._connection_pool.max_connections}")
                    
                except Exception as e:
                    logger.error(f"Failed to initialize Redis connection: {e}")
                    self._client = None
                    self._connection_pool = None
                    raise RuntimeError(f"Redis initialization failed: {str(e)}")

    async def disconnect(self):
        """Disconnect from Redis and close the connection pool."""
        if self._client:
            logger.info("Closing Redis connection and pool")
            try:
                await self._client.aclose()
                if self._connection_pool:
                    await self._connection_pool.aclose()
                logger.info("Redis connection pool closed successfully")
            except Exception as e:
                logger.error(f"Error closing Redis connection: {e}")
            finally:
                self._client = None
                self._connection_pool = None
                self._initialized = False

    async def get_client(self) -> redis.Redis:
        """Get the Redis client instance, initializing if necessary."""
        if not self._initialized or self._client is None:
            await self.initialize()
        
        if not self._client:
            raise RuntimeError("Redis client not initialized")
            
        return self._client

    @property
    def is_initialized(self) -> bool:
        """Check if Redis is initialized."""
        return self._initialized and self._client is not None

    async def get_pool_info(self) -> dict:
        """Get connection pool information for monitoring."""
        if not self._connection_pool:
            return {"status": "not_initialized"}
            
        return {
            "status": "initialized",
            "max_connections": self._connection_pool.max_connections,
            "created_connections": getattr(self._connection_pool, 'created_connections', 'unknown'),
            "available_connections": getattr(self._connection_pool, 'available_connections', 'unknown'),
        }

# Global instance
_redis_manager = RedisConnectionManager()

# Legacy compatibility - maintain existing API
client = None
_initialized = False
_init_lock = asyncio.Lock()

# Constants
REDIS_KEY_TTL = 3600 * 24  # 24 hour TTL as safety mechanism

def initialize():
    """Initialize Redis connection using environment variables (legacy sync method)."""
    global client, _initialized
    
    if not _initialized:
        load_dotenv()
        
        redis_host = os.getenv('REDIS_HOST', 'redis')
        redis_port = int(os.getenv('REDIS_PORT', 6379))
        redis_password = os.getenv('REDIS_PASSWORD', '') or None
        redis_ssl_str = os.getenv('REDIS_SSL', 'False')
        redis_ssl = redis_ssl_str.lower() == 'true'
        
        logger.info(f"Initializing Redis connection to {redis_host}:{redis_port} (legacy method)")
        
        # Create client arguments
        client_kwargs = {
            'host': redis_host,
            'port': redis_port,
            'password': redis_password,
            'decode_responses': True,
            'socket_timeout': 5.0,
            'socket_connect_timeout': 5.0,
            'retry_on_timeout': True,
            'health_check_interval': 30
        }
        
        # Only add SSL parameter if it's actually True
        if redis_ssl:
            client_kwargs['ssl'] = True
        
        client = redis.Redis(**client_kwargs)

        
        _initialized = True
    
    return client

async def initialize_async():
    """Initialize Redis connection asynchronously using the connection manager."""
    global client, _initialized
    
    await _redis_manager.initialize()
    client = await _redis_manager.get_client()
    _initialized = True
    
    return client

async def close():
    """Close Redis connection."""
    global client, _initialized
    
    await _redis_manager.disconnect()
    client = None
    _initialized = False
    logger.info("Redis connection manager closed")

async def get_client():
    """Get the Redis client, initializing if necessary."""
    global client, _initialized
    
    if not _redis_manager.is_initialized:
        await initialize_async()
    
    client = await _redis_manager.get_client()
    _initialized = True
    return client

# Basic Redis operations
async def set(key: str, value: str, ex: int = None):
    """Set a Redis key."""
    redis_client = await get_client()
    return await redis_client.set(key, value, ex=ex)

async def get(key: str, default: str = None):
    """Get a Redis key."""
    redis_client = await get_client()
    result = await redis_client.get(key)
    return result if result is not None else default

async def delete(key: str):
    """Delete a Redis key."""
    redis_client = await get_client()
    return await redis_client.delete(key)

async def publish(channel: str, message: str):
    """Publish a message to a Redis channel."""
    redis_client = await get_client()
    return await redis_client.publish(channel, message)

async def create_pubsub():
    """Create a Redis pubsub object."""
    redis_client = await get_client()
    return redis_client.pubsub()

# List operations
async def rpush(key: str, *values: Any):
    """Append one or more values to a list."""
    redis_client = await get_client()
    return await redis_client.rpush(key, *values)

async def lrange(key: str, start: int, end: int) -> List[str]:
    """Get a range of elements from a list."""
    redis_client = await get_client()
    return await redis_client.lrange(key, start, end)

async def llen(key: str) -> int:
    """Get the length of a list."""
    redis_client = await get_client()
    return await redis_client.llen(key)

# Key management
async def expire(key: str, time: int):
    """Set a key's time to live in seconds."""
    redis_client = await get_client()
    return await redis_client.expire(key, time)

async def keys(pattern: str) -> List[str]:
    """Get keys matching a pattern."""
    redis_client = await get_client()
    return await redis_client.keys(pattern)

# Monitoring functions
async def get_connection_info():
    """Get Redis connection pool information for monitoring."""
    return await _redis_manager.get_pool_info()

async def health_check():
    """Perform a health check on Redis connection."""
    try:
        redis_client = await get_client()
        await redis_client.ping()
        pool_info = await get_connection_info()
        return {
            "status": "healthy",
            "pool_info": pool_info
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
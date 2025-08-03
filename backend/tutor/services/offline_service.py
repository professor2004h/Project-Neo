"""
Offline Service - Handles offline data management, caching, and sync queue processing
Task 8.2 implementation
"""
import asyncio
import json
import time
import gzip
from typing import Dict, List, Optional, Any, Tuple, Set
from datetime import datetime, timezone, timedelta
import redis.asyncio as redis
from collections import defaultdict
import hashlib

from utils.logger import logger
from services.supabase import DBConnection
from services.llm import make_llm_api_call
from ..repositories.user_repository import ChildProfileRepository
from ..models.offline_models import (
    CacheLevel,
    CacheStatus,
    ContentType,
    ConnectivityStatus,
    CacheEntry,
    OfflineContent,
    OfflineSession,
    CacheConfiguration,
    OfflineQueue,
    ConnectivityMonitor
)
from ..models.sync_models import (
    OfflineOperation,
    SyncOperation,
    DataType,
    SyncStatus
)
from ..models.user_models import Subject


class CacheManager:
    """
    Manages local data caching for offline functionality
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        
        # Cache key patterns
        self.cache_key_pattern = "cache:{user_id}:{device_id}:{key}"
        self.cache_meta_key = "cache_meta:{user_id}:{device_id}"
        self.cache_index_key = "cache_index:{user_id}:{device_id}"
        
        # Cache statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "storage_used": 0
        }
    
    async def put(self, user_id: str, device_id: str, key: str, 
                 data: Dict[str, Any], cache_level: CacheLevel = CacheLevel.MEDIUM,
                 ttl_hours: Optional[int] = None) -> bool:
        """
        Store data in cache
        
        Args:
            user_id: User ID
            device_id: Device ID
            key: Cache key
            data: Data to cache
            cache_level: Cache priority level
            ttl_hours: Time to live in hours
            
        Returns:
            True if successfully cached
        """
        try:
            # Create cache entry
            cache_entry = CacheEntry(
                key=key,
                data_type=DataType.CONTENT,  # Default, should be specified
                data=data,
                cache_level=cache_level,
                size_bytes=len(json.dumps(data))
            )
            
            # Set expiration if specified
            if ttl_hours:
                cache_entry.expires_at = datetime.now(timezone.utc) + timedelta(hours=ttl_hours)
            
            # Check cache limits before adding
            config = await self._get_cache_config(user_id, device_id)
            if not await self._check_cache_limits(user_id, device_id, cache_entry, config):
                # Evict entries to make space
                await self._evict_entries(user_id, device_id, cache_entry.size_bytes, config)
            
            # Store cache entry
            cache_key = self.cache_key_pattern.format(
                user_id=user_id, device_id=device_id, key=key
            )
            
            # Compress data if enabled
            entry_data = cache_entry.json()
            if config.cache_compression_enabled:
                entry_data = gzip.compress(entry_data.encode()).decode('latin-1')
            
            # Set expiration in Redis
            expire_seconds = ttl_hours * 3600 if ttl_hours else 24 * 3600
            await self.redis.setex(cache_key, expire_seconds, entry_data)
            
            # Update cache index
            await self._update_cache_index(user_id, device_id, key, cache_entry)
            
            # Update statistics
            await self._update_cache_stats(user_id, device_id, "put", cache_entry.size_bytes)
            
            logger.debug(f"Cached data with key {key} for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error caching data: {str(e)}")
            return False
    
    async def get(self, user_id: str, device_id: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve data from cache
        
        Args:
            user_id: User ID
            device_id: Device ID
            key: Cache key
            
        Returns:
            Cached data or None if not found/expired
        """
        try:
            cache_key = self.cache_key_pattern.format(
                user_id=user_id, device_id=device_id, key=key
            )
            
            # Get from Redis
            entry_data = await self.redis.get(cache_key)
            
            if entry_data is None:
                self.stats["misses"] += 1
                return None
            
            # Decompress if needed
            config = await self._get_cache_config(user_id, device_id)
            if config.cache_compression_enabled:
                try:
                    entry_data = gzip.decompress(entry_data.encode('latin-1')).decode()
                except:
                    # Not compressed or corrupted
                    pass
            
            # Parse cache entry
            cache_entry = CacheEntry.parse_raw(entry_data)
            
            # Check if entry is valid
            if not cache_entry.is_valid():
                await self.delete(user_id, device_id, key)
                self.stats["misses"] += 1
                return None
            
            # Update access information
            cache_entry.touch()
            
            # Update in Redis
            updated_data = cache_entry.json()
            if config.cache_compression_enabled:
                updated_data = gzip.compress(updated_data.encode()).decode('latin-1')
            
            await self.redis.set(cache_key, updated_data, keep_ttl=True)
            
            # Update statistics
            self.stats["hits"] += 1
            await self._update_cache_stats(user_id, device_id, "get", 0)
            
            return cache_entry.data
            
        except Exception as e:
            logger.error(f"Error retrieving cached data: {str(e)}")
            self.stats["misses"] += 1
            return None
    
    async def delete(self, user_id: str, device_id: str, key: str) -> bool:
        """Delete data from cache"""
        try:
            cache_key = self.cache_key_pattern.format(
                user_id=user_id, device_id=device_id, key=key
            )
            
            # Remove from Redis
            result = await self.redis.delete(cache_key)
            
            if result > 0:
                # Update cache index
                await self._remove_from_cache_index(user_id, device_id, key)
                
                # Update statistics
                await self._update_cache_stats(user_id, device_id, "delete", 0)
                
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error deleting cached data: {str(e)}")
            return False
    
    async def clear_cache(self, user_id: str, device_id: str) -> bool:
        """Clear all cache for user/device"""
        try:
            # Get all cache keys
            pattern = self.cache_key_pattern.format(
                user_id=user_id, device_id=device_id, key="*"
            )
            
            cache_keys = await self.redis.keys(pattern)
            
            if cache_keys:
                await self.redis.delete(*cache_keys)
            
            # Clear metadata
            meta_key = self.cache_meta_key.format(user_id=user_id, device_id=device_id)
            index_key = self.cache_index_key.format(user_id=user_id, device_id=device_id)
            
            await self.redis.delete(meta_key, index_key)
            
            logger.info(f"Cleared cache for user {user_id}, device {device_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False
    
    async def get_cache_status(self, user_id: str, device_id: str) -> Dict[str, Any]:
        """Get cache status information"""
        try:
            # Get cache index
            index_key = self.cache_index_key.format(user_id=user_id, device_id=device_id)
            index_data = await self.redis.get(index_key)
            
            if not index_data:
                return {"total_entries": 0, "total_size_mb": 0, "cache_levels": {}}
            
            index = json.loads(index_data)
            
            total_size = sum(entry.get("size_bytes", 0) for entry in index.values())
            cache_levels = defaultdict(int)
            
            for entry in index.values():
                cache_levels[entry.get("cache_level", "unknown")] += 1
            
            return {
                "total_entries": len(index),
                "total_size_mb": total_size / (1024 * 1024),
                "cache_levels": dict(cache_levels),
                "last_accessed": max((entry.get("accessed_at", "") for entry in index.values()), default=""),
                "stats": self.stats
            }
            
        except Exception as e:
            logger.error(f"Error getting cache status: {str(e)}")
            return {"total_entries": 0, "total_size_mb": 0, "error": str(e)}
    
    # Private helper methods
    
    async def _get_cache_config(self, user_id: str, device_id: str) -> CacheConfiguration:
        """Get cache configuration for user/device"""
        try:
            # In production, this would load from database
            return CacheConfiguration(user_id=user_id, device_id=device_id)
        except Exception:
            return CacheConfiguration(user_id=user_id, device_id=device_id)
    
    async def _check_cache_limits(self, user_id: str, device_id: str, 
                                 new_entry: CacheEntry, config: CacheConfiguration) -> bool:
        """Check if adding new entry would exceed cache limits"""
        status = await self.get_cache_status(user_id, device_id)
        
        # Check size limit
        new_total_size = status["total_size_mb"] + (new_entry.size_bytes / (1024 * 1024))
        if new_total_size > config.max_cache_size_mb:
            return False
        
        # Check entry count limit
        if status["total_entries"] >= config.max_entries:
            return False
        
        return True
    
    async def _evict_entries(self, user_id: str, device_id: str, 
                           required_size: int, config: CacheConfiguration) -> None:
        """Evict cache entries to make space"""
        try:
            # Get cache index
            index_key = self.cache_index_key.format(user_id=user_id, device_id=device_id)
            index_data = await self.redis.get(index_key)
            
            if not index_data:
                return
            
            index = json.loads(index_data)
            
            # Calculate priority scores for all entries
            entries_with_scores = []
            for key, entry_data in index.items():
                cache_entry = CacheEntry.parse_obj(entry_data)
                score = cache_entry.calculate_priority_score()
                entries_with_scores.append((key, cache_entry, score))
            
            # Sort by priority (lowest first = first to evict)
            entries_with_scores.sort(key=lambda x: x[2])
            
            # Evict entries until we have enough space
            evicted_size = 0
            for key, entry, score in entries_with_scores:
                if evicted_size >= required_size:
                    break
                
                # Don't evict critical entries unless absolutely necessary
                if entry.cache_level == CacheLevel.CRITICAL and evicted_size > 0:
                    continue
                
                await self.delete(user_id, device_id, key)
                evicted_size += entry.size_bytes
                self.stats["evictions"] += 1
            
            logger.info(f"Evicted {evicted_size} bytes from cache for user {user_id}")
            
        except Exception as e:
            logger.error(f"Error evicting cache entries: {str(e)}")
    
    async def _update_cache_index(self, user_id: str, device_id: str, 
                                 key: str, cache_entry: CacheEntry) -> None:
        """Update cache index with new entry"""
        try:
            index_key = self.cache_index_key.format(user_id=user_id, device_id=device_id)
            
            # Get current index
            index_data = await self.redis.get(index_key)
            index = json.loads(index_data) if index_data else {}
            
            # Update entry
            index[key] = cache_entry.dict()
            
            # Store updated index
            await self.redis.set(index_key, json.dumps(index))
            
        except Exception as e:
            logger.error(f"Error updating cache index: {str(e)}")
    
    async def _remove_from_cache_index(self, user_id: str, device_id: str, key: str) -> None:
        """Remove entry from cache index"""
        try:
            index_key = self.cache_index_key.format(user_id=user_id, device_id=device_id)
            
            # Get current index
            index_data = await self.redis.get(index_key)
            if not index_data:
                return
            
            index = json.loads(index_data)
            
            # Remove entry
            if key in index:
                del index[key]
                
                # Store updated index
                await self.redis.set(index_key, json.dumps(index))
            
        except Exception as e:
            logger.error(f"Error removing from cache index: {str(e)}")
    
    async def _update_cache_stats(self, user_id: str, device_id: str, 
                                 operation: str, size_change: int) -> None:
        """Update cache statistics"""
        try:
            meta_key = self.cache_meta_key.format(user_id=user_id, device_id=device_id)
            
            # Get current stats
            stats_data = await self.redis.get(meta_key)
            stats = json.loads(stats_data) if stats_data else {}
            
            # Update stats
            stats["last_operation"] = operation
            stats["last_operation_at"] = datetime.now(timezone.utc).isoformat()
            stats["operations_count"] = stats.get("operations_count", 0) + 1
            
            if size_change != 0:
                stats["storage_used"] = stats.get("storage_used", 0) + size_change
            
            # Store updated stats
            await self.redis.setex(meta_key, 7 * 24 * 3600, json.dumps(stats))  # 7 days TTL
            
        except Exception as e:
            logger.error(f"Error updating cache stats: {str(e)}")


class OfflineContentManager:
    """
    Manages offline content availability and delivery
    """
    
    def __init__(self, db: DBConnection, cache_manager: CacheManager):
        self.db = db
        self.cache_manager = cache_manager
        self.child_repo = ChildProfileRepository(db)
        
        # Content storage (in production, this would be database tables)
        self.offline_content_store: Dict[str, OfflineContent] = {}
        
        # Content download queue
        self.download_queue: Dict[str, List[str]] = defaultdict(list)  # device_id -> content_ids
    
    async def make_content_available_offline(self, user_id: str, device_id: str,
                                           content_id: str) -> bool:
        """
        Make content available for offline use
        
        Args:
            user_id: User ID
            device_id: Device ID
            content_id: Content ID to make available offline
            
        Returns:
            True if successfully prepared for offline use
        """
        try:
            # Get content information
            content = await self._get_content_info(content_id)
            if not content:
                logger.warning(f"Content {content_id} not found")
                return False
            
            # Check cache configuration
            config = await self.cache_manager._get_cache_config(user_id, device_id)
            if not config.should_cache_content(content):
                logger.info(f"Content {content_id} not suitable for caching")
                return False
            
            # Download and cache content
            success = await self._download_and_cache_content(user_id, device_id, content)
            
            if success:
                # Mark as offline available
                content.is_offline_available = True
                content.cached_at = datetime.now(timezone.utc)
                content.cache_expires_at = datetime.now(timezone.utc) + timedelta(
                    hours=config.get_ttl_for_cache_level(CacheLevel.MEDIUM)
                )
                
                # Store updated content info
                self.offline_content_store[content_id] = content
                
                logger.info(f"Made content {content_id} available offline for user {user_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error making content available offline: {str(e)}")
            return False
    
    async def get_offline_content(self, user_id: str, device_id: str,
                                content_id: str) -> Optional[Dict[str, Any]]:
        """
        Get content for offline use
        
        Args:
            user_id: User ID
            device_id: Device ID
            content_id: Content ID
            
        Returns:
            Content data or None if not available offline
        """
        try:
            # Check if content is available offline
            content = self.offline_content_store.get(content_id)
            if not content or not content.is_offline_available:
                return None
            
            # Check cache validity
            if not content.is_cache_valid():
                # Try to refresh cache
                await self.make_content_available_offline(user_id, device_id, content_id)
                content = self.offline_content_store.get(content_id)
                
                if not content or not content.is_cache_valid():
                    return None
            
            # Get from cache
            cache_key = f"content:{content_id}"
            content_data = await self.cache_manager.get(user_id, device_id, cache_key)
            
            if content_data:
                # Mark offline access
                content.mark_offline_access()
                self.offline_content_store[content_id] = content
                
                logger.debug(f"Delivered offline content {content_id} to user {user_id}")
            
            return content_data
            
        except Exception as e:
            logger.error(f"Error getting offline content: {str(e)}")
            return None
    
    async def get_available_offline_content(self, user_id: str, device_id: str,
                                          subject: Subject = None) -> List[OfflineContent]:
        """Get list of content available offline"""
        try:
            available_content = []
            
            for content in self.offline_content_store.values():
                if content.is_offline_available and content.is_cache_valid():
                    if subject is None or content.subject == subject:
                        available_content.append(content)
            
            # Sort by priority and recent access
            available_content.sort(
                key=lambda c: (c.download_priority, -(c.offline_access_count or 0))
            )
            
            return available_content
            
        except Exception as e:
            logger.error(f"Error getting available offline content: {str(e)}")
            return []
    
    async def preload_content_for_offline(self, user_id: str, device_id: str,
                                        subject: Subject = None, 
                                        difficulty_range: Tuple[int, int] = (1, 5)) -> int:
        """
        Preload content for offline use based on user preferences
        
        Returns:
            Number of content items preloaded
        """
        try:
            # Get user profile for personalization
            child_profile = await self.child_repo.get_by_id(user_id, "child_id")
            if not child_profile:
                return 0
            
            # Get cache configuration
            config = await self.cache_manager._get_cache_config(user_id, device_id)
            
            # Find suitable content for preloading
            candidate_content = await self._find_preload_candidates(
                user_id, subject, difficulty_range, config
            )
            
            preloaded_count = 0
            
            for content in candidate_content:
                # Check storage limits
                cache_status = await self.cache_manager.get_cache_status(user_id, device_id)
                if cache_status["total_size_mb"] + content.offline_size_mb > config.max_cache_size_mb:
                    break
                
                # Preload content
                success = await self.make_content_available_offline(user_id, device_id, content.content_id)
                if success:
                    preloaded_count += 1
                
                # Limit preloading to avoid overwhelming storage
                if preloaded_count >= 10:
                    break
            
            logger.info(f"Preloaded {preloaded_count} content items for user {user_id}")
            return preloaded_count
            
        except Exception as e:
            logger.error(f"Error preloading content: {str(e)}")
            return 0
    
    async def cleanup_expired_content(self, user_id: str, device_id: str) -> int:
        """
        Clean up expired offline content
        
        Returns:
            Number of items cleaned up
        """
        try:
            cleaned_count = 0
            expired_content_ids = []
            
            for content_id, content in self.offline_content_store.items():
                if not content.is_cache_valid():
                    expired_content_ids.append(content_id)
            
            for content_id in expired_content_ids:
                # Remove from cache
                cache_key = f"content:{content_id}"
                await self.cache_manager.delete(user_id, device_id, cache_key)
                
                # Update content info
                content = self.offline_content_store[content_id]
                content.is_offline_available = False
                content.cached_at = None
                content.cache_expires_at = None
                
                cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} expired content items for user {user_id}")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired content: {str(e)}")
            return 0
    
    # Private helper methods
    
    async def _get_content_info(self, content_id: str) -> Optional[OfflineContent]:
        """Get content information (placeholder)"""
        # In production, this would query the content database
        # For now, create a mock content item
        
        if content_id in self.offline_content_store:
            return self.offline_content_store[content_id]
        
        # Create mock content
        content = OfflineContent(
            content_id=content_id,
            title=f"Content {content_id}",
            description="Sample educational content",
            content_type=ContentType.LESSON,
            subject=Subject.MATHEMATICS,
            offline_size_mb=5.0,
            download_priority=5,
            difficulty_level=3,
            estimated_duration_minutes=15,
            learning_objectives=["Understand basic concepts"],
            cache_version="1.0"
        )
        
        return content
    
    async def _download_and_cache_content(self, user_id: str, device_id: str,
                                        content: OfflineContent) -> bool:
        """Download and cache content data"""
        try:
            # Simulate content download (in production, would fetch from CDN/database)
            content_data = {
                "content_id": content.content_id,
                "title": content.title,
                "description": content.description,
                "content_type": content.content_type.value,
                "content_body": f"Educational content for {content.title}",
                "media_urls": content.media_urls,
                "learning_objectives": content.learning_objectives,
                "difficulty_level": content.difficulty_level,
                "estimated_duration": content.estimated_duration_minutes,
                "cached_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Store in cache
            cache_key = f"content:{content.content_id}"
            success = await self.cache_manager.put(
                user_id, device_id, cache_key, content_data,
                CacheLevel.MEDIUM, ttl_hours=24
            )
            
            if success:
                logger.debug(f"Downloaded and cached content {content.content_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error downloading and caching content: {str(e)}")
            return False
    
    async def _find_preload_candidates(self, user_id: str, subject: Subject,
                                     difficulty_range: Tuple[int, int],
                                     config: CacheConfiguration) -> List[OfflineContent]:
        """Find content suitable for preloading"""
        candidates = []
        
        # In production, this would query the content database
        # For now, create some mock content
        for i in range(20):
            content = OfflineContent(
                content_id=f"preload_content_{i}",
                title=f"Lesson {i+1}",
                content_type=ContentType.LESSON,
                subject=subject or Subject.MATHEMATICS,
                offline_size_mb=3.0 + (i % 5),
                download_priority=1 + (i % 10),
                difficulty_level=difficulty_range[0] + (i % (difficulty_range[1] - difficulty_range[0] + 1)),
                estimated_duration_minutes=10 + (i % 20)
            )
            
            if config.should_cache_content(content):
                candidates.append(content)
        
        # Sort by download priority and size
        candidates.sort(key=lambda c: (c.download_priority, c.offline_size_mb))
        
        return candidates


class SyncQueueProcessor:
    """
    Processes sync queue when connectivity is restored
    """
    
    def __init__(self, db: DBConnection, cache_manager: CacheManager):
        self.db = db
        self.cache_manager = cache_manager
        
        # Queue storage (in production, this would use database/Redis)
        self.sync_queues: Dict[str, OfflineQueue] = {}
        
        # Processing state
        self.processing_queues: Set[str] = set()
        
        # Statistics
        self.processing_stats = {
            "total_processed": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "average_processing_time_ms": 0.0
        }
    
    async def add_to_sync_queue(self, user_id: str, device_id: str,
                              operation: OfflineOperation) -> bool:
        """
        Add operation to sync queue
        
        Args:
            user_id: User ID
            device_id: Device ID
            operation: Operation to queue
            
        Returns:
            True if successfully queued
        """
        try:
            queue_key = f"{user_id}:{device_id}"
            
            # Get or create queue
            if queue_key not in self.sync_queues:
                self.sync_queues[queue_key] = OfflineQueue(
                    user_id=user_id,
                    device_id=device_id
                )
            
            queue = self.sync_queues[queue_key]
            
            # Add operation to queue
            success = queue.add_operation(operation.operation_id)
            
            if success:
                # Store operation data (in production, would use persistent storage)
                operation_key = f"operation:{operation.operation_id}"
                await self.cache_manager.put(
                    user_id, device_id, operation_key, operation.dict(),
                    CacheLevel.HIGH, ttl_hours=72  # 3 days
                )
                
                logger.debug(f"Added operation {operation.operation_id} to sync queue")
            
            return success
            
        except Exception as e:
            logger.error(f"Error adding to sync queue: {str(e)}")
            return False
    
    async def process_sync_queue(self, user_id: str, device_id: str,
                               connectivity_status: ConnectivityStatus) -> Dict[str, Any]:
        """
        Process sync queue when connectivity is available
        
        Args:
            user_id: User ID
            device_id: Device ID
            connectivity_status: Current connectivity status
            
        Returns:
            Processing results
        """
        queue_key = f"{user_id}:{device_id}"
        
        try:
            # Check if already processing
            if queue_key in self.processing_queues:
                return {"status": "already_processing"}
            
            # Check connectivity requirements
            if connectivity_status == ConnectivityStatus.OFFLINE:
                return {"status": "offline", "message": "Cannot process queue while offline"}
            
            # Get queue
            if queue_key not in self.sync_queues:
                return {"status": "no_queue", "processed": 0}
            
            queue = self.sync_queues[queue_key]
            
            if not queue.pending_operations:
                return {"status": "empty_queue", "processed": 0}
            
            # Mark queue as being processed
            self.processing_queues.add(queue_key)
            
            try:
                # Process operations
                results = await self._process_queue_operations(user_id, device_id, queue, connectivity_status)
                
                # Update queue status
                queue.last_processed_at = datetime.now(timezone.utc)
                
                logger.info(f"Processed sync queue for user {user_id}: {results}")
                
                return results
                
            finally:
                # Remove from processing set
                self.processing_queues.discard(queue_key)
            
        except Exception as e:
            logger.error(f"Error processing sync queue: {str(e)}")
            self.processing_queues.discard(queue_key)
            return {"status": "error", "error": str(e), "processed": 0}
    
    async def get_queue_status(self, user_id: str, device_id: str) -> Dict[str, Any]:
        """Get sync queue status"""
        queue_key = f"{user_id}:{device_id}"
        
        if queue_key not in self.sync_queues:
            return {"exists": False}
        
        queue = self.sync_queues[queue_key]
        status = queue.get_queue_status()
        status["exists"] = True
        status["is_processing"] = queue_key in self.processing_queues
        
        return status
    
    async def retry_failed_operations(self, user_id: str, device_id: str) -> int:
        """
        Retry failed operations in the queue
        
        Returns:
            Number of operations moved back to pending
        """
        queue_key = f"{user_id}:{device_id}"
        
        if queue_key not in self.sync_queues:
            return 0
        
        queue = self.sync_queues[queue_key]
        retried_operations = queue.retry_failed_operations()
        
        logger.info(f"Retried {len(retried_operations)} failed operations for user {user_id}")
        
        return len(retried_operations)
    
    async def clear_queue(self, user_id: str, device_id: str) -> bool:
        """Clear sync queue"""
        queue_key = f"{user_id}:{device_id}"
        
        try:
            if queue_key in self.sync_queues:
                queue = self.sync_queues[queue_key]
                
                # Clear operation data from cache
                for operation_id in (queue.pending_operations + 
                                   queue.failed_operations + 
                                   queue.completed_operations):
                    operation_key = f"operation:{operation_id}"
                    await self.cache_manager.delete(user_id, device_id, operation_key)
                
                # Remove queue
                del self.sync_queues[queue_key]
                
                logger.info(f"Cleared sync queue for user {user_id}, device {device_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error clearing sync queue: {str(e)}")
            return False
    
    # Private helper methods
    
    async def _process_queue_operations(self, user_id: str, device_id: str,
                                      queue: OfflineQueue, 
                                      connectivity_status: ConnectivityStatus) -> Dict[str, Any]:
        """Process operations in the queue"""
        processed = 0
        successful = 0
        failed = 0
        
        # Determine batch size based on connectivity
        batch_size = 5 if connectivity_status == ConnectivityStatus.LIMITED else 10
        
        # Process operations in batches
        operations_to_process = queue.pending_operations.copy()[:batch_size]
        
        for operation_id in operations_to_process:
            try:
                start_time = time.time()
                
                # Get operation data
                operation_key = f"operation:{operation_id}"
                operation_data = await self.cache_manager.get(user_id, device_id, operation_key)
                
                if not operation_data:
                    logger.warning(f"Operation data not found for {operation_id}")
                    queue.mark_operation_failed(operation_id)
                    failed += 1
                    continue
                
                operation = OfflineOperation.parse_obj(operation_data)
                
                # Execute operation
                success = await self._execute_sync_operation(operation, connectivity_status)
                
                processing_time = (time.time() - start_time) * 1000  # ms
                
                if success:
                    queue.mark_operation_completed(operation_id)
                    successful += 1
                    
                    # Remove operation data from cache
                    await self.cache_manager.delete(user_id, device_id, operation_key)
                else:
                    queue.mark_operation_failed(operation_id)
                    failed += 1
                
                processed += 1
                
                # Update processing statistics
                self.processing_stats["total_processed"] += 1
                if success:
                    self.processing_stats["successful_operations"] += 1
                else:
                    self.processing_stats["failed_operations"] += 1
                
                # Update average processing time
                total_ops = self.processing_stats["total_processed"]
                current_avg = self.processing_stats["average_processing_time_ms"]
                self.processing_stats["average_processing_time_ms"] = (
                    (current_avg * (total_ops - 1) + processing_time) / total_ops
                )
                
                # Rate limiting for poor connectivity
                if connectivity_status == ConnectivityStatus.LIMITED:
                    await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error processing operation {operation_id}: {str(e)}")
                queue.mark_operation_failed(operation_id)
                failed += 1
                processed += 1
        
        return {
            "status": "completed",
            "processed": processed,
            "successful": successful,
            "failed": failed,
            "remaining": len(queue.pending_operations)
        }
    
    async def _execute_sync_operation(self, operation: OfflineOperation,
                                    connectivity_status: ConnectivityStatus) -> bool:
        """Execute a sync operation"""
        try:
            # Simulate operation execution based on type
            if operation.operation_type == SyncOperation.CREATE:
                # Create operation
                logger.debug(f"Executing CREATE operation for {operation.data_type.value}")
                # In production, would create data on server
                
            elif operation.operation_type == SyncOperation.UPDATE:
                # Update operation
                logger.debug(f"Executing UPDATE operation for {operation.data_type.value}")
                # In production, would update data on server
                
            elif operation.operation_type == SyncOperation.DELETE:
                # Delete operation
                logger.debug(f"Executing DELETE operation for {operation.data_type.value}")
                # In production, would delete data on server
                
            # Simulate network delay based on connectivity
            if connectivity_status == ConnectivityStatus.LIMITED:
                await asyncio.sleep(0.5)  # Slower for limited connectivity
            else:
                await asyncio.sleep(0.1)  # Fast for good connectivity
            
            # Simulate success rate based on connectivity
            if connectivity_status == ConnectivityStatus.LIMITED:
                import random
                return random.random() > 0.2  # 80% success rate for limited connectivity
            else:
                return True  # High success rate for good connectivity
            
        except Exception as e:
            logger.error(f"Error executing sync operation: {str(e)}")
            return False


class OfflineService:
    """
    Main offline service coordinating all offline functionality
    """
    
    def __init__(self, db: DBConnection, redis_url: str = "redis://localhost:6379"):
        self.db = db
        
        # Initialize Redis for caching
        self.redis = redis.from_url(redis_url, decode_responses=False)
        
        # Initialize components
        self.cache_manager = CacheManager(self.redis)
        self.content_manager = OfflineContentManager(db, self.cache_manager)
        self.sync_processor = SyncQueueProcessor(db, self.cache_manager)
        
        # Connectivity monitoring
        self.connectivity_monitors: Dict[str, ConnectivityMonitor] = {}
        
        # Background tasks
        self.cleanup_task: Optional[asyncio.Task] = None
        self.sync_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start offline service background tasks"""
        try:
            # Start cleanup task (runs every hour)
            self.cleanup_task = asyncio.create_task(self._background_cleanup())
            
            # Start sync task (runs every 5 minutes)
            self.sync_task = asyncio.create_task(self._background_sync())
            
            logger.info("Offline service started")
            
        except Exception as e:
            logger.error(f"Error starting offline service: {str(e)}")
            raise
    
    async def stop(self) -> None:
        """Stop offline service"""
        try:
            # Cancel background tasks
            if self.cleanup_task:
                self.cleanup_task.cancel()
            if self.sync_task:
                self.sync_task.cancel()
            
            # Close Redis connection
            await self.redis.close()
            
            logger.info("Offline service stopped")
            
        except Exception as e:
            logger.error(f"Error stopping offline service: {str(e)}")
    
    async def update_connectivity_status(self, device_id: str, 
                                       status: ConnectivityStatus,
                                       network_info: Dict[str, Any] = None) -> bool:
        """
        Update device connectivity status
        
        Args:
            device_id: Device ID
            status: New connectivity status
            network_info: Additional network information
            
        Returns:
            True if status changed
        """
        try:
            # Get or create connectivity monitor
            if device_id not in self.connectivity_monitors:
                self.connectivity_monitors[device_id] = ConnectivityMonitor(device_id=device_id)
            
            monitor = self.connectivity_monitors[device_id]
            status_changed = monitor.update_status(status, network_info)
            
            if status_changed:
                logger.info(f"Device {device_id} connectivity changed to {status.value}")
                
                # Trigger sync if coming online
                if status in [ConnectivityStatus.ONLINE, ConnectivityStatus.LIMITED]:
                    await self._trigger_connectivity_sync(device_id, status)
            
            return status_changed
            
        except Exception as e:
            logger.error(f"Error updating connectivity status: {str(e)}")
            return False
    
    async def prepare_for_offline(self, user_id: str, device_id: str,
                                subject: Subject = None, duration_hours: int = 2) -> Dict[str, Any]:
        """
        Prepare content and data for offline use
        
        Args:
            user_id: User ID
            device_id: Device ID
            subject: Subject to focus on (optional)
            duration_hours: Expected offline duration
            
        Returns:
            Preparation results
        """
        try:
            results = {
                "content_preloaded": 0,
                "cache_prepared": False,
                "estimated_offline_hours": duration_hours,
                "storage_used_mb": 0,
                "recommendations": []
            }
            
            # Preload content based on expected usage
            content_count = await self.content_manager.preload_content_for_offline(
                user_id, device_id, subject
            )
            results["content_preloaded"] = content_count
            
            # Get cache status
            cache_status = await self.cache_manager.get_cache_status(user_id, device_id)
            results["storage_used_mb"] = cache_status["total_size_mb"]
            results["cache_prepared"] = cache_status["total_entries"] > 0
            
            # Generate recommendations
            if content_count == 0:
                results["recommendations"].append("No content available for offline use. Check network connection.")
            elif content_count < 5:
                results["recommendations"].append("Limited content available offline. Consider downloading more when connected.")
            else:
                results["recommendations"].append(f"{content_count} lessons available offline for {duration_hours} hours of learning.")
            
            logger.info(f"Prepared offline environment for user {user_id}: {content_count} content items")
            
            return results
            
        except Exception as e:
            logger.error(f"Error preparing for offline: {str(e)}")
            return {"content_preloaded": 0, "cache_prepared": False, "error": str(e)}
    
    async def get_offline_status(self, user_id: str, device_id: str) -> Dict[str, Any]:
        """Get comprehensive offline status"""
        try:
            # Connectivity status
            connectivity_info = {}
            if device_id in self.connectivity_monitors:
                monitor = self.connectivity_monitors[device_id]
                connectivity_info = monitor.get_connectivity_summary()
            
            # Cache status
            cache_status = await self.cache_manager.get_cache_status(user_id, device_id)
            
            # Available content
            available_content = await self.content_manager.get_available_offline_content(user_id, device_id)
            
            # Sync queue status
            queue_status = await self.sync_processor.get_queue_status(user_id, device_id)
            
            return {
                "connectivity": connectivity_info,
                "cache": cache_status,
                "available_content": len(available_content),
                "content_size_mb": sum(c.offline_size_mb for c in available_content),
                "sync_queue": queue_status,
                "is_ready_for_offline": len(available_content) > 0 and cache_status["total_entries"] > 0
            }
            
        except Exception as e:
            logger.error(f"Error getting offline status: {str(e)}")
            return {"error": str(e)}
    
    # Private helper methods
    
    async def _trigger_connectivity_sync(self, device_id: str, status: ConnectivityStatus) -> None:
        """Trigger sync when connectivity is restored"""
        try:
            # Find all users for this device (simplified - in production would query database)
            # For now, process all queues for this device
            for queue_key, queue in self.sync_processor.sync_queues.items():
                if queue.device_id == device_id:
                    await self.sync_processor.process_sync_queue(
                        queue.user_id, device_id, status
                    )
            
        except Exception as e:
            logger.error(f"Error triggering connectivity sync: {str(e)}")
    
    async def _background_cleanup(self) -> None:
        """Background task for cleanup operations"""
        try:
            while True:
                await asyncio.sleep(3600)  # Run every hour
                
                # Clean up expired content for all users
                for queue_key, queue in self.sync_processor.sync_queues.items():
                    try:
                        await self.content_manager.cleanup_expired_content(
                            queue.user_id, queue.device_id
                        )
                    except Exception as e:
                        logger.error(f"Error in cleanup for {queue_key}: {str(e)}")
                
                logger.debug("Completed background cleanup")
                
        except asyncio.CancelledError:
            logger.info("Background cleanup task cancelled")
        except Exception as e:
            logger.error(f"Error in background cleanup: {str(e)}")
    
    async def _background_sync(self) -> None:
        """Background task for automatic sync operations"""
        try:
            while True:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Check for devices that are online and process their queues
                for device_id, monitor in self.connectivity_monitors.items():
                    if monitor.is_online() and monitor.has_good_connectivity():
                        # Find queues for this device
                        for queue_key, queue in self.sync_processor.sync_queues.items():
                            if queue.device_id == device_id:
                                try:
                                    await self.sync_processor.process_sync_queue(
                                        queue.user_id, device_id, monitor.current_status
                                    )
                                except Exception as e:
                                    logger.error(f"Error in background sync for {queue_key}: {str(e)}")
                
                logger.debug("Completed background sync check")
                
        except asyncio.CancelledError:
            logger.info("Background sync task cancelled")
        except Exception as e:
            logger.error(f"Error in background sync: {str(e)}")
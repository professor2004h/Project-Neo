"""
Offline functionality and caching models for Cambridge AI Tutor
Task 8.2 implementation
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any, Union
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid

from .sync_models import DataType, SyncOperation
from .user_models import Subject


class CacheLevel(str, Enum):
    """Cache level enumeration"""
    CRITICAL = "critical"      # Must be cached (user profiles, auth data)
    HIGH = "high"             # Should be cached (recent activities, progress)
    MEDIUM = "medium"         # Nice to cache (content, lessons)
    LOW = "low"               # Optional cache (media, assets)


class CacheStatus(str, Enum):
    """Cache status enumeration"""
    FRESH = "fresh"           # Cache is up to date
    STALE = "stale"          # Cache is outdated but usable
    EXPIRED = "expired"       # Cache is too old to use
    INVALID = "invalid"       # Cache is corrupted or invalid


class ContentType(str, Enum):
    """Content type enumeration for caching"""
    LESSON = "lesson"
    EXERCISE = "exercise"
    ASSESSMENT = "assessment"
    MEDIA = "media"
    GAME = "game"
    EXPLANATION = "explanation"
    RESOURCE = "resource"


class ConnectivityStatus(str, Enum):
    """Connectivity status enumeration"""
    ONLINE = "online"
    OFFLINE = "offline"
    LIMITED = "limited"       # Poor connectivity
    UNKNOWN = "unknown"


class CacheEntry(BaseModel):
    """Individual cache entry"""
    cache_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key: str = Field(min_length=1, description="Unique cache key")
    data_type: DataType
    content_type: Optional[ContentType] = None
    
    # Cache data
    data: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Cache management
    cache_level: CacheLevel = CacheLevel.MEDIUM
    status: CacheStatus = CacheStatus.FRESH
    size_bytes: int = Field(ge=0, default=0)
    
    # Timing information
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    accessed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    last_modified: Optional[datetime] = None
    
    # Dependency tracking
    depends_on: List[str] = Field(default_factory=list)  # Cache keys this depends on
    invalidates: List[str] = Field(default_factory=list)  # Cache keys this invalidates
    
    # Access patterns
    access_count: int = Field(ge=0, default=0)
    access_frequency: float = Field(ge=0.0, default=0.0)  # Accesses per day
    
    def is_valid(self) -> bool:
        """Check if cache entry is valid"""
        if self.status == CacheStatus.INVALID:
            return False
        
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        
        return True
    
    def is_fresh(self) -> bool:
        """Check if cache entry is fresh"""
        return self.status == CacheStatus.FRESH and self.is_valid()
    
    def is_stale(self) -> bool:
        """Check if cache entry is stale but usable"""
        return self.status == CacheStatus.STALE and self.is_valid()
    
    def touch(self) -> None:
        """Update access information"""
        now = datetime.now(timezone.utc)
        self.accessed_at = now
        self.access_count += 1
        
        # Update access frequency (accesses per day)
        age_days = (now - self.created_at).total_seconds() / (24 * 60 * 60)
        if age_days > 0:
            self.access_frequency = self.access_count / age_days
    
    def mark_stale(self) -> None:
        """Mark cache entry as stale"""
        self.status = CacheStatus.STALE
    
    def mark_invalid(self) -> None:
        """Mark cache entry as invalid"""
        self.status = CacheStatus.INVALID
    
    def calculate_priority_score(self) -> float:
        """Calculate priority score for cache eviction"""
        base_score = 0.0
        
        # Level priority
        level_scores = {
            CacheLevel.CRITICAL: 1000,
            CacheLevel.HIGH: 500,
            CacheLevel.MEDIUM: 100,
            CacheLevel.LOW: 50
        }
        base_score += level_scores.get(self.cache_level, 50)
        
        # Recency bonus (accessed recently = higher priority)
        age_hours = (datetime.now(timezone.utc) - self.accessed_at).total_seconds() / 3600
        recency_bonus = max(0, 100 - age_hours)  # Max 100 points for recent access
        base_score += recency_bonus
        
        # Frequency bonus
        base_score += min(self.access_frequency * 10, 100)  # Max 100 points
        
        # Status penalty
        if self.status == CacheStatus.STALE:
            base_score *= 0.8
        elif self.status == CacheStatus.EXPIRED:
            base_score *= 0.5
        elif self.status == CacheStatus.INVALID:
            base_score *= 0.1
        
        return base_score


class OfflineContent(BaseModel):
    """Content available for offline use"""
    content_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="")
    content_type: ContentType
    subject: Optional[Subject] = None
    
    # Content data
    content_data: Dict[str, Any] = Field(default_factory=dict)
    media_urls: List[str] = Field(default_factory=list)
    dependencies: List[str] = Field(default_factory=list)  # Other content IDs needed
    
    # Offline availability
    is_offline_available: bool = False
    offline_size_mb: float = Field(ge=0.0, default=0.0)
    download_priority: int = Field(ge=1, le=10, default=5)  # 1=highest, 10=lowest
    
    # Educational metadata
    difficulty_level: int = Field(ge=1, le=5, default=3)
    estimated_duration_minutes: int = Field(ge=1, default=15)
    learning_objectives: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    
    # Offline usage
    offline_access_count: int = Field(ge=0, default=0)
    last_offline_access: Optional[datetime] = None
    offline_completion_rate: float = Field(ge=0.0, le=1.0, default=0.0)
    
    # Caching information
    cached_at: Optional[datetime] = None
    cache_expires_at: Optional[datetime] = None
    cache_version: str = Field(default="1.0")
    
    @field_validator('content_id')
    @classmethod
    def validate_content_id(cls, v):
        """Validate content ID format"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')
    
    def is_cache_valid(self) -> bool:
        """Check if cached content is still valid"""
        if not self.cached_at:
            return False
        
        if self.cache_expires_at and datetime.now(timezone.utc) > self.cache_expires_at:
            return False
        
        return True
    
    def mark_offline_access(self) -> None:
        """Mark content as accessed offline"""
        self.offline_access_count += 1
        self.last_offline_access = datetime.now(timezone.utc)
    
    def get_cache_size_estimate(self) -> float:
        """Estimate total cache size including dependencies"""
        return self.offline_size_mb  # In real implementation, would calculate dependencies


class OfflineSession(BaseModel):
    """Offline learning session"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    
    # Session timing
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    total_duration_minutes: int = Field(ge=0, default=0)
    
    # Connectivity status during session
    initial_connectivity: ConnectivityStatus = ConnectivityStatus.OFFLINE
    connectivity_changes: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Activities during session
    activities_attempted: List[str] = Field(default_factory=list)  # Activity IDs
    activities_completed: List[str] = Field(default_factory=list)
    content_accessed: List[str] = Field(default_factory=list)  # Content IDs
    
    # Performance tracking
    total_score: float = Field(ge=0.0, default=0.0)
    accuracy_rate: float = Field(ge=0.0, le=1.0, default=0.0)
    engagement_level: float = Field(ge=0.0, le=1.0, default=0.5)
    
    # Sync status
    is_synced: bool = False
    sync_attempted_at: Optional[datetime] = None
    sync_completed_at: Optional[datetime] = None
    sync_errors: List[str] = Field(default_factory=list)
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        """Validate UUID format for user ID"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')
    
    def add_connectivity_change(self, new_status: ConnectivityStatus, details: Dict[str, Any] = None) -> None:
        """Add connectivity status change"""
        change = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "from_status": self.get_current_connectivity(),
            "to_status": new_status.value,
            "details": details or {}
        }
        self.connectivity_changes.append(change)
    
    def get_current_connectivity(self) -> str:
        """Get current connectivity status"""
        if self.connectivity_changes:
            return self.connectivity_changes[-1]["to_status"]
        return self.initial_connectivity.value
    
    def end_session(self) -> None:
        """End the offline session"""
        if not self.ended_at:
            self.ended_at = datetime.now(timezone.utc)
            self.total_duration_minutes = int((self.ended_at - self.started_at).total_seconds() / 60)
    
    def calculate_offline_percentage(self) -> float:
        """Calculate percentage of session spent offline"""
        if not self.connectivity_changes:
            return 1.0 if self.initial_connectivity == ConnectivityStatus.OFFLINE else 0.0
        
        total_duration = (self.ended_at or datetime.now(timezone.utc)) - self.started_at
        offline_duration = timedelta(0)
        
        current_status = self.initial_connectivity
        last_timestamp = self.started_at
        
        for change in self.connectivity_changes:
            change_time = datetime.fromisoformat(change["timestamp"].replace('Z', '+00:00'))
            
            if current_status == ConnectivityStatus.OFFLINE:
                offline_duration += change_time - last_timestamp
            
            current_status = ConnectivityStatus(change["to_status"])
            last_timestamp = change_time
        
        # Check final period
        final_timestamp = self.ended_at or datetime.now(timezone.utc)
        if current_status == ConnectivityStatus.OFFLINE:
            offline_duration += final_timestamp - last_timestamp
        
        return offline_duration.total_seconds() / total_duration.total_seconds() if total_duration.total_seconds() > 0 else 0.0


class CacheConfiguration(BaseModel):
    """Configuration for offline caching"""
    user_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    
    # Cache limits
    max_cache_size_mb: float = Field(ge=10.0, le=1000.0, default=100.0)
    max_entries: int = Field(ge=100, le=10000, default=1000)
    
    # Cache policies
    default_ttl_hours: int = Field(ge=1, le=168, default=24)  # 1 hour to 1 week
    critical_ttl_hours: int = Field(ge=6, le=720, default=168)  # 6 hours to 30 days
    auto_cache_enabled: bool = True
    aggressive_caching: bool = False  # Cache more content proactively
    
    # Content preferences
    preferred_subjects: List[Subject] = Field(default_factory=list)
    max_content_size_mb: float = Field(ge=1.0, le=100.0, default=20.0)  # Per content item
    auto_download_on_wifi: bool = True
    
    # Sync preferences
    sync_on_connectivity: bool = True
    max_queue_size: int = Field(ge=10, le=1000, default=100)
    retry_failed_operations: bool = True
    
    # Performance settings
    background_sync_enabled: bool = True
    low_storage_threshold_mb: float = Field(ge=50.0, default=200.0)
    cache_compression_enabled: bool = True
    
    # Last update
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        """Validate UUID format for user ID"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')
    
    def should_cache_content(self, content: OfflineContent) -> bool:
        """Determine if content should be cached based on configuration"""
        # Check size limits
        if content.offline_size_mb > self.max_content_size_mb:
            return False
        
        # Check subject preferences
        if self.preferred_subjects and content.subject not in self.preferred_subjects:
            return False
        
        # Check priority
        if not self.aggressive_caching and content.download_priority > 7:
            return False
        
        return True
    
    def get_ttl_for_cache_level(self, cache_level: CacheLevel) -> int:
        """Get TTL in hours for cache level"""
        if cache_level == CacheLevel.CRITICAL:
            return self.critical_ttl_hours
        else:
            return self.default_ttl_hours


class OfflineQueue(BaseModel):
    """Queue for operations pending sync"""
    queue_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    
    # Queue metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_processed_at: Optional[datetime] = None
    
    # Queue operations
    pending_operations: List[str] = Field(default_factory=list)  # Operation IDs
    failed_operations: List[str] = Field(default_factory=list)  # Operation IDs
    completed_operations: List[str] = Field(default_factory=list)  # Operation IDs
    
    # Queue statistics
    total_operations: int = Field(ge=0, default=0)
    success_rate: float = Field(ge=0.0, le=1.0, default=0.0)
    average_processing_time_ms: float = Field(ge=0.0, default=0.0)
    
    # Queue settings
    max_size: int = Field(ge=10, le=1000, default=100)
    auto_retry_failed: bool = True
    max_retry_attempts: int = Field(ge=1, le=10, default=3)
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        """Validate UUID format for user ID"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')
    
    def add_operation(self, operation_id: str) -> bool:
        """Add operation to pending queue"""
        if len(self.pending_operations) >= self.max_size:
            return False
        
        if operation_id not in self.pending_operations:
            self.pending_operations.append(operation_id)
            self.total_operations += 1
            return True
        
        return False
    
    def mark_operation_completed(self, operation_id: str) -> None:
        """Mark operation as completed"""
        if operation_id in self.pending_operations:
            self.pending_operations.remove(operation_id)
        
        if operation_id in self.failed_operations:
            self.failed_operations.remove(operation_id)
        
        if operation_id not in self.completed_operations:
            self.completed_operations.append(operation_id)
            self._update_success_rate()
    
    def mark_operation_failed(self, operation_id: str) -> None:
        """Mark operation as failed"""
        if operation_id in self.pending_operations:
            self.pending_operations.remove(operation_id)
        
        if operation_id not in self.failed_operations:
            self.failed_operations.append(operation_id)
            self._update_success_rate()
    
    def retry_failed_operations(self) -> List[str]:
        """Move failed operations back to pending"""
        if not self.auto_retry_failed:
            return []
        
        operations_to_retry = self.failed_operations.copy()
        self.failed_operations.clear()
        
        for operation_id in operations_to_retry:
            self.add_operation(operation_id)
        
        return operations_to_retry
    
    def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            "queue_id": self.queue_id,
            "pending": len(self.pending_operations),
            "failed": len(self.failed_operations),
            "completed": len(self.completed_operations),
            "total": self.total_operations,
            "success_rate": self.success_rate,
            "is_full": len(self.pending_operations) >= self.max_size
        }
    
    def _update_success_rate(self) -> None:
        """Update success rate calculation"""
        total_processed = len(self.completed_operations) + len(self.failed_operations)
        if total_processed > 0:
            self.success_rate = len(self.completed_operations) / total_processed


class ConnectivityMonitor(BaseModel):
    """Monitors device connectivity status"""
    monitor_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str = Field(min_length=1)
    
    # Current status
    current_status: ConnectivityStatus = ConnectivityStatus.UNKNOWN
    last_status_change: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Status history
    status_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Network information
    network_type: Optional[str] = None  # wifi, cellular, ethernet
    connection_quality: float = Field(ge=0.0, le=1.0, default=0.0)
    latency_ms: Optional[float] = None
    bandwidth_mbps: Optional[float] = None
    
    # Monitoring settings
    check_interval_seconds: int = Field(ge=5, le=300, default=30)
    last_check_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Statistics
    uptime_percentage: float = Field(ge=0.0, le=1.0, default=0.0)
    average_connection_duration_minutes: float = Field(ge=0.0, default=0.0)
    total_offline_time_minutes: float = Field(ge=0.0, default=0.0)
    
    def update_status(self, new_status: ConnectivityStatus, 
                     network_info: Dict[str, Any] = None) -> bool:
        """
        Update connectivity status
        
        Returns:
            True if status changed
        """
        if new_status != self.current_status:
            # Record status change
            self.status_history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "from_status": self.current_status.value,
                "to_status": new_status.value,
                "duration_seconds": (datetime.now(timezone.utc) - self.last_status_change).total_seconds()
            })
            
            self.current_status = new_status
            self.last_status_change = datetime.now(timezone.utc)
            
            # Update network info
            if network_info:
                self.network_type = network_info.get("type")
                self.connection_quality = network_info.get("quality", 0.0)
                self.latency_ms = network_info.get("latency_ms")
                self.bandwidth_mbps = network_info.get("bandwidth_mbps")
            
            # Update statistics
            self._update_statistics()
            
            return True
        
        self.last_check_at = datetime.now(timezone.utc)
        return False
    
    def is_online(self) -> bool:
        """Check if device is currently online"""
        return self.current_status in [ConnectivityStatus.ONLINE, ConnectivityStatus.LIMITED]
    
    def has_good_connectivity(self) -> bool:
        """Check if device has good connectivity for sync operations"""
        return (self.current_status == ConnectivityStatus.ONLINE and 
                self.connection_quality > 0.7)
    
    def get_connectivity_summary(self) -> Dict[str, Any]:
        """Get connectivity summary"""
        return {
            "current_status": self.current_status.value,
            "uptime_percentage": self.uptime_percentage,
            "network_type": self.network_type,
            "connection_quality": self.connection_quality,
            "total_status_changes": len(self.status_history),
            "last_change": self.last_status_change.isoformat()
        }
    
    def _update_statistics(self) -> None:
        """Update connectivity statistics"""
        if not self.status_history:
            return
        
        total_time = 0.0
        online_time = 0.0
        offline_time = 0.0
        
        for entry in self.status_history:
            duration = entry["duration_seconds"]
            total_time += duration
            
            if entry["from_status"] in ["online", "limited"]:
                online_time += duration
            else:
                offline_time += duration
        
        if total_time > 0:
            self.uptime_percentage = online_time / total_time
        
        self.total_offline_time_minutes = offline_time / 60
"""
Synchronization and conflict resolution models for Cambridge AI Tutor
Task 8.1 implementation
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any, Union
from datetime import datetime, timezone
from enum import Enum
import uuid

from .user_models import Subject


class SyncOperation(str, Enum):
    """Synchronization operation types"""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    MERGE = "merge"


class ConflictResolution(str, Enum):
    """Conflict resolution strategies"""
    SERVER_WINS = "server_wins"
    CLIENT_WINS = "client_wins"
    MERGE = "merge"
    MANUAL = "manual"
    TIMESTAMP_BASED = "timestamp_based"
    USER_CHOICE = "user_choice"


class SyncStatus(str, Enum):
    """Synchronization status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CONFLICT = "conflict"
    CANCELLED = "cancelled"


class DataType(str, Enum):
    """Types of data that can be synchronized"""
    USER_PROFILE = "user_profile"
    LEARNING_ACTIVITY = "learning_activity"
    PROGRESS_RECORD = "progress_record"
    ACHIEVEMENT = "achievement"
    GAMIFICATION_PROFILE = "gamification_profile"
    SETTINGS = "settings"
    CONTENT = "content"
    CACHE = "cache"


class DeviceInfo(BaseModel):
    """Device information for synchronization tracking"""
    device_id: str = Field(min_length=1)
    device_type: str = Field(min_length=1)  # web, mobile, tablet, extension
    platform: str = Field(min_length=1)  # windows, macos, ios, android, chrome
    app_version: str = Field(min_length=1)
    last_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_online: bool = True
    capabilities: Dict[str, bool] = Field(default_factory=dict)  # offline, voice, etc.
    
    @field_validator('device_id')
    @classmethod
    def validate_device_id(cls, v):
        """Validate device ID format"""
        if len(v) < 8:
            raise ValueError('Device ID must be at least 8 characters')
        return v


class DataVersion(BaseModel):
    """Version information for data synchronization"""
    version_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    data_id: str = Field(min_length=1)
    data_type: DataType
    version_number: int = Field(ge=1, default=1)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    device_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    checksum: str = Field(min_length=1)  # Data integrity check
    
    # Change tracking
    changes: List[str] = Field(default_factory=list)  # List of changed fields
    previous_version: Optional[str] = None
    
    @field_validator('user_id', 'data_id')
    @classmethod
    def validate_uuid_format(cls, v):
        """Validate UUID format"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')


class SyncData(BaseModel):
    """Data payload for synchronization"""
    data_id: str = Field(min_length=1)
    data_type: DataType
    content: Dict[str, Any] = Field(default_factory=dict)
    version: DataVersion
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Synchronization flags
    is_deleted: bool = False
    requires_merge: bool = False
    conflict_detected: bool = False
    
    def get_checksum(self) -> str:
        """Calculate checksum for data integrity"""
        import hashlib
        import json
        
        # Create deterministic JSON representation
        content_str = json.dumps(self.content, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def update_version(self, device_id: str, changes: List[str] = None) -> None:
        """Update version information for changes"""
        self.version.version_number += 1
        self.version.timestamp = datetime.now(timezone.utc)
        self.version.device_id = device_id
        self.version.changes = changes or []
        self.version.checksum = self.get_checksum()


class DataConflict(BaseModel):
    """Represents a data synchronization conflict"""
    conflict_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    data_id: str = Field(min_length=1)
    data_type: DataType
    user_id: str = Field(min_length=1)
    
    # Conflicting versions
    server_version: DataVersion
    client_version: DataVersion
    
    # Conflict details
    conflicted_fields: List[str] = Field(default_factory=list)
    conflict_description: str = Field(default="")
    severity: str = Field(default="medium")  # low, medium, high, critical
    
    # Resolution
    resolution_strategy: Optional[ConflictResolution] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None  # device_id or user_id
    resolution_data: Optional[Dict[str, Any]] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    auto_resolvable: bool = False
    
    def can_auto_resolve(self) -> bool:
        """Check if conflict can be automatically resolved"""
        # Auto-resolve if one version is clearly newer and non-conflicting
        time_diff = abs((self.server_version.timestamp - self.client_version.timestamp).total_seconds())
        
        # If versions are more than 5 minutes apart, use timestamp-based resolution
        if time_diff > 300:  # 5 minutes
            self.auto_resolvable = True
            self.resolution_strategy = ConflictResolution.TIMESTAMP_BASED
            return True
        
        # If only metadata changes, prefer newer version
        if set(self.conflicted_fields).issubset({'metadata', 'updated_at', 'last_seen'}):
            self.auto_resolvable = True
            self.resolution_strategy = ConflictResolution.TIMESTAMP_BASED
            return True
        
        return False
    
    def resolve(self, strategy: ConflictResolution, resolved_by: str, 
                resolution_data: Dict[str, Any] = None) -> None:
        """Mark conflict as resolved"""
        self.resolution_strategy = strategy
        self.resolved_at = datetime.now(timezone.utc)
        self.resolved_by = resolved_by
        self.resolution_data = resolution_data or {}


class SyncOperation_Model(BaseModel):
    """Represents a synchronization operation"""
    operation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    operation_type: SyncOperation
    data_type: DataType
    data_id: str = Field(min_length=1)
    
    # Operation details
    data_payload: Optional[SyncData] = None
    previous_version: Optional[str] = None
    target_version: Optional[str] = None
    
    # Status tracking
    status: SyncStatus = SyncStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Error handling
    error_message: Optional[str] = None
    retry_count: int = Field(ge=0, default=0)
    max_retries: int = Field(ge=0, default=3)
    
    # Dependencies
    depends_on: List[str] = Field(default_factory=list)  # Operation IDs this depends on
    blocks: List[str] = Field(default_factory=list)  # Operation IDs blocked by this
    
    # Priority and scheduling
    priority: int = Field(ge=1, le=10, default=5)  # 1=highest, 10=lowest
    scheduled_at: Optional[datetime] = None
    
    def can_execute(self, completed_operations: set) -> bool:
        """Check if operation can be executed based on dependencies"""
        return all(dep_id in completed_operations for dep_id in self.depends_on)
    
    def mark_started(self) -> None:
        """Mark operation as started"""
        self.status = SyncStatus.IN_PROGRESS
        self.started_at = datetime.now(timezone.utc)
    
    def mark_completed(self) -> None:
        """Mark operation as completed"""
        self.status = SyncStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
    
    def mark_failed(self, error: str) -> None:
        """Mark operation as failed"""
        self.status = SyncStatus.FAILED
        self.error_message = error
        self.completed_at = datetime.now(timezone.utc)
    
    def can_retry(self) -> bool:
        """Check if operation can be retried"""
        return self.retry_count < self.max_retries and self.status == SyncStatus.FAILED


class SyncResult(BaseModel):
    """Result of a synchronization operation"""
    sync_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    
    # Results summary
    total_operations: int = Field(ge=0, default=0)
    successful_operations: int = Field(ge=0, default=0)
    failed_operations: int = Field(ge=0, default=0)
    conflicts_detected: int = Field(ge=0, default=0)
    conflicts_resolved: int = Field(ge=0, default=0)
    
    # Timing information
    started_at: datetime
    completed_at: datetime
    duration_seconds: float = Field(ge=0.0, default=0.0)
    
    # Detailed results
    operations: List[SyncOperation_Model] = Field(default_factory=list)
    conflicts: List[DataConflict] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Data transfer statistics
    bytes_uploaded: int = Field(ge=0, default=0)
    bytes_downloaded: int = Field(ge=0, default=0)
    items_synchronized: Dict[str, int] = Field(default_factory=dict)  # data_type -> count
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        """Validate UUID format for user ID"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')
    
    def calculate_success_rate(self) -> float:
        """Calculate operation success rate"""
        if self.total_operations == 0:
            return 1.0
        return self.successful_operations / self.total_operations
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of sync results"""
        return {
            "sync_id": self.sync_id,
            "success_rate": self.calculate_success_rate(),
            "duration_seconds": self.duration_seconds,
            "total_operations": self.total_operations,
            "conflicts": self.conflicts_detected,
            "data_transferred_mb": (self.bytes_uploaded + self.bytes_downloaded) / (1024 * 1024),
            "items_by_type": self.items_synchronized
        }


class OfflineOperation(BaseModel):
    """Represents an operation queued while offline"""
    operation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    
    # Operation details
    operation_type: SyncOperation
    data_type: DataType
    data_id: str = Field(min_length=1)
    operation_data: Dict[str, Any] = Field(default_factory=dict)
    
    # Queuing information
    queued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    attempts: int = Field(ge=0, default=0)
    max_attempts: int = Field(ge=1, default=5)
    
    # Status
    is_critical: bool = False  # Critical operations get priority
    requires_network: bool = True
    can_batch: bool = True  # Can be batched with other operations
    
    # Dependencies
    depends_on_operations: List[str] = Field(default_factory=list)
    
    # Error tracking
    last_error: Optional[str] = None
    error_count: int = Field(ge=0, default=0)
    
    def can_execute_offline(self) -> bool:
        """Check if operation can be executed offline"""
        # Some operations like reading cached data can be done offline
        return not self.requires_network
    
    def increment_attempt(self) -> None:
        """Increment attempt counter"""
        self.attempts += 1
    
    def can_retry(self) -> bool:
        """Check if operation can be retried"""
        return self.attempts < self.max_attempts
    
    def mark_error(self, error: str) -> None:
        """Mark operation as having an error"""
        self.last_error = error
        self.error_count += 1


class SyncConfiguration(BaseModel):
    """Configuration for synchronization behavior"""
    user_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    
    # Sync preferences
    auto_sync_enabled: bool = True
    sync_interval_minutes: int = Field(ge=1, le=1440, default=15)  # 1 min to 24 hours
    sync_on_app_start: bool = True
    sync_on_app_close: bool = True
    
    # Conflict resolution preferences
    default_conflict_resolution: ConflictResolution = ConflictResolution.TIMESTAMP_BASED
    auto_resolve_conflicts: bool = True
    notify_on_conflicts: bool = True
    
    # Data priorities
    priority_data_types: List[DataType] = Field(default_factory=lambda: [
        DataType.PROGRESS_RECORD,
        DataType.LEARNING_ACTIVITY,
        DataType.USER_PROFILE
    ])
    
    # Network settings
    max_concurrent_operations: int = Field(ge=1, le=10, default=3)
    operation_timeout_seconds: int = Field(ge=10, le=300, default=60)
    retry_delay_seconds: int = Field(ge=1, le=60, default=5)
    
    # Storage limits
    max_offline_operations: int = Field(ge=10, le=1000, default=100)
    max_cache_size_mb: int = Field(ge=10, le=500, default=50)
    
    # Last sync tracking
    last_sync_at: Optional[datetime] = None
    last_successful_sync_at: Optional[datetime] = None
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        """Validate UUID format for user ID"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')
    
    def needs_sync(self) -> bool:
        """Check if sync is needed based on interval"""
        if not self.last_sync_at:
            return True
        
        time_since_sync = (datetime.now(timezone.utc) - self.last_sync_at).total_seconds()
        return time_since_sync >= (self.sync_interval_minutes * 60)
    
    def update_last_sync(self, successful: bool = True) -> None:
        """Update last sync timestamps"""
        now = datetime.now(timezone.utc)
        self.last_sync_at = now
        if successful:
            self.last_successful_sync_at = now


class RealtimeUpdate(BaseModel):
    """Real-time update message for WebSocket communication"""
    update_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(min_length=1)
    update_type: str = Field(min_length=1)  # data_change, sync_status, conflict, etc.
    
    # Update content
    data_type: Optional[DataType] = None
    data_id: Optional[str] = None
    data_payload: Optional[Dict[str, Any]] = None
    
    # Routing information
    target_devices: List[str] = Field(default_factory=list)  # Empty = broadcast to all
    exclude_devices: List[str] = Field(default_factory=list)
    
    # Metadata
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source_device: Optional[str] = None
    priority: int = Field(ge=1, le=10, default=5)
    
    # Delivery tracking
    delivery_attempts: int = Field(ge=0, default=0)
    max_delivery_attempts: int = Field(ge=1, default=3)
    expires_at: Optional[datetime] = None
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        """Validate UUID format for user ID"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')
    
    def is_expired(self) -> bool:
        """Check if update has expired"""
        if self.expires_at:
            return datetime.now(timezone.utc) > self.expires_at
        return False
    
    def can_retry_delivery(self) -> bool:
        """Check if delivery can be retried"""
        return self.delivery_attempts < self.max_delivery_attempts and not self.is_expired()
    
    def increment_delivery_attempt(self) -> None:
        """Increment delivery attempt counter"""
        self.delivery_attempts += 1
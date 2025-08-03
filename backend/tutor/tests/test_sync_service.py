"""
Unit tests for Synchronization Services - Task 8.1
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import json
import uuid

from tutor.services.sync_service import SyncService, ConflictResolver, OfflineManager, RealtimeUpdater
from tutor.services.realtime_sync_service import RealtimeSyncService, WebSocketConnectionManager
from tutor.services.data_versioning_service import DataVersioningService, VersionControlService, MergeStrategyService
from tutor.models.sync_models import (
    SyncOperation,
    ConflictResolution,
    SyncStatus,
    DataType,
    DeviceInfo,
    DataVersion,
    SyncData,
    DataConflict,
    SyncOperation_Model,
    SyncResult,
    OfflineOperation,
    SyncConfiguration,
    RealtimeUpdate
)


class TestSyncModels:
    """Test cases for Sync Models"""
    
    def test_device_info_creation(self):
        """Test creating device info"""
        device_info = DeviceInfo(
            device_id="device-123",
            device_type="mobile",
            platform="ios",
            app_version="1.0.0"
        )
        
        assert device_info.device_id == "device-123"
        assert device_info.device_type == "mobile"
        assert device_info.platform == "ios"
        assert device_info.is_online is True
        assert device_info.last_seen is not None
    
    def test_data_version_creation(self):
        """Test creating data version"""
        version = DataVersion(
            data_id="data-123",
            data_type=DataType.USER_PROFILE,
            device_id="device-123",
            user_id="user-123",
            checksum="abc123"
        )
        
        assert version.data_id == "data-123"
        assert version.data_type == DataType.USER_PROFILE
        assert version.version_number == 1
        assert version.device_id == "device-123"
        assert version.user_id == "user-123"
        assert version.checksum == "abc123"
        assert version.timestamp is not None
    
    def test_sync_data_checksum(self):
        """Test sync data checksum calculation"""
        sync_data = SyncData(
            data_id="data-123",
            data_type=DataType.PROGRESS_RECORD,
            content={"skill_level": 0.8, "name": "test"},
            version=DataVersion(
                data_id="data-123",
                data_type=DataType.PROGRESS_RECORD,
                device_id="device-123",
                user_id="user-123",
                checksum=""
            )
        )
        
        checksum = sync_data.get_checksum()
        assert len(checksum) == 64  # SHA256 length
        
        # Same content should produce same checksum
        sync_data2 = SyncData(
            data_id="data-456",
            data_type=DataType.LEARNING_ACTIVITY,
            content={"skill_level": 0.8, "name": "test"},  # Same content
            version=DataVersion(
                data_id="data-456",
                data_type=DataType.LEARNING_ACTIVITY,
                device_id="device-456",
                user_id="user-456",
                checksum=""
            )
        )
        
        assert sync_data.get_checksum() == sync_data2.get_checksum()
    
    def test_sync_data_version_update(self):
        """Test updating sync data version"""
        sync_data = SyncData(
            data_id="data-123",
            data_type=DataType.SETTINGS,
            content={"setting1": "value1"},
            version=DataVersion(
                data_id="data-123",
                data_type=DataType.SETTINGS,
                device_id="device-123",
                user_id="user-123",
                checksum="old_checksum"
            )
        )
        
        old_version = sync_data.version.version_number
        old_timestamp = sync_data.version.timestamp
        
        sync_data.update_version("device-456", ["setting1"])
        
        assert sync_data.version.version_number == old_version + 1
        assert sync_data.version.timestamp > old_timestamp
        assert sync_data.version.device_id == "device-456"
        assert sync_data.version.changes == ["setting1"]
        assert sync_data.version.checksum != "old_checksum"
    
    def test_data_conflict_auto_resolve(self):
        """Test data conflict auto-resolution detection"""
        now = datetime.now(timezone.utc)
        
        # Test time-based auto-resolution (5+ minutes apart)
        conflict = DataConflict(
            data_id="data-123",
            data_type=DataType.USER_PROFILE,
            user_id="user-123",
            server_version=DataVersion(
                data_id="data-123",
                data_type=DataType.USER_PROFILE,
                device_id="server",
                user_id="user-123",
                checksum="server",
                timestamp=now - timedelta(minutes=10)
            ),
            client_version=DataVersion(
                data_id="data-123",
                data_type=DataType.USER_PROFILE,
                device_id="client",
                user_id="user-123",
                checksum="client",
                timestamp=now
            ),
            conflicted_fields=["name", "email"]
        )
        
        assert conflict.can_auto_resolve() is True
        assert conflict.resolution_strategy == ConflictResolution.TIMESTAMP_BASED
        
        # Test metadata-only conflicts
        conflict.conflicted_fields = ["metadata", "updated_at"]
        conflict.auto_resolvable = False  # Reset
        conflict.resolution_strategy = None
        
        assert conflict.can_auto_resolve() is True
        assert conflict.resolution_strategy == ConflictResolution.TIMESTAMP_BASED
    
    def test_conflict_resolution(self):
        """Test conflict resolution"""
        conflict = DataConflict(
            data_id="data-123",
            data_type=DataType.PROGRESS_RECORD,
            user_id="user-123",
            server_version=DataVersion(
                data_id="data-123",
                data_type=DataType.PROGRESS_RECORD,
                device_id="server",
                user_id="user-123",
                checksum="server"
            ),
            client_version=DataVersion(
                data_id="data-123",
                data_type=DataType.PROGRESS_RECORD,
                device_id="client",
                user_id="user-123",
                checksum="client"
            )
        )
        
        assert conflict.resolved_at is None
        assert conflict.resolution_strategy is None
        
        resolution_data = {"resolved_by": "system", "method": "auto"}
        conflict.resolve(ConflictResolution.MERGE, "system", resolution_data)
        
        assert conflict.resolution_strategy == ConflictResolution.MERGE
        assert conflict.resolved_at is not None
        assert conflict.resolved_by == "system"
        assert conflict.resolution_data == resolution_data
    
    def test_sync_operation_dependencies(self):
        """Test sync operation dependency tracking"""
        operation = SyncOperation_Model(
            user_id="user-123",
            device_id="device-123",
            operation_type=SyncOperation.UPDATE,
            data_type=DataType.LEARNING_ACTIVITY,
            data_id="activity-123",
            depends_on=["op-1", "op-2"]
        )
        
        # Should not be able to execute with incomplete dependencies
        assert operation.can_execute(set()) is False
        assert operation.can_execute({"op-1"}) is False
        
        # Should be able to execute with all dependencies complete
        assert operation.can_execute({"op-1", "op-2"}) is True
        assert operation.can_execute({"op-1", "op-2", "op-3"}) is True
    
    def test_sync_operation_lifecycle(self):
        """Test sync operation lifecycle"""
        operation = SyncOperation_Model(
            user_id="user-123",
            device_id="device-123",
            operation_type=SyncOperation.CREATE,
            data_type=DataType.ACHIEVEMENT,
            data_id="achievement-123"
        )
        
        # Initial state
        assert operation.status == SyncStatus.PENDING
        assert operation.started_at is None
        assert operation.completed_at is None
        
        # Mark as started
        operation.mark_started()
        assert operation.status == SyncStatus.IN_PROGRESS
        assert operation.started_at is not None
        
        # Mark as completed
        operation.mark_completed()
        assert operation.status == SyncStatus.COMPLETED
        assert operation.completed_at is not None
        
        # Test retry logic
        operation.mark_failed("Test error")
        assert operation.status == SyncStatus.FAILED
        assert operation.error_message == "Test error"
        assert operation.can_retry() is True
        
        # Exhaust retries
        operation.retry_count = operation.max_retries
        assert operation.can_retry() is False
    
    def test_offline_operation(self):
        """Test offline operation"""
        operation = OfflineOperation(
            user_id="user-123",
            device_id="device-123",
            operation_type=SyncOperation.DELETE,
            data_type=DataType.CACHE,
            data_id="cache-123",
            requires_network=False
        )
        
        assert operation.can_execute_offline() is True
        assert operation.can_retry() is True
        
        # Test attempt tracking
        operation.increment_attempt()
        assert operation.attempts == 1
        
        # Test error handling
        operation.mark_error("Network error")
        assert operation.last_error == "Network error"
        assert operation.error_count == 1
    
    def test_sync_result_calculations(self):
        """Test sync result calculations"""
        sync_result = SyncResult(
            user_id="user-123",
            device_id="device-123",
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
            total_operations=10,
            successful_operations=8,
            failed_operations=2
        )
        
        success_rate = sync_result.calculate_success_rate()
        assert success_rate == 0.8
        
        # Test with zero operations
        sync_result.total_operations = 0
        assert sync_result.calculate_success_rate() == 1.0
        
        summary = sync_result.get_summary()
        assert "sync_id" in summary
        assert "success_rate" in summary
        assert "duration_seconds" in summary
    
    def test_realtime_update(self):
        """Test realtime update"""
        update = RealtimeUpdate(
            user_id="user-123",
            update_type="data_change",
            data_type=DataType.PROGRESS_RECORD,
            data_id="progress-123",
            target_devices=["device-1", "device-2"],
            exclude_devices=["device-3"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        assert update.user_id == "user-123"
        assert update.update_type == "data_change"
        assert update.data_type == DataType.PROGRESS_RECORD
        assert update.is_expired() is False
        assert update.can_retry_delivery() is True
        
        # Test delivery attempt tracking
        update.increment_delivery_attempt()
        assert update.delivery_attempts == 1
        
        # Test expiration
        update.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        assert update.is_expired() is True
        assert update.can_retry_delivery() is False


class TestConflictResolver:
    """Test cases for ConflictResolver"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        return Mock()
    
    @pytest.fixture
    def conflict_resolver(self, mock_db):
        """Create conflict resolver with mocked dependencies"""
        return ConflictResolver(mock_db)
    
    @pytest.fixture
    def sample_conflict(self):
        """Create sample conflict for testing"""
        return DataConflict(
            data_id="data-123",
            data_type=DataType.USER_PROFILE,
            user_id="user-123",
            server_version=DataVersion(
                data_id="data-123",
                data_type=DataType.USER_PROFILE,
                device_id="server",
                user_id="user-123",
                checksum="server_checksum",
                timestamp=datetime.now(timezone.utc) - timedelta(minutes=10)
            ),
            client_version=DataVersion(
                data_id="data-123",
                data_type=DataType.USER_PROFILE,
                device_id="client",
                user_id="user-123",
                checksum="client_checksum",
                timestamp=datetime.now(timezone.utc)
            ),
            conflicted_fields=["name", "preferences"]
        )
    
    @pytest.mark.asyncio
    async def test_resolve_conflict_auto_resolvable(self, conflict_resolver, sample_conflict):
        """Test resolving auto-resolvable conflict"""
        # Make conflict auto-resolvable
        sample_conflict.conflicted_fields = ["metadata", "updated_at"]
        
        with patch.object(conflict_resolver, '_get_sync_data_for_version') as mock_get_data:
            mock_sync_data = SyncData(
                data_id="data-123",
                data_type=DataType.USER_PROFILE,
                content={"name": "test", "metadata": "updated"},
                version=sample_conflict.client_version
            )
            mock_get_data.return_value = mock_sync_data
            
            result = await conflict_resolver.resolve_conflict(sample_conflict)
            
            assert result is not None
            assert result.data_id == "data-123"
            assert sample_conflict.resolution_strategy == ConflictResolution.TIMESTAMP_BASED
    
    @pytest.mark.asyncio
    async def test_resolve_by_timestamp(self, conflict_resolver, sample_conflict):
        """Test timestamp-based conflict resolution"""
        with patch.object(conflict_resolver, '_get_sync_data_for_version') as mock_get_data:
            client_data = SyncData(
                data_id="data-123",
                data_type=DataType.USER_PROFILE,
                content={"name": "client_name"},
                version=sample_conflict.client_version
            )
            mock_get_data.return_value = client_data
            
            # Client version is newer (created later)
            result = await conflict_resolver._resolve_by_timestamp(sample_conflict)
            
            assert result == client_data
            mock_get_data.assert_called_once_with(sample_conflict.client_version)
    
    @pytest.mark.asyncio
    async def test_resolve_by_merge(self, conflict_resolver, sample_conflict):
        """Test merge-based conflict resolution"""
        server_content = {"name": "server_name", "email": "server@test.com", "preferences": {"theme": "dark"}}
        client_content = {"name": "client_name", "email": "server@test.com", "preferences": {"theme": "light"}}
        
        server_data = SyncData(
            data_id="data-123",
            data_type=DataType.USER_PROFILE,
            content=server_content,
            version=sample_conflict.server_version
        )
        
        client_data = SyncData(
            data_id="data-123",
            data_type=DataType.USER_PROFILE,
            content=client_content,
            version=sample_conflict.client_version
        )
        
        def mock_get_data(version):
            if version == sample_conflict.server_version:
                return server_data
            else:
                return client_data
        
        with patch.object(conflict_resolver, '_get_sync_data_for_version', side_effect=mock_get_data):
            result = await conflict_resolver._resolve_by_merge(sample_conflict)
            
            assert result is not None
            assert result.data_id == "data-123"
            assert result.version.version_number > max(
                sample_conflict.server_version.version_number,
                sample_conflict.client_version.version_number
            )
    
    @pytest.mark.asyncio
    async def test_merge_data_content_user_profile(self, conflict_resolver):
        """Test merging user profile data"""
        server_content = {
            "name": "Server Name",
            "language": "en",
            "theme": "dark",
            "computed_score": 85
        }
        
        client_content = {
            "name": "Client Name", 
            "language": "es",
            "theme": "light",
            "computed_score": 75
        }
        
        conflicted_fields = ["language", "theme"]
        
        merged = await conflict_resolver._merge_data_content(
            server_content, client_content, DataType.USER_PROFILE, conflicted_fields
        )
        
        # Client preferences should win for user profile
        assert merged["language"] == "es"  # Client preference
        assert merged["theme"] == "light"  # Client preference
        assert merged["name"] == "Server Name"  # Not in conflicted fields, server version kept
    
    @pytest.mark.asyncio
    async def test_merge_data_content_progress_record(self, conflict_resolver):
        """Test merging progress record data"""
        server_content = {
            "skill_level": 0.8,
            "confidence_score": 0.7,
            "total_time": 120,
            "completed_activities": ["act1", "act2"],
            "last_activity": "act2"
        }
        
        client_content = {
            "skill_level": 0.9,  # Higher
            "confidence_score": 0.6,  # Lower
            "total_time": 150,  # Higher
            "completed_activities": ["act2", "act3"],  # Different
            "last_activity": "act3"
        }
        
        conflicted_fields = ["skill_level", "confidence_score", "total_time", "completed_activities"]
        
        merged = await conflict_resolver._merge_data_content(
            server_content, client_content, DataType.PROGRESS_RECORD, conflicted_fields
        )
        
        # Should take maximum values for numeric fields
        assert merged["skill_level"] == 0.9  # Max of 0.8 and 0.9
        assert merged["confidence_score"] == 0.7  # Max of 0.7 and 0.6
        assert merged["total_time"] == 150  # Max of 120 and 150
        
        # Should merge arrays (union)
        expected_activities = ["act1", "act2", "act3"]
        assert set(merged["completed_activities"]) == set(expected_activities)


class TestOfflineManager:
    """Test cases for OfflineManager"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        return Mock()
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        redis_mock = AsyncMock()
        redis_mock.zadd = AsyncMock(return_value=1)
        redis_mock.expire = AsyncMock(return_value=True)
        redis_mock.zrevrange = AsyncMock(return_value=[])
        redis_mock.zrem = AsyncMock(return_value=1)
        redis_mock.zcard = AsyncMock(return_value=0)
        redis_mock.zrange = AsyncMock(return_value=[])
        redis_mock.delete = AsyncMock(return_value=1)
        return redis_mock
    
    @pytest.fixture
    def offline_manager(self, mock_db, mock_redis):
        """Create offline manager with mocked dependencies"""
        return OfflineManager(mock_db, mock_redis)
    
    @pytest.fixture
    def sample_operation(self):
        """Create sample offline operation"""
        return OfflineOperation(
            user_id="user-123",
            device_id="device-123",
            operation_type=SyncOperation.UPDATE,
            data_type=DataType.LEARNING_ACTIVITY,
            data_id="activity-123",
            operation_data={"field": "value"},
            is_critical=True
        )
    
    @pytest.mark.asyncio
    async def test_queue_operation(self, offline_manager, sample_operation):
        """Test queuing an offline operation"""
        result = await offline_manager.queue_operation(sample_operation)
        
        assert result is True
        offline_manager.redis.zadd.assert_called_once()
        offline_manager.redis.expire.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_queued_operations(self, offline_manager, mock_redis, sample_operation):
        """Test retrieving queued operations"""
        # Mock Redis returning serialized operation
        operation_json = sample_operation.json()
        mock_redis.zrevrange.return_value = [operation_json]
        
        operations = await offline_manager.get_queued_operations("user-123", "device-123")
        
        assert len(operations) == 1
        assert operations[0].operation_id == sample_operation.operation_id
        assert operations[0].operation_type == sample_operation.operation_type
    
    @pytest.mark.asyncio
    async def test_remove_operation(self, offline_manager, mock_redis, sample_operation):
        """Test removing operation from queue"""
        # Mock Redis returning the operation to be removed
        operation_json = sample_operation.json()
        mock_redis.zrange.return_value = [operation_json]
        
        result = await offline_manager.remove_operation("user-123", "device-123", sample_operation.operation_id)
        
        assert result is True
        mock_redis.zrem.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_clear_queue(self, offline_manager):
        """Test clearing offline queue"""
        result = await offline_manager.clear_queue("user-123", "device-123")
        
        assert result is True
        offline_manager.redis.delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_queue_status(self, offline_manager, mock_redis, sample_operation):
        """Test getting queue status"""
        mock_redis.zcard.return_value = 2
        operation_json = sample_operation.json()
        mock_redis.zrange.return_value = [operation_json, operation_json]
        
        status = await offline_manager.get_queue_status("user-123", "device-123")
        
        assert status["total_operations"] == 2
        assert "operations_by_type" in status
        assert SyncOperation.UPDATE.value in status["operations_by_type"]
    
    def test_calculate_priority_score(self, offline_manager, sample_operation):
        """Test priority score calculation"""
        # Critical operation should get high priority
        score1 = offline_manager._calculate_priority_score(sample_operation)
        assert score1 > 1000  # Critical bonus
        
        # Non-critical operation
        sample_operation.is_critical = False
        score2 = offline_manager._calculate_priority_score(sample_operation)
        assert score2 < score1  # Should be lower than critical
        
        # Different operation types should have different scores
        sample_operation.operation_type = SyncOperation.CREATE
        score3 = offline_manager._calculate_priority_score(sample_operation)
        
        sample_operation.operation_type = SyncOperation.DELETE
        score4 = offline_manager._calculate_priority_score(sample_operation)
        
        assert score3 != score4  # Different operation types should have different priorities


class TestRealtimeUpdater:
    """Test cases for RealtimeUpdater"""
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client"""
        redis_mock = AsyncMock()
        redis_mock.publish = AsyncMock(return_value=1)
        redis_mock.lpush = AsyncMock(return_value=1)
        redis_mock.ltrim = AsyncMock(return_value=True)
        redis_mock.expire = AsyncMock(return_value=True)
        redis_mock.lrange = AsyncMock(return_value=[])
        redis_mock.delete = AsyncMock(return_value=1)
        return redis_mock
    
    @pytest.fixture
    def realtime_updater(self, mock_redis):
        """Create realtime updater with mocked dependencies"""
        return RealtimeUpdater(mock_redis)
    
    @pytest.fixture
    def sample_update(self):
        """Create sample realtime update"""
        return RealtimeUpdate(
            user_id="user-123",
            update_type="data_change",
            data_type=DataType.PROGRESS_RECORD,
            data_id="progress-123",
            data_payload={"field": "value"},
            target_devices=["device-1", "device-2"],
            exclude_devices=["device-3"]
        )
    
    @pytest.mark.asyncio
    async def test_broadcast_update(self, realtime_updater, sample_update):
        """Test broadcasting realtime update"""
        result = await realtime_updater.broadcast_update(sample_update)
        
        assert result is True
        
        # Should publish to user channel
        expected_user_channel = f"realtime_updates:{sample_update.user_id}"
        realtime_updater.redis.publish.assert_any_call(expected_user_channel, sample_update.json())
        
        # Should publish to target device channels
        for device_id in sample_update.target_devices:
            expected_device_channel = f"device_updates:{device_id}"
            realtime_updater.redis.publish.assert_any_call(expected_device_channel, sample_update.json())
    
    @pytest.mark.asyncio
    async def test_get_missed_updates(self, realtime_updater, mock_redis):
        """Test getting missed updates"""
        since = datetime.now(timezone.utc) - timedelta(hours=1)
        
        # Mock stored update
        update = RealtimeUpdate(
            user_id="user-123",
            update_type="sync_status",
            timestamp=datetime.now(timezone.utc)
        )
        mock_redis.lrange.return_value = [update.json()]
        
        missed_updates = await realtime_updater.get_missed_updates("user-123", "device-123", since)
        
        assert len(missed_updates) == 1
        assert missed_updates[0].update_type == "sync_status"
    
    @pytest.mark.asyncio
    async def test_notify_sync_status(self, realtime_updater):
        """Test sync status notification"""
        await realtime_updater.notify_sync_status(
            "user-123", "device-123", SyncStatus.COMPLETED, {"success": True}
        )
        
        # Should publish update
        realtime_updater.redis.publish.assert_called()
    
    @pytest.mark.asyncio
    async def test_notify_conflict_detected(self, realtime_updater):
        """Test conflict detection notification"""
        conflict = DataConflict(
            data_id="data-123",
            data_type=DataType.USER_PROFILE,
            user_id="user-123",
            server_version=DataVersion(
                data_id="data-123",
                data_type=DataType.USER_PROFILE,
                device_id="server",
                user_id="user-123",
                checksum="server"
            ),
            client_version=DataVersion(
                data_id="data-123",
                data_type=DataType.USER_PROFILE,
                device_id="client",
                user_id="user-123",
                checksum="client"
            ),
            conflicted_fields=["name"],
            severity="high"
        )
        
        await realtime_updater.notify_conflict_detected(conflict)
        
        # Should publish high priority update
        realtime_updater.redis.publish.assert_called()


class TestSyncService:
    """Test cases for SyncService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        return Mock()
    
    @pytest.fixture
    def mock_redis_url(self):
        """Mock Redis URL"""
        return "redis://test:6379"
    
    @pytest.fixture
    def sync_service(self, mock_db, mock_redis_url):
        """Create sync service with mocked dependencies"""
        with patch('tutor.services.sync_service.redis.from_url') as mock_redis_factory:
            mock_redis = AsyncMock()
            mock_redis_factory.return_value = mock_redis
            
            with patch('tutor.services.sync_service.ChildProfileRepository'):
                service = SyncService(mock_db, mock_redis_url)
                service.redis = mock_redis
                return service
    
    @pytest.mark.asyncio
    async def test_sync_user_data_success(self, sync_service):
        """Test successful user data synchronization"""
        # Mock components
        sync_service.offline_manager.get_queued_operations = AsyncMock(return_value=[])
        sync_service.realtime_updater.notify_sync_status = AsyncMock()
        
        with patch.object(sync_service, '_get_server_updates', return_value=[]), \
             patch.object(sync_service, '_apply_server_updates'), \
             patch.object(sync_service, '_update_device_info'):
            
            result = await sync_service.sync_user_data("user-123", "device-123")
            
            assert result.user_id == "user-123"
            assert result.device_id == "device-123"
            assert result.completed_at is not None
            assert result.duration_seconds >= 0
    
    @pytest.mark.asyncio
    async def test_sync_user_data_with_conflicts(self, sync_service):
        """Test sync with conflicts"""
        # Create mock conflict
        conflict = DataConflict(
            data_id="data-123",
            data_type=DataType.PROGRESS_RECORD,
            user_id="user-123",
            server_version=DataVersion(
                data_id="data-123",
                data_type=DataType.PROGRESS_RECORD,
                device_id="server",
                user_id="user-123",
                checksum="server"
            ),
            client_version=DataVersion(
                data_id="data-123",
                data_type=DataType.PROGRESS_RECORD,
                device_id="client",
                user_id="user-123",
                checksum="client"
            )
        )
        
        # Mock local data that will create conflicts
        local_data = [
            SyncData(
                data_id="data-123",
                data_type=DataType.PROGRESS_RECORD,
                content={"skill_level": 0.9},
                version=DataVersion(
                    data_id="data-123",
                    data_type=DataType.PROGRESS_RECORD,
                    device_id="client",
                    user_id="user-123",
                    checksum="client"
                )
            )
        ]
        
        # Mock methods
        sync_service.offline_manager.get_queued_operations = AsyncMock(return_value=[])
        sync_service.realtime_updater.notify_sync_status = AsyncMock()
        sync_service.conflict_resolver.resolve_conflict = AsyncMock(return_value=local_data[0])
        
        with patch.object(sync_service, '_check_for_conflicts', return_value=conflict), \
             patch.object(sync_service, '_get_server_updates', return_value=[]), \
             patch.object(sync_service, '_apply_server_updates'), \
             patch.object(sync_service, '_update_device_info'), \
             patch.object(sync_service, '_apply_resolved_data', return_value=True):
            
            result = await sync_service.sync_user_data("user-123", "device-123", local_data)
            
            assert result.conflicts_detected > 0
            assert len(result.conflicts) > 0
    
    @pytest.mark.asyncio
    async def test_handle_offline_queue(self, sync_service):
        """Test handling offline operation queue"""
        # Create mock offline operations
        operations = [
            OfflineOperation(
                user_id="user-123",
                device_id="device-123",
                operation_type=SyncOperation.CREATE,
                data_type=DataType.ACHIEVEMENT,
                data_id="achievement-123"
            ),
            OfflineOperation(
                user_id="user-123", 
                device_id="device-123",
                operation_type=SyncOperation.UPDATE,
                data_type=DataType.PROGRESS_RECORD,
                data_id="progress-123"
            )
        ]
        
        sync_service.offline_manager.get_queued_operations = AsyncMock(return_value=operations)
        sync_service.offline_manager.remove_operation = AsyncMock(return_value=True)
        
        with patch.object(sync_service, '_execute_offline_operation', return_value=True):
            result = await sync_service.handle_offline_queue("user-123", "device-123")
            
            assert result["processed"] == 2
            assert result["success"] == 2
            assert result["failed"] == 0
    
    @pytest.mark.asyncio
    async def test_resolve_conflicts(self, sync_service):
        """Test conflict resolution"""
        conflicts = [
            DataConflict(
                data_id="data-1",
                data_type=DataType.USER_PROFILE,
                user_id="user-123",
                server_version=DataVersion(
                    data_id="data-1",
                    data_type=DataType.USER_PROFILE,
                    device_id="server",
                    user_id="user-123",
                    checksum="server"
                ),
                client_version=DataVersion(
                    data_id="data-1",
                    data_type=DataType.USER_PROFILE,
                    device_id="client",
                    user_id="user-123",
                    checksum="client"
                )
            )
        ]
        
        resolved_data = SyncData(
            data_id="data-1",
            data_type=DataType.USER_PROFILE,
            content={"name": "resolved"},
            version=conflicts[0].server_version
        )
        
        sync_service.conflict_resolver.resolve_conflict = AsyncMock(return_value=resolved_data)
        
        with patch.object(sync_service, '_apply_resolved_data', return_value=True):
            result = await sync_service.resolve_conflicts(conflicts)
            
            assert result["resolved"] == 1
            assert result["failed"] == 0
    
    @pytest.mark.asyncio
    async def test_error_handling(self, sync_service):
        """Test error handling in sync service"""
        # Mock error in sync process
        sync_service.offline_manager.get_queued_operations = AsyncMock(side_effect=Exception("Redis error"))
        sync_service.realtime_updater.notify_sync_status = AsyncMock()
        
        with patch.object(sync_service, '_update_device_info'):
            result = await sync_service.sync_user_data("user-123", "device-123")
            
            assert len(result.errors) > 0
            assert "Redis error" in result.errors[0]


class TestWebSocketConnectionManager:
    """Test cases for WebSocketConnectionManager"""
    
    @pytest.fixture
    def connection_manager(self):
        """Create WebSocket connection manager"""
        return WebSocketConnectionManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """Mock WebSocket connection"""
        ws = AsyncMock()
        ws.closed = False
        ws.send = AsyncMock()
        ws.close = AsyncMock()
        return ws
    
    @pytest.mark.asyncio
    async def test_register_connection(self, connection_manager, mock_websocket):
        """Test registering WebSocket connection"""
        user_id = "user-123"
        device_id = "device-123"
        device_info = {"type": "mobile", "platform": "ios"}
        
        result = await connection_manager.register_connection(
            mock_websocket, user_id, device_id, device_info
        )
        
        assert result is True
        assert device_id in connection_manager.connections
        assert device_id in connection_manager.user_devices[user_id]
        assert connection_manager.device_users[device_id] == user_id
        assert device_id in connection_manager.connection_info
        
        # Should have sent welcome message
        mock_websocket.send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_unregister_connection(self, connection_manager, mock_websocket):
        """Test unregistering WebSocket connection"""
        user_id = "user-123"
        device_id = "device-123"
        
        # First register
        await connection_manager.register_connection(
            mock_websocket, user_id, device_id, {}
        )
        
        # Then unregister
        await connection_manager.unregister_connection(device_id)
        
        assert device_id not in connection_manager.connections
        assert device_id not in connection_manager.user_devices.get(user_id, set())
        assert device_id not in connection_manager.device_users
        assert device_id not in connection_manager.connection_info
        
        # Should have closed WebSocket
        mock_websocket.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_message(self, connection_manager, mock_websocket):
        """Test sending message to device"""
        user_id = "user-123"
        device_id = "device-123"
        
        # Register connection
        await connection_manager.register_connection(
            mock_websocket, user_id, device_id, {}
        )
        
        # Send message
        message = {"type": "test", "data": "hello"}
        result = await connection_manager.send_message(device_id, message)
        
        assert result is True
        
        # Should have sent message with timestamp and ID
        call_args = mock_websocket.send.call_args_list[-1]  # Last call
        sent_data = json.loads(call_args[0][0])
        assert sent_data["type"] == "test"
        assert sent_data["data"] == "hello"
        assert "timestamp" in sent_data
        assert "message_id" in sent_data
    
    @pytest.mark.asyncio
    async def test_broadcast_to_user(self, connection_manager):
        """Test broadcasting to all user devices"""
        user_id = "user-123"
        
        # Register multiple devices for user
        mock_ws1 = AsyncMock()
        mock_ws1.closed = False
        mock_ws2 = AsyncMock()
        mock_ws2.closed = False
        
        await connection_manager.register_connection(mock_ws1, user_id, "device-1", {})
        await connection_manager.register_connection(mock_ws2, user_id, "device-2", {})
        
        # Broadcast message
        message = {"type": "broadcast", "data": "hello all"}
        sent_count = await connection_manager.broadcast_to_user(user_id, message)
        
        assert sent_count == 2
        
        # Both devices should have received the message
        mock_ws1.send.assert_called()
        mock_ws2.send.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_user_devices(self, connection_manager, mock_websocket):
        """Test getting user devices"""
        user_id = "user-123"
        device_id = "device-123"
        
        # Initially no devices
        devices = await connection_manager.get_user_devices(user_id)
        assert len(devices) == 0
        
        # Register device
        await connection_manager.register_connection(
            mock_websocket, user_id, device_id, {}
        )
        
        devices = await connection_manager.get_user_devices(user_id)
        assert len(devices) == 1
        assert device_id in devices
    
    @pytest.mark.asyncio
    async def test_connection_stats(self, connection_manager, mock_websocket):
        """Test connection statistics"""
        # Initial stats
        stats = await connection_manager.get_connection_stats()
        assert stats["active_connections"] == 0
        
        # Register connection
        await connection_manager.register_connection(
            mock_websocket, "user-123", "device-123", {}
        )
        
        # Updated stats
        stats = await connection_manager.get_connection_stats()
        assert stats["active_connections"] == 1
        assert stats["total_connections"] == 1
        assert "devices_by_user" in stats
        assert "uptime_by_device" in stats
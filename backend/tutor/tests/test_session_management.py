"""
Unit tests for session management service with multi-device support and parental oversight
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
from typing import Dict, Any

from ..services.session_management_service import SessionManagementService, SessionStatus
from ..models.user_models import UserSession, ChildProfile, ParentProfile
from services.supabase import DBConnection


@pytest.fixture
def mock_db():
    """Mock database connection"""
    return MagicMock(spec=DBConnection)


@pytest.fixture
def session_service(mock_db):
    """Create session management service with mocked dependencies"""
    return SessionManagementService(mock_db)


@pytest.fixture
def sample_child_profile():
    """Sample child profile"""
    return ChildProfile(
        child_id="child-123",
        parent_id="parent-123",
        name="Test Child",
        age=8,
        grade_level=3,
        safety_settings={
            "session_time_limits": {
                "daily_limit_minutes": 60,
                "max_consecutive_minutes": 30
            },
            "quiet_hours": {"start": "20:00", "end": "07:00"}
        }
    )


@pytest.fixture
def sample_session():
    """Sample user session"""
    return UserSession(
        session_id="session-123",
        user_id="child-123",
        device_id="device-456",
        device_type="web",
        started_at=datetime.now(timezone.utc) - timedelta(minutes=15),
        last_activity=datetime.now(timezone.utc),
        is_active=True,
        sync_status="synced"
    )


class TestSessionStart:
    """Test session start functionality"""
    
    @pytest.mark.asyncio
    async def test_start_session_success_new(self, session_service, sample_child_profile):
        """Test successful start of new session"""
        # Mock safety validation success
        session_service.safety_service.validate_session_safety = AsyncMock(
            return_value={"allowed": True, "reason": "Session validation passed"}
        )
        
        # Mock no existing sessions
        session_service.session_repo.get_active_sessions_by_user_id = AsyncMock(return_value=[])
        
        # Mock session creation
        new_session = UserSession(
            session_id="session-123",
            user_id="child-123",
            device_id="device-456",
            device_type="web"
        )
        session_service.session_repo.create_session = AsyncMock(return_value=new_session)
        session_service._log_session_event = AsyncMock()
        
        result = await session_service.start_session(
            "child-123",
            "device-456",
            "web",
            parent_supervision=True
        )
        
        assert result["success"] is True
        assert result["session_id"] == "session-123"
        assert result["resumed"] is False
        session_service.session_repo.create_session.assert_called_once()
        session_service._log_session_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_session_resume_existing(self, session_service, sample_session):
        """Test resuming existing session on same device"""
        # Mock safety validation success
        session_service.safety_service.validate_session_safety = AsyncMock(
            return_value={"allowed": True, "reason": "Session validation passed"}
        )
        
        # Mock existing session on same device
        session_service.session_repo.get_active_sessions_by_user_id = AsyncMock(
            return_value=[sample_session]
        )
        session_service.session_repo.update_session_activity = AsyncMock(return_value=sample_session)
        
        result = await session_service.start_session(
            "child-123",
            "device-456",
            "web"
        )
        
        assert result["success"] is True
        assert result["session_id"] == "session-123"
        assert result["resumed"] is True
        session_service.session_repo.update_session_activity.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_session_safety_blocked(self, session_service):
        """Test session start blocked by safety validation"""
        # Mock safety validation failure
        session_service.safety_service.validate_session_safety = AsyncMock(
            return_value={"allowed": False, "reason": "Daily time limit exceeded"}
        )
        
        result = await session_service.start_session(
            "child-123",
            "device-456",
            "web"
        )
        
        assert result["success"] is False
        assert result["reason"] == "Daily time limit exceeded"
        assert result["session_id"] is None
    
    @pytest.mark.asyncio
    async def test_start_session_error_handling(self, session_service):
        """Test session start error handling"""
        # Mock safety service to raise exception
        session_service.safety_service.validate_session_safety = AsyncMock(
            side_effect=Exception("Database error")
        )
        
        result = await session_service.start_session(
            "child-123",
            "device-456",
            "web"
        )
        
        assert result["success"] is False
        assert result["reason"] == "Session start error"


class TestSessionEnd:
    """Test session end functionality"""
    
    @pytest.mark.asyncio
    async def test_end_session_success(self, session_service, sample_session):
        """Test successful session end"""
        # Mock session retrieval
        session_service.session_repo.get_session_by_id = AsyncMock(return_value=sample_session)
        session_service.session_repo.deactivate_session = AsyncMock(return_value=sample_session)
        
        # Mock time tracking
        session_service.time_tracking_repo.record_session_time = AsyncMock()
        session_service.time_tracking_repo.get_daily_usage = AsyncMock(return_value=45)
        session_service._log_session_event = AsyncMock()
        
        result = await session_service.end_session("session-123", "user_ended")
        
        assert result["success"] is True
        assert "duration_minutes" in result
        assert result["total_daily_usage"] == 45
        
        session_service.session_repo.deactivate_session.assert_called_once_with("session-123")
        session_service.time_tracking_repo.record_session_time.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_end_session_not_found(self, session_service):
        """Test ending non-existent session"""
        session_service.session_repo.get_session_by_id = AsyncMock(return_value=None)
        
        result = await session_service.end_session("nonexistent-session")
        
        assert result["success"] is False
        assert result["reason"] == "Session not found"
    
    @pytest.mark.asyncio
    async def test_end_session_already_ended(self, session_service, sample_session):
        """Test ending already inactive session"""
        sample_session.is_active = False
        session_service.session_repo.get_session_by_id = AsyncMock(return_value=sample_session)
        
        result = await session_service.end_session("session-123")
        
        assert result["success"] is False
        assert result["reason"] == "Session already ended"
    
    @pytest.mark.asyncio
    async def test_end_session_calculates_duration(self, session_service):
        """Test that session end correctly calculates duration"""
        # Create session that started 25 minutes ago
        session = UserSession(
            session_id="session-123",
            user_id="child-123",
            device_id="device-456",
            device_type="web",
            started_at=datetime.now(timezone.utc) - timedelta(minutes=25),
            is_active=True
        )
        
        session_service.session_repo.get_session_by_id = AsyncMock(return_value=session)
        session_service.session_repo.deactivate_session = AsyncMock()
        session_service.time_tracking_repo.record_session_time = AsyncMock()
        session_service.time_tracking_repo.get_daily_usage = AsyncMock(return_value=25)
        session_service._log_session_event = AsyncMock()
        
        result = await session_service.end_session("session-123")
        
        assert result["success"] is True
        # Duration should be approximately 25 minutes (allowing for small timing differences)
        assert 24 <= result["duration_minutes"] <= 26


class TestSessionPauseResume:
    """Test session pause and resume functionality"""
    
    @pytest.mark.asyncio
    async def test_pause_session_success(self, session_service, sample_session):
        """Test successful session pause"""
        session_service.session_repo.get_session_by_id = AsyncMock(return_value=sample_session)
        session_service.session_repo.update_sync_status = AsyncMock()
        session_service._log_session_event = AsyncMock()
        
        result = await session_service.pause_session("session-123", "break_time")
        
        assert result["success"] is True
        assert result["reason"] == "Session paused"
        
        session_service.session_repo.update_sync_status.assert_called_once_with("session-123", "pending")
        session_service._log_session_event.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_resume_session_success(self, session_service, sample_session):
        """Test successful session resume"""
        session_service.session_repo.get_session_by_id = AsyncMock(return_value=sample_session)
        
        # Mock safety validation success
        session_service.safety_service.validate_session_safety = AsyncMock(
            return_value={"allowed": True, "reason": "Session validation passed"}
        )
        
        session_service.session_repo.update_session_activity = AsyncMock()
        session_service.session_repo.update_sync_status = AsyncMock()
        session_service._log_session_event = AsyncMock()
        
        result = await session_service.resume_session("session-123")
        
        assert result["success"] is True
        assert result["reason"] == "Session resumed"
        
        session_service.session_repo.update_session_activity.assert_called_once()
        session_service.session_repo.update_sync_status.assert_called_once_with("session-123", "synced")
    
    @pytest.mark.asyncio
    async def test_resume_session_safety_blocked(self, session_service, sample_session):
        """Test session resume blocked by safety validation"""
        session_service.session_repo.get_session_by_id = AsyncMock(return_value=sample_session)
        
        # Mock safety validation failure
        session_service.safety_service.validate_session_safety = AsyncMock(
            return_value={"allowed": False, "reason": "Time limit exceeded"}
        )
        
        result = await session_service.resume_session("session-123")
        
        assert result["success"] is False
        assert result["reason"] == "Time limit exceeded"


class TestSessionSuspension:
    """Test session suspension functionality"""
    
    @pytest.mark.asyncio
    async def test_suspend_session_success(self, session_service, sample_session, sample_child_profile):
        """Test successful session suspension"""
        session_service.session_repo.get_session_by_id = AsyncMock(return_value=sample_session)
        session_service.session_repo.deactivate_session = AsyncMock()
        session_service.child_repo.get_child_profile_by_id = AsyncMock(return_value=sample_child_profile)
        session_service._log_session_event = AsyncMock()
        session_service._notify_parent_of_suspension = AsyncMock()
        
        result = await session_service.suspend_session(
            "session-123",
            "inappropriate_content",
            "violation-456"
        )
        
        assert result["success"] is True
        assert result["reason"] == "Session suspended due to safety violation"
        
        session_service.session_repo.deactivate_session.assert_called_once()
        session_service._notify_parent_of_suspension.assert_called_once_with(
            "parent-123", "session-123", "inappropriate_content"
        )
    
    @pytest.mark.asyncio
    async def test_suspend_session_not_found(self, session_service):
        """Test suspending non-existent session"""
        session_service.session_repo.get_session_by_id = AsyncMock(return_value=None)
        
        result = await session_service.suspend_session("nonexistent-session", "violation")
        
        assert result["success"] is False
        assert result["reason"] == "Session not found"


class TestMultiDeviceSupport:
    """Test multi-device session support"""
    
    @pytest.mark.asyncio
    async def test_get_active_sessions_for_child(self, session_service):
        """Test getting active sessions for a child across devices"""
        sessions = [
            UserSession(
                session_id="session-web",
                user_id="child-123",
                device_id="device-web",
                device_type="web",
                started_at=datetime.now(timezone.utc) - timedelta(minutes=20)
            ),
            UserSession(
                session_id="session-mobile",
                user_id="child-123",
                device_id="device-mobile",
                device_type="mobile",
                started_at=datetime.now(timezone.utc) - timedelta(minutes=10)
            )
        ]
        
        session_service.session_repo.get_active_sessions_by_user_id = AsyncMock(return_value=sessions)
        
        result = await session_service.get_active_sessions_for_child("child-123")
        
        assert len(result) == 2
        assert result[0]["device_type"] == "web"
        assert result[1]["device_type"] == "mobile"
        assert result[0]["duration_minutes"] >= 19  # Approximately 20 minutes
        assert result[1]["duration_minutes"] >= 9   # Approximately 10 minutes
    
    @pytest.mark.asyncio
    async def test_sync_session_data(self, session_service, sample_session):
        """Test syncing session data across devices"""
        session_service.session_repo.get_session_by_id = AsyncMock(return_value=sample_session)
        session_service.session_repo.update_session_activity = AsyncMock()
        session_service.session_repo.update_sync_status = AsyncMock()
        session_service._log_session_event = AsyncMock()
        
        data_updates = {
            "progress": {"topic_id": "math-123", "completed": True},
            "preferences": {"difficulty": "medium"}
        }
        
        result = await session_service.sync_session_data("session-123", data_updates)
        
        assert result["success"] is True
        assert result["reason"] == "Data synced successfully"
        
        session_service.session_repo.update_session_activity.assert_called_once()
        session_service.session_repo.update_sync_status.assert_called_once_with("session-123", "synced")


class TestParentalOversight:
    """Test parental oversight functionality"""
    
    @pytest.mark.asyncio
    async def test_get_parental_oversight_info(self, session_service):
        """Test getting parental oversight information"""
        from ..repositories.user_repository import ParentProfileRepository
        
        parent = ParentProfile(
            parent_id="parent-profile-123",
            user_id="parent-123",
            children_ids=["child-123", "child-456"]
        )
        
        child1 = ChildProfile(
            child_id="child-123",
            parent_id="parent-123",
            name="Child One",
            age=8,
            grade_level=3,
            safety_settings={"content_filtering_level": "strict"}
        )
        
        child2 = ChildProfile(
            child_id="child-456",
            parent_id="parent-123",
            name="Child Two",
            age=10,
            grade_level=5,
            safety_settings={"content_filtering_level": "moderate"}
        )
        
        # Mock parent repository
        with patch.object(session_service, 'db') as mock_db:
            mock_parent_repo = AsyncMock(spec=ParentProfileRepository)
            mock_parent_repo.get_parent_profile_by_user_id = AsyncMock(return_value=parent)
            
            with patch('backend.tutor.services.session_management_service.ParentProfileRepository', 
                      return_value=mock_parent_repo):
                
                session_service.child_repo.get_child_profile_by_id = AsyncMock(
                    side_effect=[child1, child2]
                )
                session_service.get_active_sessions_for_child = AsyncMock(
                    side_effect=[
                        [{"session_id": "session-1", "device_type": "web"}],  # Child 1 has 1 active session
                        []  # Child 2 has no active sessions
                    ]
                )
                session_service.time_tracking_repo.get_daily_usage = AsyncMock(
                    side_effect=[30, 15]  # Daily usage for each child
                )
                
                result = await session_service.get_parental_oversight_info("parent-123")
        
        assert result["parent_id"] == "parent-123"
        assert len(result["children_sessions"]) == 2
        assert result["total_active_sessions"] == 1
        
        # Check child 1 data
        child1_data = result["children_sessions"][0]
        assert child1_data["name"] == "Child One"
        assert len(child1_data["active_sessions"]) == 1
        assert child1_data["daily_usage_minutes"] == 30
        
        # Check child 2 data
        child2_data = result["children_sessions"][1]
        assert child2_data["name"] == "Child Two"
        assert len(child2_data["active_sessions"]) == 0
        assert child2_data["daily_usage_minutes"] == 15
    
    @pytest.mark.asyncio
    async def test_get_parental_oversight_info_parent_not_found(self, session_service):
        """Test oversight info when parent not found"""
        from ..repositories.user_repository import ParentProfileRepository
        
        with patch.object(session_service, 'db') as mock_db:
            mock_parent_repo = AsyncMock(spec=ParentProfileRepository)
            mock_parent_repo.get_parent_profile_by_user_id = AsyncMock(return_value=None)
            
            with patch('backend.tutor.services.session_management_service.ParentProfileRepository', 
                      return_value=mock_parent_repo):
                
                result = await session_service.get_parental_oversight_info("nonexistent-parent")
        
        assert "error" in result
        assert result["error"] == "Oversight info error"


class TestSessionCleanup:
    """Test session cleanup functionality"""
    
    @pytest.mark.asyncio
    async def test_cleanup_inactive_sessions(self, session_service):
        """Test cleanup of inactive sessions"""
        session_service.session_repo.cleanup_inactive_sessions = AsyncMock(return_value=5)
        
        result = await session_service.cleanup_inactive_sessions(24)
        
        assert result == 5
        session_service.session_repo.cleanup_inactive_sessions.assert_called_once_with(24)
    
    @pytest.mark.asyncio
    async def test_cleanup_inactive_sessions_error(self, session_service):
        """Test cleanup error handling"""
        session_service.session_repo.cleanup_inactive_sessions = AsyncMock(
            side_effect=Exception("Database error")
        )
        
        result = await session_service.cleanup_inactive_sessions(24)
        
        assert result == 0


class TestSessionEventLogging:
    """Test session event logging functionality"""
    
    @pytest.mark.asyncio
    async def test_log_session_event(self, session_service):
        """Test session event logging"""
        # This is a private method, so we test it indirectly through public methods
        session_service.safety_service.validate_session_safety = AsyncMock(
            return_value={"allowed": True, "reason": "Session validation passed"}
        )
        session_service.session_repo.get_active_sessions_by_user_id = AsyncMock(return_value=[])
        
        new_session = UserSession(
            session_id="session-123",
            user_id="child-123",
            device_id="device-456",
            device_type="web"
        )
        session_service.session_repo.create_session = AsyncMock(return_value=new_session)
        
        with patch.object(session_service, '_log_session_event') as mock_log:
            await session_service.start_session("child-123", "device-456", "web")
            
            mock_log.assert_called_once_with(
                "session-123",
                "session_started",
                {"parent_supervision": False}
            )


if __name__ == "__main__":
    pytest.main([__file__])
"""
Unit tests for safety service and parental controls
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta, date
from typing import Dict, Any

from ..services.safety_service import (
    SafetyService, ConsentType, SafetyViolationType,
    ParentalConsentRecord, SafetyViolationRecord
)
from ..models.user_models import ChildProfile, ChildProfileCreate, UserRole, Subject, LearningStyle
from services.supabase import DBConnection


@pytest.fixture
def mock_db():
    """Mock database connection"""
    return MagicMock(spec=DBConnection)


@pytest.fixture
def safety_service(mock_db):
    """Create safety service with mocked dependencies"""
    return SafetyService(mock_db)


@pytest.fixture
def sample_child_data():
    """Sample child profile creation data"""
    return ChildProfileCreate(
        parent_id="parent-123",
        name="Test Child",
        age=8,
        grade_level=3,
        learning_style=LearningStyle.VISUAL,
        preferred_subjects=[Subject.MATHEMATICS],
        learning_preferences={},
        safety_settings={}
    )


@pytest.fixture
def sample_child_profile():
    """Sample child profile"""
    return ChildProfile(
        child_id="child-123",
        parent_id="parent-123",
        name="Test Child",
        age=8,
        grade_level=3,
        learning_style=LearningStyle.VISUAL,
        preferred_subjects=[Subject.MATHEMATICS],
        safety_settings={
            "content_filtering_level": "strict",
            "parental_oversight_required": True,
            "session_time_limits": {
                "daily_limit_minutes": 30,
                "max_consecutive_minutes": 15
            },
            "quiet_hours": {"start": "19:00", "end": "08:00"}
        }
    )


class TestParentalConsentVerification:
    """Test parental consent verification functionality"""
    
    @pytest.mark.asyncio
    async def test_verify_parental_consent_success(self, safety_service, sample_child_profile):
        """Test successful parental consent verification"""
        # Mock repositories
        safety_service.child_repo.get_child_profile_by_id = AsyncMock(return_value=sample_child_profile)
        safety_service.consent_repo.get_consent_record = AsyncMock(return_value=None)
        safety_service.consent_repo.create_consent_record = AsyncMock()
        
        result = await safety_service.verify_parental_consent(
            "parent-123",
            "child-123",
            ConsentType.PROFILE_CREATION,
            "192.168.1.1",
            "Mozilla/5.0"
        )
        
        assert result is True
        safety_service.consent_repo.create_consent_record.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_parental_consent_invalid_relationship(self, safety_service):
        """Test consent verification with invalid parent-child relationship"""
        # Mock child with different parent
        child = ChildProfile(
            child_id="child-123",
            parent_id="different-parent",
            name="Test Child",
            age=8,
            grade_level=3
        )
        
        safety_service.child_repo.get_child_profile_by_id = AsyncMock(return_value=child)
        
        result = await safety_service.verify_parental_consent(
            "parent-123",
            "child-123",
            ConsentType.PROFILE_CREATION
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_verify_parental_consent_existing_valid(self, safety_service, sample_child_profile):
        """Test consent verification with existing valid consent"""
        existing_consent = ParentalConsentRecord(
            parent_id="parent-123",
            child_id="child-123",
            consent_type=ConsentType.PROFILE_CREATION,
            granted=True,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        
        safety_service.child_repo.get_child_profile_by_id = AsyncMock(return_value=sample_child_profile)
        safety_service.consent_repo.get_consent_record = AsyncMock(return_value=existing_consent)
        
        result = await safety_service.verify_parental_consent(
            "parent-123",
            "child-123",
            ConsentType.PROFILE_CREATION
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_verify_parental_consent_child_not_found(self, safety_service):
        """Test consent verification when child profile not found"""
        safety_service.child_repo.get_child_profile_by_id = AsyncMock(return_value=None)
        
        result = await safety_service.verify_parental_consent(
            "parent-123",
            "nonexistent-child",
            ConsentType.PROFILE_CREATION
        )
        
        assert result is False


class TestChildProfileCreationWithSafety:
    """Test child profile creation with safety settings"""
    
    @pytest.mark.asyncio
    async def test_create_child_profile_success(self, safety_service, sample_child_data):
        """Test successful child profile creation with safety settings"""
        created_profile = ChildProfile(
            child_id="child-123",
            parent_id="parent-123",
            name="Test Child",
            age=8,
            grade_level=3,
            safety_settings={
                "content_filtering_level": "strict",
                "parental_oversight_required": True
            }
        )
        
        # Mock successful consent verification
        safety_service.verify_parental_consent = AsyncMock(return_value=True)
        safety_service.child_repo.create_child_profile = AsyncMock(return_value=created_profile)
        safety_service.parent_repo.add_child_to_parent = AsyncMock()
        
        result = await safety_service.create_child_profile_with_safety(
            "parent-123",
            sample_child_data,
            ip_address="192.168.1.1"
        )
        
        assert result is not None
        assert result.child_id == "child-123"
        assert "content_filtering_level" in result.safety_settings
        
        # Verify consent was checked twice (profile creation and data collection)
        assert safety_service.verify_parental_consent.call_count == 2
    
    @pytest.mark.asyncio
    async def test_create_child_profile_no_consent(self, safety_service, sample_child_data):
        """Test child profile creation without parental consent"""
        safety_service.verify_parental_consent = AsyncMock(return_value=False)
        
        result = await safety_service.create_child_profile_with_safety(
            "parent-123",
            sample_child_data
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_create_child_profile_invalid_age(self, safety_service, sample_child_data):
        """Test child profile creation with invalid age"""
        sample_child_data.age = 15  # Too old for primary school
        
        safety_service.verify_parental_consent = AsyncMock(return_value=True)
        
        result = await safety_service.create_child_profile_with_safety(
            "parent-123",
            sample_child_data
        )
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_default_safety_settings_by_age(self, safety_service):
        """Test that default safety settings are appropriate for different ages"""
        # Test settings for young child (age 6)
        young_settings = safety_service._get_default_safety_settings(6)
        assert young_settings["content_filtering_level"] == "strict"
        assert young_settings["parental_oversight_required"] is True
        assert young_settings["session_time_limits"]["daily_limit_minutes"] == 30
        assert young_settings["voice_interaction_enabled"] is False
        
        # Test settings for middle child (age 9)
        middle_settings = safety_service._get_default_safety_settings(9)
        assert middle_settings["content_filtering_level"] == "moderate"
        assert middle_settings["session_time_limits"]["daily_limit_minutes"] == 45
        assert middle_settings["voice_interaction_enabled"] is True
        
        # Test settings for older child (age 12)
        older_settings = safety_service._get_default_safety_settings(12)
        assert older_settings["parental_oversight_required"] is False
        assert older_settings["session_time_limits"]["daily_limit_minutes"] == 60


class TestSessionSafetyValidation:
    """Test session safety validation functionality"""
    
    @pytest.mark.asyncio
    async def test_validate_session_safety_success(self, safety_service, sample_child_profile):
        """Test successful session safety validation"""
        safety_service.child_repo.get_child_profile_by_id = AsyncMock(return_value=sample_child_profile)
        safety_service.time_tracking_repo.get_daily_usage = AsyncMock(return_value=15)  # Under limit
        
        with patch('backend.tutor.services.safety_service.datetime') as mock_datetime:
            # Mock current time to be within allowed hours (10:00 AM)
            mock_datetime.now.return_value.time.return_value = datetime.strptime("10:00", "%H:%M").time()
            mock_datetime.now.return_value = datetime.now(timezone.utc)
            
            result = await safety_service.validate_session_safety(
                "child-123",
                "device-456",
                "web"
            )
        
        assert result["allowed"] is True
        assert result["reason"] == "Session validation passed"
    
    @pytest.mark.asyncio
    async def test_validate_session_safety_time_limit_exceeded(self, safety_service, sample_child_profile):
        """Test session validation when daily time limit is exceeded"""
        safety_service.child_repo.get_child_profile_by_id = AsyncMock(return_value=sample_child_profile)
        safety_service.time_tracking_repo.get_daily_usage = AsyncMock(return_value=35)  # Over 30 min limit
        
        result = await safety_service.validate_session_safety(
            "child-123",
            "device-456",
            "web"
        )
        
        assert result["allowed"] is False
        assert "time limit exceeded" in result["reason"].lower()
    
    @pytest.mark.asyncio
    async def test_validate_session_safety_quiet_hours(self, safety_service, sample_child_profile):
        """Test session validation during quiet hours"""
        safety_service.child_repo.get_child_profile_by_id = AsyncMock(return_value=sample_child_profile)
        safety_service.time_tracking_repo.get_daily_usage = AsyncMock(return_value=15)
        
        with patch('backend.tutor.services.safety_service.datetime') as mock_datetime:
            # Mock current time to be during quiet hours (20:30)
            mock_datetime.now.return_value.time.return_value = datetime.strptime("20:30", "%H:%M").time()
            mock_datetime.strptime = datetime.strptime
            
            result = await safety_service.validate_session_safety(
                "child-123",
                "device-456",
                "web"
            )
        
        assert result["allowed"] is False
        assert "quiet hours" in result["reason"].lower()
    
    @pytest.mark.asyncio
    async def test_validate_session_safety_child_not_found(self, safety_service):
        """Test session validation when child profile not found"""
        safety_service.child_repo.get_child_profile_by_id = AsyncMock(return_value=None)
        
        result = await safety_service.validate_session_safety(
            "nonexistent-child",
            "device-456",
            "web"
        )
        
        assert result["allowed"] is False
        assert result["reason"] == "Child profile not found"


class TestSessionActivityMonitoring:
    """Test session activity monitoring functionality"""
    
    @pytest.mark.asyncio
    async def test_monitor_session_activity_normal(self, safety_service, sample_child_profile):
        """Test monitoring session with normal activity"""
        from ..models.user_models import UserSession
        
        session = UserSession(
            session_id="session-123",
            user_id="child-123",
            device_id="device-456",
            device_type="web",
            started_at=datetime.now(timezone.utc) - timedelta(minutes=10)  # 10 minutes ago
        )
        
        safety_service.session_repo.get_session_by_id = AsyncMock(return_value=session)
        safety_service.child_repo.get_child_profile_by_id = AsyncMock(return_value=sample_child_profile)
        safety_service.violation_repo.create_violation_record = AsyncMock()
        
        result = await safety_service.monitor_session_activity(
            "session-123",
            {"content_flagged": False}
        )
        
        assert result["status"] == "monitored"
        assert result["violations_count"] == 0
    
    @pytest.mark.asyncio
    async def test_monitor_session_activity_excessive_time(self, safety_service, sample_child_profile):
        """Test monitoring session with excessive duration"""
        from ..models.user_models import UserSession
        
        session = UserSession(
            session_id="session-123",
            user_id="child-123",
            device_id="device-456",
            device_type="web",
            started_at=datetime.now(timezone.utc) - timedelta(minutes=35)  # 35 minutes ago (over 30 min limit)
        )
        
        safety_service.session_repo.get_session_by_id = AsyncMock(return_value=session)
        safety_service.child_repo.get_child_profile_by_id = AsyncMock(return_value=sample_child_profile)
        safety_service.violation_repo.create_violation_record = AsyncMock()
        safety_service._notify_parent_of_violation = AsyncMock()
        
        result = await safety_service.monitor_session_activity(
            "session-123",
            {"content_flagged": False}
        )
        
        assert result["status"] == "monitored"
        assert result["violations_count"] == 1
        safety_service.violation_repo.create_violation_record.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_monitor_session_activity_inappropriate_content(self, safety_service, sample_child_profile):
        """Test monitoring session with inappropriate content"""
        from ..models.user_models import UserSession
        
        session = UserSession(
            session_id="session-123",
            user_id="child-123",
            device_id="device-456",
            device_type="web",
            started_at=datetime.now(timezone.utc) - timedelta(minutes=10)
        )
        
        safety_service.session_repo.get_session_by_id = AsyncMock(return_value=session)
        safety_service.child_repo.get_child_profile_by_id = AsyncMock(return_value=sample_child_profile)
        safety_service.violation_repo.create_violation_record = AsyncMock()
        safety_service._notify_parent_of_violation = AsyncMock()
        
        result = await safety_service.monitor_session_activity(
            "session-123",
            {"content_flagged": True}
        )
        
        assert result["status"] == "monitored"
        assert result["violations_count"] == 1
        # Should notify parent for high severity violation
        safety_service._notify_parent_of_violation.assert_called_once()


class TestParentalOversightDashboard:
    """Test parental oversight dashboard functionality"""
    
    @pytest.mark.asyncio
    async def test_get_parental_oversight_dashboard_success(self, safety_service):
        """Test successful retrieval of parental oversight dashboard"""
        from ..models.user_models import ParentProfile
        
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
        
        safety_service.parent_repo.get_parent_profile_by_user_id = AsyncMock(return_value=parent)
        safety_service.child_repo.get_child_profile_by_id = AsyncMock(side_effect=[child1, child2])
        safety_service.session_repo.get_active_sessions_by_user_id = AsyncMock(return_value=[])
        safety_service.violation_repo.get_violations_for_child = AsyncMock(return_value=[])
        safety_service.time_tracking_repo.get_daily_usage = AsyncMock(return_value=25)
        
        result = await safety_service.get_parental_oversight_dashboard("parent-123")
        
        assert result["parent_id"] == "parent-123"
        assert len(result["children"]) == 2
        assert result["children"][0]["name"] == "Child One"
        assert result["children"][1]["name"] == "Child Two"
        assert result["children"][0]["daily_usage_minutes"] == 25
    
    @pytest.mark.asyncio
    async def test_get_parental_oversight_dashboard_parent_not_found(self, safety_service):
        """Test dashboard retrieval when parent profile not found"""
        safety_service.parent_repo.get_parent_profile_by_user_id = AsyncMock(return_value=None)
        
        result = await safety_service.get_parental_oversight_dashboard("nonexistent-parent")
        
        assert "error" in result
        assert result["error"] == "Parent profile not found"


class TestSafetyUtilityMethods:
    """Test utility methods in safety service"""
    
    def test_is_consent_valid_granted_not_expired(self, safety_service):
        """Test consent validity check for granted, non-expired consent"""
        consent = ParentalConsentRecord(
            parent_id="parent-123",
            child_id="child-123",
            consent_type=ConsentType.PROFILE_CREATION,
            granted=True,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30)
        )
        
        assert safety_service._is_consent_valid(consent) is True
    
    def test_is_consent_valid_not_granted(self, safety_service):
        """Test consent validity check for non-granted consent"""
        consent = ParentalConsentRecord(
            parent_id="parent-123",
            child_id="child-123",
            consent_type=ConsentType.PROFILE_CREATION,
            granted=False
        )
        
        assert safety_service._is_consent_valid(consent) is False
    
    def test_is_consent_valid_expired(self, safety_service):
        """Test consent validity check for expired consent"""
        consent = ParentalConsentRecord(
            parent_id="parent-123",
            child_id="child-123",
            consent_type=ConsentType.PROFILE_CREATION,
            granted=True,
            expires_at=datetime.now(timezone.utc) - timedelta(days=1)  # Expired yesterday
        )
        
        assert safety_service._is_consent_valid(consent) is False
    
    def test_check_device_restrictions_allowed(self, safety_service):
        """Test device restriction check for allowed device"""
        safety_settings = {"allowed_devices": ["web", "mobile"]}
        
        result = safety_service._check_device_restrictions("web", safety_settings)
        
        assert result["allowed"] is True
    
    def test_check_device_restrictions_not_allowed(self, safety_service):
        """Test device restriction check for disallowed device"""
        safety_settings = {"allowed_devices": ["web"]}
        
        result = safety_service._check_device_restrictions("mobile", safety_settings)
        
        assert result["allowed"] is False
        assert "not allowed" in result["reason"]
    
    def test_check_quiet_hours_overnight(self, safety_service):
        """Test quiet hours check for overnight quiet hours"""
        safety_settings = {"quiet_hours": {"start": "22:00", "end": "06:00"}}
        
        with patch('backend.tutor.services.safety_service.datetime') as mock_datetime:
            # Mock current time to be during quiet hours (23:30)
            mock_datetime.now.return_value.time.return_value = datetime.strptime("23:30", "%H:%M").time()
            mock_datetime.strptime = datetime.strptime
            
            result = safety_service._check_quiet_hours(safety_settings)
        
        assert result["allowed"] is False
        assert "quiet hours" in result["reason"]
    
    def test_check_quiet_hours_allowed_time(self, safety_service):
        """Test quiet hours check for allowed time"""
        safety_settings = {"quiet_hours": {"start": "22:00", "end": "06:00"}}
        
        with patch('backend.tutor.services.safety_service.datetime') as mock_datetime:
            # Mock current time to be outside quiet hours (14:00)
            mock_datetime.now.return_value.time.return_value = datetime.strptime("14:00", "%H:%M").time()
            mock_datetime.strptime = datetime.strptime
            
            result = safety_service._check_quiet_hours(safety_settings)
        
        assert result["allowed"] is True


if __name__ == "__main__":
    pytest.main([__file__])
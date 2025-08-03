"""
Simple unit tests for user models with safety settings
"""
import pytest
from datetime import datetime, timezone
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tutor.models.user_models import (
    User, UserRole, ChildProfile, ChildProfileCreate, ParentProfile,
    SafetySettings, UserSession, Subject, LearningStyle
)
from tutor.models.safety_models import ParentalConsentRecord, ConsentType


class TestUserModels:
    """Test user model validation and functionality"""
    
    def test_user_creation(self):
        """Test basic user creation"""
        user = User(
            email="test@example.com",
            role=UserRole.PARENT
        )
        
        assert user.email == "test@example.com"
        assert user.role == UserRole.PARENT
        assert user.user_id is not None
        assert isinstance(user.created_at, datetime)
    
    def test_user_email_validation(self):
        """Test user email validation"""
        # Valid email should work
        user = User(email="valid@example.com", role=UserRole.PARENT)
        assert user.email == "valid@example.com"
        
        # Invalid email should raise error
        with pytest.raises(ValueError, match="Invalid email format"):
            User(email="invalid-email", role=UserRole.PARENT)
    
    def test_child_profile_creation(self):
        """Test child profile creation with safety settings"""
        child = ChildProfile(
            parent_id="parent-123",
            name="Test Child",
            age=8,
            grade_level=3,
            learning_style=LearningStyle.VISUAL,
            preferred_subjects=[Subject.MATHEMATICS, Subject.ESL],
            safety_settings={
                "content_filtering_level": "strict",
                "parental_oversight_required": True,
                "session_time_limits": {
                    "daily_limit_minutes": 30,
                    "max_consecutive_minutes": 15
                }
            }
        )
        
        assert child.name == "Test Child"
        assert child.age == 8
        assert child.grade_level == 3
        assert child.learning_style == LearningStyle.VISUAL
        assert Subject.MATHEMATICS in child.preferred_subjects
        assert child.safety_settings["content_filtering_level"] == "strict"
    
    def test_child_profile_age_validation(self):
        """Test child profile age validation"""
        # Valid age should work
        child = ChildProfile(
            parent_id="parent-123",
            name="Valid Child",
            age=8,
            grade_level=3
        )
        assert child.age == 8
        
        # Age too young should raise error
        with pytest.raises(ValueError):
            ChildProfile(
                parent_id="parent-123",
                name="Too Young",
                age=3,  # Below minimum age of 5
                grade_level=1
            )
        
        # Age too old should raise error
        with pytest.raises(ValueError):
            ChildProfile(
                parent_id="parent-123",
                name="Too Old",
                age=15,  # Above maximum age of 12
                grade_level=6
            )
    
    def test_child_profile_name_validation(self):
        """Test child profile name validation"""
        # Valid name should work
        child = ChildProfile(
            parent_id="parent-123",
            name="Valid Name",
            age=8,
            grade_level=3
        )
        assert child.name == "Valid Name"
        
        # Empty name should raise error
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ChildProfile(
                parent_id="parent-123",
                name="",
                age=8,
                grade_level=3
            )
        
        # Whitespace-only name should be trimmed and then fail validation
        with pytest.raises(ValueError, match="Name cannot be empty"):
            ChildProfile(
                parent_id="parent-123",
                name="   ",
                age=8,
                grade_level=3
            )
    
    def test_parent_profile_creation(self):
        """Test parent profile creation"""
        parent = ParentProfile(
            user_id="user-123",
            children_ids=["child-1", "child-2"],
            preferred_language="en",
            notification_preferences={
                "email_notifications": True,
                "push_notifications": False
            },
            guidance_level="intermediate"
        )
        
        assert parent.user_id == "user-123"
        assert len(parent.children_ids) == 2
        assert parent.preferred_language == "en"
        assert parent.guidance_level == "intermediate"
    
    def test_parent_profile_guidance_level_validation(self):
        """Test parent profile guidance level validation"""
        # Valid guidance level should work
        parent = ParentProfile(
            user_id="user-123",
            guidance_level="advanced"
        )
        assert parent.guidance_level == "advanced"
        
        # Invalid guidance level should raise error
        with pytest.raises(ValueError, match="Invalid guidance level"):
            ParentProfile(
                user_id="user-123",
                guidance_level="invalid_level"
            )
    
    def test_safety_settings_model(self):
        """Test safety settings model"""
        safety = SafetySettings(
            child_id="child-123",
            parental_oversight_required=True,
            content_filtering_level="strict",
            session_time_limits={
                "daily_limit_minutes": 60,
                "weekly_limit_minutes": 300
            },
            allowed_subjects=[Subject.MATHEMATICS, Subject.ESL],
            blocked_topics=["advanced_calculus"],
            data_sharing_consent=False
        )
        
        assert safety.child_id == "child-123"
        assert safety.parental_oversight_required is True
        assert safety.content_filtering_level == "strict"
        assert safety.session_time_limits["daily_limit_minutes"] == 60
        assert Subject.MATHEMATICS in safety.allowed_subjects
        assert "advanced_calculus" in safety.blocked_topics
        assert safety.data_sharing_consent is False
    
    def test_safety_settings_content_filtering_validation(self):
        """Test safety settings content filtering level validation"""
        # Valid filtering level should work
        safety = SafetySettings(
            child_id="child-123",
            content_filtering_level="moderate"
        )
        assert safety.content_filtering_level == "moderate"
        
        # Invalid filtering level should raise error
        with pytest.raises(ValueError, match="Invalid content filtering level"):
            SafetySettings(
                child_id="child-123",
                content_filtering_level="invalid_level"
            )
    
    def test_user_session_creation(self):
        """Test user session creation"""
        session = UserSession(
            user_id="child-123",
            device_id="device-456",
            device_type="web",
            is_active=True,
            sync_status="synced"
        )
        
        assert session.user_id == "child-123"
        assert session.device_id == "device-456"
        assert session.device_type == "web"
        assert session.is_active is True
        assert session.sync_status == "synced"
        assert isinstance(session.started_at, datetime)
    
    def test_user_session_device_type_validation(self):
        """Test user session device type validation"""
        # Valid device type should work
        session = UserSession(
            user_id="child-123",
            device_id="device-456",
            device_type="mobile"
        )
        assert session.device_type == "mobile"
        
        # Invalid device type should raise error
        with pytest.raises(ValueError, match="Invalid device type"):
            UserSession(
                user_id="child-123",
                device_id="device-456",
                device_type="invalid_device"
            )
    
    def test_user_session_sync_status_validation(self):
        """Test user session sync status validation"""
        # Valid sync status should work
        session = UserSession(
            user_id="child-123",
            device_id="device-456",
            device_type="web",
            sync_status="pending"
        )
        assert session.sync_status == "pending"
        
        # Invalid sync status should raise error
        with pytest.raises(ValueError, match="Invalid sync status"):
            UserSession(
                user_id="child-123",
                device_id="device-456",
                device_type="web",
                sync_status="invalid_status"
            )


class TestSafetyModels:
    """Test safety-related models"""
    
    def test_parental_consent_record_creation(self):
        """Test parental consent record creation"""
        consent = ParentalConsentRecord(
            parent_id="parent-123",
            child_id="child-456",
            consent_type=ConsentType.PROFILE_CREATION,
            granted=True,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0"
        )
        
        assert consent.parent_id == "parent-123"
        assert consent.child_id == "child-456"
        assert consent.consent_type == ConsentType.PROFILE_CREATION
        assert consent.granted is True
        assert consent.ip_address == "192.168.1.1"
        assert isinstance(consent.granted_at, datetime)
    
    def test_consent_type_enum_values(self):
        """Test consent type enum has correct values"""
        assert ConsentType.PROFILE_CREATION == "profile_creation"
        assert ConsentType.DATA_COLLECTION == "data_collection"
        assert ConsentType.CONTENT_ACCESS == "content_access"
        assert ConsentType.VOICE_INTERACTION == "voice_interaction"
        assert ConsentType.PROGRESS_SHARING == "progress_sharing"


class TestChildProfileCreateDTO:
    """Test child profile creation DTO"""
    
    def test_child_profile_create_dto(self):
        """Test child profile creation DTO"""
        child_data = ChildProfileCreate(
            parent_id="parent-123",
            name="New Child",
            age=7,
            grade_level=2,
            learning_style=LearningStyle.AUDITORY,
            preferred_subjects=[Subject.ESL],
            safety_settings={
                "content_filtering_level": "strict"
            }
        )
        
        assert child_data.parent_id == "parent-123"
        assert child_data.name == "New Child"
        assert child_data.age == 7
        assert child_data.grade_level == 2
        assert child_data.learning_style == LearningStyle.AUDITORY
        assert Subject.ESL in child_data.preferred_subjects
        assert child_data.safety_settings["content_filtering_level"] == "strict"
    
    def test_child_profile_create_name_trimming(self):
        """Test that child profile creation trims whitespace from names"""
        child_data = ChildProfileCreate(
            parent_id="parent-123",
            name="  Trimmed Name  ",
            age=8,
            grade_level=3
        )
        
        assert child_data.name == "Trimmed Name"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
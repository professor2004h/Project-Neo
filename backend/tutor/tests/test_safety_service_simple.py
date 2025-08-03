"""
Simple unit tests for safety service functionality
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Mock the problematic imports
sys.modules['services.supabase'] = MagicMock()
sys.modules['utils.logger'] = MagicMock()

from tutor.services.safety_service import SafetyService
from tutor.models.safety_models import ConsentType, SafetyViolationType


class TestSafetyServiceBasic:
    """Basic tests for safety service functionality"""
    
    def test_consent_type_enum(self):
        """Test that consent type enum has expected values"""
        assert ConsentType.PROFILE_CREATION == "profile_creation"
        assert ConsentType.DATA_COLLECTION == "data_collection"
        assert ConsentType.CONTENT_ACCESS == "content_access"
        assert ConsentType.VOICE_INTERACTION == "voice_interaction"
        assert ConsentType.PROGRESS_SHARING == "progress_sharing"
    
    def test_safety_violation_type_enum(self):
        """Test that safety violation type enum has expected values"""
        assert SafetyViolationType.INAPPROPRIATE_CONTENT == "inappropriate_content"
        assert SafetyViolationType.EXCESSIVE_SESSION_TIME == "excessive_session_time"
        assert SafetyViolationType.UNAUTHORIZED_ACCESS == "unauthorized_access"
        assert SafetyViolationType.PRIVACY_BREACH == "privacy_breach"
    
    def test_default_safety_settings_young_child(self):
        """Test default safety settings for young children"""
        mock_db = MagicMock()
        service = SafetyService(mock_db)
        
        settings = service._get_default_safety_settings(6)
        
        assert settings["content_filtering_level"] == "strict"
        assert settings["parental_oversight_required"] is True
        assert settings["session_time_limits"]["daily_limit_minutes"] == 30
        assert settings["voice_interaction_enabled"] is False
        assert "mathematics" in settings["allowed_subjects"]
    
    def test_default_safety_settings_middle_child(self):
        """Test default safety settings for middle-age children"""
        mock_db = MagicMock()
        service = SafetyService(mock_db)
        
        settings = service._get_default_safety_settings(9)
        
        assert settings["content_filtering_level"] == "moderate"
        assert settings["parental_oversight_required"] is True
        assert settings["session_time_limits"]["daily_limit_minutes"] == 45
        assert settings["voice_interaction_enabled"] is True
        assert "mathematics" in settings["allowed_subjects"]
        assert "esl" in settings["allowed_subjects"]
    
    def test_default_safety_settings_older_child(self):
        """Test default safety settings for older children"""
        mock_db = MagicMock()
        service = SafetyService(mock_db)
        
        settings = service._get_default_safety_settings(12)
        
        assert settings["content_filtering_level"] == "moderate"
        assert settings["parental_oversight_required"] is False
        assert settings["session_time_limits"]["daily_limit_minutes"] == 60
        assert settings["voice_interaction_enabled"] is True
        assert "mathematics" in settings["allowed_subjects"]
        assert "esl" in settings["allowed_subjects"]
        assert "science" in settings["allowed_subjects"]
    
    def test_check_device_restrictions_allowed(self):
        """Test device restriction check for allowed device"""
        mock_db = MagicMock()
        service = SafetyService(mock_db)
        
        safety_settings = {"allowed_devices": ["web", "mobile"]}
        result = service._check_device_restrictions("web", safety_settings)
        
        assert result["allowed"] is True
    
    def test_check_device_restrictions_not_allowed(self):
        """Test device restriction check for disallowed device"""
        mock_db = MagicMock()
        service = SafetyService(mock_db)
        
        safety_settings = {"allowed_devices": ["web"]}
        result = service._check_device_restrictions("mobile", safety_settings)
        
        assert result["allowed"] is False
        assert "not allowed" in result["reason"]
    
    def test_check_device_restrictions_default_allowed(self):
        """Test device restriction check with default settings"""
        mock_db = MagicMock()
        service = SafetyService(mock_db)
        
        safety_settings = {}  # No restrictions specified
        result = service._check_device_restrictions("web", safety_settings)
        
        assert result["allowed"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
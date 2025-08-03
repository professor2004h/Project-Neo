"""
Safety and parental control models for the Cambridge AI Tutor
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from enum import Enum
import uuid


class ConsentType(str, Enum):
    """Types of parental consent"""
    PROFILE_CREATION = "profile_creation"
    DATA_COLLECTION = "data_collection"
    CONTENT_ACCESS = "content_access"
    VOICE_INTERACTION = "voice_interaction"
    PROGRESS_SHARING = "progress_sharing"


class SafetyViolationType(str, Enum):
    """Types of safety violations"""
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    EXCESSIVE_SESSION_TIME = "excessive_session_time"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PRIVACY_BREACH = "privacy_breach"


class ParentalConsentRecord(BaseModel):
    """Model for tracking parental consent"""
    consent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str
    child_id: str
    consent_type: ConsentType
    granted: bool
    granted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        from_attributes = True


class SafetyViolationRecord(BaseModel):
    """Model for tracking safety violations"""
    violation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    child_id: str
    violation_type: SafetyViolationType
    description: str
    severity: str = Field(default="medium")  # low, medium, high, critical
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    parent_notified: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('severity')
    @classmethod
    def validate_severity(cls, v):
        if v not in ['low', 'medium', 'high', 'critical']:
            raise ValueError('Invalid severity level')
        return v
    
    class Config:
        from_attributes = True


class SessionTimeLimit(BaseModel):
    """Model for session time limits"""
    daily_limit_minutes: int = 60  # Default 1 hour per day
    weekly_limit_minutes: int = 300  # Default 5 hours per week
    session_break_minutes: int = 15  # Required break after this many minutes
    max_consecutive_minutes: int = 30  # Maximum consecutive session time
    quiet_hours_start: str = "20:00"  # No sessions after this time
    quiet_hours_end: str = "07:00"  # No sessions before this time
    
    @field_validator('daily_limit_minutes', 'weekly_limit_minutes', 'session_break_minutes', 'max_consecutive_minutes')
    @classmethod
    def validate_positive_minutes(cls, v):
        if v <= 0:
            raise ValueError('Time limits must be positive')
        return v
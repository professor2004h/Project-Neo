"""
User-related data models for the Cambridge AI Tutor
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
from enum import Enum
import uuid


class UserRole(str, Enum):
    """User role enumeration"""
    PARENT = "parent"
    CHILD = "child"
    ADMIN = "admin"


class Subject(str, Enum):
    """Subject enumeration"""
    MATHEMATICS = "mathematics"
    ESL = "esl"
    SCIENCE = "science"


class LearningStyle(str, Enum):
    """Learning style enumeration"""
    VISUAL = "visual"
    AUDITORY = "auditory"
    KINESTHETIC = "kinesthetic"
    MIXED = "mixed"


class User(BaseModel):
    """Base user model matching tutor_user_profiles table"""
    user_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    role: UserRole
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if '@' not in v or len(v) > 255:
            raise ValueError('Invalid email format or too long')
        return v.lower()
    
    class Config:
        from_attributes = True


class ChildProfile(BaseModel):
    """Child profile model with learning preferences matching tutor_child_profiles table"""
    child_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=5, le=12)  # Primary school age range
    grade_level: int = Field(ge=1, le=6)  # Cambridge primary grades
    learning_style: LearningStyle = LearningStyle.MIXED
    preferred_subjects: List[Subject] = Field(default_factory=list)
    learning_preferences: Dict[str, Any] = Field(default_factory=dict)
    curriculum_progress: Dict[str, Any] = Field(default_factory=dict)
    safety_settings: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()
    
    @field_validator('preferred_subjects')
    @classmethod
    def validate_preferred_subjects(cls, v):
        if len(v) > 10:  # Reasonable limit
            raise ValueError('Too many preferred subjects')
        return v
    
    class Config:
        from_attributes = True


class ParentProfile(BaseModel):
    """Parent profile model matching tutor_parent_profiles table"""
    parent_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    children_ids: List[str] = Field(default_factory=list)
    preferred_language: str = Field(default="en", max_length=10)
    notification_preferences: Dict[str, bool] = Field(default_factory=dict)
    guidance_level: str = Field(default="intermediate", max_length=20)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @field_validator('guidance_level')
    @classmethod
    def validate_guidance_level(cls, v):
        if v not in ['beginner', 'intermediate', 'advanced']:
            raise ValueError('Invalid guidance level')
        return v
    
    @field_validator('children_ids')
    @classmethod
    def validate_children_ids(cls, v):
        if len(v) > 20:  # Reasonable limit for number of children
            raise ValueError('Too many children')
        return v
    
    class Config:
        from_attributes = True


class SafetySettings(BaseModel):
    """Child safety and parental control settings"""
    child_id: str
    parental_oversight_required: bool = True
    content_filtering_level: str = "strict"  # strict, moderate, minimal
    session_time_limits: Dict[str, int] = Field(default_factory=dict)  # daily, weekly limits in minutes
    allowed_subjects: List[Subject] = Field(default_factory=list)
    blocked_topics: List[str] = Field(default_factory=list)
    data_sharing_consent: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @field_validator('content_filtering_level')
    @classmethod
    def validate_content_filtering_level(cls, v):
        if v not in ['strict', 'moderate', 'minimal']:
            raise ValueError('Invalid content filtering level')
        return v
    
    @field_validator('session_time_limits')
    @classmethod
    def validate_session_time_limits(cls, v):
        for key, value in v.items():
            if not isinstance(value, int) or value < 0:
                raise ValueError('Session time limits must be non-negative integers')
        return v


class UserSession(BaseModel):
    """User session model for multi-device support matching tutor_user_sessions table"""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    device_id: str = Field(max_length=100)
    device_type: str = Field(max_length=20)  # web, mobile, extension
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_activity: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    sync_status: str = Field(default="synced", max_length=20)  # synced, pending, conflict
    
    @field_validator('device_type')
    @classmethod
    def validate_device_type(cls, v):
        if v not in ['web', 'mobile', 'extension']:
            raise ValueError('Invalid device type')
        return v
    
    @field_validator('sync_status')
    @classmethod
    def validate_sync_status(cls, v):
        if v not in ['synced', 'pending', 'conflict']:
            raise ValueError('Invalid sync status')
        return v
    
    class Config:
        from_attributes = True


# Create and Update DTOs for API operations
class UserCreate(BaseModel):
    """DTO for creating a new user"""
    email: str
    role: UserRole
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if '@' not in v or len(v) > 255:
            raise ValueError('Invalid email format or too long')
        return v.lower()


class UserUpdate(BaseModel):
    """DTO for updating a user"""
    email: Optional[str] = None
    role: Optional[UserRole] = None
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        if v is not None and ('@' not in v or len(v) > 255):
            raise ValueError('Invalid email format or too long')
        return v.lower() if v else v


class ChildProfileCreate(BaseModel):
    """DTO for creating a new child profile"""
    parent_id: str
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=5, le=12)
    grade_level: int = Field(ge=1, le=6)
    learning_style: LearningStyle = LearningStyle.MIXED
    preferred_subjects: List[Subject] = Field(default_factory=list)
    learning_preferences: Dict[str, Any] = Field(default_factory=dict)
    safety_settings: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip()


class ChildProfileUpdate(BaseModel):
    """DTO for updating a child profile"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=5, le=12)
    grade_level: Optional[int] = Field(None, ge=1, le=6)
    learning_style: Optional[LearningStyle] = None
    preferred_subjects: Optional[List[Subject]] = None
    learning_preferences: Optional[Dict[str, Any]] = None
    safety_settings: Optional[Dict[str, Any]] = None
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty')
        return v.strip() if v else v


class ParentProfileCreate(BaseModel):
    """DTO for creating a new parent profile"""
    user_id: str
    preferred_language: str = Field(default="en", max_length=10)
    notification_preferences: Dict[str, bool] = Field(default_factory=dict)
    guidance_level: str = Field(default="intermediate", max_length=20)
    
    @field_validator('guidance_level')
    @classmethod
    def validate_guidance_level(cls, v):
        if v not in ['beginner', 'intermediate', 'advanced']:
            raise ValueError('Invalid guidance level')
        return v


class ParentProfileUpdate(BaseModel):
    """DTO for updating a parent profile"""
    children_ids: Optional[List[str]] = None
    preferred_language: Optional[str] = Field(None, max_length=10)
    notification_preferences: Optional[Dict[str, bool]] = None
    guidance_level: Optional[str] = Field(None, max_length=20)
    
    @field_validator('guidance_level')
    @classmethod
    def validate_guidance_level(cls, v):
        if v is not None and v not in ['beginner', 'intermediate', 'advanced']:
            raise ValueError('Invalid guidance level')
        return v
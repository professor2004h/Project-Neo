"""
Curriculum-related data models for the Cambridge AI Tutor
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any
from datetime import datetime, timezone
from enum import Enum
import uuid

from .user_models import Subject


class DifficultyLevel(str, Enum):
    """Difficulty level enumeration"""
    BEGINNER = "beginner"
    ELEMENTARY = "elementary"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ActivityType(str, Enum):
    """Learning activity type enumeration"""
    LESSON = "lesson"
    PRACTICE = "practice"
    ASSESSMENT = "assessment"
    GAME = "game"
    EXPLANATION = "explanation"
    QUESTION = "question"


class CurriculumTopic(BaseModel):
    """Cambridge curriculum topic model"""
    topic_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    subject: Subject
    grade_level: int = Field(ge=1, le=6)
    cambridge_code: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    prerequisites: List[str] = Field(default_factory=list)  # List of topic_ids
    learning_objectives: List[str] = Field(default_factory=list)
    difficulty_level: DifficultyLevel = DifficultyLevel.ELEMENTARY
    estimated_duration_minutes: int = Field(ge=5, le=120, default=30)
    content_metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @field_validator('cambridge_code')
    @classmethod
    def validate_cambridge_code(cls, v):
        # Basic Cambridge code format validation
        if not v or len(v) < 3:
            raise ValueError('Cambridge code must be at least 3 characters')
        return v.upper()
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError('Title cannot be empty')
        return v.strip()


class LearningObjective(BaseModel):
    """Learning objective model"""
    objective_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic_id: str
    description: str = Field(min_length=1, max_length=500)
    cambridge_reference: Optional[str] = None
    assessment_criteria: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ContentItem(BaseModel):
    """Educational content item model"""
    content_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic_id: str
    title: str = Field(min_length=1, max_length=200)
    content_type: str  # text, video, image, interactive, game
    content_data: Dict[str, Any] = Field(default_factory=dict)
    difficulty_level: DifficultyLevel = DifficultyLevel.ELEMENTARY
    age_appropriateness: Dict[str, bool] = Field(default_factory=dict)  # age ranges
    curriculum_alignment: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class LearningActivity(BaseModel):
    """Learning activity model"""
    activity_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str  # child_id
    topic_id: str
    activity_type: ActivityType
    content: Dict[str, Any] = Field(default_factory=dict)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    performance_data: Dict[str, Any] = Field(default_factory=dict)
    is_completed: bool = False
    
    @field_validator('duration_minutes')
    @classmethod
    def validate_duration(cls, v):
        if v is not None and v < 0:
            raise ValueError('Duration cannot be negative')
        return v
    
    def mark_completed(self):
        """Mark the activity as completed"""
        self.completed_at = datetime.now(timezone.utc)
        self.is_completed = True
        if self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds() / 60
            self.duration_minutes = int(duration)


class Assessment(BaseModel):
    """Assessment model"""
    assessment_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    topic_id: str
    title: str = Field(min_length=1, max_length=200)
    questions: List[Dict[str, Any]] = Field(default_factory=list)
    total_points: int = Field(ge=1, default=100)
    passing_score: int = Field(ge=1, default=70)
    time_limit_minutes: Optional[int] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @field_validator('passing_score')
    @classmethod
    def validate_passing_score(cls, v):
        # Note: Cross-field validation would need model_validator in Pydantic v2
        # For now, just basic validation
        if v < 1:
            raise ValueError('Passing score must be at least 1')
        return v


class AssessmentResult(BaseModel):
    """Assessment result model"""
    result_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    assessment_id: str
    user_id: str  # child_id
    score: int = Field(ge=0)
    total_possible: int = Field(ge=1)
    percentage: float = Field(ge=0, le=100)
    passed: bool
    answers: List[Dict[str, Any]] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @field_validator('percentage')
    @classmethod
    def calculate_percentage(cls, v):
        # Note: This would need model_validator for cross-field calculation
        # For now, just validate the percentage value
        if v < 0 or v > 100:
            raise ValueError('Percentage must be between 0 and 100')
        return v
    
    @field_validator('passed')
    @classmethod
    def determine_passed(cls, v):
        # For now, just return the provided value
        # Cross-field validation would be handled in model_validator
        return v
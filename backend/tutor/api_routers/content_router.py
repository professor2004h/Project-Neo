"""
Content API Router - Curriculum content management and search
Task 10.1 implementation - Requirements: 3.1, 3.2, 3.3, 3.5
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import uuid
from datetime import datetime, timezone

from services.supabase import DBConnection
from utils.auth_utils import get_current_user_id_from_jwt
from utils.logger import logger
from ..services.content_service import ContentService
from ..services.cambridge_alignment_service import CambridgeAlignmentService
from ..models.curriculum_models import CurriculumTopic
from ..models.user_models import Subject

router = APIRouter(prefix="/content", tags=["Content Management"])

# Pydantic models for API requests/responses
class ContentSearchRequest(BaseModel):
    """Request model for content search"""
    query: str = Field(min_length=1, max_length=200, description="Search query")
    subject: Optional[Subject] = Field(None, description="Subject filter")
    grade_level: Optional[int] = Field(None, ge=1, le=12, description="Grade level filter")
    difficulty_level: Optional[int] = Field(None, ge=1, le=5, description="Difficulty filter")
    content_type: Optional[str] = Field(None, description="Content type filter")
    cambridge_code: Optional[str] = Field(None, description="Cambridge curriculum code filter")
    max_results: int = Field(default=20, ge=1, le=100, description="Maximum number of results")

class AdaptiveContentRequest(BaseModel):
    """Request model for adaptive content generation"""
    topic: str = Field(min_length=1, max_length=100, description="Learning topic")
    user_level: int = Field(ge=1, le=5, description="User's current level in this topic")
    learning_style: str = Field(default="visual", description="Preferred learning style")
    previous_performance: Optional[float] = Field(None, ge=0.0, le=1.0, description="Previous performance score")
    time_available_minutes: Optional[int] = Field(None, ge=5, le=120, description="Available time for content")

class LessonContentRequest(BaseModel):
    """Request model for lesson content"""
    lesson_id: str = Field(description="Lesson identifier")
    user_level: int = Field(ge=1, le=5, description="User's level for content adaptation")
    include_practice: bool = Field(default=True, description="Include practice exercises")
    include_assessments: bool = Field(default=False, description="Include assessment items")

class CurriculumValidationRequest(BaseModel):
    """Request model for curriculum alignment validation"""
    content_id: Optional[str] = Field(None, description="Existing content ID to validate")
    content_text: Optional[str] = Field(None, min_length=1, description="Content text to validate")
    subject: Subject = Field(description="Subject area")
    grade_level: int = Field(ge=1, le=12, description="Grade level")
    learning_objectives: List[str] = Field(description="Learning objectives to validate against")

class ContentItem(BaseModel):
    """Model for individual content items"""
    content_id: str = Field(description="Unique content identifier")
    title: str = Field(description="Content title")
    description: str = Field(description="Content description")
    subject: Subject = Field(description="Subject area")
    grade_level: int = Field(description="Grade level")
    difficulty_level: int = Field(description="Difficulty level (1-5)")
    content_type: str = Field(description="Type of content")
    cambridge_code: Optional[str] = Field(None, description="Cambridge curriculum code")
    learning_objectives: List[str] = Field(description="Learning objectives")
    prerequisites: List[str] = Field(default_factory=list, description="Required prior knowledge")
    content_url: Optional[str] = Field(None, description="URL to content resource")
    thumbnail_url: Optional[str] = Field(None, description="URL to content thumbnail")
    duration_minutes: Optional[int] = Field(None, description="Estimated duration")
    created_at: datetime = Field(description="Content creation date")
    updated_at: datetime = Field(description="Last update date")

class ContentSearchResponse(BaseModel):
    """Response model for content search"""
    query: str = Field(description="Original search query")
    total_results: int = Field(description="Total number of matching results")
    results: List[ContentItem] = Field(description="Search results")
    filters_applied: Dict[str, Any] = Field(description="Applied search filters")
    search_suggestions: List[str] = Field(default_factory=list, description="Search improvement suggestions")
    searched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class LessonContent(BaseModel):
    """Model for complete lesson content"""
    lesson_id: str = Field(description="Lesson identifier")
    title: str = Field(description="Lesson title")
    subject: Subject = Field(description="Subject area")
    grade_level: int = Field(description="Grade level")
    cambridge_code: Optional[str] = Field(None, description="Cambridge curriculum code")
    
    # Content sections
    introduction: str = Field(description="Lesson introduction")
    main_content: str = Field(description="Main lesson content")
    examples: List[Dict[str, Any]] = Field(description="Examples and demonstrations")
    practice_exercises: List[Dict[str, Any]] = Field(default_factory=list, description="Practice exercises")
    assessments: List[Dict[str, Any]] = Field(default_factory=list, description="Assessment items")
    
    # Metadata
    learning_objectives: List[str] = Field(description="Learning objectives")
    prerequisites: List[str] = Field(default_factory=list, description="Prerequisites")
    duration_minutes: int = Field(description="Estimated lesson duration")
    difficulty_level: int = Field(description="Difficulty level")
    
    # Adaptive features
    adaptations_applied: List[str] = Field(default_factory=list, description="Adaptations made for user")
    next_lessons: List[str] = Field(default_factory=list, description="Recommended next lessons")

class AdaptiveContent(BaseModel):
    """Model for adaptive content generation"""
    content_id: str = Field(description="Generated content identifier")
    topic: str = Field(description="Content topic")
    adapted_for_user: str = Field(description="User this content was adapted for")
    user_level: int = Field(description="User level this content targets")
    
    # Generated content
    explanation: str = Field(description="Adapted explanation")
    examples: List[str] = Field(description="Relevant examples")
    practice_activities: List[Dict[str, Any]] = Field(description="Practice activities")
    visual_aids: List[Dict[str, str]] = Field(default_factory=list, description="Visual aids and resources")
    
    # Adaptation metadata
    learning_style_adaptations: List[str] = Field(description="Learning style adaptations applied")
    difficulty_adjustments: List[str] = Field(description="Difficulty adjustments made")
    personalization_notes: str = Field(description="Notes about personalization")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in adaptation quality")
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class AlignmentReport(BaseModel):
    """Model for curriculum alignment validation results"""
    validation_id: str = Field(description="Unique validation identifier")
    content_id: Optional[str] = Field(None, description="Content ID if validating existing content")
    is_aligned: bool = Field(description="Whether content is properly aligned")
    alignment_score: float = Field(ge=0.0, le=1.0, description="Alignment score")
    
    # Alignment details
    matched_objectives: List[str] = Field(description="Learning objectives that match")
    missing_objectives: List[str] = Field(description="Required objectives not covered")
    extra_content: List[str] = Field(description="Content beyond required objectives")
    cambridge_codes: List[str] = Field(description="Applicable Cambridge curriculum codes")
    
    # Recommendations
    improvement_suggestions: List[str] = Field(description="Suggestions for better alignment")
    content_gaps: List[str] = Field(description="Identified content gaps")
    recommended_additions: List[str] = Field(description="Recommended content additions")
    
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Dependency to get initialized services
async def get_content_service() -> ContentService:
    """Get initialized content service"""
    from ..api import db
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return ContentService(db)

async def get_alignment_service() -> CambridgeAlignmentService:
    """Get initialized Cambridge alignment service"""
    from ..api import db
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return CambridgeAlignmentService(db)

# API Endpoints
@router.post("/search", response_model=ContentSearchResponse)
async def search_content(
    request: ContentSearchRequest,
    user_id: str = Depends(get_current_user_id_from_jwt),
    content_service: ContentService = Depends(get_content_service)
):
    """
    Search for educational content with filters
    Requirement 3.1: Ensure alignment with current Cambridge primary curriculum objectives
    """
    try:
        logger.info(f"Content search by user {user_id}: {request.query}")
        
        # Prepare search filters
        filters = {
            "subject": request.subject.value if request.subject else None,
            "grade_level": request.grade_level,
            "difficulty_level": request.difficulty_level,
            "content_type": request.content_type,
            "cambridge_code": request.cambridge_code
        }
        
        # Remove None values
        filters = {k: v for k, v in filters.items() if v is not None}
        
        # Perform search
        search_results = await content_service.search_content(
            query=request.query,
            filters=filters,
            max_results=request.max_results
        )
        
        # Convert results to API format
        content_items = []
        for result in search_results.get("results", []):
            item = ContentItem(
                content_id=result.get("content_id", str(uuid.uuid4())),
                title=result.get("title", ""),
                description=result.get("description", ""),
                subject=Subject(result.get("subject", "mathematics")),
                grade_level=result.get("grade_level", 1),
                difficulty_level=result.get("difficulty_level", 1),
                content_type=result.get("content_type", "lesson"),
                cambridge_code=result.get("cambridge_code"),
                learning_objectives=result.get("learning_objectives", []),
                prerequisites=result.get("prerequisites", []),
                content_url=result.get("content_url"),
                thumbnail_url=result.get("thumbnail_url"),
                duration_minutes=result.get("duration_minutes"),
                created_at=result.get("created_at", datetime.now(timezone.utc)),
                updated_at=result.get("updated_at", datetime.now(timezone.utc))
            )
            content_items.append(item)
        
        response = ContentSearchResponse(
            query=request.query,
            total_results=search_results.get("total_count", len(content_items)),
            results=content_items,
            filters_applied=filters,
            search_suggestions=search_results.get("suggestions", [])
        )
        
        logger.info(f"Content search completed for user {user_id}: {len(content_items)} results")
        return response
        
    except Exception as e:
        logger.error(f"Error searching content for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search content")

@router.post("/adaptive", response_model=AdaptiveContent)
async def generate_adaptive_content(
    request: AdaptiveContentRequest,
    user_id: str = Depends(get_current_user_id_from_jwt),
    content_service: ContentService = Depends(get_content_service)
):
    """
    Generate adaptive content based on user profile and learning history
    Requirement 3.2: Provide structured lessons following Cambridge progression frameworks
    """
    try:
        logger.info(f"Generating adaptive content for user {user_id}: {request.topic}")
        
        # Generate adaptive content
        content_data = await content_service.generate_adaptive_content(
            user_id=user_id,
            topic=request.topic,
            user_level=request.user_level,
            learning_style=request.learning_style,
            previous_performance=request.previous_performance,
            time_available=request.time_available_minutes
        )
        
        # Convert to API response
        adaptive_content = AdaptiveContent(
            content_id=content_data.get("content_id", str(uuid.uuid4())),
            topic=request.topic,
            adapted_for_user=user_id,
            user_level=request.user_level,
            explanation=content_data.get("explanation", ""),
            examples=content_data.get("examples", []),
            practice_activities=content_data.get("practice_activities", []),
            visual_aids=content_data.get("visual_aids", []),
            learning_style_adaptations=content_data.get("learning_style_adaptations", []),
            difficulty_adjustments=content_data.get("difficulty_adjustments", []),
            personalization_notes=content_data.get("personalization_notes", ""),
            confidence_score=content_data.get("confidence_score", 0.8)
        )
        
        logger.info(f"Adaptive content generated for user {user_id}")
        return adaptive_content
        
    except Exception as e:
        logger.error(f"Error generating adaptive content for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate adaptive content")

@router.get("/lessons/{lesson_id}", response_model=LessonContent)
async def get_lesson_content(
    lesson_id: str,
    user_level: int = Query(ge=1, le=5, description="User level for content adaptation"),
    include_practice: bool = Query(default=True, description="Include practice exercises"),
    include_assessments: bool = Query(default=False, description="Include assessment items"),
    user_id: str = Depends(get_current_user_id_from_jwt),
    content_service: ContentService = Depends(get_content_service)
):
    """
    Get detailed lesson content with user-level adaptation
    Requirement 3.3: Match the format and difficulty level of Cambridge assessments
    """
    try:
        logger.info(f"Getting lesson content {lesson_id} for user {user_id}")
        
        # Get lesson content
        lesson_data = await content_service.get_lesson_content(
            lesson_id=lesson_id,
            user_level=user_level,
            include_practice=include_practice,
            include_assessments=include_assessments
        )
        
        # Convert to API response
        lesson_content = LessonContent(
            lesson_id=lesson_id,
            title=lesson_data.get("title", ""),
            subject=Subject(lesson_data.get("subject", "mathematics")),
            grade_level=lesson_data.get("grade_level", 1),
            cambridge_code=lesson_data.get("cambridge_code"),
            introduction=lesson_data.get("introduction", ""),
            main_content=lesson_data.get("main_content", ""),
            examples=lesson_data.get("examples", []),
            practice_exercises=lesson_data.get("practice_exercises", []),
            assessments=lesson_data.get("assessments", []),
            learning_objectives=lesson_data.get("learning_objectives", []),
            prerequisites=lesson_data.get("prerequisites", []),
            duration_minutes=lesson_data.get("duration_minutes", 30),
            difficulty_level=lesson_data.get("difficulty_level", user_level),
            adaptations_applied=lesson_data.get("adaptations_applied", []),
            next_lessons=lesson_data.get("next_lessons", [])
        )
        
        logger.info(f"Lesson content retrieved for user {user_id}")
        return lesson_content
        
    except Exception as e:
        logger.error(f"Error getting lesson content for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get lesson content")

@router.post("/validate", response_model=AlignmentReport)
async def validate_curriculum_alignment(
    request: CurriculumValidationRequest,
    user_id: str = Depends(get_current_user_id_from_jwt),
    alignment_service: CambridgeAlignmentService = Depends(get_alignment_service)
):
    """
    Validate content alignment with Cambridge curriculum
    Requirement 3.5: Reference specific Cambridge curriculum codes
    """
    try:
        logger.info(f"Validating curriculum alignment for user {user_id}")
        
        # Perform validation
        validation_result = await alignment_service.validate_curriculum_alignment(
            content_id=request.content_id,
            content_text=request.content_text,
            subject=request.subject.value,
            grade_level=request.grade_level,
            learning_objectives=request.learning_objectives
        )
        
        # Convert to API response
        alignment_report = AlignmentReport(
            validation_id=validation_result.get("validation_id", str(uuid.uuid4())),
            content_id=request.content_id,
            is_aligned=validation_result.get("is_aligned", False),
            alignment_score=validation_result.get("alignment_score", 0.0),
            matched_objectives=validation_result.get("matched_objectives", []),
            missing_objectives=validation_result.get("missing_objectives", []),
            extra_content=validation_result.get("extra_content", []),
            cambridge_codes=validation_result.get("cambridge_codes", []),
            improvement_suggestions=validation_result.get("improvement_suggestions", []),
            content_gaps=validation_result.get("content_gaps", []),
            recommended_additions=validation_result.get("recommended_additions", [])
        )
        
        logger.info(f"Curriculum alignment validated for user {user_id}")
        return alignment_report
        
    except Exception as e:
        logger.error(f"Error validating curriculum alignment for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to validate curriculum alignment")

@router.get("/topics")
async def get_curriculum_topics(
    subject: Optional[Subject] = Query(None, description="Subject filter"),
    grade_level: Optional[int] = Query(None, ge=1, le=12, description="Grade level filter"),
    cambridge_code: Optional[str] = Query(None, description="Cambridge curriculum code filter"),
    user_id: str = Depends(get_current_user_id_from_jwt),
    content_service: ContentService = Depends(get_content_service)
):
    """
    Get available curriculum topics with optional filters
    """
    try:
        logger.info(f"Getting curriculum topics for user {user_id}")
        
        # Prepare filters
        filters = {}
        if subject:
            filters["subject"] = subject.value
        if grade_level:
            filters["grade_level"] = grade_level
        if cambridge_code:
            filters["cambridge_code"] = cambridge_code
        
        # Get topics
        topics_data = await content_service.get_curriculum_topics(filters)
        
        logger.info(f"Curriculum topics retrieved for user {user_id}")
        return {
            "topics": topics_data.get("topics", []),
            "total_count": topics_data.get("total_count", 0),
            "filters_applied": filters,
            "retrieved_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting curriculum topics for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get curriculum topics")

@router.get("/prerequisites/{topic_id}")
async def get_topic_prerequisites(
    topic_id: str,
    user_id: str = Depends(get_current_user_id_from_jwt),
    content_service: ContentService = Depends(get_content_service)
):
    """
    Get prerequisite topics for a specific topic
    """
    try:
        logger.info(f"Getting prerequisites for topic {topic_id} by user {user_id}")
        
        # Get prerequisites
        prerequisites_data = await content_service.get_topic_prerequisites(topic_id)
        
        logger.info(f"Prerequisites retrieved for topic {topic_id}")
        return {
            "topic_id": topic_id,
            "prerequisites": prerequisites_data.get("prerequisites", []),
            "prerequisite_paths": prerequisites_data.get("prerequisite_paths", []),
            "estimated_preparation_time": prerequisites_data.get("estimated_preparation_time"),
            "retrieved_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting prerequisites for topic {topic_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get topic prerequisites")

@router.get("/health")
async def content_health_check():
    """Health check endpoint for content management service"""
    return {
        "status": "ok",
        "service": "content_management",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "capabilities": [
            "content_search",
            "adaptive_content_generation",
            "lesson_content_delivery",
            "curriculum_alignment_validation",
            "topic_management"
        ]
    }
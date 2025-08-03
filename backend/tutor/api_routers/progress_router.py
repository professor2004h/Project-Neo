"""
Progress API Router - Learning progress tracking and analytics
Task 10.1 implementation - Requirements: 4.1, 4.2, 4.5
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, field_validator
import uuid
from datetime import datetime, timezone
from enum import Enum

from services.supabase import DBConnection
from utils.auth_utils import get_current_user_id_from_jwt
from utils.logger import logger
from ..services.progress_reporting_service import ProgressReportingService
from ..services.activity_tracking_service import ActivityTrackingService
from ..models.progress_models import ReportTimeframe, LearningInsight
from ..models.user_models import Subject

router = APIRouter(prefix="/progress", tags=["Progress Tracking"])

# Enums for API models
class ActivityType(str, Enum):
    QUESTION_ANSWERED = "question_answered"
    CONCEPT_LEARNED = "concept_learned"
    PRACTICE_COMPLETED = "practice_completed"
    ASSESSMENT_TAKEN = "assessment_taken"
    GAME_PLAYED = "game_played"

class InsightType(str, Enum):
    STRENGTH = "strength"
    IMPROVEMENT = "improvement"
    MILESTONE = "milestone"
    CONCERN = "concern"
    RECOMMENDATION = "recommendation"

# Pydantic models for API requests/responses
class ActivityTrackingRequest(BaseModel):
    """Request model for tracking learning activities"""
    activity_type: ActivityType = Field(description="Type of learning activity")
    subject: Subject = Field(description="Subject area")
    topic_id: Optional[str] = Field(None, description="Specific topic ID")
    performance_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Performance score (0-1)")
    time_spent_minutes: Optional[int] = Field(None, ge=0, description="Time spent in minutes")
    difficulty_level: Optional[int] = Field(None, ge=1, le=5, description="Difficulty level")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional activity metadata")

class ProgressReportRequest(BaseModel):
    """Request model for generating progress reports"""
    child_id: str = Field(description="Child's user ID")
    timeframe: ReportTimeframe = Field(description="Report timeframe")
    subjects: Optional[List[Subject]] = Field(None, description="Specific subjects to include")
    include_insights: bool = Field(default=True, description="Include AI-generated insights")
    start_date: Optional[datetime] = Field(None, description="Custom start date")
    end_date: Optional[datetime] = Field(None, description="Custom end date")

class PerformanceAnalysisRequest(BaseModel):
    """Request model for performance analysis"""
    subject: Subject = Field(description="Subject to analyze")
    timeframe_days: int = Field(default=30, ge=1, le=365, description="Analysis timeframe in days")
    analysis_type: str = Field(default="comprehensive", description="Type of analysis")

class ActivityResponse(BaseModel):
    """Response model for activity tracking"""
    activity_id: str = Field(description="Unique activity identifier")
    tracked_at: datetime = Field(description="When the activity was tracked")
    performance_impact: Optional[str] = Field(None, description="Impact on overall performance")
    recommendations: List[str] = Field(default_factory=list, description="Generated recommendations")

class ProgressReportResponse(BaseModel):
    """Response model for progress reports"""
    report_id: str = Field(description="Unique report identifier")
    child_id: str = Field(description="Child's user ID")
    child_name: str = Field(description="Child's name")
    child_age: int = Field(description="Child's age")
    child_grade: int = Field(description="Child's grade level")
    timeframe: ReportTimeframe = Field(description="Report timeframe")
    generated_at: datetime = Field(description="When the report was generated")
    
    # Summary metrics
    overall_progress_score: float = Field(ge=0.0, le=1.0, description="Overall progress score")
    total_activities_completed: int = Field(description="Total activities completed")
    learning_streak_days: int = Field(description="Current learning streak in days")
    subjects_practiced: List[Subject] = Field(description="Subjects practiced during timeframe")
    
    # Detailed progress data
    subject_progress: Dict[str, Any] = Field(description="Progress by subject")
    weekly_activity: List[Dict[str, Any]] = Field(description="Activity by week")
    achievements: List[Dict[str, Any]] = Field(description="Achievements earned")
    areas_for_focus: List[str] = Field(description="Areas needing attention")
    
    # AI-generated insights
    key_insights: List[LearningInsight] = Field(description="AI-generated learning insights")
    parent_summary: str = Field(description="Parent-friendly summary")
    next_steps: List[str] = Field(description="Recommended next steps")

class PerformanceAnalysisResponse(BaseModel):
    """Response model for performance analysis"""
    analysis_id: str = Field(description="Unique analysis identifier")
    subject: Subject = Field(description="Analyzed subject")
    timeframe_days: int = Field(description="Analysis timeframe")
    analyzed_at: datetime = Field(description="When analysis was performed")
    
    # Performance metrics
    average_score: float = Field(ge=0.0, le=1.0, description="Average performance score")
    improvement_trend: str = Field(description="Improvement trend (improving/stable/declining)")
    consistency_score: float = Field(ge=0.0, le=1.0, description="Consistency of performance")
    
    # Detailed analysis
    strengths: List[str] = Field(description="Identified strengths")
    weaknesses: List[str] = Field(description="Areas for improvement")
    learning_patterns: Dict[str, Any] = Field(description="Identified learning patterns")
    recommendations: List[str] = Field(description="Improvement recommendations")
    predicted_outcomes: Optional[Dict[str, Any]] = Field(None, description="Predicted learning outcomes")

class LearningInsightsResponse(BaseModel):
    """Response model for learning insights"""
    insights: List[LearningInsight] = Field(description="Generated learning insights")
    insight_count: int = Field(description="Total number of insights")
    generated_at: datetime = Field(description="When insights were generated")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Overall confidence in insights")

# Dependency to get initialized services
async def get_progress_service() -> ProgressReportingService:
    """Get initialized progress reporting service"""
    from ..api import db
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return ProgressReportingService(db)

async def get_activity_service() -> ActivityTrackingService:
    """Get initialized activity tracking service"""
    from ..api import db
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return ActivityTrackingService(db)

# API Endpoints
@router.post("/activity", response_model=ActivityResponse)
async def track_activity(
    request: ActivityTrackingRequest,
    user_id: str = Depends(get_current_user_id_from_jwt),
    activity_service: ActivityTrackingService = Depends(get_activity_service)
):
    """
    Track a learning activity
    Requirement 4.1: Track performance data and learning patterns
    """
    try:
        logger.info(f"Tracking activity for user {user_id}: {request.activity_type} in {request.subject}")
        
        # Create learning activity data
        activity_data = {
            "user_id": user_id,
            "activity_type": request.activity_type.value,
            "subject": request.subject,
            "topic_id": request.topic_id,
            "performance_score": request.performance_score,
            "time_spent_minutes": request.time_spent_minutes,
            "difficulty_level": request.difficulty_level,
            "metadata": request.metadata
        }
        
        # Track the activity
        tracking_result = await activity_service.track_learning_activity(activity_data)
        
        # Generate response
        response = ActivityResponse(
            activity_id=tracking_result.get("activity_id", str(uuid.uuid4())),
            tracked_at=datetime.now(timezone.utc),
            performance_impact=tracking_result.get("performance_impact"),
            recommendations=tracking_result.get("recommendations", [])
        )
        
        logger.info(f"Activity tracked successfully for user {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error tracking activity for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track learning activity")

@router.post("/reports", response_model=ProgressReportResponse)
async def generate_progress_report(
    request: ProgressReportRequest,
    user_id: str = Depends(get_current_user_id_from_jwt),
    progress_service: ProgressReportingService = Depends(get_progress_service)
):
    """
    Generate a comprehensive progress report
    Requirement 4.2: Generate visual reports showing strengths and improvement areas
    Requirement 4.5: Provide actionable insights for parents in plain language
    """
    try:
        logger.info(f"Generating progress report for child {request.child_id} by user {user_id}")
        
        # Generate the progress report
        report = await progress_service.generate_progress_report(
            user_id=request.child_id,
            timeframe=request.timeframe,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        # Generate parent insights if requested
        insights = []
        if request.include_insights:
            insights = await progress_service.generate_parent_insights(request.child_id, report)
        
        # Convert to API response
        response = ProgressReportResponse(
            report_id=report.report_id,
            child_id=report.child_id,
            child_name=report.child_name,
            child_age=report.child_age,
            child_grade=report.child_grade,
            timeframe=report.timeframe,
            generated_at=report.generated_at,
            overall_progress_score=report.overall_progress_score,
            total_activities_completed=report.total_activities_completed,
            learning_streak_days=report.learning_streak_days,
            subjects_practiced=report.subjects_practiced,
            subject_progress=report.subject_progress,
            weekly_activity=report.weekly_activity,
            achievements=report.achievements,
            areas_for_focus=report.areas_for_focus,
            key_insights=insights,
            parent_summary=report.parent_summary,
            next_steps=report.next_steps
        )
        
        logger.info(f"Progress report generated successfully for child {request.child_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error generating progress report for child {request.child_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate progress report")

@router.post("/analysis", response_model=PerformanceAnalysisResponse)
async def analyze_performance(
    request: PerformanceAnalysisRequest,
    user_id: str = Depends(get_current_user_id_from_jwt),
    progress_service: ProgressReportingService = Depends(get_progress_service)
):
    """
    Analyze performance for a specific subject
    Requirement 4.3: Automatically adjust content difficulty and suggest interventions
    """
    try:
        logger.info(f"Analyzing performance for user {user_id} in {request.subject}")
        
        # Perform performance analysis
        analysis_data = await progress_service.analyze_performance(
            user_id=user_id,
            subject=request.subject.value,
            timeframe_days=request.timeframe_days
        )
        
        # Convert to API response
        response = PerformanceAnalysisResponse(
            analysis_id=str(uuid.uuid4()),
            subject=request.subject,
            timeframe_days=request.timeframe_days,
            analyzed_at=datetime.now(timezone.utc),
            average_score=analysis_data.get("average_score", 0.0),
            improvement_trend=analysis_data.get("improvement_trend", "stable"),
            consistency_score=analysis_data.get("consistency_score", 0.0),
            strengths=analysis_data.get("strengths", []),
            weaknesses=analysis_data.get("weaknesses", []),
            learning_patterns=analysis_data.get("learning_patterns", {}),
            recommendations=analysis_data.get("recommendations", []),
            predicted_outcomes=analysis_data.get("predicted_outcomes")
        )
        
        logger.info(f"Performance analysis completed for user {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error analyzing performance for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze performance")

@router.get("/insights/{child_id}", response_model=LearningInsightsResponse)
async def get_learning_insights(
    child_id: str,
    timeframe_days: int = Query(default=30, ge=1, le=365, description="Timeframe for insights in days"),
    user_id: str = Depends(get_current_user_id_from_jwt),
    progress_service: ProgressReportingService = Depends(get_progress_service)
):
    """
    Get AI-generated learning insights for a child
    Requirement 4.5: Provide actionable insights for parents in plain language
    """
    try:
        logger.info(f"Generating learning insights for child {child_id} by user {user_id}")
        
        # Generate insights
        insights = await progress_service.generate_parent_insights(child_id)
        
        # Calculate overall confidence
        total_confidence = sum(insight.confidence_score for insight in insights)
        avg_confidence = total_confidence / len(insights) if insights else 0.0
        
        response = LearningInsightsResponse(
            insights=insights,
            insight_count=len(insights),
            generated_at=datetime.now(timezone.utc),
            confidence_score=avg_confidence
        )
        
        logger.info(f"Learning insights generated for child {child_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error generating learning insights for child {child_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate learning insights")

@router.get("/streaks/{child_id}")
async def get_learning_streaks(
    child_id: str,
    user_id: str = Depends(get_current_user_id_from_jwt),
    activity_service: ActivityTrackingService = Depends(get_activity_service)
):
    """
    Get learning streak information for a child
    """
    try:
        logger.info(f"Getting learning streaks for child {child_id} by user {user_id}")
        
        # Get streak data
        streak_data = await activity_service.calculate_learning_streak(child_id)
        
        logger.info(f"Learning streaks retrieved for child {child_id}")
        return {
            "child_id": child_id,
            "current_streak_days": streak_data.get("current_streak", 0),
            "longest_streak_days": streak_data.get("longest_streak", 0),
            "streak_by_subject": streak_data.get("subject_streaks", {}),
            "last_activity_date": streak_data.get("last_activity_date"),
            "retrieved_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting learning streaks for child {child_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get learning streaks")

@router.get("/summary/{child_id}")
async def get_progress_summary(
    child_id: str,
    days: int = Query(default=7, ge=1, le=90, description="Number of days for summary"),
    user_id: str = Depends(get_current_user_id_from_jwt),
    progress_service: ProgressReportingService = Depends(get_progress_service)
):
    """
    Get a quick progress summary for a child
    """
    try:
        logger.info(f"Getting progress summary for child {child_id} by user {user_id}")
        
        # Get summary data
        summary_data = await progress_service.get_progress_summary(child_id, days)
        
        logger.info(f"Progress summary retrieved for child {child_id}")
        return {
            "child_id": child_id,
            "timeframe_days": days,
            "summary": summary_data,
            "retrieved_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting progress summary for child {child_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get progress summary")

@router.get("/health")
async def progress_health_check():
    """Health check endpoint for progress tracking service"""
    return {
        "status": "ok",
        "service": "progress_tracking",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "capabilities": [
            "activity_tracking",
            "progress_reporting",
            "performance_analysis",
            "learning_insights",
            "streak_tracking"
        ]
    }
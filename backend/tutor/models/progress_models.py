"""
Progress tracking and learning activity data models for Cambridge AI Tutor
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any, Union
from datetime import datetime, timezone
from enum import Enum
import uuid

from .user_models import Subject
from .curriculum_models import ActivityType, DifficultyLevel


class ActivityStatus(str, Enum):
    """Learning activity status enumeration"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    PAUSED = "paused"


class SkillLevel(str, Enum):
    """Skill mastery level enumeration"""
    NOT_ATTEMPTED = "not_attempted"
    NOVICE = "novice"          # 0.0 - 0.3
    DEVELOPING = "developing"   # 0.3 - 0.5
    PROFICIENT = "proficient"  # 0.5 - 0.8
    MASTERED = "mastered"      # 0.8 - 1.0


class PerformanceMetrics(BaseModel):
    """Performance metrics for learning activities"""
    accuracy: float = Field(ge=0.0, le=1.0, default=0.0)
    speed_score: float = Field(ge=0.0, le=1.0, default=0.5)  # Based on completion time vs expected
    engagement_score: float = Field(ge=0.0, le=1.0, default=0.5)  # Based on interaction patterns
    help_requests: int = Field(ge=0, default=0)
    hints_used: int = Field(ge=0, default=0)
    attempts: int = Field(ge=1, default=1)
    time_spent_seconds: int = Field(ge=0, default=0)
    completion_rate: float = Field(ge=0.0, le=1.0, default=0.0)
    
    def overall_score(self) -> float:
        """Calculate overall performance score (weighted average)"""
        return (
            self.accuracy * 0.4 +
            self.speed_score * 0.2 +
            self.engagement_score * 0.2 +
            self.completion_rate * 0.2
        )


class LearningActivity(BaseModel):
    """Learning activity model with comprehensive performance tracking"""
    activity_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(min_length=1)
    topic_id: str = Field(min_length=1)
    activity_type: ActivityType
    status: ActivityStatus = ActivityStatus.NOT_STARTED
    
    # Content and metadata
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    content: Dict[str, Any] = Field(default_factory=dict)
    instructions: List[str] = Field(default_factory=list)
    expected_duration_minutes: int = Field(ge=1, le=180, default=15)
    difficulty_level: DifficultyLevel = DifficultyLevel.ELEMENTARY
    
    # Timing information
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    paused_at: Optional[datetime] = None
    last_interaction: Optional[datetime] = None
    actual_duration_minutes: Optional[int] = Field(ge=0, default=None)
    
    # Performance tracking
    performance_metrics: PerformanceMetrics = Field(default_factory=PerformanceMetrics)
    learning_objectives_met: List[str] = Field(default_factory=list)
    errors_made: List[Dict[str, Any]] = Field(default_factory=list)
    feedback_given: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Context and personalization
    learning_context: Dict[str, Any] = Field(default_factory=dict)
    personalization_applied: Dict[str, Any] = Field(default_factory=dict)
    curriculum_alignment: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @field_validator('user_id', 'topic_id')
    @classmethod
    def validate_ids(cls, v):
        """Validate UUID format for IDs"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')
    
    def start_activity(self) -> None:
        """Mark activity as started"""
        self.status = ActivityStatus.IN_PROGRESS
        self.started_at = datetime.now(timezone.utc)
        self.last_interaction = self.started_at
        self.updated_at = self.started_at
    
    def complete_activity(self) -> None:
        """Mark activity as completed and calculate duration"""
        self.status = ActivityStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc)
        self.updated_at = self.completed_at
        
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.actual_duration_minutes = int(duration.total_seconds() / 60)
        
        # Set completion rate to 1.0 for completed activities
        self.performance_metrics.completion_rate = 1.0
    
    def pause_activity(self) -> None:
        """Pause the activity"""
        self.status = ActivityStatus.PAUSED
        self.paused_at = datetime.now(timezone.utc)
        self.updated_at = self.paused_at
    
    def resume_activity(self) -> None:
        """Resume a paused activity"""
        if self.status == ActivityStatus.PAUSED:
            self.status = ActivityStatus.IN_PROGRESS
            self.paused_at = None
            self.last_interaction = datetime.now(timezone.utc)
            self.updated_at = self.last_interaction
    
    def update_interaction(self) -> None:
        """Update last interaction timestamp"""
        self.last_interaction = datetime.now(timezone.utc)
        self.updated_at = self.last_interaction
    
    def add_error(self, error_type: str, error_details: Dict[str, Any]) -> None:
        """Add an error/mistake to the activity record"""
        error_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": error_type,
            "details": error_details
        }
        self.errors_made.append(error_record)
        self.update_interaction()
    
    def add_feedback(self, feedback_type: str, feedback_content: str, effectiveness: float = None) -> None:
        """Add feedback given during the activity"""
        feedback_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": feedback_type,
            "content": feedback_content,
            "effectiveness": effectiveness
        }
        self.feedback_given.append(feedback_record)
        self.update_interaction()
    
    def calculate_skill_level(self) -> SkillLevel:
        """Calculate skill level based on performance metrics"""
        score = self.performance_metrics.overall_score()
        
        if score < 0.3:
            return SkillLevel.NOVICE
        elif score < 0.5:
            return SkillLevel.DEVELOPING
        elif score < 0.8:
            return SkillLevel.PROFICIENT
        else:
            return SkillLevel.MASTERED


class ProgressRecord(BaseModel):
    """Progress tracking record for skill development"""
    record_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(min_length=1)
    topic_id: str = Field(min_length=1)
    subject: Subject
    
    # Skill assessment
    skill_level: float = Field(ge=0.0, le=1.0, default=0.0)
    skill_level_category: SkillLevel = SkillLevel.NOT_ATTEMPTED
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.0)
    
    # Progress tracking
    activities_attempted: int = Field(ge=0, default=0)
    activities_completed: int = Field(ge=0, default=0)
    total_time_spent_minutes: int = Field(ge=0, default=0)
    last_practiced: Optional[datetime] = None
    
    # Performance indicators
    mastery_indicators: Dict[str, Any] = Field(default_factory=dict)
    improvement_areas: List[str] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    
    # Historical data
    performance_history: List[Dict[str, Any]] = Field(default_factory=list)
    learning_velocity: float = Field(ge=0.0, default=0.0)  # Rate of improvement
    consistency_score: float = Field(ge=0.0, le=1.0, default=0.0)  # How consistent performance is
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @field_validator('user_id', 'topic_id')
    @classmethod
    def validate_ids(cls, v):
        """Validate UUID format for IDs"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')
    
    def update_from_activity(self, activity: LearningActivity) -> None:
        """Update progress record based on completed learning activity"""
        if activity.status != ActivityStatus.COMPLETED:
            return
        
        # Update counts
        self.activities_attempted += 1
        self.activities_completed += 1
        
        # Update timing
        if activity.actual_duration_minutes:
            self.total_time_spent_minutes += activity.actual_duration_minutes
        self.last_practiced = activity.completed_at
        
        # Update skill level and confidence
        activity_score = activity.performance_metrics.overall_score()
        
        # Weighted average with previous skill level (70% new, 30% old)
        self.skill_level = (activity_score * 0.7) + (self.skill_level * 0.3)
        self.skill_level_category = self._calculate_skill_category()
        
        # Update confidence based on recent performance
        if activity.performance_metrics.accuracy >= 0.8:
            self.confidence_score = min(1.0, self.confidence_score + 0.1)
        elif activity.performance_metrics.accuracy < 0.5:
            self.confidence_score = max(0.0, self.confidence_score - 0.05)
        
        # Add to performance history
        performance_entry = {
            "timestamp": activity.completed_at.isoformat(),
            "activity_id": activity.activity_id,
            "activity_type": activity.activity_type,
            "score": activity_score,
            "accuracy": activity.performance_metrics.accuracy,
            "duration_minutes": activity.actual_duration_minutes
        }
        
        self.performance_history.append(performance_entry)
        
        # Keep only last 20 entries for performance
        if len(self.performance_history) > 20:
            self.performance_history = self.performance_history[-20:]
        
        # Recalculate derived metrics
        self._update_learning_velocity()
        self._update_consistency_score()
        self._update_mastery_indicators(activity)
        
        self.updated_at = datetime.now(timezone.utc)
    
    def _calculate_skill_category(self) -> SkillLevel:
        """Calculate skill level category from numerical score"""
        if self.skill_level == 0.0:
            return SkillLevel.NOT_ATTEMPTED
        elif self.skill_level < 0.3:
            return SkillLevel.NOVICE
        elif self.skill_level < 0.5:
            return SkillLevel.DEVELOPING
        elif self.skill_level < 0.8:
            return SkillLevel.PROFICIENT
        else:
            return SkillLevel.MASTERED
    
    def _update_learning_velocity(self) -> None:
        """Calculate rate of improvement over time"""
        if len(self.performance_history) < 3:
            self.learning_velocity = 0.0
            return
        
        recent_scores = [entry["score"] for entry in self.performance_history[-5:]]
        older_scores = [entry["score"] for entry in self.performance_history[-10:-5]] if len(self.performance_history) >= 10 else []
        
        if not older_scores:
            self.learning_velocity = 0.0
            return
        
        recent_avg = sum(recent_scores) / len(recent_scores)
        older_avg = sum(older_scores) / len(older_scores)
        
        # Velocity is the improvement rate (positive = improving)
        self.learning_velocity = recent_avg - older_avg
    
    def _update_consistency_score(self) -> None:
        """Calculate consistency of performance"""
        if len(self.performance_history) < 3:
            self.consistency_score = 0.0
            return
        
        recent_scores = [entry["score"] for entry in self.performance_history[-10:]]
        
        # Calculate coefficient of variation (lower = more consistent)
        if len(recent_scores) < 2:
            self.consistency_score = 0.0
            return
        
        mean_score = sum(recent_scores) / len(recent_scores)
        if mean_score == 0:
            self.consistency_score = 0.0
            return
        
        variance = sum((score - mean_score) ** 2 for score in recent_scores) / len(recent_scores)
        std_deviation = variance ** 0.5
        coefficient_of_variation = std_deviation / mean_score
        
        # Convert to consistency score (higher = more consistent)
        self.consistency_score = max(0.0, 1.0 - coefficient_of_variation)
    
    def _update_mastery_indicators(self, activity: LearningActivity) -> None:
        """Update mastery indicators based on activity performance"""
        # Track specific skills demonstrated
        for objective in activity.learning_objectives_met:
            if objective not in self.mastery_indicators:
                self.mastery_indicators[objective] = {"attempts": 0, "successes": 0, "last_attempt": None}
            
            self.mastery_indicators[objective]["attempts"] += 1
            if activity.performance_metrics.accuracy >= 0.7:
                self.mastery_indicators[objective]["successes"] += 1
            self.mastery_indicators[objective]["last_attempt"] = activity.completed_at.isoformat()
        
        # Update strengths and improvement areas
        if activity.performance_metrics.accuracy >= 0.8:
            activity_strength = f"{activity.activity_type.value}_performance"
            if activity_strength not in self.strengths:
                self.strengths.append(activity_strength)
        
        if activity.performance_metrics.accuracy < 0.5:
            improvement_area = f"{activity.activity_type.value}_accuracy"
            if improvement_area not in self.improvement_areas:
                self.improvement_areas.append(improvement_area)
    
    def get_progress_summary(self) -> Dict[str, Any]:
        """Get a summary of current progress"""
        completion_rate = (self.activities_completed / self.activities_attempted) if self.activities_attempted > 0 else 0.0
        
        return {
            "skill_level": self.skill_level,
            "skill_category": self.skill_level_category.value,
            "confidence_score": self.confidence_score,
            "activities_completed": self.activities_completed,
            "completion_rate": completion_rate,
            "total_time_spent": f"{self.total_time_spent_minutes} minutes",
            "learning_velocity": self.learning_velocity,
            "consistency_score": self.consistency_score,
            "strengths": self.strengths,
            "improvement_areas": self.improvement_areas,
            "last_practiced": self.last_practiced.isoformat() if self.last_practiced else None
        }


class ReportTimeframe(str, Enum):
    """Report timeframe enumeration"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class ProgressReportData(BaseModel):
    """Data structure for progress report visualization"""
    labels: List[str] = Field(default_factory=list)
    datasets: List[Dict[str, Any]] = Field(default_factory=list)
    chart_type: str = Field(default="line")  # line, bar, pie, radar
    title: str = Field(default="Progress Chart")
    
    def add_dataset(self, label: str, data: List[float], color: str = "#3B82F6") -> None:
        """Add a dataset to the chart"""
        dataset = {
            "label": label,
            "data": data,
            "backgroundColor": color,
            "borderColor": color,
            "fill": False
        }
        self.datasets.append(dataset)


class LearningInsight(BaseModel):
    """Individual learning insight for parents"""
    insight_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    insight_type: str  # "strength", "improvement", "milestone", "concern", "recommendation"
    priority: str = Field(default="medium")  # low, medium, high
    title: str
    description: str
    evidence: List[str] = Field(default_factory=list)  # Supporting evidence
    actionable_steps: List[str] = Field(default_factory=list)
    related_subjects: List[Subject] = Field(default_factory=list)
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.8)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProgressReport(BaseModel):
    """Comprehensive progress report for parents"""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(min_length=1)
    timeframe: ReportTimeframe
    start_date: datetime
    end_date: datetime
    
    # Summary metrics
    overall_progress_score: float = Field(ge=0.0, le=1.0, default=0.0)
    total_activities_completed: int = Field(ge=0, default=0)
    total_time_spent_minutes: int = Field(ge=0, default=0)
    learning_streak_days: int = Field(ge=0, default=0)
    subjects_practiced: List[Subject] = Field(default_factory=list)
    
    # Detailed progress by subject
    subject_progress: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    # Visual data for charts
    skill_level_chart: ProgressReportData = Field(default_factory=ProgressReportData)
    activity_distribution_chart: ProgressReportData = Field(default_factory=ProgressReportData)
    time_spent_chart: ProgressReportData = Field(default_factory=ProgressReportData)
    accuracy_trends_chart: ProgressReportData = Field(default_factory=ProgressReportData)
    
    # Key insights and recommendations
    key_insights: List[LearningInsight] = Field(default_factory=list)
    achievements: List[Dict[str, Any]] = Field(default_factory=list)
    areas_for_focus: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Parent-friendly summaries
    executive_summary: str = Field(default="")
    detailed_analysis: str = Field(default="")
    next_steps: List[str] = Field(default_factory=list)
    
    # Metadata
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    child_name: Optional[str] = None
    child_age: Optional[int] = None
    child_grade: Optional[int] = None
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        """Validate UUID format for user ID"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')
    
    def add_insight(self, insight: LearningInsight) -> None:
        """Add a learning insight to the report"""
        self.key_insights.append(insight)
        # Sort insights by priority (high, medium, low)
        priority_order = {"high": 0, "medium": 1, "low": 2}
        self.key_insights.sort(key=lambda x: priority_order.get(x.priority, 1))
    
    def add_achievement(self, title: str, description: str, evidence: List[str] = None) -> None:
        """Add an achievement to the report"""
        achievement = {
            "id": str(uuid.uuid4()),
            "title": title,
            "description": description,
            "evidence": evidence or [],
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        self.achievements.append(achievement)
    
    def add_focus_area(self, title: str, description: str, suggestions: List[str] = None) -> None:
        """Add an area for focus to the report"""
        focus_area = {
            "id": str(uuid.uuid4()),
            "title": title,
            "description": description,
            "suggestions": suggestions or [],
            "priority": "medium"
        }
        self.areas_for_focus.append(focus_area)
    
    def get_parent_summary(self) -> Dict[str, Any]:
        """Get a parent-friendly summary of the report"""
        # Calculate average daily time
        days_in_period = (self.end_date - self.start_date).days + 1
        avg_daily_time = self.total_time_spent_minutes / days_in_period if days_in_period > 0 else 0
        
        # Get top performing subject
        best_subject = None
        best_score = 0.0
        for subject, data in self.subject_progress.items():
            if data.get("average_score", 0) > best_score:
                best_score = data["average_score"]
                best_subject = subject
        
        # Count high priority insights
        high_priority_insights = len([i for i in self.key_insights if i.priority == "high"])
        
        return {
            "report_period": f"{self.start_date.strftime('%B %d')} - {self.end_date.strftime('%B %d, %Y')}",
            "overall_progress": {
                "score": round(self.overall_progress_score * 100, 1),
                "interpretation": self._interpret_progress_score(self.overall_progress_score)
            },
            "activity_summary": {
                "total_completed": self.total_activities_completed,
                "average_daily_time_minutes": round(avg_daily_time, 1),
                "learning_streak_days": self.learning_streak_days,
                "subjects_practiced": len(self.subjects_practiced)
            },
            "top_performing_subject": {
                "subject": best_subject,
                "score": round(best_score * 100, 1) if best_subject else 0
            },
            "key_highlights": {
                "achievements": len(self.achievements),
                "areas_for_focus": len(self.areas_for_focus),
                "high_priority_insights": high_priority_insights
            },
            "executive_summary": self.executive_summary,
            "next_steps_count": len(self.next_steps)
        }
    
    def _interpret_progress_score(self, score: float) -> str:
        """Interpret progress score for parents"""
        if score >= 0.9:
            return "Excellent progress! Your child is excelling."
        elif score >= 0.8:
            return "Very good progress with strong performance."
        elif score >= 0.7:
            return "Good progress with steady improvement."
        elif score >= 0.6:
            return "Satisfactory progress with some areas to focus on."
        elif score >= 0.5:
            return "Progress is being made, but additional support may help."
        else:
            return "Your child may benefit from extra support and encouragement."
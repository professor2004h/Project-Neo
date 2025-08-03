"""
Progress tracking repository for database operations
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta

from .base_repository import BaseRepository
from ..models.progress_models import (
    LearningActivity, 
    ProgressRecord, 
    ActivityStatus,
    SkillLevel,
    PerformanceMetrics
)
from ..models.user_models import Subject
from utils.logger import logger


class LearningActivityRepository(BaseRepository):
    """Repository for learning activity operations"""
    
    def __init__(self, db):
        super().__init__(db, "tutor_learning_activities")
    
    async def create_activity(self, activity: LearningActivity) -> LearningActivity:
        """Create a new learning activity"""
        try:
            data = {
                "activity_id": activity.activity_id,
                "user_id": activity.user_id,
                "topic_id": activity.topic_id,
                "activity_type": activity.activity_type.value,
                "content": activity.content,
                "started_at": activity.started_at.isoformat() if activity.started_at else None,
                "completed_at": activity.completed_at.isoformat() if activity.completed_at else None,
                "duration_minutes": activity.actual_duration_minutes,
                "performance_data": {
                    "title": activity.title,
                    "description": activity.description,
                    "status": activity.status.value,
                    "performance_metrics": activity.performance_metrics.dict(),
                    "learning_objectives_met": activity.learning_objectives_met,
                    "errors_made": activity.errors_made,
                    "feedback_given": activity.feedback_given,
                    "learning_context": activity.learning_context,
                    "personalization_applied": activity.personalization_applied,
                    "curriculum_alignment": activity.curriculum_alignment,
                    "expected_duration_minutes": activity.expected_duration_minutes,
                    "difficulty_level": activity.difficulty_level.value,
                    "instructions": activity.instructions
                },
                "is_completed": activity.status == ActivityStatus.COMPLETED
            }
            
            result = await self.create(data)
            return activity
            
        except Exception as e:
            logger.error(f"Error creating learning activity: {str(e)}")
            raise
    
    async def update_activity(self, activity: LearningActivity) -> LearningActivity:
        """Update an existing learning activity"""
        try:
            data = {
                "activity_type": activity.activity_type.value,
                "content": activity.content,
                "started_at": activity.started_at.isoformat() if activity.started_at else None,
                "completed_at": activity.completed_at.isoformat() if activity.completed_at else None,
                "duration_minutes": activity.actual_duration_minutes,
                "performance_data": {
                    "title": activity.title,
                    "description": activity.description,
                    "status": activity.status.value,
                    "performance_metrics": activity.performance_metrics.dict(),
                    "learning_objectives_met": activity.learning_objectives_met,
                    "errors_made": activity.errors_made,
                    "feedback_given": activity.feedback_given,
                    "learning_context": activity.learning_context,
                    "personalization_applied": activity.personalization_applied,
                    "curriculum_alignment": activity.curriculum_alignment,
                    "expected_duration_minutes": activity.expected_duration_minutes,
                    "difficulty_level": activity.difficulty_level.value,
                    "instructions": activity.instructions
                },
                "is_completed": activity.status == ActivityStatus.COMPLETED
            }
            
            await self.update(activity.activity_id, data, "activity_id")
            return activity
            
        except Exception as e:
            logger.error(f"Error updating learning activity: {str(e)}")
            raise
    
    async def get_activity_by_id(self, activity_id: str) -> Optional[LearningActivity]:
        """Get learning activity by ID"""
        try:
            result = await self.get_by_id(activity_id, "activity_id")
            if result:
                return self._convert_to_activity(result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting learning activity: {str(e)}")
            raise
    
    async def get_user_activities(self, user_id: str, 
                                 limit: int = 50, 
                                 status: ActivityStatus = None,
                                 activity_type: str = None,
                                 date_from: datetime = None,
                                 date_to: datetime = None) -> List[LearningActivity]:
        """Get learning activities for a user with optional filters"""
        try:
            client = await self.get_client()
            query = client.table(self.table_name).select("*").eq("user_id", user_id)
            
            if status:
                # Filter by status in performance_data
                query = query.contains("performance_data", {"status": status.value})
            
            if activity_type:
                query = query.eq("activity_type", activity_type)
            
            if date_from:
                query = query.gte("started_at", date_from.isoformat())
            
            if date_to:
                query = query.lte("started_at", date_to.isoformat())
            
            query = query.order("started_at", desc=True).limit(limit)
            result = await query.execute()
            
            activities = []
            for row in result.data:
                activity = self._convert_to_activity(row)
                if activity:
                    activities.append(activity)
            
            return activities
            
        except Exception as e:
            logger.error(f"Error getting user activities: {str(e)}")
            raise
    
    async def get_activities_by_topic(self, topic_id: str, limit: int = 50) -> List[LearningActivity]:
        """Get all activities for a specific topic"""
        try:
            client = await self.get_client()
            query = client.table(self.table_name).select("*").eq("topic_id", topic_id)
            query = query.order("started_at", desc=True).limit(limit)
            result = await query.execute()
            
            activities = []
            for row in result.data:
                activity = self._convert_to_activity(row)
                if activity:
                    activities.append(activity)
            
            return activities
            
        except Exception as e:
            logger.error(f"Error getting activities by topic: {str(e)}")
            raise
    
    async def get_recent_activities(self, user_id: str, days: int = 7) -> List[LearningActivity]:
        """Get recent activities for a user"""
        date_from = datetime.now(timezone.utc) - timedelta(days=days)
        return await self.get_user_activities(user_id, date_from=date_from)
    
    def _convert_to_activity(self, row: Dict[str, Any]) -> Optional[LearningActivity]:
        """Convert database row to LearningActivity model"""
        try:
            performance_data = row.get("performance_data", {})
            
            # Extract performance metrics
            metrics_data = performance_data.get("performance_metrics", {})
            performance_metrics = PerformanceMetrics(**metrics_data) if metrics_data else PerformanceMetrics()
            
            # Parse datetime fields
            started_at = None
            if row.get("started_at"):
                started_at = datetime.fromisoformat(row["started_at"].replace('Z', '+00:00'))
            
            completed_at = None
            if row.get("completed_at"):
                completed_at = datetime.fromisoformat(row["completed_at"].replace('Z', '+00:00'))
            
            activity = LearningActivity(
                activity_id=row["activity_id"],
                user_id=row["user_id"],
                topic_id=row["topic_id"],
                activity_type=row["activity_type"],
                title=performance_data.get("title", "Untitled Activity"),
                description=performance_data.get("description"),
                content=row.get("content", {}),
                status=ActivityStatus(performance_data.get("status", "not_started")),
                started_at=started_at,
                completed_at=completed_at,
                actual_duration_minutes=row.get("duration_minutes"),
                performance_metrics=performance_metrics,
                learning_objectives_met=performance_data.get("learning_objectives_met", []),
                errors_made=performance_data.get("errors_made", []),
                feedback_given=performance_data.get("feedback_given", []),
                learning_context=performance_data.get("learning_context", {}),
                personalization_applied=performance_data.get("personalization_applied", {}),
                curriculum_alignment=performance_data.get("curriculum_alignment", {}),
                expected_duration_minutes=performance_data.get("expected_duration_minutes", 15),
                difficulty_level=performance_data.get("difficulty_level", "elementary"),
                instructions=performance_data.get("instructions", [])
            )
            
            return activity
            
        except Exception as e:
            logger.warning(f"Error converting row to activity: {str(e)}")
            return None


class ProgressRecordRepository(BaseRepository):
    """Repository for progress record operations"""
    
    def __init__(self, db):
        super().__init__(db, "tutor_progress_records")
    
    async def create_or_update_progress(self, progress: ProgressRecord) -> ProgressRecord:
        """Create new progress record or update existing one"""
        try:
            # Check if record exists
            existing = await self.get_progress_record(progress.user_id, progress.topic_id)
            
            if existing:
                return await self.update_progress(progress)
            else:
                return await self.create_progress(progress)
                
        except Exception as e:
            logger.error(f"Error creating/updating progress: {str(e)}")
            raise
    
    async def create_progress(self, progress: ProgressRecord) -> ProgressRecord:
        """Create new progress record"""
        try:
            data = {
                "record_id": progress.record_id,
                "user_id": progress.user_id,
                "topic_id": progress.topic_id,
                "skill_level": progress.skill_level,
                "confidence_score": progress.confidence_score,
                "last_practiced": progress.last_practiced.isoformat() if progress.last_practiced else None,
                "mastery_indicators": {
                    "subject": progress.subject.value,
                    "skill_level_category": progress.skill_level_category.value,
                    "activities_attempted": progress.activities_attempted,
                    "activities_completed": progress.activities_completed,
                    "total_time_spent_minutes": progress.total_time_spent_minutes,
                    "performance_history": progress.performance_history,
                    "learning_velocity": progress.learning_velocity,
                    "consistency_score": progress.consistency_score,
                    "mastery_details": progress.mastery_indicators
                },
                "improvement_areas": progress.improvement_areas
            }
            
            result = await self.create(data)
            return progress
            
        except Exception as e:
            logger.error(f"Error creating progress record: {str(e)}")
            raise
    
    async def update_progress(self, progress: ProgressRecord) -> ProgressRecord:
        """Update existing progress record"""
        try:
            data = {
                "skill_level": progress.skill_level,
                "confidence_score": progress.confidence_score,
                "last_practiced": progress.last_practiced.isoformat() if progress.last_practiced else None,
                "mastery_indicators": {
                    "subject": progress.subject.value,
                    "skill_level_category": progress.skill_level_category.value,
                    "activities_attempted": progress.activities_attempted,
                    "activities_completed": progress.activities_completed,
                    "total_time_spent_minutes": progress.total_time_spent_minutes,
                    "performance_history": progress.performance_history,
                    "learning_velocity": progress.learning_velocity,
                    "consistency_score": progress.consistency_score,
                    "mastery_details": progress.mastery_indicators
                },
                "improvement_areas": progress.improvement_areas
            }
            
            client = await self.get_client()
            await client.table(self.table_name).update(data).eq("user_id", progress.user_id).eq("topic_id", progress.topic_id).execute()
            
            return progress
            
        except Exception as e:
            logger.error(f"Error updating progress record: {str(e)}")
            raise
    
    async def get_progress_record(self, user_id: str, topic_id: str) -> Optional[ProgressRecord]:
        """Get progress record for user and topic"""
        try:
            client = await self.get_client()
            result = await client.table(self.table_name).select("*").eq("user_id", user_id).eq("topic_id", topic_id).execute()
            
            if result.data:
                return self._convert_to_progress(result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting progress record: {str(e)}")
            raise
    
    async def get_user_progress(self, user_id: str, subject: Subject = None) -> List[ProgressRecord]:
        """Get all progress records for a user, optionally filtered by subject"""
        try:
            client = await self.get_client()
            query = client.table(self.table_name).select("*").eq("user_id", user_id)
            
            if subject:
                query = query.contains("mastery_indicators", {"subject": subject.value})
            
            result = await query.execute()
            
            progress_records = []
            for row in result.data:
                progress = self._convert_to_progress(row)
                if progress and (not subject or progress.subject == subject):
                    progress_records.append(progress)
            
            return progress_records
            
        except Exception as e:
            logger.error(f"Error getting user progress: {str(e)}")
            raise
    
    async def get_topic_progress_summary(self, topic_id: str) -> Dict[str, Any]:
        """Get progress summary for all users on a topic"""
        try:
            client = await self.get_client()
            result = await client.table(self.table_name).select("*").eq("topic_id", topic_id).execute()
            
            if not result.data:
                return {"total_users": 0, "average_skill_level": 0.0, "mastery_rate": 0.0}
            
            total_users = len(result.data)
            skill_levels = [row["skill_level"] for row in result.data if row["skill_level"]]
            average_skill = sum(skill_levels) / len(skill_levels) if skill_levels else 0.0
            
            # Count users who have mastered (skill_level >= 0.8)
            mastered_users = sum(1 for level in skill_levels if level >= 0.8)
            mastery_rate = mastered_users / total_users if total_users > 0 else 0.0
            
            return {
                "total_users": total_users,
                "average_skill_level": round(average_skill, 3),
                "mastery_rate": round(mastery_rate, 3),
                "skill_distribution": self._calculate_skill_distribution(skill_levels)
            }
            
        except Exception as e:
            logger.error(f"Error getting topic progress summary: {str(e)}")
            raise
    
    def _convert_to_progress(self, row: Dict[str, Any]) -> Optional[ProgressRecord]:
        """Convert database row to ProgressRecord model"""
        try:
            mastery_data = row.get("mastery_indicators", {})
            
            # Parse last_practiced
            last_practiced = None
            if row.get("last_practiced"):
                last_practiced = datetime.fromisoformat(row["last_practiced"].replace('Z', '+00:00'))
            
            progress = ProgressRecord(
                record_id=row["record_id"],
                user_id=row["user_id"],
                topic_id=row["topic_id"],
                subject=Subject(mastery_data.get("subject", "mathematics")),
                skill_level=row.get("skill_level", 0.0),
                skill_level_category=SkillLevel(mastery_data.get("skill_level_category", "not_attempted")),
                confidence_score=row.get("confidence_score", 0.0),
                activities_attempted=mastery_data.get("activities_attempted", 0),
                activities_completed=mastery_data.get("activities_completed", 0),
                total_time_spent_minutes=mastery_data.get("total_time_spent_minutes", 0),
                last_practiced=last_practiced,
                mastery_indicators=mastery_data.get("mastery_details", {}),
                improvement_areas=row.get("improvement_areas", []),
                strengths=[],  # Will be populated from mastery_indicators if needed
                performance_history=mastery_data.get("performance_history", []),
                learning_velocity=mastery_data.get("learning_velocity", 0.0),
                consistency_score=mastery_data.get("consistency_score", 0.0)
            )
            
            return progress
            
        except Exception as e:
            logger.warning(f"Error converting row to progress: {str(e)}")
            return None
    
    def _calculate_skill_distribution(self, skill_levels: List[float]) -> Dict[str, int]:
        """Calculate distribution of skill levels"""
        distribution = {
            "not_attempted": 0,
            "novice": 0,
            "developing": 0,
            "proficient": 0,
            "mastered": 0
        }
        
        for level in skill_levels:
            if level == 0.0:
                distribution["not_attempted"] += 1
            elif level < 0.3:
                distribution["novice"] += 1
            elif level < 0.5:
                distribution["developing"] += 1
            elif level < 0.8:
                distribution["proficient"] += 1
            else:
                distribution["mastered"] += 1
        
        return distribution
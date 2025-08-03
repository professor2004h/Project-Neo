"""
Activity Tracking Service - Handles learning activity logging and progress calculation
Task 5.1 implementation
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
import uuid

from utils.logger import logger
from services.supabase import DBConnection
from ..repositories.progress_repository import LearningActivityRepository, ProgressRecordRepository
from ..repositories.user_repository import ChildProfileRepository
from ..repositories.curriculum_repository import CurriculumTopicRepository
from ..models.progress_models import (
    LearningActivity,
    ProgressRecord,
    ActivityStatus,
    SkillLevel,
    PerformanceMetrics,
    ActivityType
)
from ..models.user_models import Subject
from ..models.curriculum_models import DifficultyLevel


class ActivityTrackingService:
    """
    Service for tracking learning activities and calculating progress metrics
    """
    
    def __init__(self, db: DBConnection):
        self.db = db
        self.activity_repo = LearningActivityRepository(db)
        self.progress_repo = ProgressRecordRepository(db)
        self.child_repo = ChildProfileRepository(db)
        self.curriculum_repo = CurriculumTopicRepository(db)
    
    async def create_activity(self, 
                            user_id: str,
                            topic_id: str,
                            activity_type: ActivityType,
                            title: str,
                            content: Dict[str, Any] = None,
                            expected_duration: int = 15,
                            difficulty_level: DifficultyLevel = DifficultyLevel.ELEMENTARY,
                            learning_context: Dict[str, Any] = None) -> LearningActivity:
        """
        Create a new learning activity
        
        Args:
            user_id: Child's user ID
            topic_id: Curriculum topic ID
            activity_type: Type of learning activity
            title: Activity title
            content: Activity content and materials
            expected_duration: Expected duration in minutes
            difficulty_level: Difficulty level
            learning_context: Additional context for the activity
            
        Returns:
            Created LearningActivity
        """
        try:
            activity = LearningActivity(
                user_id=user_id,
                topic_id=topic_id,
                activity_type=activity_type,
                title=title,
                content=content or {},
                expected_duration_minutes=expected_duration,
                difficulty_level=difficulty_level,
                learning_context=learning_context or {}
            )
            
            # Save to database
            await self.activity_repo.create_activity(activity)
            
            logger.info(f"Created activity {activity.activity_id} for user {user_id}")
            return activity
            
        except Exception as e:
            logger.error(f"Error creating activity: {str(e)}")
            raise
    
    async def start_activity(self, activity_id: str) -> LearningActivity:
        """
        Start a learning activity
        
        Args:
            activity_id: Activity ID to start
            
        Returns:
            Updated LearningActivity
        """
        try:
            activity = await self.activity_repo.get_activity_by_id(activity_id)
            if not activity:
                raise ValueError(f"Activity not found: {activity_id}")
            
            activity.start_activity()
            await self.activity_repo.update_activity(activity)
            
            logger.info(f"Started activity {activity_id}")
            return activity
            
        except Exception as e:
            logger.error(f"Error starting activity: {str(e)}")
            raise
    
    async def update_activity_performance(self,
                                        activity_id: str,
                                        performance_update: Dict[str, Any]) -> LearningActivity:
        """
        Update performance metrics for an ongoing activity
        
        Args:
            activity_id: Activity ID
            performance_update: Performance data to update
            
        Returns:
            Updated LearningActivity
        """
        try:
            activity = await self.activity_repo.get_activity_by_id(activity_id)
            if not activity:
                raise ValueError(f"Activity not found: {activity_id}")
            
            # Update performance metrics
            if "accuracy" in performance_update:
                activity.performance_metrics.accuracy = performance_update["accuracy"]
            
            if "speed_score" in performance_update:
                activity.performance_metrics.speed_score = performance_update["speed_score"]
            
            if "engagement_score" in performance_update:
                activity.performance_metrics.engagement_score = performance_update["engagement_score"]
            
            if "help_requests" in performance_update:
                activity.performance_metrics.help_requests = performance_update["help_requests"]
            
            if "hints_used" in performance_update:
                activity.performance_metrics.hints_used = performance_update["hints_used"]
            
            if "attempts" in performance_update:
                activity.performance_metrics.attempts = performance_update["attempts"]
            
            if "time_spent_seconds" in performance_update:
                activity.performance_metrics.time_spent_seconds = performance_update["time_spent_seconds"]
            
            if "completion_rate" in performance_update:
                activity.performance_metrics.completion_rate = performance_update["completion_rate"]
            
            # Update learning objectives met
            if "learning_objectives_met" in performance_update:
                activity.learning_objectives_met.extend(performance_update["learning_objectives_met"])
                # Remove duplicates
                activity.learning_objectives_met = list(set(activity.learning_objectives_met))
            
            activity.update_interaction()
            await self.activity_repo.update_activity(activity)
            
            logger.info(f"Updated performance for activity {activity_id}")
            return activity
            
        except Exception as e:
            logger.error(f"Error updating activity performance: {str(e)}")
            raise
    
    async def add_activity_error(self,
                               activity_id: str,
                               error_type: str,
                               error_details: Dict[str, Any]) -> LearningActivity:
        """
        Add an error/mistake to the activity record
        
        Args:
            activity_id: Activity ID
            error_type: Type of error (e.g., "incorrect_answer", "misconception")
            error_details: Details about the error
            
        Returns:
            Updated LearningActivity
        """
        try:
            activity = await self.activity_repo.get_activity_by_id(activity_id)
            if not activity:
                raise ValueError(f"Activity not found: {activity_id}")
            
            activity.add_error(error_type, error_details)
            await self.activity_repo.update_activity(activity)
            
            logger.info(f"Added error to activity {activity_id}: {error_type}")
            return activity
            
        except Exception as e:
            logger.error(f"Error adding activity error: {str(e)}")
            raise
    
    async def add_activity_feedback(self,
                                  activity_id: str,
                                  feedback_type: str,
                                  feedback_content: str,
                                  effectiveness: float = None) -> LearningActivity:
        """
        Add feedback given during the activity
        
        Args:
            activity_id: Activity ID
            feedback_type: Type of feedback (e.g., "hint", "encouragement", "correction")
            feedback_content: Feedback content
            effectiveness: Effectiveness score (0-1)
            
        Returns:
            Updated LearningActivity
        """
        try:
            activity = await self.activity_repo.get_activity_by_id(activity_id)
            if not activity:
                raise ValueError(f"Activity not found: {activity_id}")
            
            activity.add_feedback(feedback_type, feedback_content, effectiveness)
            await self.activity_repo.update_activity(activity)
            
            logger.info(f"Added feedback to activity {activity_id}: {feedback_type}")
            return activity
            
        except Exception as e:
            logger.error(f"Error adding activity feedback: {str(e)}")
            raise
    
    async def complete_activity(self, activity_id: str) -> Dict[str, Any]:
        """
        Complete a learning activity and update progress records
        
        Args:
            activity_id: Activity ID to complete
            
        Returns:
            Completion summary with progress updates
        """
        try:
            activity = await self.activity_repo.get_activity_by_id(activity_id)
            if not activity:
                raise ValueError(f"Activity not found: {activity_id}")
            
            # Mark activity as completed
            activity.complete_activity()
            await self.activity_repo.update_activity(activity)
            
            # Update progress record
            progress_update = await self.update_progress_from_activity(activity)
            
            # Calculate skill level assessment
            skill_assessment = await self.calculate_skill_level(activity.user_id, activity.topic_id)
            
            completion_summary = {
                "activity_id": activity_id,
                "completed_at": activity.completed_at.isoformat(),
                "duration_minutes": activity.actual_duration_minutes,
                "performance_score": activity.performance_metrics.overall_score(),
                "skill_level_before": progress_update.get("previous_skill_level", 0.0),
                "skill_level_after": skill_assessment["skill_level"],
                "skill_category": skill_assessment["skill_category"],
                "progress_made": skill_assessment["skill_level"] - progress_update.get("previous_skill_level", 0.0),
                "learning_objectives_met": activity.learning_objectives_met,
                "recommendations": await self.generate_activity_recommendations(activity)
            }
            
            logger.info(f"Completed activity {activity_id} with score {completion_summary['performance_score']:.2f}")
            return completion_summary
            
        except Exception as e:
            logger.error(f"Error completing activity: {str(e)}")
            raise
    
    async def update_progress_from_activity(self, activity: LearningActivity) -> Dict[str, Any]:
        """
        Update progress record based on completed activity
        
        Args:
            activity: Completed LearningActivity
            
        Returns:
            Dictionary with progress update details
        """
        try:
            if activity.status != ActivityStatus.COMPLETED:
                raise ValueError("Activity must be completed to update progress")
            
            # Get or create progress record
            existing_progress = await self.progress_repo.get_progress_record(
                activity.user_id, activity.topic_id
            )
            
            # Get topic information for subject
            topic_info = await self.curriculum_repo.get_by_id(activity.topic_id, "topic_id")
            subject = Subject(topic_info["subject"]) if topic_info else Subject.MATHEMATICS
            
            if existing_progress:
                previous_skill_level = existing_progress.skill_level
                existing_progress.update_from_activity(activity)
                await self.progress_repo.update_progress(existing_progress)
                progress_record = existing_progress
            else:
                # Create new progress record
                progress_record = ProgressRecord(
                    user_id=activity.user_id,
                    topic_id=activity.topic_id,
                    subject=subject
                )
                previous_skill_level = 0.0
                progress_record.update_from_activity(activity)
                await self.progress_repo.create_progress(progress_record)
            
            return {
                "previous_skill_level": previous_skill_level,
                "new_skill_level": progress_record.skill_level,
                "skill_category": progress_record.skill_level_category.value,
                "confidence_score": progress_record.confidence_score,
                "activities_completed": progress_record.activities_completed,
                "learning_velocity": progress_record.learning_velocity,
                "consistency_score": progress_record.consistency_score
            }
            
        except Exception as e:
            logger.error(f"Error updating progress from activity: {str(e)}")
            raise
    
    async def calculate_skill_level(self, user_id: str, topic_id: str) -> Dict[str, Any]:
        """
        Calculate current skill level for a user and topic
        
        Args:
            user_id: Child's user ID
            topic_id: Curriculum topic ID
            
        Returns:
            Dictionary with skill level assessment
        """
        try:
            progress_record = await self.progress_repo.get_progress_record(user_id, topic_id)
            
            if not progress_record:
                return {
                    "skill_level": 0.0,
                    "skill_category": SkillLevel.NOT_ATTEMPTED.value,
                    "confidence_score": 0.0,
                    "assessment_basis": "no_activities"
                }
            
            # Get recent activities for more detailed assessment
            recent_activities = await self.activity_repo.get_recent_activities(user_id, days=30)
            topic_activities = [a for a in recent_activities if a.topic_id == topic_id and a.status == ActivityStatus.COMPLETED]
            
            if not topic_activities:
                return {
                    "skill_level": progress_record.skill_level,
                    "skill_category": progress_record.skill_level_category.value,
                    "confidence_score": progress_record.confidence_score,
                    "assessment_basis": "progress_record_only"
                }
            
            # Calculate weighted skill level based on recent performance
            total_weight = 0
            weighted_score = 0
            
            for i, activity in enumerate(topic_activities[:10]):  # Last 10 activities
                # More recent activities have higher weight
                weight = 1.0 - (i * 0.1)  # Decreasing weight for older activities
                score = activity.performance_metrics.overall_score()
                
                weighted_score += score * weight
                total_weight += weight
            
            if total_weight > 0:
                current_skill_level = weighted_score / total_weight
            else:
                current_skill_level = progress_record.skill_level
            
            # Determine skill category
            if current_skill_level == 0.0:
                skill_category = SkillLevel.NOT_ATTEMPTED
            elif current_skill_level < 0.3:
                skill_category = SkillLevel.NOVICE
            elif current_skill_level < 0.5:
                skill_category = SkillLevel.DEVELOPING
            elif current_skill_level < 0.8:
                skill_category = SkillLevel.PROFICIENT
            else:
                skill_category = SkillLevel.MASTERED
            
            # Calculate confidence based on consistency
            confidence_score = progress_record.consistency_score * progress_record.confidence_score
            
            return {
                "skill_level": round(current_skill_level, 3),
                "skill_category": skill_category.value,
                "confidence_score": round(confidence_score, 3),
                "assessment_basis": "recent_activities",
                "activities_analyzed": len(topic_activities),
                "learning_velocity": progress_record.learning_velocity,
                "consistency_score": progress_record.consistency_score
            }
            
        except Exception as e:
            logger.error(f"Error calculating skill level: {str(e)}")
            raise
    
    async def generate_activity_recommendations(self, activity: LearningActivity) -> List[Dict[str, Any]]:
        """
        Generate recommendations based on activity performance
        
        Args:
            activity: Completed LearningActivity
            
        Returns:
            List of recommendations
        """
        try:
            recommendations = []
            performance_score = activity.performance_metrics.overall_score()
            
            # Performance-based recommendations
            if performance_score >= 0.9:
                recommendations.append({
                    "type": "advancement",
                    "priority": "high",
                    "message": "Excellent performance! Consider advancing to more challenging activities.",
                    "action": "increase_difficulty"
                })
            elif performance_score >= 0.7:
                recommendations.append({
                    "type": "reinforcement",
                    "priority": "medium",
                    "message": "Good progress! Practice similar activities to strengthen understanding.",
                    "action": "similar_practice"
                })
            elif performance_score >= 0.5:
                recommendations.append({
                    "type": "review",
                    "priority": "medium",
                    "message": "Some concepts need review. Consider revisiting prerequisite topics.",
                    "action": "review_prerequisites"
                })
            else:
                recommendations.append({
                    "type": "support",
                    "priority": "high",
                    "message": "Additional support needed. Break down concepts into smaller steps.",
                    "action": "simplify_content"
                })
            
            # Time-based recommendations
            if activity.actual_duration_minutes and activity.expected_duration_minutes:
                time_ratio = activity.actual_duration_minutes / activity.expected_duration_minutes
                
                if time_ratio > 2.0:
                    recommendations.append({
                        "type": "pacing",
                        "priority": "medium",
                        "message": "Consider shorter, more focused activities to maintain engagement.",
                        "action": "reduce_session_length"
                    })
                elif time_ratio < 0.5:
                    recommendations.append({
                        "type": "challenge",
                        "priority": "low",
                        "message": "Activity completed quickly. Consider more challenging content.",
                        "action": "increase_complexity"
                    })
            
            # Error pattern recommendations
            if len(activity.errors_made) > 3:
                error_types = [error.get("type") for error in activity.errors_made]
                common_errors = {error: error_types.count(error) for error in set(error_types)}
                most_common = max(common_errors.items(), key=lambda x: x[1]) if common_errors else None
                
                if most_common:
                    recommendations.append({
                        "type": "error_pattern",
                        "priority": "high",
                        "message": f"Pattern detected: {most_common[0]} errors. Targeted practice recommended.",
                        "action": "targeted_practice",
                        "focus_area": most_common[0]
                    })
            
            # Help-seeking recommendations
            if activity.performance_metrics.help_requests > 5:
                recommendations.append({
                    "type": "support_strategy",
                    "priority": "medium",
                    "message": "Frequent help requests indicate need for more scaffolding.",
                    "action": "increase_scaffolding"
                })
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return []
    
    async def get_activity_summary(self, user_id: str, timeframe_days: int = 7) -> Dict[str, Any]:
        """
        Get activity summary for a user over a timeframe
        
        Args:
            user_id: Child's user ID
            timeframe_days: Number of days to analyze
            
        Returns:
            Activity summary statistics
        """
        try:
            date_from = datetime.now(timezone.utc) - timedelta(days=timeframe_days)
            activities = await self.activity_repo.get_user_activities(
                user_id, 
                limit=100, 
                date_from=date_from
            )
            
            if not activities:
                return {
                    "total_activities": 0,
                    "completed_activities": 0,
                    "total_time_minutes": 0,
                    "average_score": 0.0,
                    "subjects_practiced": [],
                    "activity_types": {}
                }
            
            # Calculate summary statistics
            completed_activities = [a for a in activities if a.status == ActivityStatus.COMPLETED]
            total_time = sum(a.actual_duration_minutes or 0 for a in completed_activities)
            
            if completed_activities:
                scores = [a.performance_metrics.overall_score() for a in completed_activities]
                average_score = sum(scores) / len(scores)
            else:
                average_score = 0.0
            
            # Activity type distribution
            activity_types = {}
            for activity in activities:
                activity_type = activity.activity_type.value
                if activity_type not in activity_types:
                    activity_types[activity_type] = 0
                activity_types[activity_type] += 1
            
            # Get subjects practiced
            topic_ids = list(set(a.topic_id for a in activities))
            subjects_practiced = []
            
            for topic_id in topic_ids:
                try:
                    topic_info = await self.curriculum_repo.get_by_id(topic_id, "topic_id")
                    if topic_info and topic_info["subject"] not in subjects_practiced:
                        subjects_practiced.append(topic_info["subject"])
                except:
                    continue
            
            return {
                "timeframe_days": timeframe_days,
                "total_activities": len(activities),
                "completed_activities": len(completed_activities),
                "completion_rate": len(completed_activities) / len(activities) if activities else 0.0,
                "total_time_minutes": total_time,
                "average_session_minutes": total_time / len(completed_activities) if completed_activities else 0.0,
                "average_score": round(average_score, 3),
                "subjects_practiced": subjects_practiced,
                "activity_types": activity_types,
                "daily_activity_count": len(activities) / timeframe_days,
                "learning_streak_days": await self._calculate_learning_streak(user_id)
            }
            
        except Exception as e:
            logger.error(f"Error getting activity summary: {str(e)}")
            raise
    
    async def _calculate_learning_streak(self, user_id: str) -> int:
        """Calculate consecutive days of learning activity"""
        try:
            # Get activities from the last 30 days
            date_from = datetime.now(timezone.utc) - timedelta(days=30)
            activities = await self.activity_repo.get_user_activities(
                user_id,
                limit=200,
                status=ActivityStatus.COMPLETED,
                date_from=date_from
            )
            
            if not activities:
                return 0
            
            # Group activities by date
            activity_dates = set()
            for activity in activities:
                if activity.completed_at:
                    date = activity.completed_at.date()
                    activity_dates.add(date)
            
            # Calculate streak from today backwards
            current_date = datetime.now(timezone.utc).date()
            streak = 0
            
            while current_date in activity_dates:
                streak += 1
                current_date = current_date - timedelta(days=1)
            
            return streak
            
        except Exception as e:
            logger.warning(f"Error calculating learning streak: {str(e)}")
            return 0
"""
Progress Reporting Service - Generates comprehensive progress reports and parent insights
Task 5.2 implementation
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
import statistics
import json

from utils.logger import logger
from services.llm import make_llm_api_call
from services.supabase import DBConnection
from ..repositories.progress_repository import LearningActivityRepository, ProgressRecordRepository
from ..repositories.user_repository import ChildProfileRepository
from ..repositories.curriculum_repository import CurriculumTopicRepository
from ..models.progress_models import (
    ProgressReport,
    ReportTimeframe,
    ProgressReportData,
    LearningInsight,
    LearningActivity,
    ProgressRecord,
    ActivityStatus,
    SkillLevel
)
from ..models.user_models import Subject
from .activity_tracking_service import ActivityTrackingService


class ProgressReportingService:
    """
    Service for generating comprehensive progress reports and parent insights
    """
    
    def __init__(self, db: DBConnection):
        self.db = db
        self.activity_repo = LearningActivityRepository(db)
        self.progress_repo = ProgressRecordRepository(db)
        self.child_repo = ChildProfileRepository(db)
        self.curriculum_repo = CurriculumTopicRepository(db)
        self.activity_tracking = ActivityTrackingService(db)
        
        # Color schemes for charts
        self.chart_colors = {
            "primary": "#3B82F6",
            "success": "#10B981",
            "warning": "#F59E0B",
            "danger": "#EF4444",
            "info": "#6366F1",
            "secondary": "#6B7280"
        }
        
        # Subject colors for consistency
        self.subject_colors = {
            Subject.MATHEMATICS: "#3B82F6",
            Subject.ESL: "#10B981",
            Subject.SCIENCE: "#F59E0B"
        }
    
    async def generate_progress_report(self, 
                                     user_id: str,
                                     timeframe: ReportTimeframe,
                                     start_date: datetime = None,
                                     end_date: datetime = None) -> ProgressReport:
        """
        Generate a comprehensive progress report
        
        Args:
            user_id: Child's user ID
            timeframe: Report timeframe (daily, weekly, monthly, etc.)
            start_date: Optional custom start date
            end_date: Optional custom end date
            
        Returns:
            Comprehensive ProgressReport
        """
        try:
            # Calculate date range if not provided
            if not start_date or not end_date:
                start_date, end_date = self._calculate_date_range(timeframe)
            
            # Get child profile
            child_profile = await self.child_repo.get_by_id(user_id, "child_id")
            if not child_profile:
                raise ValueError(f"Child profile not found: {user_id}")
            
            # Initialize progress report
            report = ProgressReport(
                user_id=user_id,
                timeframe=timeframe,
                start_date=start_date,
                end_date=end_date,
                child_name=child_profile.get("name"),
                child_age=child_profile.get("age"),
                child_grade=child_profile.get("grade_level")
            )
            
            # Get activities and progress data
            activities = await self.activity_repo.get_user_activities(
                user_id,
                limit=200,
                date_from=start_date,
                date_to=end_date
            )
            
            completed_activities = [a for a in activities if a.status == ActivityStatus.COMPLETED]
            progress_records = await self.progress_repo.get_user_progress(user_id)
            
            # Calculate summary metrics
            await self._populate_summary_metrics(report, completed_activities, progress_records)
            
            # Generate visual charts
            await self._generate_visual_charts(report, completed_activities, progress_records)
            
            # Analyze subject-specific progress
            await self._analyze_subject_progress(report, completed_activities, progress_records)
            
            # Generate insights and recommendations
            await self._generate_learning_insights(report, completed_activities, progress_records, child_profile)
            
            # Create parent-friendly summaries
            await self._generate_parent_summaries(report, child_profile)
            
            logger.info(f"Generated {timeframe.value} progress report for user {user_id}")
            return report
            
        except Exception as e:
            logger.error(f"Error generating progress report: {str(e)}")
            raise
    
    async def identify_strengths_and_weaknesses(self, user_id: str, 
                                              timeframe_days: int = 30) -> Dict[str, Any]:
        """
        Identify learning strengths and areas for improvement
        
        Args:
            user_id: Child's user ID
            timeframe_days: Number of days to analyze
            
        Returns:
            Dictionary with strengths and weaknesses analysis
        """
        try:
            date_from = datetime.now(timezone.utc) - timedelta(days=timeframe_days)
            
            # Get recent activities and progress
            activities = await self.activity_repo.get_user_activities(
                user_id,
                limit=100,
                date_from=date_from
            )
            
            completed_activities = [a for a in activities if a.status == ActivityStatus.COMPLETED]
            progress_records = await self.progress_repo.get_user_progress(user_id)
            
            # Analyze performance by different dimensions
            strengths = []
            weaknesses = []
            
            # Subject-based analysis
            subject_performance = await self._analyze_subject_performance(completed_activities)
            
            for subject, data in subject_performance.items():
                if data["average_score"] >= 0.8:
                    strengths.append({
                        "type": "subject_mastery",
                        "category": subject,
                        "description": f"Strong performance in {subject}",
                        "score": data["average_score"],
                        "evidence": [
                            f"Average score: {data['average_score']:.1%}",
                            f"Activities completed: {data['activities_count']}",
                            f"Consistency: {data['consistency']:.1%}"
                        ]
                    })
                elif data["average_score"] < 0.6:
                    weaknesses.append({
                        "type": "subject_difficulty",
                        "category": subject,
                        "description": f"Needs support in {subject}",
                        "score": data["average_score"],
                        "suggestions": [
                            f"Focus on {subject} fundamentals",
                            "Break down complex concepts into smaller steps",
                            "Increase practice frequency"
                        ]
                    })
            
            # Activity type analysis
            activity_type_performance = await self._analyze_activity_type_performance(completed_activities)
            
            for activity_type, data in activity_type_performance.items():
                if data["average_score"] >= 0.85:
                    strengths.append({
                        "type": "learning_style",
                        "category": activity_type,
                        "description": f"Excels at {activity_type} activities",
                        "score": data["average_score"],
                        "evidence": [
                            f"Average score: {data['average_score']:.1%}",
                            f"Success rate: {data['success_rate']:.1%}"
                        ]
                    })
                elif data["average_score"] < 0.5:
                    weaknesses.append({
                        "type": "learning_approach",
                        "category": activity_type,
                        "description": f"Struggles with {activity_type} activities",
                        "score": data["average_score"],
                        "suggestions": [
                            f"Adapt {activity_type} activities to learning style",
                            "Provide additional scaffolding",
                            "Consider alternative approaches"
                        ]
                    })
            
            # Skill-based analysis
            skill_analysis = await self._analyze_skill_patterns(progress_records)
            
            # Time management analysis
            time_patterns = await self._analyze_time_patterns(completed_activities)
            
            if time_patterns["optimal_session_length"]:
                if time_patterns["average_session"] > time_patterns["optimal_session_length"] * 1.5:
                    weaknesses.append({
                        "type": "attention_span",
                        "category": "time_management",
                        "description": "Sessions may be too long for optimal focus",
                        "suggestions": [
                            "Break learning into shorter sessions",
                            "Include more breaks",
                            "Vary activity types"
                        ]
                    })
            
            # Engagement analysis
            engagement_analysis = await self._analyze_engagement_patterns(completed_activities)
            
            return {
                "analysis_period": f"{timeframe_days} days",
                "total_activities_analyzed": len(completed_activities),
                "strengths": {
                    "count": len(strengths),
                    "items": strengths[:5],  # Top 5 strengths
                    "summary": self._summarize_strengths(strengths)
                },
                "areas_for_improvement": {
                    "count": len(weaknesses),
                    "items": weaknesses[:5],  # Top 5 areas to improve
                    "summary": self._summarize_weaknesses(weaknesses)
                },
                "skill_patterns": skill_analysis,
                "time_patterns": time_patterns,
                "engagement_patterns": engagement_analysis,
                "recommendations": await self._generate_improvement_recommendations(strengths, weaknesses, time_patterns)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing strengths and weaknesses: {str(e)}")
            raise
    
    async def generate_parent_insights(self, user_id: str, 
                                     progress_report: ProgressReport = None) -> List[LearningInsight]:
        """
        Generate actionable insights for parents using AI analysis
        
        Args:
            user_id: Child's user ID
            progress_report: Optional existing progress report
            
        Returns:
            List of parent-friendly learning insights
        """
        try:
            # Generate progress report if not provided
            if not progress_report:
                progress_report = await self.generate_progress_report(user_id, ReportTimeframe.WEEKLY)
            
            # Get child profile for context
            child_profile = await self.child_repo.get_by_id(user_id, "child_id")
            
            # Prepare data for AI analysis
            analysis_data = {
                "child_age": progress_report.child_age,
                "child_grade": progress_report.child_grade,
                "overall_progress_score": progress_report.overall_progress_score,
                "total_activities": progress_report.total_activities_completed,
                "learning_streak": progress_report.learning_streak_days,
                "subjects_practiced": [s.value for s in progress_report.subjects_practiced],
                "subject_progress": progress_report.subject_progress,
                "achievements": len(progress_report.achievements),
                "focus_areas": len(progress_report.areas_for_focus)
            }
            
            # Build AI prompt for insight generation
            system_prompt = f"""You are an expert educational consultant generating insights for parents about their {progress_report.child_age}-year-old child's learning progress.

Create actionable insights that help parents understand their child's learning journey and know how to support them at home.

CHILD PROFILE:
- Age: {progress_report.child_age} years
- Grade: {progress_report.child_grade}
- Learning period: {progress_report.timeframe.value} report

PROGRESS DATA:
{json.dumps(analysis_data, indent=2)}

INSIGHT REQUIREMENTS:
1. Use encouraging, supportive language
2. Focus on specific, actionable steps parents can take
3. Explain what the data means in plain language
4. Provide concrete examples of home support activities
5. Celebrate achievements while addressing areas for growth

RESPONSE FORMAT (JSON):
{{
    "insights": [
        {{
            "insight_type": "strength|improvement|milestone|concern|recommendation",
            "priority": "high|medium|low",
            "title": "Clear, engaging title for parents",
            "description": "Detailed explanation in parent-friendly language",
            "evidence": ["Specific data points supporting this insight"],
            "actionable_steps": ["Specific things parents can do at home"],
            "confidence_score": 0.9
        }}
    ]
}}

Generate 3-5 insights covering the most important aspects of the child's learning."""

            user_message = f"Please analyze this child's learning data and generate actionable insights for parents."
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Make AI API call
            response = await make_llm_api_call(
                messages=messages,
                model_name="gpt-4",
                temperature=0.4,
                max_tokens=1200,
                response_format={"type": "json_object"}
            )
            
            # Parse AI response
            llm_content = response.choices[0].message.content
            try:
                ai_insights = json.loads(llm_content)
            except json.JSONDecodeError:
                logger.warning("Failed to parse AI insights, using fallback")
                ai_insights = {"insights": []}
            
            # Convert to LearningInsight objects
            insights = []
            for insight_data in ai_insights.get("insights", []):
                try:
                    insight = LearningInsight(
                        insight_type=insight_data.get("insight_type", "recommendation"),
                        priority=insight_data.get("priority", "medium"),
                        title=insight_data.get("title", "Learning Insight"),
                        description=insight_data.get("description", ""),
                        evidence=insight_data.get("evidence", []),
                        actionable_steps=insight_data.get("actionable_steps", []),
                        related_subjects=[],  # Will be populated based on context
                        confidence_score=insight_data.get("confidence_score", 0.8)
                    )
                    insights.append(insight)
                except Exception as e:
                    logger.warning(f"Error creating insight: {str(e)}")
                    continue
            
            # Add fallback insights if AI didn't generate enough
            if len(insights) < 3:
                insights.extend(await self._generate_fallback_insights(progress_report))
            
            logger.info(f"Generated {len(insights)} parent insights for user {user_id}")
            return insights[:5]  # Return top 5 insights
            
        except Exception as e:
            logger.error(f"Error generating parent insights: {str(e)}")
            # Return fallback insights
            return await self._generate_fallback_insights(progress_report or ProgressReport(user_id=user_id, timeframe=ReportTimeframe.WEEKLY, start_date=datetime.now(timezone.utc), end_date=datetime.now(timezone.utc)))
    
    def _calculate_date_range(self, timeframe: ReportTimeframe) -> Tuple[datetime, datetime]:
        """Calculate start and end dates for the given timeframe"""
        now = datetime.now(timezone.utc)
        
        if timeframe == ReportTimeframe.DAILY:
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif timeframe == ReportTimeframe.WEEKLY:
            days_since_monday = now.weekday()
            start_date = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif timeframe == ReportTimeframe.MONTHLY:
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        elif timeframe == ReportTimeframe.QUARTERLY:
            quarter_start_month = ((now.month - 1) // 3) * 3 + 1
            start_date = now.replace(month=quarter_start_month, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        else:  # YEARLY
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = now
        
        return start_date, end_date
    
    async def _populate_summary_metrics(self, report: ProgressReport, 
                                       activities: List[LearningActivity],
                                       progress_records: List[ProgressRecord]) -> None:
        """Populate summary metrics in the report"""
        # Basic activity metrics
        report.total_activities_completed = len(activities)
        report.total_time_spent_minutes = sum(a.actual_duration_minutes or 0 for a in activities)
        
        # Calculate overall progress score
        if progress_records:
            scores = [p.skill_level for p in progress_records if p.skill_level > 0]
            report.overall_progress_score = statistics.mean(scores) if scores else 0.0
        
        # Get learning streak
        report.learning_streak_days = await self.activity_tracking._calculate_learning_streak(report.user_id)
        
        # Identify subjects practiced
        topic_ids = list(set(a.topic_id for a in activities))
        subjects_practiced = set()
        
        for topic_id in topic_ids:
            try:
                topic_info = await self.curriculum_repo.get_by_id(topic_id, "topic_id")
                if topic_info:
                    subjects_practiced.add(Subject(topic_info["subject"]))
            except:
                continue
        
        report.subjects_practiced = list(subjects_practiced)
    
    async def _generate_visual_charts(self, report: ProgressReport,
                                    activities: List[LearningActivity],
                                    progress_records: List[ProgressRecord]) -> None:
        """Generate visual chart data for the report"""
        # Skill level progression chart
        if progress_records:
            subjects = list(set(p.subject for p in progress_records))
            report.skill_level_chart.title = "Skill Level by Subject"
            report.skill_level_chart.chart_type = "radar"
            report.skill_level_chart.labels = [s.value.title() for s in subjects]
            
            skill_data = []
            for subject in subjects:
                subject_records = [p for p in progress_records if p.subject == subject]
                avg_skill = statistics.mean([p.skill_level for p in subject_records]) if subject_records else 0
                skill_data.append(avg_skill)
            
            report.skill_level_chart.add_dataset(
                "Skill Level",
                skill_data,
                self.chart_colors["primary"]
            )
        
        # Activity distribution chart
        if activities:
            activity_types = {}
            for activity in activities:
                activity_type = activity.activity_type.value
                activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
            
            report.activity_distribution_chart.title = "Activities by Type"
            report.activity_distribution_chart.chart_type = "pie"
            report.activity_distribution_chart.labels = list(activity_types.keys())
            report.activity_distribution_chart.add_dataset(
                "Activities",
                list(activity_types.values()),
                [self.chart_colors["primary"], self.chart_colors["success"], 
                 self.chart_colors["warning"], self.chart_colors["info"]][:len(activity_types)]
            )
        
        # Time spent chart (daily breakdown)
        await self._generate_time_spent_chart(report, activities)
        
        # Accuracy trends chart
        await self._generate_accuracy_trends_chart(report, activities)
    
    async def _generate_time_spent_chart(self, report: ProgressReport, activities: List[LearningActivity]) -> None:
        """Generate time spent chart with daily breakdown"""
        if not activities:
            return
        
        # Group activities by date
        daily_time = {}
        for activity in activities:
            if activity.completed_at and activity.actual_duration_minutes:
                date_key = activity.completed_at.strftime("%Y-%m-%d")
                daily_time[date_key] = daily_time.get(date_key, 0) + activity.actual_duration_minutes
        
        # Sort dates and prepare chart data
        sorted_dates = sorted(daily_time.keys())
        
        report.time_spent_chart.title = "Daily Learning Time"
        report.time_spent_chart.chart_type = "bar"
        report.time_spent_chart.labels = [datetime.strptime(d, "%Y-%m-%d").strftime("%m/%d") for d in sorted_dates]
        report.time_spent_chart.add_dataset(
            "Minutes",
            [daily_time[date] for date in sorted_dates],
            self.chart_colors["success"]
        )
    
    async def _generate_accuracy_trends_chart(self, report: ProgressReport, activities: List[LearningActivity]) -> None:
        """Generate accuracy trends chart"""
        if not activities:
            return
        
        # Group by date and calculate daily average accuracy
        daily_accuracy = {}
        for activity in activities:
            if activity.completed_at:
                date_key = activity.completed_at.strftime("%Y-%m-%d")
                if date_key not in daily_accuracy:
                    daily_accuracy[date_key] = []
                daily_accuracy[date_key].append(activity.performance_metrics.accuracy)
        
        # Calculate averages
        daily_avg_accuracy = {}
        for date, accuracies in daily_accuracy.items():
            daily_avg_accuracy[date] = statistics.mean(accuracies)
        
        sorted_dates = sorted(daily_avg_accuracy.keys())
        
        report.accuracy_trends_chart.title = "Accuracy Trends"
        report.accuracy_trends_chart.chart_type = "line"
        report.accuracy_trends_chart.labels = [datetime.strptime(d, "%Y-%m-%d").strftime("%m/%d") for d in sorted_dates]
        report.accuracy_trends_chart.add_dataset(
            "Accuracy",
            [daily_avg_accuracy[date] for date in sorted_dates],
            self.chart_colors["primary"]
        )
    
    async def _analyze_subject_progress(self, report: ProgressReport,
                                      activities: List[LearningActivity],
                                      progress_records: List[ProgressRecord]) -> None:
        """Analyze progress by subject"""
        for subject in report.subjects_practiced:
            subject_activities = []
            subject_progress = []
            
            # Get subject-specific data
            for activity in activities:
                try:
                    topic_info = await self.curriculum_repo.get_by_id(activity.topic_id, "topic_id")
                    if topic_info and Subject(topic_info["subject"]) == subject:
                        subject_activities.append(activity)
                except:
                    continue
            
            subject_progress = [p for p in progress_records if p.subject == subject]
            
            if subject_activities or subject_progress:
                # Calculate subject metrics
                total_activities = len(subject_activities)
                avg_score = statistics.mean([a.performance_metrics.overall_score() for a in subject_activities]) if subject_activities else 0
                avg_skill_level = statistics.mean([p.skill_level for p in subject_progress]) if subject_progress else 0
                total_time = sum(a.actual_duration_minutes or 0 for a in subject_activities)
                
                report.subject_progress[subject.value] = {
                    "total_activities": total_activities,
                    "average_score": avg_score,
                    "average_skill_level": avg_skill_level,
                    "total_time_minutes": total_time,
                    "progress_records_count": len(subject_progress)
                }
    
    async def _generate_learning_insights(self, report: ProgressReport,
                                        activities: List[LearningActivity],
                                        progress_records: List[ProgressRecord],
                                        child_profile: Dict[str, Any]) -> None:
        """Generate AI-powered learning insights"""
        insights = await self.generate_parent_insights(report.user_id, report)
        
        for insight in insights:
            report.add_insight(insight)
        
        # Add achievements and focus areas based on data analysis
        await self._identify_achievements(report, activities, progress_records)
        await self._identify_focus_areas(report, activities, progress_records)
    
    async def _generate_parent_summaries(self, report: ProgressReport, child_profile: Dict[str, Any]) -> None:
        """Generate parent-friendly summaries using AI"""
        try:
            # Build context for AI summary generation
            summary_data = {
                "child_name": report.child_name,
                "child_age": report.child_age,
                "timeframe": report.timeframe.value,
                "total_activities": report.total_activities_completed,
                "overall_score": report.overall_progress_score,
                "learning_streak": report.learning_streak_days,
                "subjects": [s.value for s in report.subjects_practiced],
                "achievements_count": len(report.achievements),
                "insights_count": len(report.key_insights)
            }
            
            system_prompt = f"""You are an educational consultant writing a progress summary for parents. Write in a warm, encouraging tone that celebrates progress while providing actionable guidance.

CHILD: {report.child_name}, age {report.child_age}
PERIOD: {report.timeframe.value} report

Create two summaries:
1. Executive Summary (2-3 sentences): High-level overview for busy parents
2. Detailed Analysis (1 paragraph): More comprehensive explanation

RESPONSE FORMAT (JSON):
{{
    "executive_summary": "Brief, encouraging overview highlighting key progress",
    "detailed_analysis": "Comprehensive paragraph explaining progress patterns and recommendations",
    "next_steps": ["3-4 specific actions parents can take"]
}}

Use encouraging language and focus on the child's learning journey."""

            user_message = f"Create parent summaries for this progress data: {json.dumps(summary_data)}"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            response = await make_llm_api_call(
                messages=messages,
                model_name="gpt-4",
                temperature=0.5,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            summary_content = json.loads(response.choices[0].message.content)
            
            report.executive_summary = summary_content.get("executive_summary", "Your child is making progress in their learning journey.")
            report.detailed_analysis = summary_content.get("detailed_analysis", "Continued support and encouragement will help maintain positive learning momentum.")
            report.next_steps = summary_content.get("next_steps", ["Continue regular practice", "Celebrate achievements", "Provide encouragement"])
            
        except Exception as e:
            logger.warning(f"Error generating AI summaries: {str(e)}")
            # Fallback summaries
            report.executive_summary = f"{report.child_name} completed {report.total_activities_completed} activities with an overall progress score of {report.overall_progress_score:.1%}."
            report.detailed_analysis = f"During this {report.timeframe.value} period, {report.child_name} showed consistent engagement in learning activities across {len(report.subjects_practiced)} subjects."
            report.next_steps = ["Continue regular practice", "Celebrate small wins", "Provide encouragement and support"]
    
    async def _analyze_subject_performance(self, activities: List[LearningActivity]) -> Dict[str, Dict[str, Any]]:
        """Analyze performance by subject"""
        subject_data = {}
        
        for activity in activities:
            try:
                topic_info = await self.curriculum_repo.get_by_id(activity.topic_id, "topic_id")
                if not topic_info:
                    continue
                
                subject = topic_info["subject"]
                score = activity.performance_metrics.overall_score()
                
                if subject not in subject_data:
                    subject_data[subject] = {"scores": [], "activities_count": 0}
                
                subject_data[subject]["scores"].append(score)
                subject_data[subject]["activities_count"] += 1
                
            except:
                continue
        
        # Calculate metrics
        for subject, data in subject_data.items():
            scores = data["scores"]
            data["average_score"] = statistics.mean(scores) if scores else 0
            data["consistency"] = 1.0 - (statistics.stdev(scores) / statistics.mean(scores)) if len(scores) > 1 and statistics.mean(scores) > 0 else 0
        
        return subject_data
    
    async def _analyze_activity_type_performance(self, activities: List[LearningActivity]) -> Dict[str, Dict[str, Any]]:
        """Analyze performance by activity type"""
        type_data = {}
        
        for activity in activities:
            activity_type = activity.activity_type.value
            score = activity.performance_metrics.overall_score()
            
            if activity_type not in type_data:
                type_data[activity_type] = {"scores": [], "success_count": 0, "total_count": 0}
            
            type_data[activity_type]["scores"].append(score)
            type_data[activity_type]["total_count"] += 1
            
            if score >= 0.7:  # Consider 70%+ as success
                type_data[activity_type]["success_count"] += 1
        
        # Calculate metrics
        for activity_type, data in type_data.items():
            scores = data["scores"]
            data["average_score"] = statistics.mean(scores) if scores else 0
            data["success_rate"] = data["success_count"] / data["total_count"] if data["total_count"] > 0 else 0
        
        return type_data
    
    async def _analyze_skill_patterns(self, progress_records: List[ProgressRecord]) -> Dict[str, Any]:
        """Analyze skill development patterns"""
        if not progress_records:
            return {"skill_levels": {}, "improvement_trends": {}}
        
        skill_levels = {}
        improvement_trends = {}
        
        for record in progress_records:
            subject = record.subject.value
            skill_levels[subject] = record.skill_level
            improvement_trends[subject] = record.learning_velocity
        
        return {
            "skill_levels": skill_levels,
            "improvement_trends": improvement_trends,
            "average_skill_level": statistics.mean(skill_levels.values()) if skill_levels else 0,
            "subjects_improving": len([v for v in improvement_trends.values() if v > 0])
        }
    
    async def _analyze_time_patterns(self, activities: List[LearningActivity]) -> Dict[str, Any]:
        """Analyze time and session patterns"""
        if not activities:
            return {"average_session": 0, "optimal_session_length": None, "peak_performance_time": None}
        
        session_lengths = [a.actual_duration_minutes for a in activities if a.actual_duration_minutes]
        
        if not session_lengths:
            return {"average_session": 0, "optimal_session_length": None, "peak_performance_time": None}
        
        average_session = statistics.mean(session_lengths)
        
        # Find optimal session length (where performance is highest)
        performance_by_duration = {}
        for activity in activities:
            if activity.actual_duration_minutes:
                duration_bucket = (activity.actual_duration_minutes // 5) * 5  # 5-minute buckets
                if duration_bucket not in performance_by_duration:
                    performance_by_duration[duration_bucket] = []
                performance_by_duration[duration_bucket].append(activity.performance_metrics.overall_score())
        
        optimal_duration = None
        best_performance = 0
        for duration, scores in performance_by_duration.items():
            avg_performance = statistics.mean(scores)
            if avg_performance > best_performance:
                best_performance = avg_performance
                optimal_duration = duration
        
        return {
            "average_session": round(average_session, 1),
            "optimal_session_length": optimal_duration,
            "session_count": len(session_lengths),
            "total_time": sum(session_lengths)
        }
    
    async def _analyze_engagement_patterns(self, activities: List[LearningActivity]) -> Dict[str, Any]:
        """Analyze engagement patterns"""
        if not activities:
            return {"average_engagement": 0, "engagement_trend": "stable"}
        
        engagement_scores = [a.performance_metrics.engagement_score for a in activities]
        average_engagement = statistics.mean(engagement_scores)
        
        # Calculate trend
        if len(engagement_scores) >= 5:
            recent_engagement = statistics.mean(engagement_scores[-5:])
            older_engagement = statistics.mean(engagement_scores[:-5]) if len(engagement_scores) > 5 else average_engagement
            
            if recent_engagement > older_engagement + 0.1:
                trend = "improving"
            elif recent_engagement < older_engagement - 0.1:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"
        
        return {
            "average_engagement": round(average_engagement, 3),
            "engagement_trend": trend,
            "high_engagement_activities": len([s for s in engagement_scores if s >= 0.8])
        }
    
    def _summarize_strengths(self, strengths: List[Dict[str, Any]]) -> str:
        """Create a summary of identified strengths"""
        if not strengths:
            return "Areas of strength are still being identified through continued learning."
        
        strength_types = [s["type"] for s in strengths]
        subject_strengths = [s for s in strengths if s["type"] == "subject_mastery"]
        
        if subject_strengths:
            subjects = [s["category"] for s in subject_strengths]
            return f"Shows strong performance in {', '.join(subjects)} with consistent high scores."
        else:
            return "Demonstrates good learning capabilities with developing strengths."
    
    def _summarize_weaknesses(self, weaknesses: List[Dict[str, Any]]) -> str:
        """Create a summary of areas for improvement"""
        if not weaknesses:
            return "No significant areas of concern identified. Continue current learning approach."
        
        subject_weaknesses = [w for w in weaknesses if w["type"] == "subject_difficulty"]
        
        if subject_weaknesses:
            subjects = [w["category"] for w in subject_weaknesses]
            return f"May benefit from additional support in {', '.join(subjects)} with focused practice."
        else:
            return "Some learning approaches may need adjustment for optimal results."
    
    async def _generate_improvement_recommendations(self, strengths: List[Dict[str, Any]], 
                                                  weaknesses: List[Dict[str, Any]],
                                                  time_patterns: Dict[str, Any]) -> List[str]:
        """Generate specific improvement recommendations"""
        recommendations = []
        
        # Time-based recommendations
        if time_patterns.get("optimal_session_length"):
            recommendations.append(f"Optimal learning sessions appear to be around {time_patterns['optimal_session_length']} minutes")
        
        # Subject-specific recommendations
        for weakness in weaknesses[:3]:  # Top 3 weaknesses
            if weakness["type"] == "subject_difficulty":
                recommendations.append(f"Focus on {weakness['category']} fundamentals with shorter, more frequent practice sessions")
        
        # Leverage strengths
        for strength in strengths[:2]:  # Top 2 strengths
            if strength["type"] == "subject_mastery":
                recommendations.append(f"Use confidence in {strength['category']} to build motivation for other subjects")
        
        return recommendations[:5]  # Return top 5 recommendations
    
    async def _identify_achievements(self, report: ProgressReport,
                                   activities: List[LearningActivity],
                                   progress_records: List[ProgressRecord]) -> None:
        """Identify and add achievements to the report"""
        # Learning streak achievement
        if report.learning_streak_days >= 7:
            report.add_achievement(
                "Learning Streak Champion",
                f"Maintained a {report.learning_streak_days}-day learning streak!",
                [f"{report.learning_streak_days} consecutive days of learning", "Consistent engagement"]
            )
        
        # High performance achievement
        if report.overall_progress_score >= 0.8:
            report.add_achievement(
                "Excellence in Learning",
                f"Achieved an overall progress score of {report.overall_progress_score:.1%}",
                ["High performance across subjects", "Strong skill development"]
            )
        
        # Subject mastery achievement
        for subject, data in report.subject_progress.items():
            if data["average_score"] >= 0.85:
                report.add_achievement(
                    f"{subject.title()} Star",
                    f"Excellent performance in {subject} with {data['average_score']:.1%} average score",
                    [f"{data['total_activities']} activities completed", f"Average score: {data['average_score']:.1%}"]
                )
    
    async def _identify_focus_areas(self, report: ProgressReport,
                                  activities: List[LearningActivity],
                                  progress_records: List[ProgressRecord]) -> None:
        """Identify and add focus areas to the report"""
        # Subject-specific focus areas
        for subject, data in report.subject_progress.items():
            if data["average_score"] < 0.6:
                report.add_focus_area(
                    f"{subject.title()} Support",
                    f"Additional practice needed in {subject}",
                    [
                        "Break down complex concepts into smaller steps",
                        "Increase practice frequency",
                        "Use visual aids and concrete examples",
                        "Celebrate small improvements"
                    ]
                )
        
        # Time management focus
        if report.total_time_spent_minutes < 30 * len(report.subjects_practiced):  # Less than 30 min per subject
            report.add_focus_area(
                "Learning Time",
                "Consider increasing daily learning time for better skill development",
                [
                    "Aim for 15-20 minutes per subject",
                    "Create a consistent daily learning routine",
                    "Use short, focused sessions"
                ]
            )
    
    async def _generate_fallback_insights(self, report: ProgressReport) -> List[LearningInsight]:
        """Generate fallback insights when AI generation fails"""
        insights = []
        
        # Progress insight
        if report.overall_progress_score >= 0.7:
            insights.append(LearningInsight(
                insight_type="strength",
                priority="medium",
                title="Good Progress Momentum",
                description=f"Your child is making solid progress with a {report.overall_progress_score:.1%} overall score.",
                evidence=[f"Overall score: {report.overall_progress_score:.1%}", f"Activities completed: {report.total_activities_completed}"],
                actionable_steps=["Continue current learning routine", "Celebrate achievements", "Maintain consistent practice"]
            ))
        
        # Engagement insight
        if report.learning_streak_days > 0:
            insights.append(LearningInsight(
                insight_type="milestone",
                priority="high",
                title="Consistent Learning Habit",
                description=f"Great job maintaining a {report.learning_streak_days}-day learning streak!",
                evidence=[f"{report.learning_streak_days} consecutive days", "Regular engagement"],
                actionable_steps=["Keep the momentum going", "Reward consistency", "Plan tomorrow's learning time"]
            ))
        
        # Subject diversity insight
        if len(report.subjects_practiced) >= 2:
            insights.append(LearningInsight(
                insight_type="recommendation",
                priority="low",
                title="Well-Rounded Learning",
                description=f"Excellent exposure to {len(report.subjects_practiced)} different subjects this period.",
                evidence=[f"{len(report.subjects_practiced)} subjects practiced", "Diverse learning experience"],
                actionable_steps=["Continue balanced approach", "Connect learning across subjects", "Encourage curiosity"]
            ))
        
        return insights
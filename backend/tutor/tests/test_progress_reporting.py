"""
Unit tests for Progress Reporting Service - Task 5.2
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone, timedelta
import json

from tutor.services.progress_reporting_service import ProgressReportingService
from tutor.models.progress_models import (
    ProgressReport,
    ReportTimeframe,
    ProgressReportData,
    LearningInsight,
    LearningActivity,
    ProgressRecord,
    ActivityStatus,
    SkillLevel,
    PerformanceMetrics,
    ActivityType
)
from tutor.models.user_models import Subject
from tutor.models.curriculum_models import DifficultyLevel


class TestProgressReportData:
    """Test cases for ProgressReportData model"""
    
    def test_progress_report_data_creation(self):
        """Test creating progress report data for charts"""
        chart_data = ProgressReportData(
            chart_type="bar",
            title="Test Chart"
        )
        
        assert chart_data.chart_type == "bar"
        assert chart_data.title == "Test Chart"
        assert chart_data.labels == []
        assert chart_data.datasets == []
    
    def test_add_dataset(self):
        """Test adding dataset to chart"""
        chart_data = ProgressReportData(title="Skill Levels")
        
        chart_data.add_dataset("Mathematics", [0.8, 0.7, 0.9], "#3B82F6")
        
        assert len(chart_data.datasets) == 1
        dataset = chart_data.datasets[0]
        assert dataset["label"] == "Mathematics"
        assert dataset["data"] == [0.8, 0.7, 0.9]
        assert dataset["backgroundColor"] == "#3B82F6"
        assert dataset["borderColor"] == "#3B82F6"
        assert dataset["fill"] is False


class TestLearningInsight:
    """Test cases for LearningInsight model"""
    
    def test_learning_insight_creation(self):
        """Test creating a learning insight"""
        insight = LearningInsight(
            insight_type="strength",
            priority="high",
            title="Mathematics Excellence",
            description="Your child shows excellent understanding of mathematical concepts.",
            evidence=["High accuracy scores", "Consistent performance"],
            actionable_steps=["Continue current approach", "Introduce advanced topics"],
            related_subjects=[Subject.MATHEMATICS],
            confidence_score=0.9
        )
        
        assert insight.insight_type == "strength"
        assert insight.priority == "high"
        assert insight.title == "Mathematics Excellence"
        assert "excellent understanding" in insight.description
        assert len(insight.evidence) == 2
        assert len(insight.actionable_steps) == 2
        assert Subject.MATHEMATICS in insight.related_subjects
        assert insight.confidence_score == 0.9
        assert insight.insight_id is not None


class TestProgressReport:
    """Test cases for ProgressReport model"""
    
    def test_progress_report_creation(self):
        """Test creating a progress report"""
        start_date = datetime.now(timezone.utc) - timedelta(days=7)
        end_date = datetime.now(timezone.utc)
        
        report = ProgressReport(
            user_id="child-123",
            timeframe=ReportTimeframe.WEEKLY,
            start_date=start_date,
            end_date=end_date,
            child_name="Alice",
            child_age=8,
            child_grade=3
        )
        
        assert report.user_id == "child-123"
        assert report.timeframe == ReportTimeframe.WEEKLY
        assert report.start_date == start_date
        assert report.end_date == end_date
        assert report.child_name == "Alice"
        assert report.child_age == 8
        assert report.child_grade == 3
        assert report.overall_progress_score == 0.0
        assert report.total_activities_completed == 0
        assert len(report.key_insights) == 0
        assert len(report.achievements) == 0
    
    def test_add_insight(self):
        """Test adding insights to report"""
        report = ProgressReport(
            user_id="child-123",
            timeframe=ReportTimeframe.WEEKLY,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc)
        )
        
        high_insight = LearningInsight(
            insight_type="concern",
            priority="high",
            title="High Priority Insight",
            description="Important insight"
        )
        
        medium_insight = LearningInsight(
            insight_type="recommendation",
            priority="medium",
            title="Medium Priority Insight",
            description="Medium insight"
        )
        
        report.add_insight(medium_insight)
        report.add_insight(high_insight)
        
        # Should be sorted by priority (high first)
        assert len(report.key_insights) == 2
        assert report.key_insights[0].priority == "high"
        assert report.key_insights[1].priority == "medium"
    
    def test_add_achievement(self):
        """Test adding achievements to report"""
        report = ProgressReport(
            user_id="child-123",
            timeframe=ReportTimeframe.WEEKLY,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc)
        )
        
        report.add_achievement(
            "Math Champion",
            "Completed 10 math activities with high scores",
            ["10 activities completed", "Average score: 90%"]
        )
        
        assert len(report.achievements) == 1
        achievement = report.achievements[0]
        assert achievement["title"] == "Math Champion"
        assert achievement["description"] == "Completed 10 math activities with high scores"
        assert len(achievement["evidence"]) == 2
        assert "id" in achievement
        assert "timestamp" in achievement
    
    def test_add_focus_area(self):
        """Test adding focus areas to report"""
        report = ProgressReport(
            user_id="child-123",
            timeframe=ReportTimeframe.WEEKLY,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc)
        )
        
        report.add_focus_area(
            "Reading Comprehension",
            "Needs more practice with reading comprehension",
            ["Practice daily reading", "Use guided questions", "Start with shorter texts"]
        )
        
        assert len(report.areas_for_focus) == 1
        focus_area = report.areas_for_focus[0]
        assert focus_area["title"] == "Reading Comprehension"
        assert focus_area["description"] == "Needs more practice with reading comprehension"
        assert len(focus_area["suggestions"]) == 3
        assert focus_area["priority"] == "medium"
    
    def test_get_parent_summary(self):
        """Test generating parent-friendly summary"""
        start_date = datetime.now(timezone.utc) - timedelta(days=7)
        end_date = datetime.now(timezone.utc)
        
        report = ProgressReport(
            user_id="child-123",
            timeframe=ReportTimeframe.WEEKLY,
            start_date=start_date,
            end_date=end_date,
            overall_progress_score=0.75,
            total_activities_completed=15,
            total_time_spent_minutes=180,
            learning_streak_days=5,
            subjects_practiced=[Subject.MATHEMATICS, Subject.SCIENCE]
        )
        
        # Add subject progress
        report.subject_progress["mathematics"] = {"average_score": 0.8}
        report.subject_progress["science"] = {"average_score": 0.7}
        
        # Add some achievements and insights
        report.add_achievement("Test Achievement", "Description")
        report.add_focus_area("Test Focus", "Description")
        
        high_insight = LearningInsight(
            insight_type="concern",
            priority="high",
            title="High Priority",
            description="Important"
        )
        report.add_insight(high_insight)
        
        report.executive_summary = "Great progress this week!"
        report.next_steps = ["Keep practicing", "Try new activities"]
        
        summary = report.get_parent_summary()
        
        assert "overall_progress" in summary
        assert summary["overall_progress"]["score"] == 75.0
        assert "Very good progress" in summary["overall_progress"]["interpretation"]
        
        assert summary["activity_summary"]["total_completed"] == 15
        assert summary["activity_summary"]["learning_streak_days"] == 5
        assert summary["activity_summary"]["subjects_practiced"] == 2
        
        assert summary["top_performing_subject"]["subject"] == "mathematics"
        assert summary["top_performing_subject"]["score"] == 80.0
        
        assert summary["key_highlights"]["achievements"] == 1
        assert summary["key_highlights"]["areas_for_focus"] == 1
        assert summary["key_highlights"]["high_priority_insights"] == 1
        
        assert summary["executive_summary"] == "Great progress this week!"
        assert summary["next_steps_count"] == 2
    
    def test_interpret_progress_score(self):
        """Test progress score interpretation"""
        report = ProgressReport(
            user_id="child-123",
            timeframe=ReportTimeframe.WEEKLY,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc)
        )
        
        # Test different score interpretations
        assert "Excellent progress" in report._interpret_progress_score(0.95)
        assert "Very good progress" in report._interpret_progress_score(0.85)
        assert "Good progress" in report._interpret_progress_score(0.75)
        assert "Satisfactory progress" in report._interpret_progress_score(0.65)
        assert "additional support may help" in report._interpret_progress_score(0.55)
        assert "extra support and encouragement" in report._interpret_progress_score(0.4)


class TestProgressReportingService:
    """Test cases for ProgressReportingService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        return Mock()
    
    @pytest.fixture
    def mock_activity_repo(self):
        """Mock activity repository"""
        repo = AsyncMock()
        repo.get_user_activities = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_progress_repo(self):
        """Mock progress repository"""
        repo = AsyncMock()
        repo.get_user_progress = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_child_repo(self):
        """Mock child repository"""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_curriculum_repo(self):
        """Mock curriculum repository"""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_activity_tracking(self):
        """Mock activity tracking service"""
        service = AsyncMock()
        service._calculate_learning_streak = AsyncMock()
        return service
    
    @pytest.fixture
    def reporting_service(self, mock_db):
        """Create reporting service with mocked dependencies"""
        with patch('tutor.services.progress_reporting_service.LearningActivityRepository') as mock_activity, \
             patch('tutor.services.progress_reporting_service.ProgressRecordRepository') as mock_progress, \
             patch('tutor.services.progress_reporting_service.ChildProfileRepository') as mock_child, \
             patch('tutor.services.progress_reporting_service.CurriculumTopicRepository') as mock_curriculum, \
             patch('tutor.services.progress_reporting_service.ActivityTrackingService') as mock_tracking:
            
            service = ProgressReportingService(mock_db)
            service.activity_repo = mock_activity.return_value
            service.progress_repo = mock_progress.return_value
            service.child_repo = mock_child.return_value
            service.curriculum_repo = mock_curriculum.return_value
            service.activity_tracking = mock_tracking.return_value
            return service
    
    @pytest.mark.asyncio
    async def test_calculate_date_range_weekly(self, reporting_service):
        """Test weekly date range calculation"""
        start_date, end_date = reporting_service._calculate_date_range(ReportTimeframe.WEEKLY)
        
        # Should start from Monday of current week
        assert start_date.weekday() == 0  # Monday
        assert start_date.hour == 0
        assert start_date.minute == 0
        assert end_date > start_date
        assert (end_date - start_date).days <= 7
    
    @pytest.mark.asyncio
    async def test_calculate_date_range_monthly(self, reporting_service):
        """Test monthly date range calculation"""
        start_date, end_date = reporting_service._calculate_date_range(ReportTimeframe.MONTHLY)
        
        # Should start from first day of current month
        assert start_date.day == 1
        assert start_date.hour == 0
        assert start_date.minute == 0
        assert end_date > start_date
        assert (end_date - start_date).days >= 28
    
    @pytest.mark.asyncio
    async def test_generate_progress_report(self, reporting_service):
        """Test comprehensive progress report generation"""
        # Mock child profile
        child_profile = {
            "child_id": "child-123",
            "name": "Alice",
            "age": 8,
            "grade_level": 3
        }
        reporting_service.child_repo.get_by_id.return_value = child_profile
        
        # Mock activities
        activities = []
        for i in range(5):
            activity = LearningActivity(
                user_id="child-123",
                topic_id=f"topic-{i}",
                activity_type=ActivityType.PRACTICE,
                title=f"Activity {i}"
            )
            activity.status = ActivityStatus.COMPLETED
            activity.actual_duration_minutes = 15
            activity.performance_metrics.accuracy = 0.8
            activity.completed_at = datetime.now(timezone.utc) - timedelta(days=i)
            activities.append(activity)
        
        reporting_service.activity_repo.get_user_activities.return_value = activities
        
        # Mock progress records
        progress_records = [
            ProgressRecord(
                user_id="child-123",
                topic_id="topic-math",
                subject=Subject.MATHEMATICS,
                skill_level=0.8
            )
        ]
        reporting_service.progress_repo.get_user_progress.return_value = progress_records
        
        # Mock curriculum topics
        def mock_get_topic(topic_id, field):
            return {"subject": "mathematics", "title": f"Topic {topic_id}"}
        
        reporting_service.curriculum_repo.get_by_id.side_effect = mock_get_topic
        
        # Mock learning streak
        reporting_service.activity_tracking._calculate_learning_streak.return_value = 3
        
        # Mock AI-generated insights
        mock_insights_response = Mock()
        mock_insights_response.choices = [Mock()]
        mock_insights_response.choices[0].message.content = json.dumps({
            "insights": [
                {
                    "insight_type": "strength",
                    "priority": "medium",
                    "title": "Good Progress",
                    "description": "Child is making steady progress",
                    "evidence": ["Consistent activity completion"],
                    "actionable_steps": ["Continue current approach"],
                    "confidence_score": 0.8
                }
            ]
        })
        
        # Mock AI-generated summaries
        mock_summary_response = Mock()
        mock_summary_response.choices = [Mock()]
        mock_summary_response.choices[0].message.content = json.dumps({
            "executive_summary": "Alice is making excellent progress this week.",
            "detailed_analysis": "Strong performance across all activities with consistent engagement.",
            "next_steps": ["Continue regular practice", "Try more challenging activities"]
        })
        
        with patch('tutor.services.progress_reporting_service.make_llm_api_call') as mock_llm:
            mock_llm.side_effect = [mock_insights_response, mock_summary_response]
            
            report = await reporting_service.generate_progress_report(
                user_id="child-123",
                timeframe=ReportTimeframe.WEEKLY
            )
        
        # Verify report structure
        assert report.user_id == "child-123"
        assert report.timeframe == ReportTimeframe.WEEKLY
        assert report.child_name == "Alice"
        assert report.child_age == 8
        assert report.child_grade == 3
        assert report.total_activities_completed == 5
        assert report.total_time_spent_minutes == 75  # 5 * 15 minutes
        assert report.learning_streak_days == 3
        assert Subject.MATHEMATICS in report.subjects_practiced
        assert report.overall_progress_score == 0.8
        
        # Verify charts are generated
        assert report.skill_level_chart.title == "Skill Level by Subject"
        assert len(report.skill_level_chart.datasets) > 0
        
        # Verify insights and summaries
        assert len(report.key_insights) > 0
        assert report.executive_summary == "Alice is making excellent progress this week."
        assert len(report.next_steps) == 2
    
    @pytest.mark.asyncio
    async def test_identify_strengths_and_weaknesses(self, reporting_service):
        """Test strengths and weaknesses identification"""
        # Mock activities with varied performance
        activities = []
        
        # Strong math activities
        for i in range(3):
            activity = LearningActivity(
                user_id="child-123",
                topic_id="math-topic",
                activity_type=ActivityType.PRACTICE,
                title=f"Math Activity {i}"
            )
            activity.status = ActivityStatus.COMPLETED
            activity.performance_metrics.accuracy = 0.9
            activity.performance_metrics.engagement_score = 0.8
            activities.append(activity)
        
        # Weak science activities
        for i in range(2):
            activity = LearningActivity(
                user_id="child-123",
                topic_id="science-topic",
                activity_type=ActivityType.LESSON,
                title=f"Science Activity {i}"
            )
            activity.status = ActivityStatus.COMPLETED
            activity.performance_metrics.accuracy = 0.4
            activity.performance_metrics.engagement_score = 0.5
            activities.append(activity)
        
        reporting_service.activity_repo.get_user_activities.return_value = activities
        
        # Mock progress records
        progress_records = [
            ProgressRecord(
                user_id="child-123",
                topic_id="math-topic",
                subject=Subject.MATHEMATICS,
                skill_level=0.9
            ),
            ProgressRecord(
                user_id="child-123",
                topic_id="science-topic", 
                subject=Subject.SCIENCE,
                skill_level=0.4
            )
        ]
        reporting_service.progress_repo.get_user_progress.return_value = progress_records
        
        # Mock curriculum topics
        def mock_get_topic(topic_id, field):
            if "math" in topic_id:
                return {"subject": "mathematics", "title": "Math Topic"}
            else:
                return {"subject": "science", "title": "Science Topic"}
        
        reporting_service.curriculum_repo.get_by_id.side_effect = mock_get_topic
        
        result = await reporting_service.identify_strengths_and_weaknesses("child-123", 30)
        
        # Verify analysis structure
        assert "strengths" in result
        assert "areas_for_improvement" in result
        assert "total_activities_analyzed" in result
        assert result["total_activities_analyzed"] == 5
        
        # Should identify math as strength
        math_strengths = [s for s in result["strengths"]["items"] if "mathematics" in s.get("category", "")]
        assert len(math_strengths) > 0
        
        # Should identify science as weakness
        science_weaknesses = [w for w in result["areas_for_improvement"]["items"] if "science" in w.get("category", "")]
        assert len(science_weaknesses) > 0
        
        # Verify recommendations
        assert "recommendations" in result
        assert len(result["recommendations"]) > 0
    
    @pytest.mark.asyncio
    async def test_generate_parent_insights(self, reporting_service):
        """Test AI-powered parent insights generation"""
        # Create mock progress report
        progress_report = ProgressReport(
            user_id="child-123",
            timeframe=ReportTimeframe.WEEKLY,
            start_date=datetime.now(timezone.utc) - timedelta(days=7),
            end_date=datetime.now(timezone.utc),
            child_name="Alice",
            child_age=8,
            child_grade=3,
            overall_progress_score=0.75,
            total_activities_completed=10,
            learning_streak_days=5
        )
        
        # Mock child profile
        child_profile = {"child_id": "child-123", "name": "Alice", "age": 8, "grade_level": 3}
        reporting_service.child_repo.get_by_id.return_value = child_profile
        
        # Mock AI response
        mock_ai_response = Mock()
        mock_ai_response.choices = [Mock()]
        mock_ai_response.choices[0].message.content = json.dumps({
            "insights": [
                {
                    "insight_type": "strength",
                    "priority": "high",
                    "title": "Excellent Learning Streak",
                    "description": "Alice has maintained a consistent 5-day learning streak, showing great dedication.",
                    "evidence": ["5 consecutive days of learning", "Regular engagement"],
                    "actionable_steps": ["Celebrate this achievement", "Continue the momentum"],
                    "confidence_score": 0.9
                },
                {
                    "insight_type": "recommendation",
                    "priority": "medium",
                    "title": "Balanced Learning",
                    "description": "Alice would benefit from a mix of different activity types.",
                    "evidence": ["Good overall progress", "Multiple subjects practiced"],
                    "actionable_steps": ["Vary activity types", "Include games and assessments"],
                    "confidence_score": 0.8
                }
            ]
        })
        
        with patch('tutor.services.progress_reporting_service.make_llm_api_call', return_value=mock_ai_response):
            insights = await reporting_service.generate_parent_insights("child-123", progress_report)
        
        # Verify insights
        assert len(insights) >= 2
        
        # Check first insight (strength)
        strength_insight = insights[0]
        assert strength_insight.insight_type == "strength"
        assert strength_insight.priority == "high"
        assert "Learning Streak" in strength_insight.title
        assert "5-day" in strength_insight.description
        assert len(strength_insight.evidence) == 2
        assert len(strength_insight.actionable_steps) == 2
        assert strength_insight.confidence_score == 0.9
        
        # Check second insight (recommendation)
        rec_insight = insights[1]
        assert rec_insight.insight_type == "recommendation"
        assert rec_insight.priority == "medium"
        assert "Balanced" in rec_insight.title
        assert len(rec_insight.actionable_steps) == 2
    
    @pytest.mark.asyncio
    async def test_generate_parent_insights_fallback(self, reporting_service):
        """Test fallback insights when AI generation fails"""
        progress_report = ProgressReport(
            user_id="child-123",
            timeframe=ReportTimeframe.WEEKLY,
            start_date=datetime.now(timezone.utc) - timedelta(days=7),
            end_date=datetime.now(timezone.utc),
            overall_progress_score=0.8,
            total_activities_completed=5,
            learning_streak_days=3,
            subjects_practiced=[Subject.MATHEMATICS, Subject.SCIENCE]
        )
        
        child_profile = {"child_id": "child-123", "name": "Alice", "age": 8, "grade_level": 3}
        reporting_service.child_repo.get_by_id.return_value = child_profile
        
        # Mock AI failure
        with patch('tutor.services.progress_reporting_service.make_llm_api_call', side_effect=Exception("AI Error")):
            insights = await reporting_service.generate_parent_insights("child-123", progress_report)
        
        # Should still generate fallback insights
        assert len(insights) >= 3
        
        # Check for expected fallback insight types
        insight_types = [i.insight_type for i in insights]
        assert "strength" in insight_types  # Progress insight
        assert "milestone" in insight_types  # Streak insight
        assert "recommendation" in insight_types  # Subject diversity insight
    
    @pytest.mark.asyncio
    async def test_analyze_subject_performance(self, reporting_service):
        """Test subject-specific performance analysis"""
        # Mock activities for different subjects
        activities = []
        
        # Math activities (high performance)
        for i in range(3):
            activity = LearningActivity(
                user_id="child-123",
                topic_id="math-topic",
                activity_type=ActivityType.PRACTICE,
                title=f"Math {i}"
            )
            activity.status = ActivityStatus.COMPLETED
            activity.performance_metrics.accuracy = 0.9
            activities.append(activity)
        
        # Science activities (lower performance)
        for i in range(2):
            activity = LearningActivity(
                user_id="child-123",
                topic_id="science-topic",
                activity_type=ActivityType.LESSON,
                title=f"Science {i}"
            )
            activity.status = ActivityStatus.COMPLETED
            activity.performance_metrics.accuracy = 0.6
            activities.append(activity)
        
        # Mock curriculum topics
        def mock_get_topic(topic_id, field):
            if "math" in topic_id:
                return {"subject": "mathematics", "title": "Math Topic"}
            else:
                return {"subject": "science", "title": "Science Topic"}
        
        reporting_service.curriculum_repo.get_by_id.side_effect = mock_get_topic
        
        subject_performance = await reporting_service._analyze_subject_performance(activities)
        
        # Verify analysis
        assert "mathematics" in subject_performance
        assert "science" in subject_performance
        
        math_data = subject_performance["mathematics"]
        assert math_data["average_score"] == 0.9
        assert math_data["activities_count"] == 3
        assert math_data["consistency"] >= 0  # Should have consistency score
        
        science_data = subject_performance["science"]
        assert science_data["average_score"] == 0.6
        assert science_data["activities_count"] == 2
    
    @pytest.mark.asyncio
    async def test_analyze_activity_type_performance(self, reporting_service):
        """Test activity type performance analysis"""
        activities = []
        
        # Practice activities (high success)
        for i in range(4):
            activity = LearningActivity(
                user_id="child-123",
                topic_id="topic-1",
                activity_type=ActivityType.PRACTICE,
                title=f"Practice {i}"
            )
            activity.status = ActivityStatus.COMPLETED
            activity.performance_metrics.accuracy = 0.8
            activities.append(activity)
        
        # Assessment activities (lower success)
        for i in range(2):
            activity = LearningActivity(
                user_id="child-123",
                topic_id="topic-2",
                activity_type=ActivityType.ASSESSMENT,
                title=f"Assessment {i}"
            )
            activity.status = ActivityStatus.COMPLETED
            activity.performance_metrics.accuracy = 0.5
            activities.append(activity)
        
        type_performance = await reporting_service._analyze_activity_type_performance(activities)
        
        # Verify analysis
        assert "practice" in type_performance
        assert "assessment" in type_performance
        
        practice_data = type_performance["practice"]
        assert practice_data["average_score"] == 0.8
        assert practice_data["total_count"] == 4
        assert practice_data["success_count"] == 4  # All above 0.7
        assert practice_data["success_rate"] == 1.0
        
        assessment_data = type_performance["assessment"]
        assert assessment_data["average_score"] == 0.5
        assert assessment_data["total_count"] == 2
        assert assessment_data["success_count"] == 0  # None above 0.7
        assert assessment_data["success_rate"] == 0.0
    
    @pytest.mark.asyncio
    async def test_analyze_time_patterns(self, reporting_service):
        """Test time and session pattern analysis"""
        activities = []
        
        # Create activities with varying durations and performance
        durations_and_scores = [(10, 0.6), (15, 0.8), (20, 0.9), (25, 0.7), (30, 0.5)]
        
        for i, (duration, score) in enumerate(durations_and_scores):
            activity = LearningActivity(
                user_id="child-123",
                topic_id=f"topic-{i}",
                activity_type=ActivityType.PRACTICE,
                title=f"Activity {i}"
            )
            activity.status = ActivityStatus.COMPLETED
            activity.actual_duration_minutes = duration
            activity.performance_metrics.accuracy = score
            activities.append(activity)
        
        time_patterns = await reporting_service._analyze_time_patterns(activities)
        
        # Verify analysis
        assert "average_session" in time_patterns
        assert "optimal_session_length" in time_patterns
        assert "session_count" in time_patterns
        assert "total_time" in time_patterns
        
        assert time_patterns["average_session"] == 20.0  # (10+15+20+25+30)/5
        assert time_patterns["session_count"] == 5
        assert time_patterns["total_time"] == 100
        assert time_patterns["optimal_session_length"] == 20  # Best performance was at 20 minutes
    
    @pytest.mark.asyncio
    async def test_analyze_engagement_patterns(self, reporting_service):
        """Test engagement pattern analysis"""
        activities = []
        
        # Create activities with engagement progression
        engagement_scores = [0.5, 0.6, 0.7, 0.8, 0.9]  # Improving trend
        
        for i, engagement in enumerate(engagement_scores):
            activity = LearningActivity(
                user_id="child-123",
                topic_id=f"topic-{i}",
                activity_type=ActivityType.PRACTICE,
                title=f"Activity {i}"
            )
            activity.status = ActivityStatus.COMPLETED
            activity.performance_metrics.engagement_score = engagement
            activities.append(activity)
        
        engagement_patterns = await reporting_service._analyze_engagement_patterns(activities)
        
        # Verify analysis
        assert "average_engagement" in engagement_patterns
        assert "engagement_trend" in engagement_patterns
        assert "high_engagement_activities" in engagement_patterns
        
        assert engagement_patterns["average_engagement"] == 0.7
        assert engagement_patterns["engagement_trend"] == "improving"
        assert engagement_patterns["high_engagement_activities"] == 2  # 0.8 and 0.9 >= 0.8
    
    def test_chart_colors_configuration(self, reporting_service):
        """Test chart color configuration"""
        assert reporting_service.chart_colors["primary"] == "#3B82F6"
        assert reporting_service.chart_colors["success"] == "#10B981"
        assert reporting_service.chart_colors["warning"] == "#F59E0B"
        assert reporting_service.chart_colors["danger"] == "#EF4444"
        
        assert Subject.MATHEMATICS in reporting_service.subject_colors
        assert Subject.ESL in reporting_service.subject_colors
        assert Subject.SCIENCE in reporting_service.subject_colors
    
    @pytest.mark.asyncio
    async def test_empty_data_handling(self, reporting_service):
        """Test handling of empty data sets"""
        # Test with no activities
        reporting_service.activity_repo.get_user_activities.return_value = []
        reporting_service.progress_repo.get_user_progress.return_value = []
        
        subject_performance = await reporting_service._analyze_subject_performance([])
        assert subject_performance == {}
        
        activity_performance = await reporting_service._analyze_activity_type_performance([])
        assert activity_performance == {}
        
        time_patterns = await reporting_service._analyze_time_patterns([])
        assert time_patterns["average_session"] == 0
        assert time_patterns["optimal_session_length"] is None
        
        engagement_patterns = await reporting_service._analyze_engagement_patterns([])
        assert engagement_patterns["average_engagement"] == 0
        assert engagement_patterns["engagement_trend"] == "stable"
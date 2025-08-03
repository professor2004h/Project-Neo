"""
Unit tests for Activity Tracking Service and Progress Models - Task 5.1
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone, timedelta

from tutor.services.activity_tracking_service import ActivityTrackingService
from tutor.models.progress_models import (
    LearningActivity,
    ProgressRecord,
    ActivityStatus,
    SkillLevel,
    PerformanceMetrics,
    ActivityType
)
from tutor.models.user_models import Subject
from tutor.models.curriculum_models import DifficultyLevel


class TestPerformanceMetrics:
    """Test cases for PerformanceMetrics model"""
    
    def test_performance_metrics_creation(self):
        """Test creating performance metrics with default values"""
        metrics = PerformanceMetrics()
        
        assert metrics.accuracy == 0.0
        assert metrics.speed_score == 0.5
        assert metrics.engagement_score == 0.5
        assert metrics.help_requests == 0
        assert metrics.hints_used == 0
        assert metrics.attempts == 1
        assert metrics.time_spent_seconds == 0
        assert metrics.completion_rate == 0.0
    
    def test_overall_score_calculation(self):
        """Test overall performance score calculation"""
        metrics = PerformanceMetrics(
            accuracy=0.9,
            speed_score=0.8,
            engagement_score=0.7,
            completion_rate=1.0
        )
        
        # Expected: 0.9*0.4 + 0.8*0.2 + 0.7*0.2 + 1.0*0.2 = 0.36 + 0.16 + 0.14 + 0.2 = 0.86
        expected_score = 0.86
        assert abs(metrics.overall_score() - expected_score) < 0.01
    
    def test_performance_metrics_validation(self):
        """Test performance metrics field validation"""
        # Test valid values
        metrics = PerformanceMetrics(accuracy=0.8, speed_score=0.6)
        assert metrics.accuracy == 0.8
        assert metrics.speed_score == 0.6
        
        # Test boundary values
        metrics = PerformanceMetrics(accuracy=0.0, speed_score=1.0)
        assert metrics.accuracy == 0.0
        assert metrics.speed_score == 1.0


class TestLearningActivity:
    """Test cases for LearningActivity model"""
    
    def test_learning_activity_creation(self):
        """Test creating a learning activity"""
        activity = LearningActivity(
            user_id="child-123",
            topic_id="topic-456",
            activity_type=ActivityType.LESSON,
            title="Basic Addition"
        )
        
        assert activity.user_id == "child-123"
        assert activity.topic_id == "topic-456"
        assert activity.activity_type == ActivityType.LESSON
        assert activity.title == "Basic Addition"
        assert activity.status == ActivityStatus.NOT_STARTED
        assert activity.started_at is None
        assert activity.completed_at is None
        assert isinstance(activity.performance_metrics, PerformanceMetrics)
    
    def test_start_activity(self):
        """Test starting an activity"""
        activity = LearningActivity(
            user_id="child-123",
            topic_id="topic-456",
            activity_type=ActivityType.PRACTICE,
            title="Math Practice"
        )
        
        activity.start_activity()
        
        assert activity.status == ActivityStatus.IN_PROGRESS
        assert activity.started_at is not None
        assert activity.last_interaction is not None
        assert activity.started_at == activity.last_interaction
    
    def test_complete_activity(self):
        """Test completing an activity"""
        activity = LearningActivity(
            user_id="child-123",
            topic_id="topic-456",
            activity_type=ActivityType.ASSESSMENT,
            title="Math Assessment"
        )
        
        # Start and then complete
        activity.start_activity()
        start_time = activity.started_at
        
        # Wait a moment to simulate actual activity time
        activity.complete_activity()
        
        assert activity.status == ActivityStatus.COMPLETED
        assert activity.completed_at is not None
        assert activity.completed_at > start_time
        assert activity.actual_duration_minutes is not None
        assert activity.performance_metrics.completion_rate == 1.0
    
    def test_pause_and_resume_activity(self):
        """Test pausing and resuming an activity"""
        activity = LearningActivity(
            user_id="child-123",
            topic_id="topic-456",
            activity_type=ActivityType.GAME,
            title="Math Game"
        )
        
        activity.start_activity()
        activity.pause_activity()
        
        assert activity.status == ActivityStatus.PAUSED
        assert activity.paused_at is not None
        
        activity.resume_activity()
        
        assert activity.status == ActivityStatus.IN_PROGRESS
        assert activity.paused_at is None
        assert activity.last_interaction is not None
    
    def test_add_error(self):
        """Test adding errors to activity"""
        activity = LearningActivity(
            user_id="child-123",
            topic_id="topic-456",
            activity_type=ActivityType.PRACTICE,
            title="Practice Activity"
        )
        
        activity.add_error("incorrect_answer", {"question": "2+2", "answer": "5", "correct": "4"})
        
        assert len(activity.errors_made) == 1
        error = activity.errors_made[0]
        assert error["type"] == "incorrect_answer"
        assert error["details"]["question"] == "2+2"
        assert "timestamp" in error
    
    def test_add_feedback(self):
        """Test adding feedback to activity"""
        activity = LearningActivity(
            user_id="child-123",
            topic_id="topic-456",
            activity_type=ActivityType.LESSON,
            title="Lesson Activity"
        )
        
        activity.add_feedback("encouragement", "Great job! Keep going!", 0.8)
        
        assert len(activity.feedback_given) == 1
        feedback = activity.feedback_given[0]
        assert feedback["type"] == "encouragement"
        assert feedback["content"] == "Great job! Keep going!"
        assert feedback["effectiveness"] == 0.8
        assert "timestamp" in feedback
    
    def test_calculate_skill_level(self):
        """Test skill level calculation from performance"""
        activity = LearningActivity(
            user_id="child-123",
            topic_id="topic-456",
            activity_type=ActivityType.ASSESSMENT,
            title="Assessment"
        )
        
        # Test different performance levels
        activity.performance_metrics.accuracy = 0.9
        activity.performance_metrics.speed_score = 0.8
        activity.performance_metrics.engagement_score = 0.9
        activity.performance_metrics.completion_rate = 1.0
        
        skill_level = activity.calculate_skill_level()
        assert skill_level == SkillLevel.MASTERED
        
        # Test lower performance
        activity.performance_metrics.accuracy = 0.4
        activity.performance_metrics.speed_score = 0.3
        activity.performance_metrics.engagement_score = 0.4
        activity.performance_metrics.completion_rate = 0.6
        
        skill_level = activity.calculate_skill_level()
        assert skill_level == SkillLevel.DEVELOPING


class TestProgressRecord:
    """Test cases for ProgressRecord model"""
    
    def test_progress_record_creation(self):
        """Test creating a progress record"""
        progress = ProgressRecord(
            user_id="child-123",
            topic_id="topic-456",
            subject=Subject.MATHEMATICS
        )
        
        assert progress.user_id == "child-123"
        assert progress.topic_id == "topic-456"
        assert progress.subject == Subject.MATHEMATICS
        assert progress.skill_level == 0.0
        assert progress.skill_level_category == SkillLevel.NOT_ATTEMPTED
        assert progress.confidence_score == 0.0
        assert progress.activities_attempted == 0
        assert progress.activities_completed == 0
    
    def test_update_from_activity(self):
        """Test updating progress from completed activity"""
        progress = ProgressRecord(
            user_id="child-123",
            topic_id="topic-456",
            subject=Subject.MATHEMATICS
        )
        
        # Create completed activity
        activity = LearningActivity(
            user_id="child-123",
            topic_id="topic-456",
            activity_type=ActivityType.PRACTICE,
            title="Practice Activity"
        )
        
        activity.start_activity()
        activity.performance_metrics.accuracy = 0.8
        activity.performance_metrics.speed_score = 0.7
        activity.performance_metrics.engagement_score = 0.9
        activity.performance_metrics.completion_rate = 1.0
        activity.learning_objectives_met = ["basic_addition", "number_recognition"]
        activity.complete_activity()
        
        # Update progress
        progress.update_from_activity(activity)
        
        assert progress.activities_attempted == 1
        assert progress.activities_completed == 1
        assert progress.skill_level > 0.0
        assert progress.last_practiced == activity.completed_at
        assert len(progress.performance_history) == 1
        assert progress.mastery_indicators["basic_addition"]["attempts"] == 1
        assert progress.mastery_indicators["basic_addition"]["successes"] == 1
    
    def test_learning_velocity_calculation(self):
        """Test learning velocity calculation"""
        progress = ProgressRecord(
            user_id="child-123",
            topic_id="topic-456",
            subject=Subject.MATHEMATICS
        )
        
        # Add performance history to simulate improvement
        for i in range(10):
            progress.performance_history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "activity_id": f"activity-{i}",
                "activity_type": "practice",
                "score": 0.3 + (i * 0.05),  # Gradual improvement
                "accuracy": 0.4 + (i * 0.05),
                "duration_minutes": 15
            })
        
        progress._update_learning_velocity()
        assert progress.learning_velocity > 0  # Should show positive improvement
    
    def test_consistency_score_calculation(self):
        """Test consistency score calculation"""
        progress = ProgressRecord(
            user_id="child-123",
            topic_id="topic-456",
            subject=Subject.MATHEMATICS
        )
        
        # Add consistent performance history
        for i in range(10):
            progress.performance_history.append({
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "activity_id": f"activity-{i}",
                "activity_type": "practice",
                "score": 0.8,  # Consistent score
                "accuracy": 0.8,
                "duration_minutes": 15
            })
        
        progress._update_consistency_score()
        assert progress.consistency_score > 0.8  # Should show high consistency
    
    def test_get_progress_summary(self):
        """Test progress summary generation"""
        progress = ProgressRecord(
            user_id="child-123",
            topic_id="topic-456",
            subject=Subject.MATHEMATICS
        )
        
        progress.skill_level = 0.7
        progress.skill_level_category = SkillLevel.PROFICIENT
        progress.confidence_score = 0.8
        progress.activities_completed = 5
        progress.activities_attempted = 6
        progress.total_time_spent_minutes = 120
        progress.learning_velocity = 0.1
        progress.consistency_score = 0.9
        progress.strengths = ["problem_solving"]
        progress.improvement_areas = ["calculation_speed"]
        
        summary = progress.get_progress_summary()
        
        assert summary["skill_level"] == 0.7
        assert summary["skill_category"] == "proficient"
        assert summary["confidence_score"] == 0.8
        assert summary["activities_completed"] == 5
        assert abs(summary["completion_rate"] - 5/6) < 0.01
        assert summary["total_time_spent"] == "120 minutes"
        assert summary["learning_velocity"] == 0.1
        assert summary["consistency_score"] == 0.9
        assert summary["strengths"] == ["problem_solving"]
        assert summary["improvement_areas"] == ["calculation_speed"]


class TestActivityTrackingService:
    """Test cases for ActivityTrackingService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        return Mock()
    
    @pytest.fixture
    def mock_activity_repo(self):
        """Mock activity repository"""
        repo = AsyncMock()
        repo.create_activity = AsyncMock()
        repo.update_activity = AsyncMock()
        repo.get_activity_by_id = AsyncMock()
        repo.get_user_activities = AsyncMock()
        repo.get_recent_activities = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_progress_repo(self):
        """Mock progress repository"""
        repo = AsyncMock()
        repo.create_or_update_progress = AsyncMock()
        repo.get_progress_record = AsyncMock()
        repo.create_progress = AsyncMock()
        repo.update_progress = AsyncMock()
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
    def tracking_service(self, mock_db):
        """Create tracking service with mocked dependencies"""
        with patch('tutor.services.activity_tracking_service.LearningActivityRepository') as mock_activity, \
             patch('tutor.services.activity_tracking_service.ProgressRecordRepository') as mock_progress, \
             patch('tutor.services.activity_tracking_service.ChildProfileRepository') as mock_child, \
             patch('tutor.services.activity_tracking_service.CurriculumTopicRepository') as mock_curriculum:
            
            service = ActivityTrackingService(mock_db)
            service.activity_repo = mock_activity.return_value
            service.progress_repo = mock_progress.return_value
            service.child_repo = mock_child.return_value
            service.curriculum_repo = mock_curriculum.return_value
            return service
    
    @pytest.mark.asyncio
    async def test_create_activity(self, tracking_service):
        """Test creating a new learning activity"""
        result = await tracking_service.create_activity(
            user_id="child-123",
            topic_id="topic-456",
            activity_type=ActivityType.LESSON,
            title="Math Lesson",
            expected_duration=20
        )
        
        assert result.user_id == "child-123"
        assert result.topic_id == "topic-456"
        assert result.activity_type == ActivityType.LESSON
        assert result.title == "Math Lesson"
        assert result.expected_duration_minutes == 20
        
        # Verify repository was called
        tracking_service.activity_repo.create_activity.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_start_activity(self, tracking_service):
        """Test starting an activity"""
        # Mock activity
        mock_activity = LearningActivity(
            user_id="child-123",
            topic_id="topic-456",
            activity_type=ActivityType.PRACTICE,
            title="Practice Activity"
        )
        
        tracking_service.activity_repo.get_activity_by_id.return_value = mock_activity
        tracking_service.activity_repo.update_activity.return_value = mock_activity
        
        result = await tracking_service.start_activity("activity-123")
        
        assert result.status == ActivityStatus.IN_PROGRESS
        assert result.started_at is not None
        
        tracking_service.activity_repo.get_activity_by_id.assert_called_once_with("activity-123")
        tracking_service.activity_repo.update_activity.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_activity_performance(self, tracking_service):
        """Test updating activity performance"""
        mock_activity = LearningActivity(
            user_id="child-123",
            topic_id="topic-456",
            activity_type=ActivityType.ASSESSMENT,
            title="Assessment"
        )
        
        tracking_service.activity_repo.get_activity_by_id.return_value = mock_activity
        tracking_service.activity_repo.update_activity.return_value = mock_activity
        
        performance_update = {
            "accuracy": 0.8,
            "speed_score": 0.7,
            "engagement_score": 0.9,
            "help_requests": 2,
            "learning_objectives_met": ["addition", "subtraction"]
        }
        
        result = await tracking_service.update_activity_performance("activity-123", performance_update)
        
        assert result.performance_metrics.accuracy == 0.8
        assert result.performance_metrics.speed_score == 0.7
        assert result.performance_metrics.engagement_score == 0.9
        assert result.performance_metrics.help_requests == 2
        assert "addition" in result.learning_objectives_met
        assert "subtraction" in result.learning_objectives_met
        
        tracking_service.activity_repo.update_activity.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_complete_activity(self, tracking_service):
        """Test completing an activity"""
        # Mock activity
        mock_activity = LearningActivity(
            user_id="child-123",
            topic_id="topic-456",
            activity_type=ActivityType.PRACTICE,
            title="Practice Activity"
        )
        mock_activity.start_activity()
        mock_activity.performance_metrics.accuracy = 0.8
        
        tracking_service.activity_repo.get_activity_by_id.return_value = mock_activity
        
        # Mock progress record
        mock_progress = ProgressRecord(
            user_id="child-123",
            topic_id="topic-456",
            subject=Subject.MATHEMATICS
        )
        tracking_service.progress_repo.get_progress_record.return_value = mock_progress
        
        # Mock curriculum topic
        tracking_service.curriculum_repo.get_by_id.return_value = {
            "subject": "mathematics",
            "title": "Basic Math"
        }
        
        result = await tracking_service.complete_activity("activity-123")
        
        assert "activity_id" in result
        assert "completed_at" in result
        assert "performance_score" in result
        assert "skill_level_after" in result
        assert "recommendations" in result
        
        tracking_service.activity_repo.update_activity.assert_called()
        tracking_service.progress_repo.update_progress.assert_called()
    
    @pytest.mark.asyncio
    async def test_calculate_skill_level(self, tracking_service):
        """Test skill level calculation"""
        # Mock progress record
        mock_progress = ProgressRecord(
            user_id="child-123",
            topic_id="topic-456",
            subject=Subject.MATHEMATICS
        )
        mock_progress.skill_level = 0.7
        mock_progress.skill_level_category = SkillLevel.PROFICIENT
        mock_progress.consistency_score = 0.8
        mock_progress.confidence_score = 0.9
        
        tracking_service.progress_repo.get_progress_record.return_value = mock_progress
        
        # Mock recent activities
        mock_activities = []
        for i in range(5):
            activity = LearningActivity(
                user_id="child-123",
                topic_id="topic-456",
                activity_type=ActivityType.PRACTICE,
                title=f"Activity {i}"
            )
            activity.status = ActivityStatus.COMPLETED
            activity.performance_metrics.accuracy = 0.7 + (i * 0.05)
            mock_activities.append(activity)
        
        tracking_service.activity_repo.get_recent_activities.return_value = mock_activities
        
        result = await tracking_service.calculate_skill_level("child-123", "topic-456")
        
        assert "skill_level" in result
        assert "skill_category" in result
        assert "confidence_score" in result
        assert "assessment_basis" in result
        assert result["activities_analyzed"] == 5
    
    @pytest.mark.asyncio
    async def test_generate_activity_recommendations(self, tracking_service):
        """Test recommendation generation"""
        # Create activity with excellent performance
        activity = LearningActivity(
            user_id="child-123",
            topic_id="topic-456",
            activity_type=ActivityType.ASSESSMENT,
            title="Assessment"
        )
        activity.performance_metrics.accuracy = 0.95
        activity.performance_metrics.speed_score = 0.9
        activity.performance_metrics.engagement_score = 0.9
        activity.performance_metrics.completion_rate = 1.0
        activity.expected_duration_minutes = 20
        activity.actual_duration_minutes = 10
        
        recommendations = await tracking_service.generate_activity_recommendations(activity)
        
        assert len(recommendations) > 0
        
        # Check for advancement recommendation
        advancement_recs = [r for r in recommendations if r["type"] == "advancement"]
        assert len(advancement_recs) > 0
        assert advancement_recs[0]["action"] == "increase_difficulty"
        
        # Check for challenge recommendation (quick completion)
        challenge_recs = [r for r in recommendations if r["type"] == "challenge"]
        assert len(challenge_recs) > 0
    
    @pytest.mark.asyncio
    async def test_get_activity_summary(self, tracking_service):
        """Test activity summary generation"""
        # Mock activities
        mock_activities = []
        for i in range(7):
            activity = LearningActivity(
                user_id="child-123",
                topic_id=f"topic-{i}",
                activity_type=ActivityType.PRACTICE,
                title=f"Activity {i}"
            )
            activity.status = ActivityStatus.COMPLETED
            activity.actual_duration_minutes = 15
            activity.performance_metrics.accuracy = 0.7 + (i * 0.05)
            mock_activities.append(activity)
        
        tracking_service.activity_repo.get_user_activities.return_value = mock_activities
        
        # Mock curriculum topics
        def mock_get_topic(topic_id, field):
            return {"subject": "mathematics", "title": f"Topic {topic_id}"}
        
        tracking_service.curriculum_repo.get_by_id.side_effect = mock_get_topic
        
        result = await tracking_service.get_activity_summary("child-123", timeframe_days=7)
        
        assert result["total_activities"] == 7
        assert result["completed_activities"] == 7
        assert result["completion_rate"] == 1.0
        assert result["total_time_minutes"] == 105  # 7 * 15 minutes
        assert result["average_session_minutes"] == 15
        assert result["average_score"] > 0
        assert "mathematics" in result["subjects_practiced"]
        assert "practice" in result["activity_types"]
        assert result["activity_types"]["practice"] == 7
    
    @pytest.mark.asyncio
    async def test_activity_not_found_error(self, tracking_service):
        """Test error handling when activity not found"""
        tracking_service.activity_repo.get_activity_by_id.return_value = None
        
        with pytest.raises(ValueError) as exc_info:
            await tracking_service.start_activity("nonexistent-activity")
        
        assert "Activity not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_learning_streak_calculation(self, tracking_service):
        """Test learning streak calculation"""
        # Create activities for consecutive days
        mock_activities = []
        base_date = datetime.now(timezone.utc)
        
        for i in range(5):  # 5 consecutive days
            activity = LearningActivity(
                user_id="child-123",
                topic_id="topic-456",
                activity_type=ActivityType.PRACTICE,
                title=f"Activity {i}"
            )
            activity.status = ActivityStatus.COMPLETED
            activity.completed_at = base_date - timedelta(days=i)
            mock_activities.append(activity)
        
        tracking_service.activity_repo.get_user_activities.return_value = mock_activities
        
        streak = await tracking_service._calculate_learning_streak("child-123")
        
        assert streak == 5  # Should have 5-day streak
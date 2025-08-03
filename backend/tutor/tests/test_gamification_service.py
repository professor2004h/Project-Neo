"""
Unit tests for Gamification Service and Gamification Models - Task 7.1
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import json

from tutor.services.gamification_service import GamificationService
from tutor.models.gamification_models import (
    Achievement,
    AchievementType,
    Badge,
    BadgeCategory,
    UserGameProfile,
    Reward,
    RewardType,
    EngagementMetrics,
    EngagementLevel,
    MotivationState,
    GameElementType,
    GameElementPreference
)
from tutor.models.progress_models import (
    LearningActivity,
    ActivityStatus,
    PerformanceMetrics,
    ActivityType
)
from tutor.models.user_models import Subject
from tutor.models.curriculum_models import DifficultyLevel


class TestGamificationModels:
    """Test cases for Gamification Models"""
    
    def test_badge_creation(self):
        """Test creating a badge"""
        badge = Badge(
            name="Math Master",
            description="Excellent performance in mathematics",
            category=BadgeCategory.ACADEMIC,
            required_points=100,
            subject_specific=Subject.MATHEMATICS,
            rarity_level=3
        )
        
        assert badge.name == "Math Master"
        assert badge.category == BadgeCategory.ACADEMIC
        assert badge.required_points == 100
        assert badge.subject_specific == Subject.MATHEMATICS
        assert badge.rarity_level == 3
        assert badge.is_secret is False
        assert badge.badge_id is not None
        
        display_info = badge.get_display_info()
        assert display_info["name"] == "Math Master"
        assert display_info["category"] == "academic"
        assert display_info["rarity_level"] == 3
    
    def test_achievement_creation(self):
        """Test creating an achievement"""
        achievement = Achievement(
            user_id="child-123",
            achievement_type=AchievementType.LEARNING_STREAK,
            title="Week Warrior",
            description="Learn for 7 days in a row",
            target_value=7,
            points_reward=100,
            subject=Subject.MATHEMATICS
        )
        
        assert achievement.user_id == "child-123"
        assert achievement.achievement_type == AchievementType.LEARNING_STREAK
        assert achievement.title == "Week Warrior"
        assert achievement.target_value == 7
        assert achievement.current_value == 0
        assert achievement.is_completed is False
        assert achievement.completion_percentage == 0.0
        assert achievement.points_reward == 100
        assert achievement.subject == Subject.MATHEMATICS
    
    def test_achievement_progress_update(self):
        """Test updating achievement progress"""
        achievement = Achievement(
            user_id="child-123",
            achievement_type=AchievementType.ACTIVITY_COMPLETION,
            title="Activity Master",
            description="Complete 10 activities",
            target_value=10
        )
        
        # Update progress
        completed = achievement.update_progress(5)
        assert achievement.current_value == 5
        assert achievement.completion_percentage == 0.5
        assert achievement.is_completed is False
        assert completed is False
        
        # Complete achievement
        completed = achievement.update_progress(10)
        assert achievement.current_value == 10
        assert achievement.completion_percentage == 1.0
        assert achievement.is_completed is True
        assert achievement.completed_at is not None
        assert completed is True
        
        # Try to update beyond completion
        completed = achievement.update_progress(15)
        assert achievement.current_value == 15  # Can go beyond target
        assert achievement.completion_percentage == 1.0
        assert completed is False  # Already completed
    
    def test_achievement_milestones(self):
        """Test achievement milestone tracking"""
        achievement = Achievement(
            user_id="child-123",
            achievement_type=AchievementType.ACCURACY,
            title="Accuracy Expert",
            description="High accuracy on multiple activities",
            target_value=20
        )
        
        # Add milestones
        achievement.add_milestone(5, "First milestone")
        achievement.add_milestone(10, "Halfway there")
        achievement.add_milestone(15, "Almost done")
        
        assert len(achievement.progress_milestones) == 3
        
        # Update progress to achieve first milestone
        achievement.update_progress(7)
        
        # Check milestone status
        assert achievement.progress_milestones[0]["achieved"] is True
        assert achievement.progress_milestones[1]["achieved"] is False
        
        # Get next milestone
        next_milestone = achievement.get_next_milestone()
        assert next_milestone["value"] == 10
        assert next_milestone["description"] == "Halfway there"
    
    def test_user_game_profile_creation(self):
        """Test creating a user game profile"""
        profile = UserGameProfile(user_id="child-123")
        
        assert profile.user_id == "child-123"
        assert profile.total_points == 0
        assert profile.level == 1
        assert profile.experience_points == 0
        assert profile.current_learning_streak == 0
        assert profile.engagement_level == EngagementLevel.MODERATE
        assert profile.motivation_state == MotivationState.NEUTRAL
        assert len(profile.completed_achievements) == 0
        assert len(profile.earned_badges) == 0
    
    def test_user_profile_add_points(self):
        """Test adding points to user profile"""
        profile = UserGameProfile(user_id="child-123")
        
        # Add points
        result = profile.add_points(75, Subject.MATHEMATICS)
        
        assert profile.total_points == 75
        assert profile.experience_points == 75
        assert profile.subject_points["mathematics"] == 75
        assert result["points_added"] == 75
        assert result["level_up"] is False
        
        # Add more points to trigger level up
        result = profile.add_points(50)
        
        assert profile.total_points == 125
        assert profile.level == 2  # Should level up at 100 XP
        assert result["level_up"] is True
        assert result["old_level"] == 1
        assert result["new_level"] == 2
    
    def test_user_profile_level_rewards(self):
        """Test level-up rewards"""
        profile = UserGameProfile(user_id="child-123")
        
        # Add enough points to reach level 5
        result = profile.add_points(400)  # Should reach level 5
        
        assert profile.level == 5
        assert len(result["level_up_rewards"]) > 0
        
        # Check for customization reward at level 5
        customization_rewards = [r for r in result["level_up_rewards"] if r["type"] == "customization"]
        assert len(customization_rewards) > 0
    
    def test_user_profile_achievements_and_badges(self):
        """Test adding achievements and badges"""
        profile = UserGameProfile(user_id="child-123")
        
        # Add achievement
        achievement_id = "achievement-123"
        profile.add_achievement(achievement_id)
        
        assert achievement_id in profile.completed_achievements
        assert achievement_id not in profile.active_achievements
        
        # Add badge
        badge_id = "badge-456"
        profile.add_badge(badge_id)
        
        assert badge_id in profile.earned_badges
    
    def test_user_profile_engagement_update(self):
        """Test updating engagement and motivation"""
        profile = UserGameProfile(user_id="child-123")
        
        old_updated_at = profile.updated_at
        
        profile.update_engagement(EngagementLevel.HIGH, MotivationState.EXCITED)
        
        assert profile.engagement_level == EngagementLevel.HIGH
        assert profile.motivation_state == MotivationState.EXCITED
        assert profile.updated_at > old_updated_at
        assert profile.last_active > old_updated_at
    
    def test_user_profile_summary(self):
        """Test getting profile summary"""
        profile = UserGameProfile(
            user_id="child-123",
            total_points=250,
            level=3,
            experience_points=25,
            current_learning_streak=5,
            longest_learning_streak=8
        )
        
        profile.earned_badges = ["badge1", "badge2"]
        profile.completed_achievements = ["ach1", "ach2", "ach3"]
        
        summary = profile.get_profile_summary()
        
        assert summary["user_id"] == "child-123"
        assert summary["level"] == 3
        assert summary["total_points"] == 250
        assert summary["badges_earned"] == 2
        assert summary["achievements_completed"] == 3
        assert summary["current_streak"] == 5
        assert summary["longest_streak"] == 8
        assert "progress_to_next_level" in summary
    
    def test_reward_creation(self):
        """Test creating a reward"""
        reward = Reward(
            user_id="child-123",
            reward_type=RewardType.POINTS,
            title="Activity Complete!",
            description="You earned points for completing the activity",
            points_value=50,
            earned_from="activity",
            earned_from_id="activity-456"
        )
        
        assert reward.user_id == "child-123"
        assert reward.reward_type == RewardType.POINTS
        assert reward.points_value == 50
        assert reward.is_claimed is False
        assert reward.earned_from == "activity"
        assert reward.reward_id is not None
    
    def test_reward_claiming(self):
        """Test claiming rewards"""
        reward = Reward(
            user_id="child-123",
            reward_type=RewardType.BADGE,
            title="New Badge!",
            description="You earned a new badge",
            badge_id="badge-123",
            earned_from="achievement",
            earned_from_id="ach-456"
        )
        
        # Claim reward
        success = reward.claim_reward()
        
        assert success is True
        assert reward.is_claimed is True
        assert reward.claimed_at is not None
        
        # Try to claim again
        success = reward.claim_reward()
        assert success is False  # Already claimed
    
    def test_reward_expiration(self):
        """Test reward expiration"""
        # Create expired reward
        reward = Reward(
            user_id="child-123",
            reward_type=RewardType.UNLOCK,
            title="Limited Time Reward",
            description="This reward has expired",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            earned_from="event",
            earned_from_id="event-123"
        )
        
        assert reward.is_expired() is True
        
        # Try to claim expired reward
        success = reward.claim_reward()
        assert success is False
    
    def test_engagement_metrics_creation(self):
        """Test creating engagement metrics"""
        metrics = EngagementMetrics(
            user_id="child-123",
            measurement_period_days=7,
            sessions_completed=10,
            activities_completed=15,
            activities_started=20,
            total_time_spent_minutes=120,
            average_accuracy=0.85
        )
        
        assert metrics.user_id == "child-123"
        assert metrics.measurement_period_days == 7
        assert metrics.sessions_completed == 10
        assert metrics.completion_rate == 0.75  # 15/20
        assert metrics.average_session_duration == 8.0  # 120/15
        assert metrics.average_accuracy == 0.85
    
    def test_engagement_level_calculation(self):
        """Test engagement level calculation"""
        metrics = EngagementMetrics(user_id="child-123")
        
        # Very high engagement
        metrics.engagement_score = 0.95
        assert metrics.calculate_engagement_level() == EngagementLevel.VERY_HIGH
        
        # High engagement
        metrics.engagement_score = 0.85
        assert metrics.calculate_engagement_level() == EngagementLevel.HIGH
        
        # Moderate engagement
        metrics.engagement_score = 0.65
        assert metrics.calculate_engagement_level() == EngagementLevel.MODERATE
        
        # Low engagement
        metrics.engagement_score = 0.45
        assert metrics.calculate_engagement_level() == EngagementLevel.LOW
        
        # Very low engagement
        metrics.engagement_score = 0.25
        assert metrics.calculate_engagement_level() == EngagementLevel.VERY_LOW
    
    def test_motivation_state_calculation(self):
        """Test motivation state calculation"""
        metrics = EngagementMetrics(user_id="child-123")
        
        # Excited state
        metrics.motivation_score = 0.95
        metrics.improvement_trend = 0.2
        assert metrics.calculate_motivation_state() == MotivationState.EXCITED
        
        # Engaged state
        metrics.motivation_score = 0.75
        assert metrics.calculate_motivation_state() == MotivationState.ENGAGED
        
        # Neutral state
        metrics.motivation_score = 0.55
        metrics.improvement_trend = 0.05
        assert metrics.calculate_motivation_state() == MotivationState.NEUTRAL
        
        # Declining state
        metrics.motivation_score = 0.45
        metrics.improvement_trend = -0.15
        assert metrics.calculate_motivation_state() == MotivationState.DECLINING
        
        # Disengaged state
        metrics.motivation_score = 0.2
        assert metrics.calculate_motivation_state() == MotivationState.DISENGAGED
    
    def test_engagement_insights(self):
        """Test engagement insights generation"""
        metrics = EngagementMetrics(
            user_id="child-123",
            activities_completed=10,
            completion_rate=0.4,  # Low completion rate
            help_requests=8,  # High help requests
            early_exits=5,  # Many early exits
            voluntary_activities=4,  # Some voluntary activities
            improvement_trend=0.3  # Strong improvement
        )
        
        insights = metrics.get_engagement_insights()
        
        assert len(insights) > 0
        assert any("not finish" in insight for insight in insights)  # Low completion
        assert any("help" in insight for insight in insights)  # High help requests
        assert any("early" in insight for insight in insights)  # Early exits
        assert any("motivation" in insight for insight in insights)  # Voluntary activities
        assert any("progress" in insight for insight in insights)  # Strong improvement
    
    def test_engagement_recommendations(self):
        """Test engagement recommendations"""
        metrics = EngagementMetrics(
            user_id="child-123",
            engagement_score=0.3,  # Low engagement
            completion_rate=0.5,  # Moderate completion
            help_requests=10  # High help requests
        )
        
        recommendations = metrics.get_recommendations()
        
        assert len(recommendations) <= 3
        assert any("game" in rec.lower() for rec in recommendations)  # Game elements for low engagement
        assert any("chunk" in rec.lower() for rec in recommendations)  # Break activities down
    
    def test_game_element_preference(self):
        """Test game element preference tracking"""
        preference = GameElementPreference(
            user_id="child-123",
            element_type=GameElementType.BADGES,
            age_when_measured=8,
            subjects_context=[Subject.MATHEMATICS]
        )
        
        assert preference.user_id == "child-123"
        assert preference.element_type == GameElementType.BADGES
        assert preference.preference_score == 0.5
        assert preference.usage_count == 0
        
        # Update with positive response
        preference.update_preference(True)
        
        assert preference.usage_count == 1
        assert preference.positive_responses == 1
        assert preference.preference_score == 1.0
        
        # Update with negative response
        preference.update_preference(False)
        
        assert preference.usage_count == 2
        assert preference.negative_responses == 1
        assert preference.preference_score == 0.5  # 1 positive, 1 negative


class TestGamificationService:
    """Test cases for GamificationService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        return Mock()
    
    @pytest.fixture
    def mock_child_repo(self):
        """Mock child repository"""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_activity_repo(self):
        """Mock activity repository"""
        repo = AsyncMock()
        repo.get_user_activities = AsyncMock()
        repo.get_recent_activities = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_progress_repo(self):
        """Mock progress repository"""
        repo = AsyncMock()
        repo.get_user_progress = AsyncMock()
        return repo
    
    @pytest.fixture
    def gamification_service(self, mock_db):
        """Create gamification service with mocked dependencies"""
        with patch('tutor.services.gamification_service.ChildProfileRepository') as mock_child, \
             patch('tutor.services.gamification_service.LearningActivityRepository') as mock_activity, \
             patch('tutor.services.gamification_service.ProgressRecordRepository') as mock_progress:
            
            service = GamificationService(mock_db)
            service.child_repo = mock_child.return_value
            service.activity_repo = mock_activity.return_value
            service.progress_repo = mock_progress.return_value
            return service
    
    @pytest.mark.asyncio
    async def test_get_or_create_user_profile_new_user(self, gamification_service):
        """Test creating a new user profile"""
        user_id = "child-123"
        
        # Mock that profile doesn't exist in DB
        with patch.object(gamification_service, '_load_user_profile_from_db', return_value=None), \
             patch.object(gamification_service, '_save_user_profile_to_db'), \
             patch.object(gamification_service, '_initialize_user_achievements'):
            
            profile = await gamification_service.get_or_create_user_profile(user_id)
            
            assert profile.user_id == user_id
            assert profile.total_points == 0
            assert profile.level == 1
            assert user_id in gamification_service.user_profiles_cache
    
    @pytest.mark.asyncio
    async def test_get_or_create_user_profile_existing_user(self, gamification_service):
        """Test getting an existing user profile"""
        user_id = "child-123"
        existing_profile = UserGameProfile(
            user_id=user_id,
            total_points=500,
            level=5
        )
        
        with patch.object(gamification_service, '_load_user_profile_from_db', return_value=existing_profile):
            profile = await gamification_service.get_or_create_user_profile(user_id)
            
            assert profile.user_id == user_id
            assert profile.total_points == 500
            assert profile.level == 5
            assert user_id in gamification_service.user_profiles_cache
    
    @pytest.mark.asyncio
    async def test_calculate_rewards_for_activity(self, gamification_service):
        """Test calculating rewards for a completed activity"""
        # Create a completed activity
        activity = LearningActivity(
            user_id="child-123",
            topic_id="topic-456",
            activity_type=ActivityType.PRACTICE,
            title="Math Practice"
        )
        activity.status = ActivityStatus.COMPLETED
        activity.actual_duration_minutes = 15
        activity.performance_metrics.accuracy = 0.9
        activity.performance_metrics.engagement_score = 0.8
        activity.performance_metrics.completion_rate = 1.0
        activity.subject = Subject.MATHEMATICS
        
        # Mock user profile
        profile = UserGameProfile(user_id="child-123")
        with patch.object(gamification_service, 'get_or_create_user_profile', return_value=profile):
            rewards = await gamification_service.calculate_rewards_for_activity(activity)
            
            assert len(rewards) > 0
            
            # Should have at least a points reward
            points_rewards = [r for r in rewards if r.reward_type == RewardType.POINTS]
            assert len(points_rewards) > 0
            
            points_reward = points_rewards[0]
            assert points_reward.user_id == "child-123"
            assert points_reward.points_value > 0
            assert "Activity Completed" in points_reward.title
    
    @pytest.mark.asyncio
    async def test_calculate_rewards_perfect_score(self, gamification_service):
        """Test additional rewards for perfect performance"""
        activity = LearningActivity(
            user_id="child-123",
            topic_id="topic-456",
            activity_type=ActivityType.ASSESSMENT,
            title="Math Assessment"
        )
        activity.status = ActivityStatus.COMPLETED
        activity.performance_metrics.accuracy = 1.0
        activity.performance_metrics.speed_score = 0.95
        activity.performance_metrics.engagement_score = 0.95
        activity.performance_metrics.completion_rate = 1.0
        
        profile = UserGameProfile(user_id="child-123")
        with patch.object(gamification_service, 'get_or_create_user_profile', return_value=profile):
            rewards = await gamification_service.calculate_rewards_for_activity(activity)
            
            # Should have celebration reward for perfect score
            celebration_rewards = [r for r in rewards if r.reward_type == RewardType.CELEBRATION]
            assert len(celebration_rewards) > 0
            
            perfect_reward = celebration_rewards[0]
            assert "Perfect Score" in perfect_reward.title
    
    @pytest.mark.asyncio
    async def test_track_engagement_metrics(self, gamification_service):
        """Test tracking engagement metrics"""
        user_id = "child-123"
        
        # Mock activities
        activities = []
        for i in range(10):
            activity = LearningActivity(
                user_id=user_id,
                topic_id=f"topic-{i}",
                activity_type=ActivityType.PRACTICE,
                title=f"Activity {i}"
            )
            activity.status = ActivityStatus.COMPLETED if i < 8 else ActivityStatus.IN_PROGRESS
            activity.actual_duration_minutes = 12
            activity.performance_metrics.accuracy = 0.8
            activity.performance_metrics.help_requests = 1
            activity.performance_metrics.engagement_score = 0.7
            activities.append(activity)
        
        gamification_service.activity_repo.get_user_activities.return_value = activities
        
        metrics = await gamification_service.track_engagement_metrics(user_id, measurement_period_days=7)
        
        assert metrics.user_id == user_id
        assert metrics.activities_started == 10
        assert metrics.activities_completed == 8
        assert metrics.completion_rate == 0.8
        assert metrics.total_time_spent_minutes == 96  # 8 completed * 12 minutes
        assert metrics.help_requests == 8  # 1 per completed activity
        assert metrics.engagement_score > 0.0
    
    @pytest.mark.asyncio
    async def test_assess_motivation_level(self, gamification_service):
        """Test motivation level assessment"""
        user_id = "child-123"
        
        # Mock engagement metrics
        mock_metrics = EngagementMetrics(
            user_id=user_id,
            engagement_score=0.8,
            motivation_score=0.75,
            improvement_trend=0.1
        )
        
        # Mock profile
        profile = UserGameProfile(user_id=user_id)
        
        with patch.object(gamification_service, 'track_engagement_metrics', return_value=mock_metrics), \
             patch.object(gamification_service, 'get_or_create_user_profile', return_value=profile), \
             patch.object(gamification_service, '_generate_motivation_recommendations', return_value=["Keep up the good work!"]):
            
            motivation_state, recommendations = await gamification_service.assess_motivation_level(user_id)
            
            assert motivation_state == MotivationState.ENGAGED
            assert len(recommendations) > 0
            assert "good work" in recommendations[0]
    
    @pytest.mark.asyncio
    async def test_award_achievement(self, gamification_service):
        """Test awarding an achievement"""
        user_id = "child-123"
        achievement_id = "streak_7"
        
        # Mock achievement
        achievement = Achievement(
            achievement_id=achievement_id,
            user_id=user_id,
            achievement_type=AchievementType.LEARNING_STREAK,
            title="Week Warrior",
            description="Learn for 7 days in a row",
            target_value=7,
            points_reward=100,
            badge_rewards=["streak_badge"]
        )
        
        # Mock profile
        profile = UserGameProfile(user_id=user_id)
        
        with patch.object(gamification_service, 'get_or_create_user_profile', return_value=profile), \
             patch.object(gamification_service, '_get_achievement_by_id', return_value=achievement), \
             patch.object(gamification_service, '_get_badge_by_id', return_value=Badge(name="Streak Badge", description="7-day streak", category=BadgeCategory.BEHAVIORAL)):
            
            rewards = await gamification_service.award_achievement(user_id, achievement_id)
            
            assert len(rewards) >= 2  # Points + badge reward
            assert achievement_id in profile.completed_achievements
            assert "streak_badge" in profile.earned_badges
            
            # Check points reward
            points_rewards = [r for r in rewards if r.reward_type == RewardType.POINTS]
            assert len(points_rewards) > 0
            assert points_rewards[0].points_value == 100
            
            # Check badge reward
            badge_rewards = [r for r in rewards if r.reward_type == RewardType.BADGE]
            assert len(badge_rewards) > 0
            assert badge_rewards[0].badge_id == "streak_badge"
    
    @pytest.mark.asyncio
    async def test_update_learning_streak(self, gamification_service):
        """Test updating learning streak"""
        user_id = "child-123"
        
        # Mock completed activities for streak calculation
        activities = []
        for i in range(5):  # 5-day streak
            activity = LearningActivity(
                user_id=user_id,
                topic_id="topic-1",
                activity_type=ActivityType.PRACTICE,
                title="Daily Practice"
            )
            activity.status = ActivityStatus.COMPLETED
            activity.completed_at = datetime.now(timezone.utc) - timedelta(days=i)
            activities.append(activity)
        
        profile = UserGameProfile(user_id=user_id, current_learning_streak=0)
        
        with patch.object(gamification_service, 'get_or_create_user_profile', return_value=profile), \
             patch.object(gamification_service, '_calculate_learning_streak', return_value=5):
            
            gamification_service.activity_repo.get_recent_activities.return_value = activities
            
            result = await gamification_service.update_learning_streak(user_id)
            
            assert result["old_streak"] == 0
            assert result["new_streak"] == 5
            assert result["streak_increased"] is True
            assert profile.current_learning_streak == 5
            assert profile.longest_learning_streak == 5
    
    @pytest.mark.asyncio
    async def test_calculate_base_points(self, gamification_service):
        """Test base points calculation"""
        # Practice activity
        activity = LearningActivity(
            user_id="child-123",
            topic_id="topic-456",
            activity_type=ActivityType.PRACTICE,
            title="Practice Activity"
        )
        activity.actual_duration_minutes = 20
        activity.learning_context = {"subject": "mathematics"}
        
        base_points = await gamification_service._calculate_base_points(activity)
        
        # Base 10 + duration bonus (20//5 = 4) + math bonus (10% of 14) + practice multiplier (1.2)
        expected_base = 10 + 4  # 14
        expected_with_math = int(14 * 1.1)  # 15 (math bonus)
        expected_final = int(15 * 1.2)  # 18 (practice multiplier)
        
        assert base_points >= 15  # Should get math and duration bonuses
    
    @pytest.mark.asyncio
    async def test_calculate_performance_multiplier(self, gamification_service):
        """Test performance multiplier calculation"""
        activity = LearningActivity(
            user_id="child-123",
            topic_id="topic-456",
            activity_type=ActivityType.PRACTICE,
            title="Test Activity"
        )
        
        # Perfect performance
        activity.performance_metrics.accuracy = 1.0
        activity.performance_metrics.speed_score = 0.95
        activity.performance_metrics.engagement_score = 0.95
        activity.performance_metrics.completion_rate = 1.0
        
        multiplier = await gamification_service._calculate_performance_multiplier(activity)
        assert multiplier == 2.0  # Exceptional performance
        
        # Good performance
        activity.performance_metrics.accuracy = 0.85
        multiplier = await gamification_service._calculate_performance_multiplier(activity)
        assert multiplier == 1.5  # Good performance
        
        # Poor performance
        activity.performance_metrics.accuracy = 0.5
        multiplier = await gamification_service._calculate_performance_multiplier(activity)
        assert multiplier == 0.8  # Encouragement points
    
    @pytest.mark.asyncio
    async def test_calculate_streak_bonus(self, gamification_service):
        """Test streak bonus calculation"""
        profile = UserGameProfile(user_id="child-123")
        
        # No streak
        profile.current_learning_streak = 0
        bonus = await gamification_service._calculate_streak_bonus(profile)
        assert bonus == 0
        
        # 3-day streak
        profile.current_learning_streak = 3
        bonus = await gamification_service._calculate_streak_bonus(profile)
        assert bonus == 5
        
        # 7-day streak
        profile.current_learning_streak = 7
        bonus = await gamification_service._calculate_streak_bonus(profile)
        assert bonus == 10
        
        # 30-day streak
        profile.current_learning_streak = 30
        bonus = await gamification_service._calculate_streak_bonus(profile)
        assert bonus == 25
    
    def test_calculate_slope(self, gamification_service):
        """Test slope calculation for trends"""
        # Positive trend
        x_vals = [0, 1, 2, 3, 4]
        y_vals = [0.5, 0.6, 0.7, 0.8, 0.9]
        
        slope = gamification_service._calculate_slope(x_vals, y_vals)
        assert slope > 0  # Should be positive trend
        
        # Negative trend
        y_vals = [0.9, 0.8, 0.7, 0.6, 0.5]
        slope = gamification_service._calculate_slope(x_vals, y_vals)
        assert slope < 0  # Should be negative trend
        
        # Flat trend
        y_vals = [0.7, 0.7, 0.7, 0.7, 0.7]
        slope = gamification_service._calculate_slope(x_vals, y_vals)
        assert abs(slope) < 0.01  # Should be near zero
    
    @pytest.mark.asyncio
    async def test_calculate_learning_streak(self, gamification_service):
        """Test learning streak calculation"""
        # Create activities for consecutive days
        activities = []
        base_date = datetime.now(timezone.utc)
        
        for i in range(5):  # 5 consecutive days
            activity = LearningActivity(
                user_id="child-123",
                topic_id="topic-1",
                activity_type=ActivityType.PRACTICE,
                title=f"Activity {i}"
            )
            activity.status = ActivityStatus.COMPLETED
            activity.completed_at = base_date - timedelta(days=i)
            activities.append(activity)
        
        streak = await gamification_service._calculate_learning_streak(activities)
        assert streak == 5
        
        # Test with gap in activities
        activities[2].completed_at = base_date - timedelta(days=10)  # Create gap
        streak = await gamification_service._calculate_learning_streak(activities)
        assert streak == 2  # Should stop at the gap
    
    @pytest.mark.asyncio
    async def test_error_handling(self, gamification_service):
        """Test error handling in various methods"""
        user_id = "child-123"
        
        # Test error in get_or_create_user_profile
        with patch.object(gamification_service, '_load_user_profile_from_db', side_effect=Exception("DB Error")):
            profile = await gamification_service.get_or_create_user_profile(user_id)
            
            # Should return default profile on error
            assert profile.user_id == user_id
            assert profile.total_points == 0
        
        # Test error in calculate_rewards_for_activity
        activity = LearningActivity(
            user_id=user_id,
            topic_id="topic-456",
            activity_type=ActivityType.PRACTICE,
            title="Test Activity"
        )
        activity.status = ActivityStatus.NOT_STARTED  # Not completed
        
        rewards = await gamification_service.calculate_rewards_for_activity(activity)
        assert len(rewards) == 0  # Should return empty list for incomplete activity
    
    @pytest.mark.asyncio
    async def test_ai_recommendation_generation(self, gamification_service):
        """Test AI-powered recommendation generation"""
        metrics = EngagementMetrics(
            user_id="child-123",
            engagement_score=0.4,  # Low engagement
            completion_rate=0.6,
            improvement_trend=0.05
        )
        
        motivation_state = MotivationState.DECLINING
        
        # Mock AI response
        mock_ai_response = Mock()
        mock_ai_response.choices = [Mock()]
        mock_ai_response.choices[0].message.content = json.dumps({
            "recommendations": [
                "Introduce more game elements to increase engagement",
                "Provide immediate positive feedback for completed activities",
                "Break activities into smaller, manageable chunks"
            ]
        })
        
        with patch('tutor.services.gamification_service.make_llm_api_call', return_value=mock_ai_response):
            recommendations = await gamification_service._generate_motivation_recommendations(metrics, motivation_state)
            
            assert len(recommendations) == 3
            assert "game elements" in recommendations[0]
            assert "positive feedback" in recommendations[1]
            assert "smaller" in recommendations[2]
    
    @pytest.mark.asyncio
    async def test_ai_recommendation_fallback(self, gamification_service):
        """Test fallback to rule-based recommendations when AI fails"""
        metrics = EngagementMetrics(
            user_id="child-123",
            engagement_score=0.3,  # Low engagement
            completion_rate=0.4
        )
        
        motivation_state = MotivationState.DECLINING
        
        # Mock AI failure
        with patch('tutor.services.gamification_service.make_llm_api_call', side_effect=Exception("AI Error")):
            recommendations = await gamification_service._generate_motivation_recommendations(metrics, motivation_state)
            
            # Should fall back to rule-based recommendations
            assert len(recommendations) > 0
            assert any("game" in rec.lower() for rec in recommendations)
"""
Unit tests for Adaptive Gamification Service - Task 7.2
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
import json

from tutor.services.adaptive_gamification_service import AdaptiveGamificationService, InterestProfile, GamificationStrategy
from tutor.services.gamification_service import GamificationService
from tutor.models.gamification_models import (
    UserGameProfile,
    EngagementMetrics,
    EngagementLevel,
    MotivationState,
    GameElementType,
    GameElementPreference,
    AchievementType,
    BadgeCategory
)
from tutor.models.user_models import Subject


class TestInterestProfile:
    """Test cases for InterestProfile model"""
    
    def test_interest_profile_creation(self):
        """Test creating an interest profile"""
        profile = InterestProfile(
            user_id="child-123",
            preferred_themes=["space", "animals"],
            favorite_colors=["blue", "green"],
            preferred_difficulty="moderate",
            optimal_session_length=15
        )
        
        assert profile.user_id == "child-123"
        assert profile.preferred_themes == ["space", "animals"]
        assert profile.favorite_colors == ["blue", "green"]
        assert profile.preferred_difficulty == "moderate"
        assert profile.optimal_session_length == 15
        assert profile.confidence_score == 0.5
        assert profile.last_updated is not None
    
    def test_interest_profile_defaults(self):
        """Test interest profile with default values"""
        profile = InterestProfile(user_id="child-123")
        
        assert len(profile.preferred_themes) == 0
        assert len(profile.favorite_colors) == 0
        assert profile.preferred_difficulty == "moderate"
        assert profile.optimal_session_length == 15
        assert profile.break_frequency == 10


class TestGamificationStrategy:
    """Test cases for GamificationStrategy model"""
    
    def test_strategy_creation(self):
        """Test creating a gamification strategy"""
        strategy = GamificationStrategy(
            name="High Engagement",
            description="Strategy for high engagement users",
            target_engagement_level=EngagementLevel.HIGH,
            target_motivation_state=MotivationState.ENGAGED,
            enabled_elements=[GameElementType.BADGES, GameElementType.CHALLENGES],
            element_weights={"badges": 0.8, "challenges": 0.7}
        )
        
        assert strategy.name == "High Engagement"
        assert strategy.target_engagement_level == EngagementLevel.HIGH
        assert strategy.target_motivation_state == MotivationState.ENGAGED
        assert GameElementType.BADGES in strategy.enabled_elements
        assert strategy.element_weights["badges"] == 0.8
        assert strategy.usage_count == 0
        assert strategy.success_rate == 0.0
    
    def test_strategy_apply_to_user(self):
        """Test applying strategy to user"""
        strategy = GamificationStrategy(
            name="Test Strategy",
            description="Test strategy",
            target_engagement_level=EngagementLevel.MODERATE,
            target_motivation_state=MotivationState.NEUTRAL,
            enabled_elements=[GameElementType.POINTS, GameElementType.REWARDS],
            element_weights={"points": 0.7, "rewards": 0.9},
            reward_frequency="high",
            visual_style={"points": {"color": "gold"}}
        )
        
        user_profile = UserGameProfile(user_id="child-123")
        engagement_metrics = EngagementMetrics(user_id="child-123")
        
        adaptations = strategy.apply_to_user(user_profile, engagement_metrics)
        
        assert adaptations["strategy_name"] == "Test Strategy"
        assert "points" in adaptations["elements"]
        assert adaptations["elements"]["points"]["enabled"] is True
        assert adaptations["elements"]["points"]["prominence"] == 0.7
        assert adaptations["timing_changes"]["reward_threshold"] == 0.5  # High frequency = lower threshold


class TestAdaptiveGamificationService:
    """Test cases for AdaptiveGamificationService"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        return Mock()
    
    @pytest.fixture
    def mock_base_service(self):
        """Mock base gamification service"""
        service = AsyncMock()
        service.get_or_create_user_profile = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_child_repo(self):
        """Mock child repository"""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock()
        return repo
    
    @pytest.fixture
    def adaptive_service(self, mock_db, mock_base_service):
        """Create adaptive gamification service with mocked dependencies"""
        with patch('tutor.services.adaptive_gamification_service.ChildProfileRepository') as mock_child_repo_class:
            service = AdaptiveGamificationService(mock_db, mock_base_service)
            service.child_repo = mock_child_repo_class.return_value
            return service
    
    @pytest.mark.asyncio
    async def test_adapt_gamification_for_user(self, adaptive_service, mock_base_service):
        """Test adapting gamification for a user"""
        user_id = "child-123"
        
        # Mock user profile
        user_profile = UserGameProfile(user_id=user_id, level=3, total_points=150)
        mock_base_service.get_or_create_user_profile.return_value = user_profile
        
        # Mock interest profile
        interest_profile = InterestProfile(
            user_id=user_id,
            preferred_themes=["space", "adventure"],
            favorite_colors=["blue", "purple"]
        )
        
        # Mock engagement metrics
        engagement_metrics = EngagementMetrics(
            user_id=user_id,
            engagement_score=0.4,  # Low engagement
            motivation_score=0.3   # Declining motivation
        )
        
        with patch.object(adaptive_service, '_get_or_create_interest_profile', return_value=interest_profile), \
             patch.object(adaptive_service, '_select_optimal_strategy') as mock_select_strategy, \
             patch.object(adaptive_service, '_personalize_adaptations') as mock_personalize:
            
            # Mock strategy selection
            test_strategy = adaptive_service.strategies["reengagement"]
            mock_select_strategy.return_value = test_strategy
            
            # Mock personalization
            mock_personalize.return_value = {"test": "adaptations"}
            
            result = await adaptive_service.adapt_gamification_for_user(user_id, engagement_metrics)
            
            assert result["strategy"] == "Re-engagement Focus"
            assert "adaptations" in result
            assert "reasoning" in result
            assert "expected_outcomes" in result
            
            # Verify strategy usage was tracked
            assert test_strategy.usage_count == 1
            assert test_strategy.last_used is not None
    
    @pytest.mark.asyncio
    async def test_select_game_elements_by_interest(self, adaptive_service):
        """Test selecting game elements based on interests"""
        user_id = "child-123"
        
        # Mock interest profile
        interest_profile = InterestProfile(
            user_id=user_id,
            preferred_themes=["fantasy", "adventure"],
            preferred_difficulty="challenging"
        )
        
        # Mock child profile
        child_profile = {"child_id": user_id, "age": 10, "name": "Alice"}
        adaptive_service.child_repo.get_by_id.return_value = child_profile
        
        # Mock element effectiveness
        adaptive_service.element_effectiveness[user_id] = {
            GameElementType.BADGES: 0.8,
            GameElementType.CHALLENGES: 0.9,
            GameElementType.STORYTELLING: 0.7
        }
        
        available_elements = [
            GameElementType.BADGES,
            GameElementType.CHALLENGES, 
            GameElementType.STORYTELLING,
            GameElementType.POINTS,
            GameElementType.LEADERBOARDS
        ]
        
        with patch.object(adaptive_service, '_get_or_create_interest_profile', return_value=interest_profile):
            element_scores = await adaptive_service.select_game_elements_by_interest(user_id, available_elements)
            
            assert len(element_scores) == len(available_elements)
            
            # Should be sorted by score descending
            scores = [score for element, score in element_scores]
            assert scores == sorted(scores, reverse=True)
            
            # Check that storytelling gets bonus for fantasy theme
            storytelling_score = next(score for element, score in element_scores if element == GameElementType.STORYTELLING)
            assert storytelling_score > 0.5  # Should get theme bonus
    
    @pytest.mark.asyncio
    async def test_implement_reengagement_strategy(self, adaptive_service, mock_base_service):
        """Test implementing re-engagement strategy"""
        user_id = "child-123"
        
        # Mock engagement metrics showing disengagement
        engagement_metrics = EngagementMetrics(
            user_id=user_id,
            engagement_score=0.2,  # Very low
            motivation_score=0.1,  # Disengaged
            completion_rate=0.3,
            early_exits=5,
            help_requests=10
        )
        
        # Mock child profile
        child_profile = {"child_id": user_id, "age": 8, "name": "Bob"}
        adaptive_service.child_repo.get_by_id.return_value = child_profile
        
        # Mock user profile
        user_profile = UserGameProfile(user_id=user_id)
        mock_base_service.get_or_create_user_profile.return_value = user_profile
        
        result = await adaptive_service.implement_reengagement_strategy(user_id, engagement_metrics)
        
        assert result["urgency_level"] == "critical"  # Should be critical for very low engagement
        assert len(result["tactics"]) > 0
        assert len(result["immediate_actions"]) > 0
        assert "encouragement_message" in result
        assert result["timeline"] == "immediate"
        
        # Check for appropriate tactics for critical urgency
        tactic_types = [tactic["type"] for tactic in result["tactics"]]
        assert "immediate_reward" in tactic_types or "simplify_content" in tactic_types
    
    @pytest.mark.asyncio
    async def test_track_element_effectiveness(self, adaptive_service):
        """Test tracking game element effectiveness"""
        user_id = "child-123"
        element = GameElementType.BADGES
        
        # Initial tracking
        await adaptive_service.track_element_effectiveness(
            user_id, element, "positive", 0.2
        )
        
        assert user_id in adaptive_service.element_effectiveness
        assert element in adaptive_service.element_effectiveness[user_id]
        
        initial_effectiveness = adaptive_service.element_effectiveness[user_id][element]
        assert initial_effectiveness > 0.5  # Positive response should increase
        
        # Track negative response
        await adaptive_service.track_element_effectiveness(
            user_id, element, "negative", -0.1
        )
        
        new_effectiveness = adaptive_service.element_effectiveness[user_id][element]
        assert new_effectiveness < initial_effectiveness  # Should decrease with negative response
        
        # Track neutral response
        await adaptive_service.track_element_effectiveness(
            user_id, element, "neutral", 0.0
        )
        
        # Should be between previous values
        final_effectiveness = adaptive_service.element_effectiveness[user_id][element]
        assert 0.0 <= final_effectiveness <= 1.0
    
    @pytest.mark.asyncio
    async def test_customize_game_experience(self, adaptive_service):
        """Test customizing game experience"""
        user_id = "child-123"
        
        customization_preferences = {
            "themes": ["space", "robots"],
            "colors": ["blue", "silver"],
            "difficulty": "challenging"
        }
        
        # Mock existing interest profile
        existing_profile = InterestProfile(
            user_id=user_id,
            preferred_themes=["animals"],  # Will be updated
            favorite_colors=["red"]        # Will be updated
        )
        
        with patch.object(adaptive_service, '_get_or_create_interest_profile', return_value=existing_profile):
            customization = await adaptive_service.customize_game_experience(user_id, customization_preferences)
            
            assert "visual_theme" in customization
            assert "game_elements" in customization
            assert "content_style" in customization
            assert "interaction_patterns" in customization
            assert "reward_system" in customization
            
            # Verify profile was updated
            assert existing_profile.preferred_themes == ["space", "robots"]
            assert existing_profile.favorite_colors == ["blue", "silver"]
            assert existing_profile.preferred_difficulty == "challenging"
            assert existing_profile.confidence_score > 0.5  # Should increase with explicit preferences
    
    @pytest.mark.asyncio
    async def test_get_or_create_interest_profile_new_user(self, adaptive_service):
        """Test creating new interest profile"""
        user_id = "child-123"
        
        # Mock child profile
        child_profile = {"child_id": user_id, "age": 7, "name": "Charlie"}
        adaptive_service.child_repo.get_by_id.return_value = child_profile
        
        with patch.object(adaptive_service, '_load_interest_profile_from_db', return_value=None):
            profile = await adaptive_service._get_or_create_interest_profile(user_id)
            
            assert profile.user_id == user_id
            assert len(profile.preferred_themes) > 0  # Should get age-appropriate themes
            assert profile.optimal_session_length <= 15  # Age-appropriate session length for 7-year-old
            assert user_id in adaptive_service.user_interests_cache
    
    @pytest.mark.asyncio
    async def test_get_or_create_interest_profile_existing_user(self, adaptive_service):
        """Test getting existing interest profile"""
        user_id = "child-123"
        
        # Put profile in cache
        existing_profile = InterestProfile(
            user_id=user_id,
            preferred_themes=["space"],
            optimal_session_length=20
        )
        adaptive_service.user_interests_cache[user_id] = existing_profile
        
        profile = await adaptive_service._get_or_create_interest_profile(user_id)
        
        assert profile == existing_profile
        assert profile.preferred_themes == ["space"]
        assert profile.optimal_session_length == 20
    
    @pytest.mark.asyncio
    async def test_calculate_element_interest_score(self, adaptive_service):
        """Test calculating interest score for game elements"""
        interest_profile = InterestProfile(
            user_id="child-123",
            preferred_themes=["fantasy", "adventure"],
            favorite_colors=["purple", "gold"],
            preferred_difficulty="challenging"
        )
        
        # Test storytelling with fantasy theme (should get bonus)
        storytelling_score = await adaptive_service._calculate_element_interest_score(
            GameElementType.STORYTELLING, interest_profile
        )
        assert storytelling_score > 0.7  # Base + fantasy bonus
        
        # Test customization with favorite colors (should get bonus)
        customization_score = await adaptive_service._calculate_element_interest_score(
            GameElementType.CUSTOMIZATION, interest_profile
        )
        assert customization_score > 0.6  # Base + color bonus
        
        # Test challenges with challenging difficulty (should get bonus)
        challenges_score = await adaptive_service._calculate_element_interest_score(
            GameElementType.CHALLENGES, interest_profile
        )
        assert challenges_score > 0.7  # Base + difficulty bonus
    
    @pytest.mark.asyncio
    async def test_calculate_age_appropriateness(self, adaptive_service):
        """Test age appropriateness calculation"""
        # Young child (age 6)
        young_badges = await adaptive_service._calculate_age_appropriateness(GameElementType.BADGES, 6)
        young_leaderboards = await adaptive_service._calculate_age_appropriateness(GameElementType.LEADERBOARDS, 6)
        
        assert young_badges > young_leaderboards  # Badges better for young children
        
        # Older child (age 11)
        older_leaderboards = await adaptive_service._calculate_age_appropriateness(GameElementType.LEADERBOARDS, 11)
        older_celebrations = await adaptive_service._calculate_age_appropriateness(GameElementType.CELEBRATIONS, 11)
        
        assert older_leaderboards > young_leaderboards  # Leaderboards better for older children
    
    @pytest.mark.asyncio
    async def test_assess_reengagement_urgency(self, adaptive_service):
        """Test assessing re-engagement urgency"""
        # Critical urgency - disengaged
        critical_metrics = EngagementMetrics(user_id="child-123", engagement_score=0.1)
        urgency = await adaptive_service._assess_reengagement_urgency(critical_metrics, MotivationState.DISENGAGED)
        assert urgency == "critical"
        
        # High urgency - declining with low engagement
        high_metrics = EngagementMetrics(user_id="child-123", engagement_score=0.2)
        urgency = await adaptive_service._assess_reengagement_urgency(high_metrics, MotivationState.DECLINING)
        assert urgency == "high"
        
        # Moderate urgency - declining with moderate engagement
        moderate_metrics = EngagementMetrics(user_id="child-123", engagement_score=0.5)
        urgency = await adaptive_service._assess_reengagement_urgency(moderate_metrics, MotivationState.DECLINING)
        assert urgency == "moderate"
        
        # Low urgency - neutral state
        low_metrics = EngagementMetrics(user_id="child-123", engagement_score=0.6)
        urgency = await adaptive_service._assess_reengagement_urgency(low_metrics, MotivationState.NEUTRAL)
        assert urgency == "low"
    
    @pytest.mark.asyncio
    async def test_select_reengagement_tactics(self, adaptive_service):
        """Test selecting re-engagement tactics"""
        user_id = "child-123"
        engagement_metrics = EngagementMetrics(user_id=user_id)
        
        # Critical urgency tactics
        critical_tactics = await adaptive_service._select_reengagement_tactics(user_id, "critical", engagement_metrics)
        assert len(critical_tactics) <= 3
        tactic_types = [t["type"] for t in critical_tactics]
        assert "immediate_reward" in tactic_types
        assert "simplify_content" in tactic_types
        
        # High urgency tactics
        high_tactics = await adaptive_service._select_reengagement_tactics(user_id, "high", engagement_metrics)
        assert len(high_tactics) <= 3
        tactic_types = [t["type"] for t in high_tactics]
        assert "boost_rewards" in tactic_types or "introduce_novelty" in tactic_types
        
        # Low urgency tactics
        low_tactics = await adaptive_service._select_reengagement_tactics(user_id, "low", engagement_metrics)
        assert len(low_tactics) <= 3
        tactic_types = [t["type"] for t in low_tactics]
        assert "gentle_encouragement" in tactic_types or "goal_setting" in tactic_types
    
    @pytest.mark.asyncio
    async def test_create_immediate_interventions(self, adaptive_service):
        """Test creating immediate interventions"""
        user_id = "child-123"
        
        tactics = [
            {"type": "immediate_reward", "description": "Give bonus points"},
            {"type": "personal_message", "description": "Send encouragement"},
            {"type": "simplify_content", "description": "Make easier"}
        ]
        
        with patch.object(adaptive_service, '_generate_personalized_encouragement', return_value="Great job!"):
            interventions = await adaptive_service._create_immediate_interventions(user_id, tactics)
            
            assert len(interventions) == 3
            
            intervention_actions = [i["action"] for i in interventions]
            assert "award_bonus_points" in intervention_actions
            assert "show_encouragement" in intervention_actions
            assert "adjust_difficulty" in intervention_actions
    
    @pytest.mark.asyncio
    async def test_schedule_followup_actions(self, adaptive_service):
        """Test scheduling follow-up actions"""
        user_id = "child-123"
        tactics = [{"type": "boost_rewards", "description": "Increase rewards"}]
        
        # Critical urgency should have short follow-up interval
        critical_followups = await adaptive_service._schedule_followup_actions(user_id, tactics, "critical")
        assert len(critical_followups) >= 1
        
        # Check that engagement check is scheduled soon
        engagement_check = next(f for f in critical_followups if f["action"] == "engagement_check")
        scheduled_time = engagement_check["scheduled_at"]
        time_diff = (scheduled_time - datetime.now(timezone.utc)).total_seconds()
        assert time_diff < 3 * 3600  # Less than 3 hours for critical
        
        # Low urgency should have longer follow-up interval
        low_followups = await adaptive_service._schedule_followup_actions(user_id, tactics, "low")
        engagement_check = next(f for f in low_followups if f["action"] == "engagement_check")
        scheduled_time = engagement_check["scheduled_at"]
        time_diff = (scheduled_time - datetime.now(timezone.utc)).total_seconds()
        assert time_diff > 20 * 3600  # More than 20 hours for low urgency
    
    @pytest.mark.asyncio
    async def test_generate_personalized_encouragement(self, adaptive_service, mock_base_service):
        """Test generating personalized encouragement"""
        user_id = "child-123"
        
        # Mock child profile
        child_profile = {"child_id": user_id, "age": 8, "name": "Dave"}
        adaptive_service.child_repo.get_by_id.return_value = child_profile
        
        # Mock user game profile
        game_profile = UserGameProfile(
            user_id=user_id,
            total_points=150,
            level=3,
            current_learning_streak=5
        )
        game_profile.earned_badges = ["badge1", "badge2"]
        mock_base_service.get_or_create_user_profile.return_value = game_profile
        
        # Mock AI response
        mock_ai_response = Mock()
        mock_ai_response.choices = [Mock()]
        mock_ai_response.choices[0].message.content = "Great job, Dave! You're doing amazing with your learning!"
        
        with patch('tutor.services.adaptive_gamification_service.make_llm_api_call', return_value=mock_ai_response):
            encouragement = await adaptive_service._generate_personalized_encouragement(user_id, None)
            
            assert "Dave" in encouragement
            assert "amazing" in encouragement or "great" in encouragement.lower()
    
    @pytest.mark.asyncio
    async def test_generate_personalized_encouragement_fallback(self, adaptive_service, mock_base_service):
        """Test fallback encouragement when AI fails"""
        user_id = "child-123"
        
        # Mock child profile
        child_profile = {"child_id": user_id, "age": 8, "name": "Eve"}
        adaptive_service.child_repo.get_by_id.return_value = child_profile
        
        # Mock user game profile
        game_profile = UserGameProfile(user_id=user_id)
        mock_base_service.get_or_create_user_profile.return_value = game_profile
        
        # Mock AI failure
        with patch('tutor.services.adaptive_gamification_service.make_llm_api_call', side_effect=Exception("AI Error")):
            encouragement = await adaptive_service._generate_personalized_encouragement(user_id, None)
            
            # Should fall back to predefined messages
            assert "Eve" in encouragement
            assert len(encouragement) > 0
    
    @pytest.mark.asyncio
    async def test_select_optimal_strategy(self, adaptive_service):
        """Test selecting optimal strategy"""
        user_profile = UserGameProfile(user_id="child-123")
        interest_profile = InterestProfile(user_id="child-123")
        engagement_metrics = EngagementMetrics(user_id="child-123")
        
        # Test low engagement scenario
        strategy = await adaptive_service._select_optimal_strategy(
            user_profile, interest_profile, 
            EngagementLevel.LOW, MotivationState.DECLINING,
            engagement_metrics
        )
        
        assert strategy.name == "Re-engagement Focus"
        assert EngagementLevel.LOW in [strategy.target_engagement_level] or \
               strategy.target_engagement_level in [EngagementLevel.MODERATE, EngagementLevel.HIGH]
        
        # Test high engagement scenario
        strategy = await adaptive_service._select_optimal_strategy(
            user_profile, interest_profile,
            EngagementLevel.HIGH, MotivationState.ENGAGED,
            engagement_metrics
        )
        
        assert strategy.target_engagement_level == EngagementLevel.HIGH or \
               strategy.target_motivation_state == MotivationState.ENGAGED
    
    @pytest.mark.asyncio
    async def test_get_age_appropriate_themes(self, adaptive_service):
        """Test getting age-appropriate themes"""
        # Young child themes
        young_themes = await adaptive_service._get_age_appropriate_themes(6)
        assert "animals" in young_themes
        assert "fairy_tales" in young_themes
        
        # Middle child themes
        middle_themes = await adaptive_service._get_age_appropriate_themes(9)
        assert "adventure" in middle_themes
        assert "space" in middle_themes
        
        # Older child themes
        older_themes = await adaptive_service._get_age_appropriate_themes(12)
        assert "exploration" in older_themes
        assert "technology" in older_themes
    
    @pytest.mark.asyncio
    async def test_get_age_appropriate_session_length(self, adaptive_service):
        """Test getting age-appropriate session length"""
        # Younger children should have shorter sessions
        young_length = await adaptive_service._get_age_appropriate_session_length(6)
        assert young_length <= 10
        
        # Middle children
        middle_length = await adaptive_service._get_age_appropriate_session_length(9)
        assert 15 <= middle_length <= 20
        
        # Older children can handle longer sessions
        older_length = await adaptive_service._get_age_appropriate_session_length(12)
        assert older_length >= 20
    
    @pytest.mark.asyncio
    async def test_fallback_behaviors(self, adaptive_service):
        """Test fallback behaviors when systems fail"""
        user_id = "child-123"
        
        # Test fallback adaptations
        fallback_adaptations = await adaptive_service._get_fallback_adaptations(user_id)
        assert fallback_adaptations["strategy"] == "fallback"
        assert "points" in fallback_adaptations["adaptations"]["elements"]
        
        # Test fallback re-engagement plan
        fallback_plan = await adaptive_service._get_fallback_reengagement_plan(user_id)
        assert fallback_plan["urgency_level"] == "moderate"
        assert len(fallback_plan["immediate_actions"]) > 0
        
        # Test default customization
        default_customization = await adaptive_service._get_default_customization()
        assert "visual_theme" in default_customization
        assert "game_elements" in default_customization
    
    @pytest.mark.asyncio
    async def test_customization_helpers(self, adaptive_service):
        """Test customization helper methods"""
        interest_profile = InterestProfile(
            user_id="child-123",
            preferred_themes=["space"],
            favorite_colors=["blue", "silver"],
            preferred_difficulty="challenging",
            optimal_session_length=20,
            break_frequency=15
        )
        
        # Test visual theme creation
        visual_theme = await adaptive_service._create_visual_theme(interest_profile)
        assert visual_theme["primary_colors"] == ["blue", "silver"]
        assert visual_theme["theme_name"] == "space"
        
        # Test game elements customization
        game_elements = await adaptive_service._customize_game_elements(interest_profile)
        assert "badges" in game_elements
        assert game_elements["badges"]["style"] == "colorful"
        
        # Test content style adaptation
        content_style = await adaptive_service._adapt_content_style(interest_profile)
        assert content_style["difficulty"] == "challenging"
        assert content_style["session_length"] == 20
        assert content_style["break_frequency"] == 15
        
        # Test interaction customization
        interactions = await adaptive_service._customize_interactions(interest_profile)
        assert interactions["feedback_style"] == "encouraging"
        
        # Test reward customization
        rewards = await adaptive_service._customize_rewards(interest_profile)
        assert "points" in rewards["reward_types"]
        assert rewards["frequency"] == "balanced"
    
    @pytest.mark.asyncio
    async def test_prediction_methods(self, adaptive_service):
        """Test prediction and reasoning methods"""
        strategy = adaptive_service.strategies["balanced_engagement"]
        engagement_metrics = EngagementMetrics(user_id="child-123")
        
        # Test strategy outcome prediction
        outcomes = await adaptive_service._predict_strategy_outcomes(strategy, engagement_metrics)
        assert "engagement_boost" in outcomes
        assert "motivation_improvement" in outcomes
        assert "time_to_effect_hours" in outcomes
        assert isinstance(outcomes["engagement_boost"], float)
        
        # Test re-engagement outcome prediction
        tactics = [{"type": "immediate_reward", "description": "Give bonus"}]
        reengagement_outcomes = await adaptive_service._predict_reengagement_outcomes(tactics, engagement_metrics)
        assert "expected_engagement_increase" in reengagement_outcomes
        assert "probability_of_success" in reengagement_outcomes
        
        # Test adaptation reasoning
        reasoning = await adaptive_service._generate_adaptation_reasoning(
            strategy, EngagementLevel.MODERATE, MotivationState.NEUTRAL
        )
        assert "Balanced Engagement" in reasoning
        assert "moderate" in reasoning
        assert "neutral" in reasoning
    
    @pytest.mark.asyncio
    async def test_error_handling(self, adaptive_service, mock_base_service):
        """Test error handling in various methods"""
        user_id = "child-123"
        
        # Test adapt_gamification_for_user with error
        engagement_metrics = EngagementMetrics(user_id=user_id)
        
        with patch.object(adaptive_service, '_get_or_create_interest_profile', side_effect=Exception("Profile Error")):
            result = await adaptive_service.adapt_gamification_for_user(user_id, engagement_metrics)
            
            # Should return fallback adaptations
            assert result["strategy"] == "fallback"
        
        # Test select_game_elements_by_interest with error
        available_elements = [GameElementType.POINTS, GameElementType.BADGES]
        
        with patch.object(adaptive_service, '_get_or_create_interest_profile', side_effect=Exception("Interest Error")):
            element_scores = await adaptive_service.select_game_elements_by_interest(user_id, available_elements)
            
            # Should return default ranking with neutral scores
            assert len(element_scores) == len(available_elements)
            for element, score in element_scores:
                assert score == 0.5  # Default neutral score
        
        # Test customize_game_experience with error
        preferences = {"themes": ["space"]}
        
        with patch.object(adaptive_service, '_get_or_create_interest_profile', side_effect=Exception("Customization Error")):
            customization = await adaptive_service.customize_game_experience(user_id, preferences)
            
            # Should return default customization
            assert "visual_theme" in customization
            assert customization["visual_theme"]["style"] == "friendly"
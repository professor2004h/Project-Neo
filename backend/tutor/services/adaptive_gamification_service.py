"""
Adaptive Gamification Service - Dynamic game element selection and re-engagement strategies
Task 7.2 implementation
"""
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
import statistics
import json
import random

from utils.logger import logger
from services.llm import make_llm_api_call
from services.supabase import DBConnection
from ..repositories.user_repository import ChildProfileRepository
from ..models.gamification_models import (
    UserGameProfile,
    EngagementMetrics,
    EngagementLevel,
    MotivationState,
    GameElementType,
    GameElementPreference,
    Achievement,
    AchievementType,
    Reward,
    RewardType
)
from ..models.user_models import Subject
from .gamification_service import GamificationService


class InterestProfile(BaseModel):
    """User's interest profile for personalized gamification"""
    user_id: str = Field(min_length=1)
    preferred_themes: List[str] = Field(default_factory=list)  # space, animals, sports, fantasy, etc.
    favorite_colors: List[str] = Field(default_factory=list)
    preferred_difficulty: str = Field(default="moderate")  # easy, moderate, challenging
    learning_style_preferences: Dict[str, float] = Field(default_factory=dict)
    social_preferences: Dict[str, float] = Field(default_factory=dict)  # competitive, collaborative, individual
    reward_preferences: Dict[str, float] = Field(default_factory=dict)
    
    # Behavioral patterns
    optimal_session_length: int = Field(ge=5, le=60, default=15)  # minutes
    preferred_time_of_day: Optional[str] = None  # morning, afternoon, evening
    break_frequency: int = Field(ge=5, le=30, default=10)  # minutes between breaks
    
    # Metadata
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confidence_score: float = Field(ge=0.0, le=1.0, default=0.5)  # How confident we are in this profile
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        """Validate UUID format for user ID"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')


class GamificationStrategy(BaseModel):
    """Gamification strategy configuration"""
    strategy_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    target_engagement_level: EngagementLevel
    target_motivation_state: MotivationState
    
    # Game elements configuration
    enabled_elements: List[GameElementType] = Field(default_factory=list)
    element_weights: Dict[str, float] = Field(default_factory=dict)  # How prominent each element should be
    
    # Timing and frequency
    reward_frequency: str = Field(default="moderate")  # low, moderate, high
    celebration_style: str = Field(default="balanced")  # minimal, balanced, enthusiastic
    challenge_level: str = Field(default="adaptive")  # easy, adaptive, challenging
    
    # Customization
    theme_elements: Dict[str, Any] = Field(default_factory=dict)
    visual_style: Dict[str, Any] = Field(default_factory=dict)
    
    # Effectiveness tracking
    success_rate: float = Field(ge=0.0, le=1.0, default=0.0)
    usage_count: int = Field(ge=0, default=0)
    last_used: Optional[datetime] = None
    
    def apply_to_user(self, user_profile: UserGameProfile, engagement_metrics: EngagementMetrics) -> Dict[str, Any]:
        """Apply this strategy to a user's experience"""
        adaptations = {
            "strategy_name": self.name,
            "elements": {},
            "ui_changes": {},
            "content_changes": {},
            "timing_changes": {}
        }
        
        # Configure enabled game elements
        for element in self.enabled_elements:
            weight = self.element_weights.get(element.value, 0.5)
            adaptations["elements"][element.value] = {
                "enabled": True,
                "prominence": weight,
                "style": self.visual_style.get(element.value, {})
            }
        
        # Configure rewards based on frequency setting
        if self.reward_frequency == "high":
            adaptations["timing_changes"]["reward_threshold"] = 0.5  # Lower threshold for rewards
            adaptations["timing_changes"]["celebration_frequency"] = 1.5
        elif self.reward_frequency == "low":
            adaptations["timing_changes"]["reward_threshold"] = 2.0  # Higher threshold
            adaptations["timing_changes"]["celebration_frequency"] = 0.5
        
        # Apply theme elements
        adaptations["ui_changes"]["theme"] = self.theme_elements
        
        return adaptations


from pydantic import BaseModel, Field, field_validator
import uuid


class AdaptiveGamificationService:
    """
    Service for adaptive gamification strategies and re-engagement
    """
    
    def __init__(self, db: DBConnection, base_gamification_service: GamificationService):
        self.db = db
        self.base_service = base_gamification_service
        self.child_repo = ChildProfileRepository(db)
        
        # Strategy cache
        self.strategies_cache: Dict[str, GamificationStrategy] = {}
        self.user_interests_cache: Dict[str, InterestProfile] = {}
        
        # Predefined strategies
        self.strategies = self._initialize_strategies()
        
        # Game element effectiveness tracking
        self.element_effectiveness: Dict[str, Dict[GameElementType, float]] = {}
        
    async def adapt_gamification_for_user(self, user_id: str, 
                                        current_engagement: EngagementMetrics) -> Dict[str, Any]:
        """
        Adapt gamification strategy based on user's current engagement patterns
        
        Args:
            user_id: Child's user ID
            current_engagement: Current engagement metrics
            
        Returns:
            Adapted gamification configuration
        """
        try:
            # Get user profile and interests
            user_profile = await self.base_service.get_or_create_user_profile(user_id)
            interest_profile = await self._get_or_create_interest_profile(user_id)
            
            # Analyze current state
            engagement_level = current_engagement.calculate_engagement_level()
            motivation_state = current_engagement.calculate_motivation_state()
            
            # Select appropriate strategy
            strategy = await self._select_optimal_strategy(
                user_profile, 
                interest_profile, 
                engagement_level, 
                motivation_state,
                current_engagement
            )
            
            # Apply strategy adaptations
            adaptations = strategy.apply_to_user(user_profile, current_engagement)
            
            # Add personalized elements based on interests
            adaptations = await self._personalize_adaptations(adaptations, interest_profile)
            
            # Track strategy usage
            strategy.usage_count += 1
            strategy.last_used = datetime.now(timezone.utc)
            
            # Log adaptation
            logger.info(f"Applied gamification strategy '{strategy.name}' for user {user_id} "
                       f"(engagement: {engagement_level.value}, motivation: {motivation_state.value})")
            
            return {
                "strategy": strategy.name,
                "adaptations": adaptations,
                "reasoning": await self._generate_adaptation_reasoning(strategy, engagement_level, motivation_state),
                "expected_outcomes": await self._predict_strategy_outcomes(strategy, current_engagement)
            }
            
        except Exception as e:
            logger.error(f"Error adapting gamification for user {user_id}: {str(e)}")
            return await self._get_fallback_adaptations(user_id)
    
    async def select_game_elements_by_interest(self, user_id: str, 
                                             available_elements: List[GameElementType]) -> List[Tuple[GameElementType, float]]:
        """
        Select and rank game elements based on user interests and effectiveness
        
        Args:
            user_id: Child's user ID
            available_elements: Available game elements to choose from
            
        Returns:
            List of (element, preference_score) tuples, ranked by preference
        """
        try:
            # Get user interest profile
            interest_profile = await self._get_or_create_interest_profile(user_id)
            
            # Get historical effectiveness for this user
            user_effectiveness = self.element_effectiveness.get(user_id, {})
            
            # Score each element
            element_scores = []
            
            for element in available_elements:
                # Base preference from interest profile
                base_preference = await self._calculate_element_interest_score(element, interest_profile)
                
                # Historical effectiveness
                effectiveness = user_effectiveness.get(element, 0.5)  # Default neutral effectiveness
                
                # Age appropriateness (get child age)
                child_profile = await self.child_repo.get_by_id(user_id, "child_id")
                age_factor = await self._calculate_age_appropriateness(element, child_profile.get("age", 8) if child_profile else 8)
                
                # Combine scores
                final_score = (base_preference * 0.4 + effectiveness * 0.4 + age_factor * 0.2)
                
                element_scores.append((element, final_score))
            
            # Sort by score descending
            element_scores.sort(key=lambda x: x[1], reverse=True)
            
            logger.info(f"Selected game elements for user {user_id}: {[e.value for e, s in element_scores[:3]]}")
            
            return element_scores
            
        except Exception as e:
            logger.error(f"Error selecting game elements: {str(e)}")
            # Return default ranking
            return [(element, 0.5) for element in available_elements]
    
    async def implement_reengagement_strategy(self, user_id: str, 
                                            engagement_metrics: EngagementMetrics) -> Dict[str, Any]:
        """
        Implement re-engagement strategies for declining motivation
        
        Args:
            user_id: Child's user ID
            engagement_metrics: Current engagement metrics
            
        Returns:
            Re-engagement plan and immediate actions
        """
        try:
            motivation_state = engagement_metrics.calculate_motivation_state()
            engagement_level = engagement_metrics.calculate_engagement_level()
            
            # Determine severity of disengagement
            urgency_level = await self._assess_reengagement_urgency(engagement_metrics, motivation_state)
            
            # Select re-engagement tactics based on urgency and user profile
            tactics = await self._select_reengagement_tactics(user_id, urgency_level, engagement_metrics)
            
            # Create immediate interventions
            immediate_actions = await self._create_immediate_interventions(user_id, tactics)
            
            # Schedule follow-up actions
            follow_up_actions = await self._schedule_followup_actions(user_id, tactics, urgency_level)
            
            # Generate personalized encouragement
            encouragement = await self._generate_personalized_encouragement(user_id, engagement_metrics)
            
            reengagement_plan = {
                "urgency_level": urgency_level,
                "tactics": [t.dict() for t in tactics],
                "immediate_actions": immediate_actions,
                "follow_up_actions": follow_up_actions,
                "encouragement_message": encouragement,
                "timeline": "immediate",
                "expected_outcomes": await self._predict_reengagement_outcomes(tactics, engagement_metrics)
            }
            
            # Log re-engagement attempt
            logger.info(f"Implementing re-engagement strategy for user {user_id} "
                       f"(urgency: {urgency_level}, tactics: {len(tactics)})")
            
            return reengagement_plan
            
        except Exception as e:
            logger.error(f"Error implementing re-engagement strategy: {str(e)}")
            return await self._get_fallback_reengagement_plan(user_id)
    
    async def track_element_effectiveness(self, user_id: str, 
                                        element: GameElementType,
                                        user_response: str,
                                        engagement_change: float) -> None:
        """
        Track the effectiveness of game elements for a user
        
        Args:
            user_id: Child's user ID
            element: Game element that was used
            user_response: positive, negative, or neutral
            engagement_change: Change in engagement score (-1.0 to 1.0)
        """
        try:
            if user_id not in self.element_effectiveness:
                self.element_effectiveness[user_id] = {}
            
            current_effectiveness = self.element_effectiveness[user_id].get(element, 0.5)
            
            # Update effectiveness based on response and engagement change
            if user_response == "positive":
                response_factor = 0.8 + (engagement_change * 0.2)
            elif user_response == "negative":
                response_factor = 0.2 + (engagement_change * 0.2)
            else:  # neutral
                response_factor = 0.5 + (engagement_change * 0.1)
            
            # Weighted average with existing effectiveness
            new_effectiveness = (current_effectiveness * 0.7) + (response_factor * 0.3)
            self.element_effectiveness[user_id][element] = max(0.0, min(1.0, new_effectiveness))
            
            logger.debug(f"Updated element effectiveness for {element.value}: {new_effectiveness:.2f}")
            
        except Exception as e:
            logger.error(f"Error tracking element effectiveness: {str(e)}")
    
    async def customize_game_experience(self, user_id: str, 
                                      customization_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """
        Customize the game experience based on user preferences and interests
        
        Args:
            user_id: Child's user ID
            customization_preferences: User's stated preferences
            
        Returns:
            Customized game configuration
        """
        try:
            # Get interest profile
            interest_profile = await self._get_or_create_interest_profile(user_id)
            
            # Update interest profile with new preferences
            if "themes" in customization_preferences:
                interest_profile.preferred_themes = customization_preferences["themes"]
            
            if "colors" in customization_preferences:
                interest_profile.favorite_colors = customization_preferences["colors"]
            
            if "difficulty" in customization_preferences:
                interest_profile.preferred_difficulty = customization_preferences["difficulty"]
            
            # Generate customized experience
            customization = {
                "visual_theme": await self._create_visual_theme(interest_profile),
                "game_elements": await self._customize_game_elements(interest_profile),
                "content_style": await self._adapt_content_style(interest_profile),
                "interaction_patterns": await self._customize_interactions(interest_profile),
                "reward_system": await self._customize_rewards(interest_profile)
            }
            
            # Save updated interest profile
            interest_profile.last_updated = datetime.now(timezone.utc)
            interest_profile.confidence_score = min(1.0, interest_profile.confidence_score + 0.1)
            self.user_interests_cache[user_id] = interest_profile
            
            logger.info(f"Customized game experience for user {user_id} with {len(customization_preferences)} preferences")
            
            return customization
            
        except Exception as e:
            logger.error(f"Error customizing game experience: {str(e)}")
            return await self._get_default_customization()
    
    # Private helper methods
    
    async def _select_optimal_strategy(self, user_profile: UserGameProfile,
                                     interest_profile: InterestProfile,
                                     engagement_level: EngagementLevel,
                                     motivation_state: MotivationState,
                                     metrics: EngagementMetrics) -> GamificationStrategy:
        """Select the best strategy for current user state"""
        
        # Filter strategies by target engagement/motivation
        suitable_strategies = []
        
        for strategy in self.strategies.values():
            # Check if strategy targets current state or improvement
            if (strategy.target_engagement_level == engagement_level or
                (engagement_level in [EngagementLevel.LOW, EngagementLevel.VERY_LOW] and 
                 strategy.target_engagement_level in [EngagementLevel.MODERATE, EngagementLevel.HIGH])):
                
                if (strategy.target_motivation_state == motivation_state or
                    (motivation_state in [MotivationState.DECLINING, MotivationState.DISENGAGED] and
                     strategy.target_motivation_state in [MotivationState.NEUTRAL, MotivationState.ENGAGED])):
                    
                    suitable_strategies.append(strategy)
        
        if not suitable_strategies:
            # Fallback to balanced strategy
            return self.strategies["balanced_engagement"]
        
        # Score strategies based on user profile and effectiveness
        strategy_scores = []
        
        for strategy in suitable_strategies:
            # Base score from historical success rate
            score = strategy.success_rate
            
            # Bonus for preferred game elements
            for element in strategy.enabled_elements:
                if element in interest_profile.learning_style_preferences:
                    score += interest_profile.learning_style_preferences[element] * 0.1
            
            # Penalty for overused strategies
            if strategy.usage_count > 10:
                score *= 0.9
            
            strategy_scores.append((strategy, score))
        
        # Select best strategy
        strategy_scores.sort(key=lambda x: x[1], reverse=True)
        return strategy_scores[0][0]
    
    async def _get_or_create_interest_profile(self, user_id: str) -> InterestProfile:
        """Get or create interest profile for user"""
        if user_id in self.user_interests_cache:
            return self.user_interests_cache[user_id]
        
        # Try to load from database (placeholder)
        profile = await self._load_interest_profile_from_db(user_id)
        
        if not profile:
            # Create new profile with defaults based on age
            child_profile = await self.child_repo.get_by_id(user_id, "child_id")
            age = child_profile.get("age", 8) if child_profile else 8
            
            profile = InterestProfile(
                user_id=user_id,
                preferred_themes=await self._get_age_appropriate_themes(age),
                optimal_session_length=await self._get_age_appropriate_session_length(age)
            )
        
        self.user_interests_cache[user_id] = profile
        return profile
    
    async def _calculate_element_interest_score(self, element: GameElementType, 
                                              interest_profile: InterestProfile) -> float:
        """Calculate interest score for a game element"""
        # Base scores for different elements
        base_scores = {
            GameElementType.POINTS: 0.7,
            GameElementType.BADGES: 0.8,
            GameElementType.PROGRESS_BARS: 0.6,
            GameElementType.CHALLENGES: 0.7,
            GameElementType.REWARDS: 0.9,
            GameElementType.CELEBRATIONS: 0.8,
            GameElementType.CUSTOMIZATION: 0.6,
            GameElementType.SOCIAL: 0.5,
            GameElementType.STORYTELLING: 0.7,
            GameElementType.LEADERBOARDS: 0.4
        }
        
        base_score = base_scores.get(element, 0.5)
        
        # Modify based on interests
        if element == GameElementType.STORYTELLING and "fantasy" in interest_profile.preferred_themes:
            base_score += 0.2
        
        if element == GameElementType.CUSTOMIZATION and len(interest_profile.favorite_colors) > 0:
            base_score += 0.1
        
        if element == GameElementType.CHALLENGES and interest_profile.preferred_difficulty == "challenging":
            base_score += 0.15
        
        return min(1.0, base_score)
    
    async def _calculate_age_appropriateness(self, element: GameElementType, age: int) -> float:
        """Calculate age appropriateness factor for game element"""
        age_factors = {
            # Younger children (5-7)
            5: {
                GameElementType.POINTS: 0.6,
                GameElementType.BADGES: 0.9,
                GameElementType.CELEBRATIONS: 1.0,
                GameElementType.REWARDS: 0.9,
                GameElementType.STORYTELLING: 0.8,
                GameElementType.CUSTOMIZATION: 0.7,
                GameElementType.PROGRESS_BARS: 0.5,
                GameElementType.LEADERBOARDS: 0.2,
                GameElementType.SOCIAL: 0.3
            },
            # Middle children (8-10)
            8: {
                GameElementType.POINTS: 0.8,
                GameElementType.BADGES: 0.9,
                GameElementType.CHALLENGES: 0.8,
                GameElementType.PROGRESS_BARS: 0.8,
                GameElementType.REWARDS: 0.8,
                GameElementType.CUSTOMIZATION: 0.9,
                GameElementType.STORYTELLING: 0.7,
                GameElementType.SOCIAL: 0.6,
                GameElementType.LEADERBOARDS: 0.5
            },
            # Older children (11-12)
            11: {
                GameElementType.POINTS: 0.9,
                GameElementType.BADGES: 0.8,
                GameElementType.CHALLENGES: 0.9,
                GameElementType.PROGRESS_BARS: 0.8,
                GameElementType.LEADERBOARDS: 0.8,
                GameElementType.SOCIAL: 0.8,
                GameElementType.CUSTOMIZATION: 0.9,
                GameElementType.STORYTELLING: 0.6,
                GameElementType.REWARDS: 0.7
            }
        }
        
        # Find closest age group
        closest_age = min(age_factors.keys(), key=lambda x: abs(x - age))
        factors = age_factors[closest_age]
        
        return factors.get(element, 0.5)
    
    async def _assess_reengagement_urgency(self, metrics: EngagementMetrics, 
                                         motivation_state: MotivationState) -> str:
        """Assess urgency level for re-engagement"""
        if motivation_state == MotivationState.DISENGAGED:
            return "critical"
        elif motivation_state == MotivationState.DECLINING:
            if metrics.engagement_score < 0.3:
                return "high"
            else:
                return "moderate"
        elif metrics.engagement_score < 0.4:
            return "moderate"
        else:
            return "low"
    
    async def _select_reengagement_tactics(self, user_id: str, urgency_level: str, 
                                         metrics: EngagementMetrics) -> List[Dict[str, Any]]:
        """Select appropriate re-engagement tactics"""
        tactics = []
        
        if urgency_level == "critical":
            tactics.extend([
                {"type": "immediate_reward", "description": "Provide immediate positive reinforcement"},
                {"type": "simplify_content", "description": "Reduce difficulty to rebuild confidence"},
                {"type": "personal_message", "description": "Send encouraging personal message"},
                {"type": "break_suggestion", "description": "Suggest taking a short break"}
            ])
        elif urgency_level == "high":
            tactics.extend([
                {"type": "boost_rewards", "description": "Increase reward frequency temporarily"},
                {"type": "introduce_novelty", "description": "Introduce new game elements"},
                {"type": "adjust_difficulty", "description": "Fine-tune content difficulty"},
                {"type": "celebration_focus", "description": "Emphasize celebrations and achievements"}
            ])
        elif urgency_level == "moderate":
            tactics.extend([
                {"type": "variety_injection", "description": "Add variety to activities"},
                {"type": "progress_highlighting", "description": "Highlight recent progress"},
                {"type": "social_elements", "description": "Add collaborative or competitive elements"}
            ])
        else:  # low urgency
            tactics.extend([
                {"type": "gentle_encouragement", "description": "Provide gentle encouragement"},
                {"type": "goal_setting", "description": "Help set achievable short-term goals"}
            ])
        
        return tactics[:3]  # Return top 3 tactics
    
    async def _create_immediate_interventions(self, user_id: str, tactics: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Create immediate interventions based on tactics"""
        interventions = []
        
        for tactic in tactics:
            if tactic["type"] == "immediate_reward":
                interventions.append({
                    "action": "award_bonus_points",
                    "details": {"points": 50, "message": "Here's a bonus for your efforts!"}
                })
            elif tactic["type"] == "personal_message":
                message = await self._generate_personalized_encouragement(user_id, None)
                interventions.append({
                    "action": "show_encouragement",
                    "details": {"message": message}
                })
            elif tactic["type"] == "simplify_content":
                interventions.append({
                    "action": "adjust_difficulty",
                    "details": {"new_difficulty": "easier", "temporary": True}
                })
            elif tactic["type"] == "boost_rewards":
                interventions.append({
                    "action": "increase_reward_frequency",
                    "details": {"multiplier": 1.5, "duration_hours": 24}
                })
        
        return interventions
    
    async def _schedule_followup_actions(self, user_id: str, tactics: List[Dict[str, Any]], 
                                       urgency_level: str) -> List[Dict[str, Any]]:
        """Schedule follow-up actions"""
        follow_ups = []
        
        # Schedule engagement check
        if urgency_level in ["critical", "high"]:
            check_interval = 2  # hours
        else:
            check_interval = 24  # hours
        
        follow_ups.append({
            "action": "engagement_check",
            "scheduled_at": datetime.now(timezone.utc) + timedelta(hours=check_interval),
            "details": {"type": "reengagement_followup"}
        })
        
        # Schedule strategy adjustment
        follow_ups.append({
            "action": "strategy_review",
            "scheduled_at": datetime.now(timezone.utc) + timedelta(days=1),
            "details": {"review_effectiveness": True}
        })
        
        return follow_ups
    
    async def _generate_personalized_encouragement(self, user_id: str, 
                                                 engagement_metrics: Optional[EngagementMetrics]) -> str:
        """Generate personalized encouragement message"""
        try:
            # Get child profile for personalization
            child_profile = await self.child_repo.get_by_id(user_id, "child_id")
            child_name = child_profile.get("name", "there") if child_profile else "there"
            child_age = child_profile.get("age", 8) if child_profile else 8
            
            # Get user's game profile for context
            game_profile = await self.base_service.get_or_create_user_profile(user_id)
            
            # Build context for AI message generation
            context = {
                "child_name": child_name,
                "child_age": child_age,
                "current_streak": game_profile.current_learning_streak,
                "total_points": game_profile.total_points,
                "level": game_profile.level,
                "badges_earned": len(game_profile.earned_badges),
                "recent_engagement": engagement_metrics.engagement_score if engagement_metrics else 0.5
            }
            
            system_prompt = f"""You are a supportive AI tutor creating an encouraging message for {child_name}, a {child_age}-year-old child.

Create a warm, age-appropriate encouragement message that:
- Uses their name naturally
- Celebrates their progress and effort
- Motivates them to continue learning
- Is positive and supportive
- Matches their age level (simple language for younger kids, more sophisticated for older)

Keep the message to 1-2 sentences and make it feel personal and genuine."""

            user_message = f"Create an encouraging message for this child: {json.dumps(context)}"
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            response = await make_llm_api_call(
                messages=messages,
                model_name="gpt-4",
                temperature=0.8,
                max_tokens=100
            )
            
            encouragement = response.choices[0].message.content.strip()
            return encouragement
            
        except Exception as e:
            logger.warning(f"AI encouragement generation failed: {str(e)}")
            # Fallback messages
            fallback_messages = [
                f"Great job, {child_name}! Keep up the wonderful learning!",
                f"You're doing amazing, {child_name}! Every step counts!",
                f"I'm proud of your effort, {child_name}! Let's keep going!",
                f"You're becoming such a great learner, {child_name}!"
            ]
            return random.choice(fallback_messages)
    
    def _initialize_strategies(self) -> Dict[str, GamificationStrategy]:
        """Initialize predefined gamification strategies"""
        strategies = {}
        
        # High engagement strategy
        strategies["high_engagement"] = GamificationStrategy(
            name="High Engagement Booster",
            description="For users with already high engagement",
            target_engagement_level=EngagementLevel.HIGH,
            target_motivation_state=MotivationState.ENGAGED,
            enabled_elements=[
                GameElementType.CHALLENGES,
                GameElementType.LEADERBOARDS,
                GameElementType.BADGES,
                GameElementType.PROGRESS_BARS
            ],
            element_weights={
                "challenges": 0.8,
                "leaderboards": 0.7,
                "badges": 0.6,
                "progress_bars": 0.5
            },
            reward_frequency="moderate",
            challenge_level="challenging"
        )
        
        # Re-engagement strategy
        strategies["reengagement"] = GamificationStrategy(
            name="Re-engagement Focus",
            description="For users with declining engagement",
            target_engagement_level=EngagementLevel.LOW,
            target_motivation_state=MotivationState.DECLINING,
            enabled_elements=[
                GameElementType.REWARDS,
                GameElementType.CELEBRATIONS,
                GameElementType.CUSTOMIZATION,
                GameElementType.STORYTELLING
            ],
            element_weights={
                "rewards": 0.9,
                "celebrations": 0.8,
                "customization": 0.7,
                "storytelling": 0.6
            },
            reward_frequency="high",
            celebration_style="enthusiastic",
            challenge_level="easy"
        )
        
        # Balanced strategy
        strategies["balanced_engagement"] = GamificationStrategy(
            name="Balanced Engagement",
            description="Balanced approach for moderate engagement",
            target_engagement_level=EngagementLevel.MODERATE,
            target_motivation_state=MotivationState.NEUTRAL,
            enabled_elements=[
                GameElementType.POINTS,
                GameElementType.BADGES,
                GameElementType.PROGRESS_BARS,
                GameElementType.REWARDS,
                GameElementType.CELEBRATIONS
            ],
            element_weights={
                "points": 0.7,
                "badges": 0.6,
                "progress_bars": 0.6,
                "rewards": 0.7,
                "celebrations": 0.5
            },
            reward_frequency="moderate",
            challenge_level="adaptive"
        )
        
        # Social engagement strategy
        strategies["social_focus"] = GamificationStrategy(
            name="Social Learning",
            description="Emphasizes social and collaborative elements",
            target_engagement_level=EngagementLevel.MODERATE,
            target_motivation_state=MotivationState.ENGAGED,
            enabled_elements=[
                GameElementType.SOCIAL,
                GameElementType.LEADERBOARDS,
                GameElementType.BADGES,
                GameElementType.CHALLENGES
            ],
            element_weights={
                "social": 0.8,
                "leaderboards": 0.7,
                "badges": 0.6,
                "challenges": 0.5
            },
            reward_frequency="moderate"
        )
        
        return strategies
    
    async def _get_age_appropriate_themes(self, age: int) -> List[str]:
        """Get age-appropriate theme suggestions"""
        if age <= 7:
            return ["animals", "fairy_tales", "colors", "nature"]
        elif age <= 10:
            return ["adventure", "space", "dinosaurs", "superheroes", "magic"]
        else:
            return ["exploration", "mystery", "technology", "mythology", "science"]
    
    async def _get_age_appropriate_session_length(self, age: int) -> int:
        """Get age-appropriate session length in minutes"""
        if age <= 6:
            return 10
        elif age <= 8:
            return 15
        elif age <= 10:
            return 20
        else:
            return 25
    
    # Placeholder methods for future database integration
    
    async def _load_interest_profile_from_db(self, user_id: str) -> Optional[InterestProfile]:
        """Load interest profile from database (placeholder)"""
        return None
    
    async def _save_interest_profile_to_db(self, profile: InterestProfile) -> None:
        """Save interest profile to database (placeholder)"""
        pass
    
    async def _get_fallback_adaptations(self, user_id: str) -> Dict[str, Any]:
        """Get fallback adaptations when main system fails"""
        return {
            "strategy": "fallback",
            "adaptations": {
                "elements": {
                    "points": {"enabled": True, "prominence": 0.7},
                    "celebrations": {"enabled": True, "prominence": 0.8}
                }
            },
            "reasoning": "Using safe fallback strategy",
            "expected_outcomes": {"engagement_boost": 0.1}
        }
    
    async def _get_fallback_reengagement_plan(self, user_id: str) -> Dict[str, Any]:
        """Get fallback re-engagement plan"""
        return {
            "urgency_level": "moderate",
            "tactics": [{"type": "encouragement", "description": "Provide positive encouragement"}],
            "immediate_actions": [{"action": "show_encouragement", "details": {"message": "Keep up the great work!"}}],
            "follow_up_actions": [],
            "encouragement_message": "You're doing great! Let's keep learning together!",
            "timeline": "immediate"
        }
    
    async def _get_default_customization(self) -> Dict[str, Any]:
        """Get default customization when system fails"""
        return {
            "visual_theme": {"colors": ["blue", "green"], "style": "friendly"},
            "game_elements": {"points": True, "badges": True},
            "content_style": "balanced",
            "interaction_patterns": "standard",
            "reward_system": "balanced"
        }
    
    # Additional helper methods for customization
    
    async def _create_visual_theme(self, interest_profile: InterestProfile) -> Dict[str, Any]:
        """Create visual theme based on interests"""
        theme = {
            "primary_colors": interest_profile.favorite_colors[:2] if interest_profile.favorite_colors else ["blue", "green"],
            "theme_name": interest_profile.preferred_themes[0] if interest_profile.preferred_themes else "default",
            "style": "friendly"
        }
        return theme
    
    async def _customize_game_elements(self, interest_profile: InterestProfile) -> Dict[str, Any]:
        """Customize game elements based on interests"""
        return {
            "badges": {"style": "colorful" if interest_profile.favorite_colors else "standard"},
            "progress_bars": {"animated": True},
            "celebrations": {"intensity": "moderate"}
        }
    
    async def _adapt_content_style(self, interest_profile: InterestProfile) -> Dict[str, Any]:
        """Adapt content style based on preferences"""
        return {
            "difficulty": interest_profile.preferred_difficulty,
            "session_length": interest_profile.optimal_session_length,
            "break_frequency": interest_profile.break_frequency
        }
    
    async def _customize_interactions(self, interest_profile: InterestProfile) -> Dict[str, Any]:
        """Customize interaction patterns"""
        return {
            "feedback_style": "encouraging",
            "hint_frequency": "adaptive",
            "celebration_timing": "immediate"
        }
    
    async def _customize_rewards(self, interest_profile: InterestProfile) -> Dict[str, Any]:
        """Customize reward system"""
        return {
            "reward_types": ["points", "badges", "celebrations"],
            "frequency": "balanced",
            "surprise_factor": 0.2
        }
    
    async def _generate_adaptation_reasoning(self, strategy: GamificationStrategy, 
                                           engagement_level: EngagementLevel,
                                           motivation_state: MotivationState) -> str:
        """Generate reasoning for why this strategy was selected"""
        return f"Selected '{strategy.name}' strategy to address {engagement_level.value} engagement and {motivation_state.value} motivation state."
    
    async def _predict_strategy_outcomes(self, strategy: GamificationStrategy, 
                                       current_engagement: EngagementMetrics) -> Dict[str, float]:
        """Predict expected outcomes of applying this strategy"""
        return {
            "engagement_boost": 0.15,
            "motivation_improvement": 0.2,
            "completion_rate_increase": 0.1,
            "time_to_effect_hours": 2
        }
    
    async def _predict_reengagement_outcomes(self, tactics: List[Dict[str, Any]], 
                                           current_metrics: EngagementMetrics) -> Dict[str, Any]:
        """Predict outcomes of re-engagement tactics"""
        return {
            "expected_engagement_increase": 0.2,
            "probability_of_success": 0.75,
            "estimated_time_to_improvement": "2-4 hours"
        }
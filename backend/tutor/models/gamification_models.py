"""
Gamification and achievement models for Cambridge AI Tutor
Tasks 7.1 and 7.2 implementation
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, Any, Union
from datetime import datetime, timezone, timedelta
from enum import Enum
import uuid

from .user_models import Subject
from .progress_models import ActivityType


class AchievementType(str, Enum):
    """Achievement type enumeration"""
    LEARNING_STREAK = "learning_streak"
    SUBJECT_MASTERY = "subject_mastery"
    ACTIVITY_COMPLETION = "activity_completion"
    IMPROVEMENT = "improvement"
    CONSISTENCY = "consistency"
    SPEED = "speed"
    ACCURACY = "accuracy"
    EXPLORATION = "exploration"
    PERSISTENCE = "persistence"
    MILESTONE = "milestone"


class BadgeCategory(str, Enum):
    """Badge category enumeration"""
    ACADEMIC = "academic"
    BEHAVIORAL = "behavioral"
    SOCIAL = "social"
    SPECIAL = "special"
    SEASONAL = "seasonal"


class RewardType(str, Enum):
    """Reward type enumeration"""
    POINTS = "points"
    BADGE = "badge"
    UNLOCK = "unlock"
    PRIVILEGE = "privilege"
    CUSTOMIZATION = "customization"
    CELEBRATION = "celebration"


class EngagementLevel(str, Enum):
    """Engagement level enumeration"""
    VERY_HIGH = "very_high"    # 90-100%
    HIGH = "high"              # 80-89%
    MODERATE = "moderate"      # 60-79%
    LOW = "low"                # 40-59%
    VERY_LOW = "very_low"      # 0-39%


class MotivationState(str, Enum):
    """Motivation state enumeration"""
    EXCITED = "excited"
    ENGAGED = "engaged"
    NEUTRAL = "neutral"
    DECLINING = "declining"
    DISENGAGED = "disengaged"


class GameElementType(str, Enum):
    """Game element type enumeration"""
    POINTS = "points"
    BADGES = "badges"
    LEADERBOARDS = "leaderboards"
    PROGRESS_BARS = "progress_bars"
    CHALLENGES = "challenges"
    REWARDS = "rewards"
    CELEBRATIONS = "celebrations"
    CUSTOMIZATION = "customization"
    SOCIAL = "social"
    STORYTELLING = "storytelling"


class Badge(BaseModel):
    """Badge model for gamification achievements"""
    badge_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=500)
    category: BadgeCategory
    icon_url: Optional[str] = None
    color_scheme: Dict[str, str] = Field(default_factory=dict)
    
    # Requirements for earning
    required_achievements: List[str] = Field(default_factory=list)
    required_points: int = Field(ge=0, default=0)
    required_streak: int = Field(ge=0, default=0)
    subject_specific: Optional[Subject] = None
    
    # Rarity and prestige
    rarity_level: int = Field(ge=1, le=5, default=1)  # 1=common, 5=legendary
    is_secret: bool = False
    is_limited_time: bool = False
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    def get_display_info(self) -> Dict[str, Any]:
        """Get display information for the badge"""
        return {
            "badge_id": self.badge_id,
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "icon_url": self.icon_url,
            "rarity_level": self.rarity_level,
            "is_secret": self.is_secret,
            "color_scheme": self.color_scheme
        }


class Achievement(BaseModel):
    """Achievement model for gamification milestones"""
    achievement_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(min_length=1)
    achievement_type: AchievementType
    title: str = Field(min_length=1, max_length=150)
    description: str = Field(min_length=1, max_length=500)
    
    # Achievement criteria
    target_value: Union[int, float] = Field(default=1)
    current_value: Union[int, float] = Field(default=0)
    is_completed: bool = False
    completion_percentage: float = Field(ge=0.0, le=1.0, default=0.0)
    
    # Context
    subject: Optional[Subject] = None
    activity_type: Optional[ActivityType] = None
    difficulty_level: Optional[int] = Field(ge=1, le=5, default=None)
    
    # Rewards
    points_reward: int = Field(ge=0, default=10)
    badge_rewards: List[str] = Field(default_factory=list)  # Badge IDs
    unlock_rewards: List[str] = Field(default_factory=list)  # What gets unlocked
    
    # Timing
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Progress tracking
    progress_milestones: List[Dict[str, Any]] = Field(default_factory=list)
    last_progress_update: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        """Validate UUID format for user ID"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')
    
    def update_progress(self, new_value: Union[int, float]) -> bool:
        """
        Update achievement progress
        
        Args:
            new_value: New progress value
            
        Returns:
            True if achievement was completed
        """
        old_value = self.current_value
        self.current_value = max(self.current_value, new_value)  # Only increase
        self.completion_percentage = min(self.current_value / self.target_value, 1.0) if self.target_value > 0 else 0.0
        self.last_progress_update = datetime.now(timezone.utc)
        
        # Check if completed
        if not self.is_completed and self.current_value >= self.target_value:
            self.is_completed = True
            self.completed_at = datetime.now(timezone.utc)
            self.completion_percentage = 1.0
            return True
        
        return False
    
    def add_milestone(self, milestone_value: Union[int, float], description: str) -> None:
        """Add a progress milestone"""
        milestone = {
            "value": milestone_value,
            "description": description,
            "achieved": self.current_value >= milestone_value,
            "achieved_at": datetime.now(timezone.utc).isoformat() if self.current_value >= milestone_value else None
        }
        
        # Update existing milestone or add new one
        for i, existing in enumerate(self.progress_milestones):
            if existing["value"] == milestone_value:
                self.progress_milestones[i] = milestone
                return
        
        self.progress_milestones.append(milestone)
        self.progress_milestones.sort(key=lambda x: x["value"])
    
    def get_next_milestone(self) -> Optional[Dict[str, Any]]:
        """Get the next unachieved milestone"""
        for milestone in self.progress_milestones:
            if not milestone["achieved"]:
                return milestone
        return None
    
    def is_expired(self) -> bool:
        """Check if achievement has expired"""
        if self.expires_at:
            return datetime.now(timezone.utc) > self.expires_at
        return False


class UserGameProfile(BaseModel):
    """User's gamification profile and statistics"""
    user_id: str = Field(min_length=1)
    total_points: int = Field(ge=0, default=0)
    level: int = Field(ge=1, default=1)
    experience_points: int = Field(ge=0, default=0)
    points_to_next_level: int = Field(ge=0, default=100)
    
    # Achievements and badges
    completed_achievements: List[str] = Field(default_factory=list)  # Achievement IDs
    earned_badges: List[str] = Field(default_factory=list)  # Badge IDs
    active_achievements: List[str] = Field(default_factory=list)  # Achievement IDs
    
    # Streaks and statistics
    current_learning_streak: int = Field(ge=0, default=0)
    longest_learning_streak: int = Field(ge=0, default=0)
    total_activities_completed: int = Field(ge=0, default=0)
    total_time_spent_minutes: int = Field(ge=0, default=0)
    
    # Subject-specific progress
    subject_levels: Dict[str, int] = Field(default_factory=dict)
    subject_points: Dict[str, int] = Field(default_factory=dict)
    
    # Engagement metrics
    engagement_level: EngagementLevel = EngagementLevel.MODERATE
    motivation_state: MotivationState = MotivationState.NEUTRAL
    last_active: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Preferences
    preferred_game_elements: List[GameElementType] = Field(default_factory=list)
    celebration_preferences: Dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        """Validate UUID format for user ID"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')
    
    def add_points(self, points: int, subject: Subject = None) -> Dict[str, Any]:
        """
        Add points to the user's profile
        
        Args:
            points: Points to add
            subject: Subject context for points
            
        Returns:
            Level up information if applicable
        """
        old_level = self.level
        self.total_points += points
        self.experience_points += points
        
        # Add subject-specific points
        if subject:
            subject_key = subject.value
            self.subject_points[subject_key] = self.subject_points.get(subject_key, 0) + points
        
        # Check for level up
        level_up_info = self._check_level_up()
        
        self.updated_at = datetime.now(timezone.utc)
        
        return {
            "points_added": points,
            "total_points": self.total_points,
            "old_level": old_level,
            "new_level": self.level,
            "level_up": level_up_info["leveled_up"],
            "level_up_rewards": level_up_info.get("rewards", [])
        }
    
    def _check_level_up(self) -> Dict[str, Any]:
        """Check if user has leveled up and handle level progression"""
        # Simple level calculation: 100 XP for level 1, +50 XP for each subsequent level
        required_xp = 100 + (self.level - 1) * 50
        
        leveled_up = False
        rewards = []
        
        while self.experience_points >= required_xp:
            self.level += 1
            self.experience_points -= required_xp
            leveled_up = True
            
            # Add level-up rewards
            level_rewards = self._get_level_rewards(self.level)
            rewards.extend(level_rewards)
            
            # Update required XP for next level
            required_xp = 100 + (self.level - 1) * 50
        
        # Update points to next level
        self.points_to_next_level = required_xp - self.experience_points
        
        return {
            "leveled_up": leveled_up,
            "rewards": rewards
        }
    
    def _get_level_rewards(self, level: int) -> List[Dict[str, Any]]:
        """Get rewards for reaching a specific level"""
        rewards = []
        
        # Every 5 levels: unlock new customization options
        if level % 5 == 0:
            rewards.append({
                "type": "customization",
                "item": f"level_{level}_theme",
                "description": f"Unlocked new theme for reaching level {level}!"
            })
        
        # Every 10 levels: special badge
        if level % 10 == 0:
            rewards.append({
                "type": "badge",
                "item": f"level_{level}_master",
                "description": f"Master Badge for reaching level {level}!"
            })
        
        # Special milestone rewards
        milestone_rewards = {
            5: {"type": "privilege", "item": "avatar_selection", "description": "Choose your learning avatar!"},
            10: {"type": "unlock", "item": "advanced_challenges", "description": "Advanced challenges unlocked!"},
            20: {"type": "privilege", "item": "mentor_mode", "description": "Help other students learn!"},
            50: {"type": "badge", "item": "legendary_learner", "description": "Legendary Learner status achieved!"}
        }
        
        if level in milestone_rewards:
            rewards.append(milestone_rewards[level])
        
        return rewards
    
    def add_achievement(self, achievement_id: str) -> None:
        """Add a completed achievement"""
        if achievement_id not in self.completed_achievements:
            self.completed_achievements.append(achievement_id)
            
        if achievement_id in self.active_achievements:
            self.active_achievements.remove(achievement_id)
        
        self.updated_at = datetime.now(timezone.utc)
    
    def add_badge(self, badge_id: str) -> None:
        """Add an earned badge"""
        if badge_id not in self.earned_badges:
            self.earned_badges.append(badge_id)
        
        self.updated_at = datetime.now(timezone.utc)
    
    def update_engagement(self, new_level: EngagementLevel, new_motivation: MotivationState) -> None:
        """Update engagement and motivation state"""
        self.engagement_level = new_level
        self.motivation_state = new_motivation
        self.last_active = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def get_profile_summary(self) -> Dict[str, Any]:
        """Get a summary of the user's gamification profile"""
        return {
            "user_id": self.user_id,
            "level": self.level,
            "total_points": self.total_points,
            "badges_earned": len(self.earned_badges),
            "achievements_completed": len(self.completed_achievements),
            "current_streak": self.current_learning_streak,
            "longest_streak": self.longest_learning_streak,
            "engagement_level": self.engagement_level.value,
            "motivation_state": self.motivation_state.value,
            "progress_to_next_level": {
                "current_xp": self.experience_points,
                "needed_xp": self.points_to_next_level,
                "percentage": (self.experience_points / (self.experience_points + self.points_to_next_level)) * 100
            }
        }


class Reward(BaseModel):
    """Reward model for gamification incentives"""
    reward_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = Field(min_length=1)
    reward_type: RewardType
    title: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=300)
    
    # Reward content
    points_value: int = Field(ge=0, default=0)
    badge_id: Optional[str] = None
    unlock_content: Dict[str, Any] = Field(default_factory=dict)
    
    # Conditions
    earned_from: str = Field(description="Source of reward (achievement, activity, etc.)")
    earned_from_id: str = Field(description="ID of the source")
    
    # Status
    is_claimed: bool = False
    claimed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        """Validate UUID format for user ID"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')
    
    def claim_reward(self) -> bool:
        """
        Claim the reward
        
        Returns:
            True if successfully claimed, False if already claimed or expired
        """
        if self.is_claimed:
            return False
        
        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False
        
        self.is_claimed = True
        self.claimed_at = datetime.now(timezone.utc)
        return True
    
    def is_expired(self) -> bool:
        """Check if reward has expired"""
        if self.expires_at:
            return datetime.now(timezone.utc) > self.expires_at
        return False


class EngagementMetrics(BaseModel):
    """Engagement metrics for motivation assessment"""
    user_id: str = Field(min_length=1)
    measurement_period_days: int = Field(ge=1, le=30, default=7)
    
    # Activity metrics
    sessions_completed: int = Field(ge=0, default=0)
    total_time_spent_minutes: int = Field(ge=0, default=0)
    average_session_duration: float = Field(ge=0.0, default=0.0)
    activities_started: int = Field(ge=0, default=0)
    activities_completed: int = Field(ge=0, default=0)
    completion_rate: float = Field(ge=0.0, le=1.0, default=0.0)
    
    # Interaction metrics
    help_requests: int = Field(ge=0, default=0)
    hints_used: int = Field(ge=0, default=0)
    positive_feedback_given: int = Field(ge=0, default=0)
    negative_feedback_given: int = Field(ge=0, default=0)
    
    # Performance metrics
    average_accuracy: float = Field(ge=0.0, le=1.0, default=0.0)
    improvement_trend: float = Field(default=0.0)  # Can be negative
    consistency_score: float = Field(ge=0.0, le=1.0, default=0.0)
    
    # Behavioral metrics
    early_exits: int = Field(ge=0, default=0)
    long_pauses: int = Field(ge=0, default=0)
    rapid_clicking: int = Field(ge=0, default=0)
    attention_span_minutes: float = Field(ge=0.0, default=15.0)
    
    # Engagement indicators
    voluntary_activities: int = Field(ge=0, default=0)
    exploration_activities: int = Field(ge=0, default=0)
    repeated_activities: int = Field(ge=0, default=0)
    social_interactions: int = Field(ge=0, default=0)
    
    # Calculated scores
    engagement_score: float = Field(ge=0.0, le=1.0, default=0.5)
    motivation_score: float = Field(ge=0.0, le=1.0, default=0.5)
    risk_score: float = Field(ge=0.0, le=1.0, default=0.0)  # Risk of disengagement
    
    # Metadata
    calculated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    period_start: datetime = Field(default_factory=lambda: datetime.now(timezone.utc) - timedelta(days=7))
    period_end: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        """Validate UUID format for user ID"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')
    
    def calculate_engagement_level(self) -> EngagementLevel:
        """Calculate overall engagement level"""
        if self.engagement_score >= 0.9:
            return EngagementLevel.VERY_HIGH
        elif self.engagement_score >= 0.8:
            return EngagementLevel.HIGH
        elif self.engagement_score >= 0.6:
            return EngagementLevel.MODERATE
        elif self.engagement_score >= 0.4:
            return EngagementLevel.LOW
        else:
            return EngagementLevel.VERY_LOW
    
    def calculate_motivation_state(self) -> MotivationState:
        """Calculate motivation state based on metrics"""
        # Consider engagement score, improvement trend, and behavioral indicators
        if self.motivation_score >= 0.9 and self.improvement_trend > 0.1:
            return MotivationState.EXCITED
        elif self.motivation_score >= 0.7:
            return MotivationState.ENGAGED
        elif self.motivation_score >= 0.5 and self.improvement_trend >= 0:
            return MotivationState.NEUTRAL
        elif self.motivation_score >= 0.3 or self.improvement_trend < -0.1:
            return MotivationState.DECLINING
        else:
            return MotivationState.DISENGAGED
    
    def get_engagement_insights(self) -> List[str]:
        """Get insights about engagement patterns"""
        insights = []
        
        if self.completion_rate < 0.5:
            insights.append("Student tends to start activities but not finish them")
        
        if self.help_requests > self.activities_completed * 0.5:
            insights.append("Student frequently requests help - may need easier content")
        
        if self.early_exits > 3:
            insights.append("Student often exits activities early - may indicate frustration")
        
        if self.voluntary_activities > self.activities_completed * 0.3:
            insights.append("Student shows high intrinsic motivation by choosing extra activities")
        
        if self.average_session_duration < 5:
            insights.append("Very short sessions - may need more engaging content")
        
        if self.improvement_trend > 0.2:
            insights.append("Strong learning progress - student is improving quickly")
        
        return insights
    
    def get_recommendations(self) -> List[str]:
        """Get recommendations for improving engagement"""
        recommendations = []
        
        engagement_level = self.calculate_engagement_level()
        motivation_state = self.calculate_motivation_state()
        
        if engagement_level in [EngagementLevel.LOW, EngagementLevel.VERY_LOW]:
            recommendations.append("Consider introducing more game elements and rewards")
            recommendations.append("Reduce session length and increase frequency")
        
        if motivation_state == MotivationState.DECLINING:
            recommendations.append("Provide more positive feedback and encouragement")
            recommendations.append("Introduce easier content to rebuild confidence")
        
        if self.completion_rate < 0.6:
            recommendations.append("Break activities into smaller, manageable chunks")
        
        if self.help_requests > 5:
            recommendations.append("Provide more scaffolding and hints upfront")
        
        return recommendations[:3]  # Return top 3 recommendations


class GameElementPreference(BaseModel):
    """User preferences for game elements"""
    user_id: str = Field(min_length=1)
    element_type: GameElementType
    preference_score: float = Field(ge=0.0, le=1.0, default=0.5)
    effectiveness_score: float = Field(ge=0.0, le=1.0, default=0.5)
    usage_count: int = Field(ge=0, default=0)
    positive_responses: int = Field(ge=0, default=0)
    negative_responses: int = Field(ge=0, default=0)
    
    # Context
    age_when_measured: int = Field(ge=5, le=12)
    subjects_context: List[Subject] = Field(default_factory=list)
    
    # Metadata
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        """Validate UUID format for user ID"""
        try:
            uuid.UUID(v)
            return v
        except ValueError:
            raise ValueError('Invalid UUID format')
    
    def update_preference(self, positive_response: bool) -> None:
        """Update preference based on user response"""
        self.usage_count += 1
        
        if positive_response:
            self.positive_responses += 1
        else:
            self.negative_responses += 1
        
        # Update scores based on response ratio
        if self.usage_count > 0:
            positive_ratio = self.positive_responses / self.usage_count
            self.preference_score = positive_ratio
            self.effectiveness_score = positive_ratio
        
        self.last_updated = datetime.now(timezone.utc)
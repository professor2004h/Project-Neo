"""
PersonalizationEngine - Adapts content to individual learning patterns and performance
Task 4.3 implementation
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
import statistics
import json

from utils.logger import logger
from services.llm import make_llm_api_call
from ..repositories.user_repository import ChildProfileRepository
from ..repositories.curriculum_repository import CurriculumTopicRepository
from ..models.user_models import Subject, LearningStyle
from ..models.curriculum_models import DifficultyLevel, ActivityType


class LearningPattern:
    """Represents a child's learning pattern analysis"""
    
    def __init__(self, user_id: str):
        self.user_id = user_id
        self.preferred_learning_style: Optional[LearningStyle] = None
        self.detected_strengths: List[str] = []
        self.areas_for_improvement: List[str] = []
        self.optimal_difficulty_level: float = 1.0
        self.engagement_preferences: Dict[str, float] = {}
        self.learning_pace: str = "moderate"  # slow, moderate, fast
        self.attention_span_minutes: int = 15
        self.best_time_patterns: List[str] = []
        self.response_accuracy_trends: Dict[str, float] = {}
        self.confidence_levels: Dict[str, float] = {}
        self.last_updated: datetime = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/transmission"""
        return {
            "user_id": self.user_id,
            "preferred_learning_style": self.preferred_learning_style.value if self.preferred_learning_style else None,
            "detected_strengths": self.detected_strengths,
            "areas_for_improvement": self.areas_for_improvement,
            "optimal_difficulty_level": self.optimal_difficulty_level,
            "engagement_preferences": self.engagement_preferences,
            "learning_pace": self.learning_pace,
            "attention_span_minutes": self.attention_span_minutes,
            "best_time_patterns": self.best_time_patterns,
            "response_accuracy_trends": self.response_accuracy_trends,
            "confidence_levels": self.confidence_levels,
            "last_updated": self.last_updated.isoformat()
        }


class PersonalizationEngine:
    """
    Adapts learning content and responses based on individual patterns and performance
    """
    
    def __init__(self, db):
        self.db = db
        self.child_repo = ChildProfileRepository(db)
        self.curriculum_repo = CurriculumTopicRepository(db)
        self.learning_patterns: Dict[str, LearningPattern] = {}
        
        # Learning style detection weights
        self.learning_style_indicators = {
            LearningStyle.VISUAL: {
                "keywords": ["see", "picture", "draw", "color", "diagram", "chart", "image"],
                "activity_preferences": ["drawing", "coloring", "visual_aids", "diagrams"],
                "response_patterns": ["asks_for_pictures", "mentions_colors", "draws_examples"]
            },
            LearningStyle.AUDITORY: {
                "keywords": ["hear", "listen", "sound", "music", "rhythm", "repeat", "say"],
                "activity_preferences": ["songs", "rhymes", "verbal_explanation", "discussions"],
                "response_patterns": ["asks_to_repeat", "uses_sound_analogies", "talks_through_problems"]
            },
            LearningStyle.KINESTHETIC: {
                "keywords": ["touch", "feel", "move", "build", "hands", "try", "practice"],
                "activity_preferences": ["hands_on", "movement", "building", "experiments"],
                "response_patterns": ["wants_to_try", "mentions_feeling", "asks_for_materials"]
            }
        }
        
        # Difficulty adjustment factors
        self.difficulty_factors = {
            "high_accuracy": {"threshold": 0.85, "adjustment": 0.2},
            "medium_accuracy": {"threshold": 0.65, "adjustment": 0.0},
            "low_accuracy": {"threshold": 0.45, "adjustment": -0.3},
            "very_low_accuracy": {"threshold": 0.0, "adjustment": -0.5}
        }
        
        # Engagement indicators
        self.engagement_indicators = {
            "high": ["excited", "love", "fun", "awesome", "cool", "amazing"],
            "medium": ["okay", "good", "nice", "fine", "alright"],
            "low": ["boring", "tired", "hard", "difficult", "confused", "don't like"]
        }
    
    async def analyze_learning_patterns(self, user_id: str, 
                                      interaction_history: List[Dict[str, Any]] = None,
                                      performance_data: List[Dict[str, Any]] = None) -> LearningPattern:
        """
        Analyze individual learning patterns from interaction history and performance
        
        Args:
            user_id: Child's user ID
            interaction_history: Recent interaction data
            performance_data: Recent performance/assessment data
            
        Returns:
            LearningPattern object with detected patterns
        """
        try:
            # Get or create learning pattern
            if user_id not in self.learning_patterns:
                self.learning_patterns[user_id] = LearningPattern(user_id)
            
            pattern = self.learning_patterns[user_id]
            
            # Get child profile for baseline
            child_profile = await self.child_repo.get_by_id(user_id, "child_id")
            if not child_profile:
                raise ValueError(f"Child profile not found: {user_id}")
            
            # Detect learning style from interactions
            if interaction_history:
                detected_style = self._detect_learning_style(interaction_history)
                if detected_style:
                    pattern.preferred_learning_style = detected_style
            
            # Analyze performance patterns
            if performance_data:
                pattern = self._analyze_performance_patterns(pattern, performance_data)
            
            # Analyze engagement patterns
            if interaction_history:
                pattern = self._analyze_engagement_patterns(pattern, interaction_history)
            
            # Determine optimal difficulty
            pattern.optimal_difficulty_level = self._calculate_optimal_difficulty(pattern)
            
            # Analyze learning pace
            pattern.learning_pace = self._determine_learning_pace(pattern, performance_data or [])
            
            # Estimate attention span based on age and interaction patterns
            age = child_profile["age"]
            pattern.attention_span_minutes = self._estimate_attention_span(age, interaction_history or [])
            
            # Identify strengths and improvement areas
            pattern.detected_strengths, pattern.areas_for_improvement = self._identify_strengths_and_improvements(
                performance_data or []
            )
            
            pattern.last_updated = datetime.now(timezone.utc)
            
            logger.info(f"Learning patterns analyzed for user {user_id}: {pattern.preferred_learning_style}")
            return pattern
            
        except Exception as e:
            logger.error(f"Error analyzing learning patterns: {str(e)}")
            raise
    
    async def personalize_response(self, 
                                 content: str,
                                 user_id: str,
                                 context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Personalize response content based on individual learning patterns
        
        Args:
            content: Original response content
            user_id: Child's user ID
            context: Additional context (subject, topic, etc.)
            
        Returns:
            Dictionary with personalized response and adaptations
        """
        try:
            # Get learning pattern
            pattern = self.learning_patterns.get(user_id)
            if not pattern:
                # Analyze patterns first if not available
                pattern = await self.analyze_learning_patterns(user_id)
            
            # Get child profile
            child_profile = await self.child_repo.get_by_id(user_id, "child_id")
            if not child_profile:
                raise ValueError(f"Child profile not found: {user_id}")
            
            # Build personalization prompt
            system_prompt = self._build_personalization_prompt(pattern, child_profile, context)
            
            user_message = f"""Please personalize this response for the specific child:

Original response: "{content}"

Personalization requirements:
- Learning style: {pattern.preferred_learning_style.value if pattern.preferred_learning_style else 'mixed'}
- Optimal difficulty: {pattern.optimal_difficulty_level:.1f}/5
- Learning pace: {pattern.learning_pace}
- Attention span: {pattern.attention_span_minutes} minutes
- Strengths: {', '.join(pattern.detected_strengths[:3])}
- Areas to improve: {', '.join(pattern.areas_for_improvement[:2])}

Make the response engaging and perfectly suited to this individual child."""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
            
            # Make LLM API call
            response = await make_llm_api_call(
                messages=messages,
                model_name="gpt-4",
                temperature=0.6,
                max_tokens=600,
                response_format={"type": "json_object"}
            )
            
            # Parse response
            llm_content = response.choices[0].message.content
            try:
                parsed_response = json.loads(llm_content)
            except json.JSONDecodeError:
                parsed_response = {
                    "personalized_content": llm_content,
                    "adaptations_applied": ["basic_personalization"],
                    "difficulty_adjusted": False,
                    "engagement_techniques": [],
                    "confidence": 0.7
                }
            
            personalized_result = {
                "personalization_id": f"pers_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                "user_id": user_id,
                "original_content": content,
                "personalized_content": parsed_response.get("personalized_content", content),
                "adaptations_applied": parsed_response.get("adaptations_applied", []),
                "difficulty_level": pattern.optimal_difficulty_level,
                "difficulty_adjusted": parsed_response.get("difficulty_adjusted", False),
                "learning_style_adaptations": parsed_response.get("learning_style_adaptations", []),
                "engagement_techniques": parsed_response.get("engagement_techniques", []),
                "estimated_completion_time": parsed_response.get("estimated_completion_time", pattern.attention_span_minutes),
                "follow_up_suggestions": parsed_response.get("follow_up_suggestions", []),
                "confidence_score": parsed_response.get("confidence", 0.8),
                "learning_pattern_applied": pattern.to_dict(),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Response personalized for user {user_id} with {len(personalized_result['adaptations_applied'])} adaptations")
            return personalized_result
            
        except Exception as e:
            logger.error(f"Error personalizing response: {str(e)}")
            # Return original content with minimal personalization
            return {
                "personalization_id": f"fallback_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
                "user_id": user_id,
                "original_content": content,
                "personalized_content": content,
                "adaptations_applied": [],
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def adjust_difficulty(self, 
                              current_difficulty: float,
                              user_id: str,
                              recent_performance: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Adjust difficulty level based on recent performance history
        
        Args:
            current_difficulty: Current difficulty level (1-5)
            user_id: Child's user ID
            recent_performance: Recent performance data
            
        Returns:
            Dictionary with difficulty adjustment recommendations
        """
        try:
            if not recent_performance:
                return {
                    "recommended_difficulty": current_difficulty,
                    "adjustment": 0.0,
                    "reason": "No performance data available",
                    "confidence": 0.5
                }
            
            # Calculate recent accuracy
            accuracies = [perf.get("accuracy", 0.5) for perf in recent_performance[-10:]]  # Last 10 attempts
            avg_accuracy = statistics.mean(accuracies) if accuracies else 0.5
            
            # Calculate trend (recent vs older performance)
            if len(accuracies) >= 6:
                recent_accuracy = statistics.mean(accuracies[-3:])  # Last 3
                older_accuracy = statistics.mean(accuracies[-6:-3])  # Previous 3
                trend = recent_accuracy - older_accuracy
            else:
                trend = 0.0
            
            # Determine adjustment based on accuracy and trend
            adjustment = 0.0
            reason = ""
            
            if avg_accuracy >= self.difficulty_factors["high_accuracy"]["threshold"]:
                if trend >= 0:  # Improving or stable
                    adjustment = self.difficulty_factors["high_accuracy"]["adjustment"]
                    reason = "High accuracy with positive trend - increase challenge"
                else:
                    adjustment = 0.1  # Smaller increase due to negative trend
                    reason = "High accuracy but declining - slight increase"
                    
            elif avg_accuracy >= self.difficulty_factors["medium_accuracy"]["threshold"]:
                if trend > 0.1:  # Strong positive trend
                    adjustment = 0.1
                    reason = "Medium accuracy with strong improvement - slight increase"
                elif trend < -0.1:  # Strong negative trend
                    adjustment = -0.1
                    reason = "Medium accuracy with decline - slight decrease"
                else:
                    adjustment = 0.0
                    reason = "Medium accuracy with stable performance - maintain level"
                    
            elif avg_accuracy >= self.difficulty_factors["low_accuracy"]["threshold"]:
                adjustment = self.difficulty_factors["low_accuracy"]["adjustment"]
                reason = "Low accuracy - decrease difficulty"
                
            else:
                adjustment = self.difficulty_factors["very_low_accuracy"]["adjustment"]
                reason = "Very low accuracy - significant decrease needed"
            
            # Apply time-based adjustments (struggling for multiple sessions)
            session_count = len(recent_performance)
            if session_count >= 5 and avg_accuracy < 0.6:
                adjustment -= 0.1  # Additional decrease for persistent struggles
                reason += " (persistent difficulty detected)"
            
            # Calculate recommended difficulty
            new_difficulty = max(1.0, min(5.0, current_difficulty + adjustment))
            
            # Get learning pattern for additional context
            pattern = self.learning_patterns.get(user_id)
            confidence = 0.8 if pattern else 0.6
            
            result = {
                "current_difficulty": current_difficulty,
                "recommended_difficulty": round(new_difficulty, 1),
                "adjustment": round(adjustment, 1),
                "reason": reason,
                "confidence": confidence,
                "performance_analysis": {
                    "average_accuracy": round(avg_accuracy, 3),
                    "accuracy_trend": round(trend, 3),
                    "session_count": session_count,
                    "recent_accuracies": accuracies[-5:]  # Last 5 for reference
                },
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info(f"Difficulty adjusted for user {user_id}: {current_difficulty} -> {new_difficulty} ({reason})")
            return result
            
        except Exception as e:
            logger.error(f"Error adjusting difficulty: {str(e)}")
            return {
                "current_difficulty": current_difficulty,
                "recommended_difficulty": current_difficulty,
                "adjustment": 0.0,
                "reason": f"Error in calculation: {str(e)}",
                "confidence": 0.0,
                "error": True
            }
    
    def _detect_learning_style(self, interaction_history: List[Dict[str, Any]]) -> Optional[LearningStyle]:
        """Detect learning style from interaction patterns"""
        style_scores = {style: 0.0 for style in LearningStyle}
        
        for interaction in interaction_history:
            content = interaction.get("content", "").lower()
            activity_type = interaction.get("activity_type", "")
            response_pattern = interaction.get("response_pattern", "")
            
            # Score based on keywords used
            for style, indicators in self.learning_style_indicators.items():
                for keyword in indicators["keywords"]:
                    if keyword in content:
                        style_scores[style] += 1.0
                
                # Score based on activity preferences
                if activity_type in indicators["activity_preferences"]:
                    style_scores[style] += 2.0
                
                # Score based on response patterns
                if response_pattern in indicators["response_patterns"]:
                    style_scores[style] += 1.5
        
        # Return style with highest score if significantly higher
        if not any(style_scores.values()):
            return None
        
        max_style = max(style_scores.keys(), key=lambda k: style_scores[k])
        max_score = style_scores[max_style]
        second_highest = sorted(style_scores.values(), reverse=True)[1] if len(style_scores) > 1 else 0
        
        # Require significant difference to detect specific style
        if max_score > second_highest + 2.0:
            return max_style
        
        return LearningStyle.MIXED  # Mixed if no clear preference
    
    def _analyze_performance_patterns(self, pattern: LearningPattern, 
                                    performance_data: List[Dict[str, Any]]) -> LearningPattern:
        """Analyze performance patterns and update learning pattern"""
        if not performance_data:
            return pattern
        
        # Calculate accuracy trends by subject
        subject_accuracies = {}
        for perf in performance_data:
            subject = perf.get("subject", "general")
            accuracy = perf.get("accuracy", 0.5)
            
            if subject not in subject_accuracies:
                subject_accuracies[subject] = []
            subject_accuracies[subject].append(accuracy)
        
        # Update response accuracy trends
        for subject, accuracies in subject_accuracies.items():
            pattern.response_accuracy_trends[subject] = statistics.mean(accuracies)
        
        # Calculate confidence levels
        for perf in performance_data:
            subject = perf.get("subject", "general")
            confidence = perf.get("confidence_level", 0.5)
            
            if subject not in pattern.confidence_levels:
                pattern.confidence_levels[subject] = []
            if len(pattern.confidence_levels[subject]) >= 10:
                pattern.confidence_levels[subject].pop(0)  # Keep only recent 10
            pattern.confidence_levels[subject].append(confidence)
        
        # Average confidence levels
        for subject, confidences in pattern.confidence_levels.items():
            pattern.confidence_levels[subject] = statistics.mean(confidences)
        
        return pattern
    
    def _analyze_engagement_patterns(self, pattern: LearningPattern,
                                   interaction_history: List[Dict[str, Any]]) -> LearningPattern:
        """Analyze engagement patterns from interactions"""
        engagement_scores = {"high": 0, "medium": 0, "low": 0}
        activity_engagement = {}
        
        for interaction in interaction_history:
            content = interaction.get("content", "").lower()
            activity_type = interaction.get("activity_type", "general")
            
            # Score engagement based on language used
            engagement_level = "medium"  # default
            for level, indicators in self.engagement_indicators.items():
                if any(indicator in content for indicator in indicators):
                    engagement_level = level
                    break
            
            engagement_scores[engagement_level] += 1
            
            # Track engagement by activity type
            if activity_type not in activity_engagement:
                activity_engagement[activity_type] = []
            activity_engagement[activity_type].append(engagement_level)
        
        # Calculate engagement preferences
        total_interactions = sum(engagement_scores.values())
        if total_interactions > 0:
            pattern.engagement_preferences = {
                level: score / total_interactions 
                for level, score in engagement_scores.items()
            }
        
        return pattern
    
    def _calculate_optimal_difficulty(self, pattern: LearningPattern) -> float:
        """Calculate optimal difficulty level based on performance patterns"""
        if not pattern.response_accuracy_trends:
            return 2.0  # Default moderate difficulty
        
        avg_accuracy = statistics.mean(pattern.response_accuracy_trends.values())
        
        # Map accuracy to difficulty level
        if avg_accuracy >= 0.9:
            return 4.0  # High accuracy -> increase difficulty
        elif avg_accuracy >= 0.8:
            return 3.5
        elif avg_accuracy >= 0.7:
            return 3.0
        elif avg_accuracy >= 0.6:
            return 2.5
        elif avg_accuracy >= 0.5:
            return 2.0
        else:
            return 1.5  # Low accuracy -> decrease difficulty
    
    def _determine_learning_pace(self, pattern: LearningPattern, 
                               performance_data: List[Dict[str, Any]]) -> str:
        """Determine learning pace from performance data"""
        if not performance_data:
            return "moderate"
        
        # Analyze completion times and accuracy together
        completion_times = [perf.get("completion_time_seconds", 300) for perf in performance_data if perf.get("completion_time_seconds")]
        accuracies = [perf.get("accuracy", 0.5) for perf in performance_data]
        
        if not completion_times:
            return "moderate"
        
        avg_time = statistics.mean(completion_times)
        avg_accuracy = statistics.mean(accuracies)
        
        # Fast learner: quick completion with high accuracy
        if avg_time < 180 and avg_accuracy > 0.8:
            return "fast"
        # Slow learner: long completion time or low accuracy
        elif avg_time > 600 or avg_accuracy < 0.5:
            return "slow"
        else:
            return "moderate"
    
    def _estimate_attention_span(self, age: int, interaction_history: List[Dict[str, Any]]) -> int:
        """Estimate attention span based on age and interaction patterns"""
        # Base attention span by age (rule of thumb: age × 2-3 minutes)
        base_span = age * 2.5
        
        if not interaction_history:
            return max(10, min(30, int(base_span)))
        
        # Analyze session lengths from interaction history
        session_lengths = []
        for interaction in interaction_history:
            session_length = interaction.get("session_length_minutes")
            if session_length and session_length > 0:
                session_lengths.append(session_length)
        
        if session_lengths:
            # Use actual observed session lengths
            avg_session = statistics.mean(session_lengths)
            estimated_span = (base_span + avg_session) / 2
        else:
            estimated_span = base_span
        
        # Clamp to reasonable range
        return max(10, min(30, int(estimated_span)))
    
    def _identify_strengths_and_improvements(self, performance_data: List[Dict[str, Any]]) -> Tuple[List[str], List[str]]:
        """Identify strengths and areas for improvement from performance data"""
        if not performance_data:
            return [], []
        
        subject_performance = {}
        topic_performance = {}
        
        for perf in performance_data:
            subject = perf.get("subject", "general")
            topic = perf.get("topic", "general")
            accuracy = perf.get("accuracy", 0.5)
            
            # Track by subject
            if subject not in subject_performance:
                subject_performance[subject] = []
            subject_performance[subject].append(accuracy)
            
            # Track by topic
            if topic not in topic_performance:
                topic_performance[topic] = []
            topic_performance[topic].append(accuracy)
        
        # Calculate averages
        subject_averages = {
            subject: statistics.mean(accuracies) 
            for subject, accuracies in subject_performance.items()
        }
        topic_averages = {
            topic: statistics.mean(accuracies)
            for topic, accuracies in topic_performance.items()
        }
        
        # Identify strengths (accuracy > 0.8)
        strengths = []
        strengths.extend([subj for subj, avg in subject_averages.items() if avg > 0.8])
        strengths.extend([topic for topic, avg in topic_averages.items() if avg > 0.8])
        
        # Identify improvement areas (accuracy < 0.6)
        improvements = []
        improvements.extend([subj for subj, avg in subject_averages.items() if avg < 0.6])
        improvements.extend([topic for topic, avg in topic_averages.items() if avg < 0.6])
        
        return strengths[:5], improvements[:3]  # Limit to most relevant
    
    def _build_personalization_prompt(self, pattern: LearningPattern, 
                                    child_profile: Dict[str, Any], 
                                    context: Dict[str, Any] = None) -> str:
        """Build comprehensive personalization prompt for LLM"""
        age = child_profile["age"]
        grade = child_profile["grade_level"]
        
        context_info = ""
        if context:
            context_info = f"\nCurrent context: {context.get('subject', 'General')} - {context.get('topic', 'Various topics')}"
        
        return f"""You are personalizing educational content for a specific {age}-year-old child in Grade {grade}.

CHILD'S LEARNING PROFILE:
- Preferred learning style: {pattern.preferred_learning_style.value if pattern.preferred_learning_style else 'Mixed'}
- Optimal difficulty level: {pattern.optimal_difficulty_level:.1f}/5.0
- Learning pace: {pattern.learning_pace}
- Attention span: {pattern.attention_span_minutes} minutes
- Strengths: {', '.join(pattern.detected_strengths) if pattern.detected_strengths else 'Still discovering'}
- Areas to improve: {', '.join(pattern.areas_for_improvement) if pattern.areas_for_improvement else 'None identified'}
- Engagement level: {max(pattern.engagement_preferences.items(), key=lambda x: x[1])[0] if pattern.engagement_preferences else 'moderate'}{context_info}

PERSONALIZATION REQUIREMENTS:
- Adapt difficulty to exactly match optimal level {pattern.optimal_difficulty_level:.1f}
- Use {pattern.preferred_learning_style.value if pattern.preferred_learning_style else 'mixed'} learning techniques
- Keep content within {pattern.attention_span_minutes}-minute attention span
- Leverage identified strengths: {', '.join(pattern.detected_strengths[:3])}
- Gently address improvement areas: {', '.join(pattern.areas_for_improvement[:2])}
- Match {pattern.learning_pace} learning pace

RESPONSE FORMAT (JSON):
{{
    "personalized_content": "Content adapted to child's specific learning profile",
    "adaptations_applied": ["List of specific adaptations made"],
    "difficulty_adjusted": true/false,
    "learning_style_adaptations": ["Specific style adaptations"],
    "engagement_techniques": ["Techniques to maintain engagement"],
    "estimated_completion_time": {pattern.attention_span_minutes},
    "follow_up_suggestions": ["Personalized next steps"],
    "confidence": 0.9
}}

Make every word count for this specific child's learning journey!"""
"""
Unit tests for PersonalizationEngine - Task 4.3 personalization and adaptation logic
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import json
from datetime import datetime, timezone

from tutor.services.personalization_engine import PersonalizationEngine, LearningPattern
from tutor.models.user_models import Subject, LearningStyle


class TestLearningPattern:
    """Test cases for LearningPattern class"""
    
    def test_learning_pattern_creation(self):
        """Test creating a new learning pattern"""
        user_id = "child-123"
        pattern = LearningPattern(user_id)
        
        assert pattern.user_id == user_id
        assert pattern.preferred_learning_style is None
        assert pattern.detected_strengths == []
        assert pattern.areas_for_improvement == []
        assert pattern.optimal_difficulty_level == 1.0
        assert pattern.engagement_preferences == {}
        assert pattern.learning_pace == "moderate"
        assert pattern.attention_span_minutes == 15
        assert pattern.best_time_patterns == []
        assert pattern.response_accuracy_trends == {}
        assert pattern.confidence_levels == {}
        assert isinstance(pattern.last_updated, datetime)
    
    def test_learning_pattern_to_dict(self):
        """Test converting learning pattern to dictionary"""
        pattern = LearningPattern("child-123")
        pattern.preferred_learning_style = LearningStyle.VISUAL
        pattern.detected_strengths = ["mathematics", "visual processing"]
        pattern.areas_for_improvement = ["reading comprehension"]
        pattern.optimal_difficulty_level = 3.5
        pattern.engagement_preferences = {"high": 0.7, "medium": 0.3}
        pattern.learning_pace = "fast"
        pattern.attention_span_minutes = 25
        
        result = pattern.to_dict()
        
        assert result["user_id"] == "child-123"
        assert result["preferred_learning_style"] == "visual"
        assert result["detected_strengths"] == ["mathematics", "visual processing"]
        assert result["areas_for_improvement"] == ["reading comprehension"]
        assert result["optimal_difficulty_level"] == 3.5
        assert result["engagement_preferences"] == {"high": 0.7, "medium": 0.3}
        assert result["learning_pace"] == "fast"
        assert result["attention_span_minutes"] == 25
        assert "last_updated" in result


class TestPersonalizationEngine:
    """Test cases for PersonalizationEngine"""
    
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
    def mock_curriculum_repo(self):
        """Mock curriculum repository"""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock()
        return repo
    
    @pytest.fixture
    def personalization_engine(self, mock_db):
        """Create personalization engine with mocked dependencies"""
        with patch('tutor.services.personalization_engine.ChildProfileRepository') as mock_child, \
             patch('tutor.services.personalization_engine.CurriculumTopicRepository') as mock_curriculum:
            
            engine = PersonalizationEngine(mock_db)
            engine.child_repo = mock_child.return_value
            engine.curriculum_repo = mock_curriculum.return_value
            return engine
    
    def test_learning_style_indicators(self, personalization_engine):
        """Test learning style indicators are properly defined"""
        indicators = personalization_engine.learning_style_indicators
        
        # Test visual indicators
        visual = indicators[LearningStyle.VISUAL]
        assert "see" in visual["keywords"]
        assert "drawing" in visual["activity_preferences"]
        assert "asks_for_pictures" in visual["response_patterns"]
        
        # Test auditory indicators
        auditory = indicators[LearningStyle.AUDITORY]
        assert "hear" in auditory["keywords"]
        assert "songs" in auditory["activity_preferences"]
        assert "asks_to_repeat" in auditory["response_patterns"]
        
        # Test kinesthetic indicators
        kinesthetic = indicators[LearningStyle.KINESTHETIC]
        assert "touch" in kinesthetic["keywords"]
        assert "hands_on" in kinesthetic["activity_preferences"]
        assert "wants_to_try" in kinesthetic["response_patterns"]
    
    def test_difficulty_factors(self, personalization_engine):
        """Test difficulty adjustment factors"""
        factors = personalization_engine.difficulty_factors
        
        assert factors["high_accuracy"]["threshold"] == 0.85
        assert factors["high_accuracy"]["adjustment"] == 0.2
        assert factors["medium_accuracy"]["adjustment"] == 0.0
        assert factors["low_accuracy"]["adjustment"] == -0.3
        assert factors["very_low_accuracy"]["adjustment"] == -0.5
    
    def test_engagement_indicators(self, personalization_engine):
        """Test engagement level indicators"""
        indicators = personalization_engine.engagement_indicators
        
        assert "excited" in indicators["high"]
        assert "love" in indicators["high"]
        assert "okay" in indicators["medium"]
        assert "boring" in indicators["low"]
        assert "confused" in indicators["low"]
    
    def test_detect_learning_style_visual(self, personalization_engine):
        """Test visual learning style detection"""
        interaction_history = [
            {"content": "I want to see a picture of this", "activity_type": "drawing"},
            {"content": "Can you show me a diagram?", "response_pattern": "asks_for_pictures"},
            {"content": "Let me draw this to understand", "activity_type": "visual_aids"},
        ]
        
        detected_style = personalization_engine._detect_learning_style(interaction_history)
        assert detected_style == LearningStyle.VISUAL
    
    def test_detect_learning_style_auditory(self, personalization_engine):
        """Test auditory learning style detection"""
        interaction_history = [
            {"content": "Can you repeat that please?", "response_pattern": "asks_to_repeat"},
            {"content": "I like to hear the explanation", "activity_type": "verbal_explanation"},
            {"content": "That sounds like music", "response_pattern": "uses_sound_analogies"},
        ]
        
        detected_style = personalization_engine._detect_learning_style(interaction_history)
        assert detected_style == LearningStyle.AUDITORY
    
    def test_detect_learning_style_kinesthetic(self, personalization_engine):
        """Test kinesthetic learning style detection"""
        interaction_history = [
            {"content": "I want to try this myself", "response_pattern": "wants_to_try"},
            {"content": "Can I touch and feel this?", "activity_type": "hands_on"},
            {"content": "Let me build something", "activity_type": "building"},
        ]
        
        detected_style = personalization_engine._detect_learning_style(interaction_history)
        assert detected_style == LearningStyle.KINESTHETIC
    
    def test_detect_learning_style_mixed(self, personalization_engine):
        """Test mixed learning style detection when no clear preference"""
        interaction_history = [
            {"content": "I want to see this", "activity_type": "visual_aids"},
            {"content": "Can you tell me more?", "activity_type": "verbal_explanation"},
            {"content": "Let me try it", "activity_type": "hands_on"},
        ]
        
        detected_style = personalization_engine._detect_learning_style(interaction_history)
        assert detected_style == LearningStyle.MIXED
    
    def test_detect_learning_style_no_data(self, personalization_engine):
        """Test learning style detection with no interaction data"""
        interaction_history = []
        
        detected_style = personalization_engine._detect_learning_style(interaction_history)
        assert detected_style is None
    
    def test_analyze_performance_patterns(self, personalization_engine):
        """Test performance pattern analysis"""
        pattern = LearningPattern("child-123")
        performance_data = [
            {"subject": "mathematics", "accuracy": 0.9, "confidence_level": 0.8},
            {"subject": "mathematics", "accuracy": 0.85, "confidence_level": 0.9},
            {"subject": "science", "accuracy": 0.7, "confidence_level": 0.6},
            {"subject": "science", "accuracy": 0.75, "confidence_level": 0.7},
        ]
        
        updated_pattern = personalization_engine._analyze_performance_patterns(pattern, performance_data)
        
        # Check accuracy trends
        assert updated_pattern.response_accuracy_trends["mathematics"] == 0.875  # (0.9 + 0.85) / 2
        assert updated_pattern.response_accuracy_trends["science"] == 0.725  # (0.7 + 0.75) / 2
        
        # Check confidence levels
        assert updated_pattern.confidence_levels["mathematics"] == 0.85  # (0.8 + 0.9) / 2
        assert updated_pattern.confidence_levels["science"] == 0.65  # (0.6 + 0.7) / 2
    
    def test_analyze_engagement_patterns(self, personalization_engine):
        """Test engagement pattern analysis"""
        pattern = LearningPattern("child-123")
        interaction_history = [
            {"content": "This is so cool and awesome!", "activity_type": "visual_aids"},
            {"content": "I love this activity", "activity_type": "hands_on"},
            {"content": "This is okay I guess", "activity_type": "reading"},
            {"content": "This is boring", "activity_type": "listening"},
        ]
        
        updated_pattern = personalization_engine._analyze_engagement_patterns(pattern, interaction_history)
        
        # Check engagement preferences (2 high, 1 medium, 1 low out of 4 total)
        assert updated_pattern.engagement_preferences["high"] == 0.5  # 2/4
        assert updated_pattern.engagement_preferences["medium"] == 0.25  # 1/4
        assert updated_pattern.engagement_preferences["low"] == 0.25  # 1/4
    
    def test_calculate_optimal_difficulty(self, personalization_engine):
        """Test optimal difficulty calculation"""
        pattern = LearningPattern("child-123")
        
        # Test high accuracy -> high difficulty
        pattern.response_accuracy_trends = {"math": 0.95, "science": 0.9}
        difficulty = personalization_engine._calculate_optimal_difficulty(pattern)
        assert difficulty == 4.0
        
        # Test medium accuracy -> medium difficulty
        pattern.response_accuracy_trends = {"math": 0.75, "science": 0.7}
        difficulty = personalization_engine._calculate_optimal_difficulty(pattern)
        assert difficulty == 3.0
        
        # Test low accuracy -> low difficulty
        pattern.response_accuracy_trends = {"math": 0.4, "science": 0.3}
        difficulty = personalization_engine._calculate_optimal_difficulty(pattern)
        assert difficulty == 1.5
        
        # Test no data -> default difficulty
        pattern.response_accuracy_trends = {}
        difficulty = personalization_engine._calculate_optimal_difficulty(pattern)
        assert difficulty == 2.0
    
    def test_determine_learning_pace(self, personalization_engine):
        """Test learning pace determination"""
        pattern = LearningPattern("child-123")
        
        # Test fast pace (quick completion with high accuracy)
        performance_data = [
            {"completion_time_seconds": 150, "accuracy": 0.9},
            {"completion_time_seconds": 160, "accuracy": 0.85},
        ]
        pace = personalization_engine._determine_learning_pace(pattern, performance_data)
        assert pace == "fast"
        
        # Test slow pace (long completion time)
        performance_data = [
            {"completion_time_seconds": 700, "accuracy": 0.7},
            {"completion_time_seconds": 650, "accuracy": 0.6},
        ]
        pace = personalization_engine._determine_learning_pace(pattern, performance_data)
        assert pace == "slow"
        
        # Test slow pace (low accuracy)
        performance_data = [
            {"completion_time_seconds": 300, "accuracy": 0.3},
            {"completion_time_seconds": 350, "accuracy": 0.4},
        ]
        pace = personalization_engine._determine_learning_pace(pattern, performance_data)
        assert pace == "slow"
        
        # Test moderate pace
        performance_data = [
            {"completion_time_seconds": 300, "accuracy": 0.7},
            {"completion_time_seconds": 350, "accuracy": 0.75},
        ]
        pace = personalization_engine._determine_learning_pace(pattern, performance_data)
        assert pace == "moderate"
    
    def test_estimate_attention_span(self, personalization_engine):
        """Test attention span estimation"""
        # Test with age only (no interaction history)
        attention_span = personalization_engine._estimate_attention_span(8, [])
        assert attention_span == 20  # 8 * 2.5 = 20
        
        # Test with interaction history
        interaction_history = [
            {"session_length_minutes": 25},
            {"session_length_minutes": 30},
            {"session_length_minutes": 20},
        ]
        attention_span = personalization_engine._estimate_attention_span(8, interaction_history)
        assert attention_span == 22  # (20 + 25) / 2 = 22.5, rounded down
        
        # Test bounds (minimum 10, maximum 30)
        attention_span = personalization_engine._estimate_attention_span(3, [])  # Very young
        assert attention_span >= 10
        
        attention_span = personalization_engine._estimate_attention_span(15, [])  # Older child
        assert attention_span <= 30
    
    def test_identify_strengths_and_improvements(self, personalization_engine):
        """Test identification of strengths and improvement areas"""
        performance_data = [
            {"subject": "mathematics", "topic": "addition", "accuracy": 0.9},
            {"subject": "mathematics", "topic": "subtraction", "accuracy": 0.85},
            {"subject": "science", "topic": "plants", "accuracy": 0.5},
            {"subject": "science", "topic": "animals", "accuracy": 0.4},
            {"subject": "english", "topic": "reading", "accuracy": 0.75},
        ]
        
        strengths, improvements = personalization_engine._identify_strengths_and_improvements(performance_data)
        
        # Strengths should include high-performing subjects/topics (>0.8)
        assert "mathematics" in strengths
        assert "addition" in strengths
        assert "subtraction" in strengths
        
        # Improvements should include low-performing subjects/topics (<0.6)
        assert "science" in improvements
        assert "plants" in improvements
        assert "animals" in improvements
        
        # Medium performance (0.6-0.8) should not be in either list
        assert "english" not in strengths
        assert "english" not in improvements
        assert "reading" not in strengths
        assert "reading" not in improvements
    
    @pytest.mark.asyncio
    async def test_analyze_learning_patterns_complete(self, personalization_engine):
        """Test complete learning pattern analysis"""
        # Mock child profile
        child_profile = {
            "child_id": "child-123",
            "age": 8,
            "grade_level": 3
        }
        personalization_engine.child_repo.get_by_id.return_value = child_profile
        
        # Mock interaction and performance data
        interaction_history = [
            {"content": "I love to see pictures", "activity_type": "visual_aids"},
            {"content": "This is awesome!", "activity_type": "drawing"},
        ]
        performance_data = [
            {"subject": "mathematics", "accuracy": 0.9, "confidence_level": 0.8, "completion_time_seconds": 200},
            {"subject": "science", "accuracy": 0.5, "confidence_level": 0.4, "completion_time_seconds": 400},
        ]
        
        pattern = await personalization_engine.analyze_learning_patterns(
            user_id="child-123",
            interaction_history=interaction_history,
            performance_data=performance_data
        )
        
        # Verify pattern analysis results
        assert pattern.user_id == "child-123"
        assert pattern.preferred_learning_style == LearningStyle.VISUAL
        assert pattern.optimal_difficulty_level > 1.0  # Should be increased due to good math performance
        assert pattern.attention_span_minutes == 20  # Age 8 * 2.5
        assert "mathematics" in pattern.detected_strengths
        assert "science" in pattern.areas_for_improvement
        assert isinstance(pattern.last_updated, datetime)
    
    @pytest.mark.asyncio
    async def test_personalize_response_success(self, personalization_engine):
        """Test successful response personalization"""
        # Setup learning pattern
        pattern = LearningPattern("child-123")
        pattern.preferred_learning_style = LearningStyle.VISUAL
        pattern.optimal_difficulty_level = 3.0
        pattern.learning_pace = "moderate"
        pattern.attention_span_minutes = 20
        pattern.detected_strengths = ["mathematics", "visual processing"]
        pattern.areas_for_improvement = ["reading comprehension"]
        personalization_engine.learning_patterns["child-123"] = pattern
        
        # Mock child profile
        child_profile = {
            "child_id": "child-123",
            "age": 8,
            "grade_level": 3
        }
        personalization_engine.child_repo.get_by_id.return_value = child_profile
        
        # Mock LLM response
        mock_llm_response = Mock()
        mock_llm_response.choices = [Mock()]
        mock_llm_response.choices[0].message.content = json.dumps({
            "personalized_content": "Let's picture fractions like a pizza! Visual learners like you can imagine cutting a pizza into equal slices.",
            "adaptations_applied": ["visual_metaphors", "age_appropriate_language", "difficulty_adjusted"],
            "difficulty_adjusted": True,
            "learning_style_adaptations": ["Added visual pizza metaphor", "Suggested drawing activity"],
            "engagement_techniques": ["Visual imagery", "Relatable food example"],
            "estimated_completion_time": 18,
            "follow_up_suggestions": ["Draw your own fraction pizzas", "Try with different foods"],
            "confidence": 0.9
        })
        
        with patch('tutor.services.personalization_engine.make_llm_api_call', return_value=mock_llm_response):
            result = await personalization_engine.personalize_response(
                content="Fractions represent parts of a whole number.",
                user_id="child-123",
                context={"subject": "mathematics"}
            )
        
        # Verify personalization result
        assert result["user_id"] == "child-123"
        assert "pizza" in result["personalized_content"]
        assert "visual_metaphors" in result["adaptations_applied"]
        assert result["difficulty_level"] == 3.0
        assert result["difficulty_adjusted"] is True
        assert "Added visual pizza metaphor" in result["learning_style_adaptations"]
        assert result["estimated_completion_time"] == 18
        assert result["confidence_score"] == 0.9
        assert "learning_pattern_applied" in result
    
    @pytest.mark.asyncio
    async def test_personalize_response_no_pattern(self, personalization_engine):
        """Test response personalization when no learning pattern exists"""
        # Mock child profile
        child_profile = {
            "child_id": "child-456",
            "age": 7,
            "grade_level": 2
        }
        personalization_engine.child_repo.get_by_id.return_value = child_profile
        
        # Mock analyze_learning_patterns to return a basic pattern
        basic_pattern = LearningPattern("child-456")
        with patch.object(personalization_engine, 'analyze_learning_patterns', return_value=basic_pattern):
            # Mock LLM response
            mock_llm_response = Mock()
            mock_llm_response.choices = [Mock()]
            mock_llm_response.choices[0].message.content = json.dumps({
                "personalized_content": "Basic personalized content",
                "adaptations_applied": ["age_appropriate"],
                "confidence": 0.7
            })
            
            with patch('tutor.services.personalization_engine.make_llm_api_call', return_value=mock_llm_response):
                result = await personalization_engine.personalize_response(
                    content="Test content",
                    user_id="child-456"
                )
        
        # Should have analyzed patterns first
        assert result["user_id"] == "child-456"
        assert result["personalized_content"] == "Basic personalized content"
        assert "age_appropriate" in result["adaptations_applied"]
    
    @pytest.mark.asyncio
    async def test_personalize_response_error(self, personalization_engine):
        """Test response personalization error handling"""
        with patch.object(personalization_engine.child_repo, 'get_by_id', side_effect=Exception("DB Error")):
            result = await personalization_engine.personalize_response(
                content="Test content",
                user_id="child-123"
            )
        
        # Should return fallback response
        assert result["user_id"] == "child-123"
        assert result["personalized_content"] == "Test content"  # Original content
        assert result["adaptations_applied"] == []
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_adjust_difficulty_high_accuracy(self, personalization_engine):
        """Test difficulty adjustment for high accuracy performance"""
        recent_performance = [
            {"accuracy": 0.9, "subject": "mathematics"},
            {"accuracy": 0.88, "subject": "mathematics"},
            {"accuracy": 0.92, "subject": "mathematics"},
        ]
        
        result = await personalization_engine.adjust_difficulty(
            current_difficulty=2.5,
            user_id="child-123",
            recent_performance=recent_performance
        )
        
        # Should increase difficulty due to high accuracy
        assert result["current_difficulty"] == 2.5
        assert result["recommended_difficulty"] > 2.5
        assert result["adjustment"] > 0
        assert "High accuracy" in result["reason"]
        assert result["performance_analysis"]["average_accuracy"] == 0.9
    
    @pytest.mark.asyncio
    async def test_adjust_difficulty_low_accuracy(self, personalization_engine):
        """Test difficulty adjustment for low accuracy performance"""
        recent_performance = [
            {"accuracy": 0.4, "subject": "mathematics"},
            {"accuracy": 0.3, "subject": "mathematics"},
            {"accuracy": 0.35, "subject": "mathematics"},
        ]
        
        result = await personalization_engine.adjust_difficulty(
            current_difficulty=3.0,
            user_id="child-123",
            recent_performance=recent_performance
        )
        
        # Should decrease difficulty due to low accuracy
        assert result["current_difficulty"] == 3.0
        assert result["recommended_difficulty"] < 3.0
        assert result["adjustment"] < 0
        assert "Low accuracy" in result["reason"]
        assert result["performance_analysis"]["average_accuracy"] < 0.5
    
    @pytest.mark.asyncio
    async def test_adjust_difficulty_no_data(self, personalization_engine):
        """Test difficulty adjustment with no performance data"""
        result = await personalization_engine.adjust_difficulty(
            current_difficulty=2.0,
            user_id="child-123",
            recent_performance=[]
        )
        
        # Should maintain current difficulty
        assert result["current_difficulty"] == 2.0
        assert result["recommended_difficulty"] == 2.0
        assert result["adjustment"] == 0.0
        assert "No performance data" in result["reason"]
        assert result["confidence"] == 0.5
    
    @pytest.mark.asyncio
    async def test_adjust_difficulty_with_trend(self, personalization_engine):
        """Test difficulty adjustment considering performance trends"""
        # Recent improvement trend
        recent_performance = [
            {"accuracy": 0.6, "subject": "mathematics"},  # Older
            {"accuracy": 0.65, "subject": "mathematics"},
            {"accuracy": 0.7, "subject": "mathematics"},
            {"accuracy": 0.75, "subject": "mathematics"},  # Recent (improving)
            {"accuracy": 0.8, "subject": "mathematics"},
            {"accuracy": 0.85, "subject": "mathematics"},
        ]
        
        result = await personalization_engine.adjust_difficulty(
            current_difficulty=2.0,
            user_id="child-123",
            recent_performance=recent_performance
        )
        
        # Should consider positive trend in adjustment
        assert result["performance_analysis"]["accuracy_trend"] > 0
        assert result["adjustment"] >= 0  # Should increase or maintain due to improvement
    
    @pytest.mark.asyncio
    async def test_adjust_difficulty_persistent_struggle(self, personalization_engine):
        """Test difficulty adjustment for persistent low performance"""
        # Multiple sessions with low accuracy
        recent_performance = [
            {"accuracy": 0.5, "subject": "mathematics"} for _ in range(8)
        ]
        
        result = await personalization_engine.adjust_difficulty(
            current_difficulty=3.0,
            user_id="child-123",
            recent_performance=recent_performance
        )
        
        # Should apply additional decrease for persistent difficulty
        assert result["adjustment"] <= -0.4  # Base low adjustment + persistent struggle penalty
        assert "persistent difficulty" in result["reason"]
        assert result["performance_analysis"]["session_count"] == 8
    
    def test_build_personalization_prompt(self, personalization_engine):
        """Test personalization prompt building"""
        pattern = LearningPattern("child-123")
        pattern.preferred_learning_style = LearningStyle.VISUAL
        pattern.optimal_difficulty_level = 3.2
        pattern.learning_pace = "fast"
        pattern.attention_span_minutes = 25
        pattern.detected_strengths = ["mathematics", "problem solving"]
        pattern.areas_for_improvement = ["reading comprehension"]
        pattern.engagement_preferences = {"high": 0.8, "medium": 0.2}
        
        child_profile = {"age": 9, "grade_level": 4}
        context = {"subject": "science", "topic": "plants"}
        
        prompt = personalization_engine._build_personalization_prompt(pattern, child_profile, context)
        
        # Verify prompt includes all key information
        assert "9-year-old child in Grade 4" in prompt
        assert "visual learning techniques" in prompt
        assert "3.2" in prompt  # Optimal difficulty
        assert "fast learning pace" in prompt
        assert "25-minute attention span" in prompt
        assert "mathematics" in prompt  # Strengths
        assert "reading comprehension" in prompt  # Improvements
        assert "science - plants" in prompt  # Context
        assert "JSON" in prompt  # Response format
        assert "personalized_content" in prompt
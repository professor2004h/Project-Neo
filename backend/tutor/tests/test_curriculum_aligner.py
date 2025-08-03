"""
Unit tests for CurriculumAligner - Task 4.2 curriculum alignment and explanation adaptation
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
import json

from tutor.services.curriculum_aligner import CurriculumAligner
from tutor.models.user_models import Subject, LearningStyle
from tutor.models.curriculum_models import DifficultyLevel


class TestCurriculumAligner:
    """Test cases for curriculum alignment and learning style adaptation"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        return Mock()
    
    @pytest.fixture
    def mock_curriculum_repo(self):
        """Mock curriculum repository"""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_objectives_repo(self):
        """Mock objectives repository"""
        repo = AsyncMock()
        repo.get_by_topic_id = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_alignment_service(self):
        """Mock alignment service"""
        service = AsyncMock()
        service.validate_cambridge_code = Mock()
        return service
    
    @pytest.fixture
    def curriculum_aligner(self, mock_db):
        """Create curriculum aligner with mocked dependencies"""
        with patch('tutor.services.curriculum_aligner.CurriculumTopicRepository') as mock_curriculum, \
             patch('tutor.services.curriculum_aligner.LearningObjectiveRepository') as mock_objectives, \
             patch('tutor.services.curriculum_aligner.CambridgeAlignmentService') as mock_alignment:
            
            aligner = CurriculumAligner(mock_db)
            aligner.curriculum_repo = mock_curriculum.return_value
            aligner.objectives_repo = mock_objectives.return_value
            aligner.alignment_service = mock_alignment.return_value
            return aligner
    
    def test_curriculum_progression_mapping(self, curriculum_aligner):
        """Test curriculum progression mapping is properly defined"""
        # Test Mathematics progression
        math_progression = curriculum_aligner.curriculum_progression[Subject.MATHEMATICS]
        assert len(math_progression) == 6  # Grades 1-6
        assert "Number recognition" in math_progression[1][0]
        assert "Advanced calculations" in math_progression[6][0]
        
        # Test ESL progression
        esl_progression = curriculum_aligner.curriculum_progression[Subject.ESL]
        assert len(esl_progression) == 6
        assert "Basic vocabulary" in esl_progression[1][0]
        assert "Critical thinking" in esl_progression[6][0]
        
        # Test Science progression
        science_progression = curriculum_aligner.curriculum_progression[Subject.SCIENCE]
        assert len(science_progression) == 6
        assert "Living/non-living" in science_progression[1][0]
        assert "Environmental science" in science_progression[6][0]
    
    def test_learning_style_adaptations(self, curriculum_aligner):
        """Test learning style adaptation strategies are defined"""
        # Test visual adaptations
        visual = curriculum_aligner.style_adaptations[LearningStyle.VISUAL]
        assert "diagrams" in visual["techniques"]
        assert "picture" in visual["language"]
        assert "mind maps" in visual["tools"]
        
        # Test auditory adaptations
        auditory = curriculum_aligner.style_adaptations[LearningStyle.AUDITORY]
        assert "verbal explanations" in auditory["techniques"]
        assert "listen" in auditory["language"]
        assert "rhymes" in auditory["tools"]
        
        # Test kinesthetic adaptations
        kinesthetic = curriculum_aligner.style_adaptations[LearningStyle.KINESTHETIC]
        assert "hands-on activities" in kinesthetic["techniques"]
        assert "feel" in kinesthetic["language"]
        assert "physical objects" in kinesthetic["tools"]
        
        # Test mixed adaptations
        mixed = curriculum_aligner.style_adaptations[LearningStyle.MIXED]
        assert "multi-sensory" in mixed["techniques"]
        assert "explore" in mixed["language"]
    
    @pytest.mark.asyncio
    async def test_align_explanation_success(self, curriculum_aligner):
        """Test successful explanation alignment"""
        # Mock LLM response
        mock_llm_response = Mock()
        mock_llm_response.choices = [Mock()]
        mock_llm_response.choices[0].message.content = json.dumps({
            "aligned_content": "Fractions are parts of a whole. Think of a pizza cut into equal pieces!",
            "cambridge_codes": ["3Ma2a"],
            "curriculum_alignment_score": 0.95,
            "learning_style_adaptations": ["Added visual pizza metaphor", "Suggested drawing activities"],
            "prerequisite_concepts": ["Understanding of 'whole' and 'parts'"],
            "next_steps": ["Practice with real objects", "Try different fractions"],
            "vocabulary_level": "appropriate",
            "complexity_score": 0.6
        })
        
        # Mock curriculum context
        curriculum_aligner.curriculum_repo.get_by_id.return_value = {
            "title": "Introduction to Fractions",
            "cambridge_code": "3Ma2a",
            "learning_objectives": ["Understand fractions as parts of a whole"]
        }
        curriculum_aligner.objectives_repo.get_by_topic_id.return_value = [
            {"description": "Identify fractions in everyday objects"}
        ]
        
        # Mock validation
        curriculum_aligner.alignment_service.validate_cambridge_code.return_value = {
            "is_valid": True,
            "grade_level": 3
        }
        
        with patch('tutor.services.curriculum_aligner.make_llm_api_call', return_value=mock_llm_response):
            result = await curriculum_aligner.align_explanation(
                content="Fractions are mathematical expressions.",
                subject=Subject.MATHEMATICS,
                grade_level=3,
                learning_style=LearningStyle.VISUAL,
                age=8,
                topic_id="topic-123"
            )
        
        # Verify alignment result
        assert result["subject"] == "mathematics"
        assert result["grade_level"] == 3
        assert result["learning_style"] == "visual"
        assert result["age_targeted"] == 8
        assert "pizza" in result["aligned_content"]
        assert "3Ma2a" in result["cambridge_codes"]
        assert result["curriculum_alignment_score"] == 0.95
        assert len(result["learning_style_adaptations"]) == 2
        assert "explanation_id" in result
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_align_explanation_with_fallback(self, curriculum_aligner):
        """Test explanation alignment with JSON parsing fallback"""
        # Mock LLM response with invalid JSON
        mock_llm_response = Mock()
        mock_llm_response.choices = [Mock()]
        mock_llm_response.choices[0].message.content = "Invalid JSON response about fractions"
        
        with patch('tutor.services.curriculum_aligner.make_llm_api_call', return_value=mock_llm_response):
            result = await curriculum_aligner.align_explanation(
                content="Fractions are mathematical expressions.",
                subject=Subject.MATHEMATICS,
                grade_level=3,
                learning_style=LearningStyle.VISUAL,
                age=8
            )
        
        # Should handle gracefully with fallback
        assert result["aligned_content"] == "Invalid JSON response about fractions"
        assert result["cambridge_codes"] == []
        assert result["curriculum_alignment_score"] == 0.7
    
    @pytest.mark.asyncio
    async def test_align_explanation_error_handling(self, curriculum_aligner):
        """Test explanation alignment error handling"""
        with patch('tutor.services.curriculum_aligner.make_llm_api_call', side_effect=Exception("API Error")):
            result = await curriculum_aligner.align_explanation(
                content="Test content",
                subject=Subject.MATHEMATICS,
                grade_level=3,
                learning_style=LearningStyle.VISUAL,
                age=8
            )
        
        # Should return original content with error
        assert result["aligned_content"] == "Test content"
        assert "error" in result
        assert result["curriculum_alignment_score"] == 0.5
    
    @pytest.mark.asyncio
    async def test_break_down_complex_concept(self, curriculum_aligner):
        """Test complex concept breakdown functionality"""
        mock_llm_response = Mock()
        mock_llm_response.choices = [Mock()]
        mock_llm_response.choices[0].message.content = json.dumps({
            "breakdown_steps": [
                {
                    "step_number": 1,
                    "title": "What is multiplication?",
                    "explanation": "Multiplication is adding the same number many times",
                    "example": "3 × 4 means 3 + 3 + 3 + 3",
                    "activity": "Use blocks to group and count",
                    "prerequisite": "Know how to add numbers"
                },
                {
                    "step_number": 2,
                    "title": "Multiplication patterns",
                    "explanation": "We can see patterns in multiplication tables",
                    "example": "2 × 1 = 2, 2 × 2 = 4, 2 × 3 = 6",
                    "activity": "Draw arrays with objects",
                    "prerequisite": "Understand counting in twos"
                }
            ],
            "learning_sequence": ["Start with addition", "Show patterns", "Practice together"],
            "visual_aids": ["Number lines", "Array diagrams", "Counting objects"],
            "practice_activities": ["Group objects in arrays", "Skip counting games"],
            "assessment_questions": ["Can you show me 3 × 2 with blocks?"],
            "common_misconceptions": ["Thinking multiplication is just harder addition"],
            "parent_tips": ["Use everyday objects for counting"]
        })
        
        with patch('tutor.services.curriculum_aligner.make_llm_api_call', return_value=mock_llm_response):
            result = await curriculum_aligner.break_down_complex_concept(
                concept="Multiplication tables",
                subject=Subject.MATHEMATICS,
                grade_level=3,
                learning_style=LearningStyle.VISUAL,
                age=8
            )
        
        # Verify breakdown result
        assert result["original_concept"] == "Multiplication tables"
        assert result["subject"] == "mathematics"
        assert result["grade_level"] == 3
        assert result["learning_style"] == "visual"
        assert result["age_targeted"] == 8
        assert len(result["breakdown_steps"]) == 2
        assert result["total_steps"] == 2
        assert result["estimated_time_minutes"] == 20  # 2 steps × 10 minutes
        
        # Check step structure
        first_step = result["breakdown_steps"][0]
        assert first_step["step_number"] == 1
        assert first_step["title"] == "What is multiplication?"
        assert "adding the same number" in first_step["explanation"]
        assert "prerequisite" in first_step
        
        # Check additional components
        assert "Number lines" in result["visual_aids"]
        assert len(result["practice_activities"]) == 2
        assert len(result["assessment_questions"]) == 1
        assert len(result["common_misconceptions"]) == 1
        assert len(result["parent_tips"]) == 1
    
    @pytest.mark.asyncio
    async def test_break_down_complex_concept_fallback(self, curriculum_aligner):
        """Test complex concept breakdown with JSON parsing fallback"""
        mock_llm_response = Mock()
        mock_llm_response.choices = [Mock()]
        mock_llm_response.choices[0].message.content = "Invalid JSON about multiplication"
        
        with patch('tutor.services.curriculum_aligner.make_llm_api_call', return_value=mock_llm_response):
            result = await curriculum_aligner.break_down_complex_concept(
                concept="Multiplication",
                subject=Subject.MATHEMATICS,
                grade_level=3,
                learning_style=LearningStyle.VISUAL,
                age=8
            )
        
        # Should use fallback breakdown
        assert len(result["breakdown_steps"]) == 1
        assert result["breakdown_steps"][0]["title"] == "Understanding the basics"
        assert "Multiplication" in result["breakdown_steps"][0]["explanation"]
        assert result["total_steps"] == 1
    
    @pytest.mark.asyncio
    async def test_adapt_for_learning_style_visual(self, curriculum_aligner):
        """Test adaptation for visual learning style"""
        mock_llm_response = Mock()
        mock_llm_response.choices = [Mock()]
        mock_llm_response.choices[0].message.content = json.dumps({
            "adapted_content": "Picture fractions like a chocolate bar. Each piece is one part of the whole bar!",
            "learning_activities": ["Draw fractions", "Color fraction circles", "Cut paper into parts"],
            "materials_needed": ["Paper", "Colored pencils", "Scissors"],
            "step_by_step_instructions": [
                "Show a whole object", 
                "Draw lines to divide it", 
                "Color the parts differently"
            ],
            "engagement_techniques": ["Use bright colors", "Make it visual", "Let them draw"],
            "assessment_methods": ["Ask them to draw examples", "Point to fraction parts"]
        })
        
        with patch('tutor.services.curriculum_aligner.make_llm_api_call', return_value=mock_llm_response):
            result = await curriculum_aligner.adapt_for_learning_style(
                content="Fractions represent parts of a whole.",
                learning_style=LearningStyle.VISUAL,
                subject=Subject.MATHEMATICS,
                age=8
            )
        
        # Verify visual adaptation
        assert result["learning_style"] == "visual"
        assert result["age_targeted"] == 8
        assert "chocolate bar" in result["adapted_content"]
        assert "Draw fractions" in result["learning_activities"]
        assert "Paper" in result["materials_needed"]
        assert "Show a whole object" in result["step_by_step_instructions"]
        assert "Use bright colors" in result["engagement_techniques"]
        assert "draw examples" in result["assessment_methods"][0]
        
        # Check adaptation strategies
        visual_strategies = curriculum_aligner.style_adaptations[LearningStyle.VISUAL]["techniques"]
        assert result["adaptation_strategies_used"] == visual_strategies
    
    @pytest.mark.asyncio
    async def test_adapt_for_learning_style_auditory(self, curriculum_aligner):
        """Test adaptation for auditory learning style"""
        mock_llm_response = Mock()
        mock_llm_response.choices = [Mock()]
        mock_llm_response.choices[0].message.content = json.dumps({
            "adapted_content": "Listen to this fraction song: 'One half, one half, split it down the middle!'",
            "learning_activities": ["Sing fraction songs", "Clap rhythm patterns", "Discuss out loud"],
            "materials_needed": ["Audio recordings", "Musical instruments"],
            "step_by_step_instructions": ["Explain verbally", "Have them repeat", "Use rhythm"],
            "engagement_techniques": ["Use songs", "Create rhymes", "Encourage talking"],
            "assessment_methods": ["Ask them to explain aloud", "Listen to their reasoning"]
        })
        
        with patch('tutor.services.curriculum_aligner.make_llm_api_call', return_value=mock_llm_response):
            result = await curriculum_aligner.adapt_for_learning_style(
                content="Fractions represent parts of a whole.",
                learning_style=LearningStyle.AUDITORY,
                subject=Subject.MATHEMATICS,
                age=8
            )
        
        # Verify auditory adaptation
        assert result["learning_style"] == "auditory"
        assert "song" in result["adapted_content"]
        assert "Sing fraction songs" in result["learning_activities"]
        assert "Audio recordings" in result["materials_needed"]
        assert "Explain verbally" in result["step_by_step_instructions"]
        assert "Use songs" in result["engagement_techniques"]
        assert "explain aloud" in result["assessment_methods"][0]
    
    @pytest.mark.asyncio
    async def test_adapt_for_learning_style_kinesthetic(self, curriculum_aligner):
        """Test adaptation for kinesthetic learning style"""
        mock_llm_response = Mock()
        mock_llm_response.choices = [Mock()]
        mock_llm_response.choices[0].message.content = json.dumps({
            "adapted_content": "Feel fractions with your hands! Break a cookie into equal pieces and touch each part.",
            "learning_activities": ["Break objects into parts", "Build fraction models", "Use manipulatives"],
            "materials_needed": ["Blocks", "Clay", "Food items", "Fraction tiles"],
            "step_by_step_instructions": ["Give them objects to handle", "Let them break things apart", "Build together"],
            "engagement_techniques": ["Let them move around", "Use hands-on materials", "Physical demonstrations"],
            "assessment_methods": ["Watch them manipulate objects", "Have them build examples"]
        })
        
        with patch('tutor.services.curriculum_aligner.make_llm_api_call', return_value=mock_llm_response):
            result = await curriculum_aligner.adapt_for_learning_style(
                content="Fractions represent parts of a whole.",
                learning_style=LearningStyle.KINESTHETIC,
                subject=Subject.MATHEMATICS,
                age=8
            )
        
        # Verify kinesthetic adaptation
        assert result["learning_style"] == "kinesthetic"
        assert "hands" in result["adapted_content"]
        assert "Break objects" in result["learning_activities"]
        assert "Blocks" in result["materials_needed"]
        assert "Give them objects" in result["step_by_step_instructions"]
        assert "move around" in result["engagement_techniques"]
        assert "manipulate objects" in result["assessment_methods"][0]
    
    def test_get_prerequisite_knowledge(self, curriculum_aligner):
        """Test prerequisite knowledge retrieval"""
        # Test grade 1 (should return basic skills)
        prereqs_grade1 = curriculum_aligner._get_prerequisite_knowledge(Subject.MATHEMATICS, 1)
        expected_basic = ["Basic recognition", "Simple counting", "Following instructions"]
        assert prereqs_grade1 == expected_basic
        
        # Test grade 3 (should include grade 1 and 2 concepts)
        prereqs_grade3 = curriculum_aligner._get_prerequisite_knowledge(Subject.MATHEMATICS, 3)
        assert len(prereqs_grade3) > 0
        assert len(prereqs_grade3) <= 5  # Should limit to most recent 5
        
        # Test grade 6 (should include recent grades)
        prereqs_grade6 = curriculum_aligner._get_prerequisite_knowledge(Subject.MATHEMATICS, 6)
        assert len(prereqs_grade6) == 5  # Should limit to 5 most recent
    
    @pytest.mark.asyncio
    async def test_get_curriculum_context_with_topic(self, curriculum_aligner):
        """Test curriculum context retrieval with specific topic"""
        # Mock topic information
        curriculum_aligner.curriculum_repo.get_by_id.return_value = {
            "title": "Basic Addition",
            "cambridge_code": "2Ma1a",
            "learning_objectives": ["Add numbers to 20"]
        }
        curriculum_aligner.objectives_repo.get_by_topic_id.return_value = [
            {"description": "Add single digit numbers"},
            {"description": "Understand addition as combining"}
        ]
        
        context = await curriculum_aligner._get_curriculum_context(
            Subject.MATHEMATICS, 2, "topic-123"
        )
        
        # Should include grade objectives and topic-specific info
        assert "grade_objectives" in context
        assert "prerequisite_grade" in context
        assert "next_grade" in context
        assert "topic" in context
        assert "detailed_objectives" in context
        
        assert context["topic"]["title"] == "Basic Addition"
        assert context["topic"]["cambridge_code"] == "2Ma1a"
        assert len(context["detailed_objectives"]) == 2
    
    @pytest.mark.asyncio
    async def test_get_curriculum_context_without_topic(self, curriculum_aligner):
        """Test curriculum context retrieval without specific topic"""
        context = await curriculum_aligner._get_curriculum_context(
            Subject.MATHEMATICS, 3
        )
        
        # Should include grade progression but no topic-specific info
        assert "grade_objectives" in context
        assert "prerequisite_grade" in context
        assert "next_grade" in context
        assert "topic" not in context
        assert "detailed_objectives" not in context
        
        # Check content of grade objectives
        assert len(context["grade_objectives"]) > 0
        assert "Fractions" in str(context["grade_objectives"])  # Grade 3 includes fractions
    
    def test_get_learning_style_context(self, curriculum_aligner):
        """Test learning style context retrieval"""
        # Test known learning style
        visual_context = curriculum_aligner._get_learning_style_context(LearningStyle.VISUAL)
        assert "diagrams" in visual_context["techniques"]
        assert "picture" in visual_context["language"]
        
        # Test mixed learning style
        mixed_context = curriculum_aligner._get_learning_style_context(LearningStyle.MIXED)
        assert "multi-sensory" in mixed_context["techniques"]
    
    def test_build_alignment_prompt(self, curriculum_aligner):
        """Test alignment prompt building"""
        curriculum_context = {
            "grade_objectives": ["Number to 1000", "Multiplication tables"],
            "prerequisite_grade": ["Number to 100", "Basic addition"]
        }
        style_context = {
            "techniques": ["diagrams", "charts"],
            "tools": ["mind maps", "flowcharts"],
            "language": ["picture", "see"]
        }
        
        prompt = curriculum_aligner._build_alignment_prompt(
            Subject.MATHEMATICS, 3, LearningStyle.VISUAL, 8, curriculum_context, style_context
        )
        
        assert "MATHEMATICS GRADE 3" in prompt
        assert "Number to 1000" in prompt
        assert "diagrams" in prompt
        assert "mind maps" in prompt
        assert "age 8" in prompt
        assert "JSON" in prompt
        assert "cambridge_codes" in prompt
    
    @pytest.mark.asyncio
    async def test_validate_alignment_valid_codes(self, curriculum_aligner):
        """Test alignment validation with valid Cambridge codes"""
        response = {
            "aligned_content": "fractions are parts number recognition counting",
            "cambridge_codes": ["3Ma2a"]
        }
        
        # Mock valid Cambridge code
        curriculum_aligner.alignment_service.validate_cambridge_code.return_value = {
            "is_valid": True,
            "grade_level": 3
        }
        
        validation = await curriculum_aligner._validate_alignment(
            response, Subject.MATHEMATICS, 3
        )
        
        assert validation["is_aligned"] is True
        assert validation["alignment_score"] >= 0.7
        assert len(validation["issues"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_alignment_invalid_codes(self, curriculum_aligner):
        """Test alignment validation with invalid Cambridge codes"""
        response = {
            "aligned_content": "test content",
            "cambridge_codes": ["INVALID", "3Ma2a"]
        }
        
        # Mock validation responses
        def mock_validate(code, subject):
            if code == "INVALID":
                return {"is_valid": False}
            else:
                return {"is_valid": True, "grade_level": 3}
        
        curriculum_aligner.alignment_service.validate_cambridge_code.side_effect = mock_validate
        
        validation = await curriculum_aligner._validate_alignment(
            response, Subject.MATHEMATICS, 3
        )
        
        assert validation["alignment_score"] < 0.8  # Should be reduced due to invalid code
        assert len(validation["issues"]) == 1
        assert "Invalid Cambridge code: INVALID" in validation["issues"][0]
    
    @pytest.mark.asyncio
    async def test_validate_alignment_grade_mismatch(self, curriculum_aligner):
        """Test alignment validation with grade level mismatch"""
        response = {
            "aligned_content": "advanced content",
            "cambridge_codes": ["5Ma3a"]  # Grade 5 code for Grade 3 content
        }
        
        curriculum_aligner.alignment_service.validate_cambridge_code.return_value = {
            "is_valid": True,
            "grade_level": 5  # Mismatch with expected grade 3
        }
        
        validation = await curriculum_aligner._validate_alignment(
            response, Subject.MATHEMATICS, 3
        )
        
        assert validation["alignment_score"] < 0.8
        assert len(validation["issues"]) == 1
        assert "Grade mismatch" in validation["issues"][0]
    
    @pytest.mark.asyncio
    async def test_validate_alignment_no_grade_concepts(self, curriculum_aligner):
        """Test alignment validation when content doesn't reference grade concepts"""
        response = {
            "aligned_content": "generic math content without specific concepts",
            "cambridge_codes": []
        }
        
        validation = await curriculum_aligner._validate_alignment(
            response, Subject.MATHEMATICS, 3
        )
        
        assert validation["alignment_score"] < 0.7
        assert validation["is_aligned"] is False
        assert "doesn't reference grade-level concepts" in validation["issues"][0]
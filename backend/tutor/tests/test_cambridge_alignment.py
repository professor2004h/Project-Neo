"""
Unit tests for Cambridge Alignment Service - Task 3.1
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime

from tutor.services.cambridge_alignment_service import CambridgeAlignmentService
from tutor.models.curriculum_models import Subject, DifficultyLevel


class TestCambridgeAlignmentService:
    """Test cases for Cambridge curriculum alignment validation"""
    
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
    def alignment_service(self, mock_db):
        """Create alignment service with mocked dependencies"""
        with patch('tutor.services.cambridge_alignment_service.CurriculumTopicRepository'), \
             patch('tutor.services.cambridge_alignment_service.LearningObjectiveRepository'):
            return CambridgeAlignmentService(mock_db)
    
    def test_validate_cambridge_code_valid_mathematics(self, alignment_service):
        """Test validation of valid mathematics Cambridge code"""
        # Test valid mathematics code
        result = alignment_service.validate_cambridge_code("3Ma1a", Subject.MATHEMATICS)
        
        assert result["is_valid"] is True
        assert result["subject"] == Subject.MATHEMATICS
        assert result["grade_level"] == 3
        assert result["strand"] == "1"
        assert result["sub_strand"] == "a"
        assert len(result["errors"]) == 0
    
    def test_validate_cambridge_code_valid_esl(self, alignment_service):
        """Test validation of valid ESL Cambridge code"""
        result = alignment_service.validate_cambridge_code("2E3b", Subject.ESL)
        
        assert result["is_valid"] is True
        assert result["subject"] == Subject.ESL
        assert result["grade_level"] == 2
        assert result["strand"] == "3"
        assert result["sub_strand"] == "b"
    
    def test_validate_cambridge_code_valid_science(self, alignment_service):
        """Test validation of valid science Cambridge code"""
        result = alignment_service.validate_cambridge_code("4Sc2a", Subject.SCIENCE)
        
        assert result["is_valid"] is True
        assert result["subject"] == Subject.SCIENCE
        assert result["grade_level"] == 4
        assert result["strand"] == "2"
        assert result["sub_strand"] == "a"
    
    def test_validate_cambridge_code_without_substrand(self, alignment_service):
        """Test validation of Cambridge code without sub-strand"""
        result = alignment_service.validate_cambridge_code("1Ma2")
        
        assert result["is_valid"] is True
        assert result["subject"] == Subject.MATHEMATICS
        assert result["grade_level"] == 1
        assert result["strand"] == "2"
        assert result["sub_strand"] is None
    
    def test_validate_cambridge_code_invalid_format(self, alignment_service):
        """Test validation of invalid Cambridge code format"""
        result = alignment_service.validate_cambridge_code("invalid", Subject.MATHEMATICS)
        
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0
        assert "pattern" in result["errors"][0].lower()
    
    def test_validate_cambridge_code_empty(self, alignment_service):
        """Test validation of empty Cambridge code"""
        result = alignment_service.validate_cambridge_code("")
        
        assert result["is_valid"] is False
        assert len(result["errors"]) > 0
        assert "empty" in result["errors"][0].lower()
    
    def test_validate_cambridge_code_invalid_grade(self, alignment_service):
        """Test validation of Cambridge code with invalid grade level"""
        result = alignment_service.validate_cambridge_code("7Ma1a", Subject.MATHEMATICS)
        
        assert result["is_valid"] is False
        assert "grade level must be between 1 and 6" in result["errors"][0]
    
    def test_validate_cambridge_code_case_insensitive(self, alignment_service):
        """Test that Cambridge code validation is case insensitive"""
        result = alignment_service.validate_cambridge_code("3ma1a", Subject.MATHEMATICS)
        
        assert result["is_valid"] is True
        assert result["cambridge_code"] == "3MA1A"  # Should be normalized to uppercase
    
    def test_validate_cambridge_code_auto_detect_subject(self, alignment_service):
        """Test automatic subject detection from Cambridge code"""
        # Mathematics
        result = alignment_service.validate_cambridge_code("3Ma1a")
        assert result["is_valid"] is True
        assert result["subject"] == Subject.MATHEMATICS
        
        # ESL
        result = alignment_service.validate_cambridge_code("2E3b")
        assert result["is_valid"] is True
        assert result["subject"] == Subject.ESL
        
        # Science
        result = alignment_service.validate_cambridge_code("4Sc2a")
        assert result["is_valid"] is True
        assert result["subject"] == Subject.SCIENCE
    
    @pytest.mark.asyncio
    async def test_validate_curriculum_alignment_valid_content(self, alignment_service):
        """Test curriculum alignment validation for valid content"""
        # Mock the topic alignment validation
        alignment_service._validate_topic_alignment = AsyncMock(return_value={
            "topic_found": True,
            "alignment_score": 1.0,
            "matching_codes": ["3Ma1a"]
        })
        
        content_data = {
            "content_id": "test-content-1",
            "topic_id": "test-topic-1",
            "cambridge_codes": ["3Ma1a", "3Ma1b"]
        }
        
        result = await alignment_service.validate_curriculum_alignment(content_data)
        
        assert result["is_aligned"] is True
        assert result["alignment_score"] >= 0.8
        assert len(result["validated_codes"]) == 2
        assert len(result["invalid_codes"]) == 0
    
    @pytest.mark.asyncio
    async def test_validate_curriculum_alignment_invalid_codes(self, alignment_service):
        """Test curriculum alignment validation with invalid codes"""
        alignment_service._validate_topic_alignment = AsyncMock(return_value={
            "topic_found": True,
            "alignment_score": 0.5
        })
        
        content_data = {
            "content_id": "test-content-2",
            "topic_id": "test-topic-1",
            "cambridge_codes": ["3Ma1a", "invalid-code", "7Ma1a"]  # Mix of valid and invalid
        }
        
        result = await alignment_service.validate_curriculum_alignment(content_data)
        
        assert result["is_aligned"] is False  # Should fail due to invalid codes
        assert len(result["validated_codes"]) == 1  # Only "3Ma1a" is valid
        assert len(result["invalid_codes"]) == 2  # "invalid-code" and "7Ma1a"
        assert len(result["recommendations"]) > 0
    
    @pytest.mark.asyncio
    async def test_validate_topic_alignment_exact_match(self, alignment_service):
        """Test topic alignment with exact Cambridge code match"""
        # Mock repository response
        alignment_service.curriculum_repo.get_by_id = AsyncMock(return_value={
            "topic_id": "test-topic-1",
            "cambridge_code": "3Ma1a",
            "subject": "mathematics",
            "grade_level": 3
        })
        
        result = await alignment_service._validate_topic_alignment("test-topic-1", ["3Ma1a", "3Ma1b"])
        
        assert result["topic_found"] is True
        assert result["alignment_score"] == 1.0
        assert "3Ma1a" in result["matching_codes"]
    
    @pytest.mark.asyncio
    async def test_validate_topic_alignment_partial_match(self, alignment_service):
        """Test topic alignment with partial match (same subject and grade)"""
        alignment_service.curriculum_repo.get_by_id = AsyncMock(return_value={
            "topic_id": "test-topic-1",
            "cambridge_code": "3Ma1a",
            "subject": "mathematics",
            "grade_level": 3
        })
        
        result = await alignment_service._validate_topic_alignment("test-topic-1", ["3Ma2b"])  # Different strand
        
        assert result["topic_found"] is True
        assert result["alignment_score"] == 0.7  # Partial match
        assert "3Ma2b" in result["matching_codes"]
    
    @pytest.mark.asyncio
    async def test_validate_topic_alignment_no_topic(self, alignment_service):
        """Test topic alignment when topic is not found"""
        alignment_service.curriculum_repo.get_by_id = AsyncMock(return_value=None)
        
        result = await alignment_service._validate_topic_alignment("nonexistent-topic", ["3Ma1a"])
        
        assert result["topic_found"] is False
        assert result["alignment_score"] == 0
        assert "not found" in result["message"].lower()
    
    def test_validate_age_appropriateness_appropriate_content(self, alignment_service):
        """Test age appropriateness validation for appropriate content"""
        content_data = {
            "content_id": "test-content-1",
            "difficulty_level": "elementary",
            "grade_level": 3
        }
        
        result = alignment_service.validate_age_appropriateness(content_data, 8)  # Age 8 = Grade 3
        
        assert result["is_appropriate"] is True
        assert result["appropriateness_score"] == 1.0
        assert result["target_age"] == 8
        assert len(result["recommendations"]) == 0
    
    def test_validate_age_appropriateness_too_difficult(self, alignment_service):
        """Test age appropriateness validation for content that's too difficult"""
        content_data = {
            "content_id": "test-content-1",
            "difficulty_level": "advanced",  # Advanced content
            "grade_level": 6
        }
        
        result = alignment_service.validate_age_appropriateness(content_data, 6)  # Age 6 = Grade 1
        
        assert result["is_appropriate"] is False
        assert result["appropriateness_score"] < 0.7
        assert len(result["recommendations"]) > 0
        assert "too high" in result["recommendations"][0].lower()
    
    def test_validate_age_appropriateness_invalid_age(self, alignment_service):
        """Test age appropriateness validation for invalid age"""
        content_data = {
            "content_id": "test-content-1",
            "difficulty_level": "elementary"
        }
        
        result = alignment_service.validate_age_appropriateness(content_data, 15)  # Too old
        
        assert result["is_appropriate"] is False
        assert len(result["issues"]) > 0
        assert "outside primary school range" in result["issues"][0]
    
    def test_validate_age_appropriateness_difficulty_mapping(self, alignment_service):
        """Test age appropriateness using difficulty level mapping"""
        content_data = {
            "content_id": "test-content-1",
            "difficulty_level": "intermediate"  # Grades 3-5
        }
        
        # Test age 9 (Grade 4) - should be appropriate
        result = alignment_service.validate_age_appropriateness(content_data, 9)
        
        assert result["is_appropriate"] is True
        assert result["appropriateness_score"] == 0.9
        assert result["recommended_age_range"]["min_grade"] == 3
        assert result["recommended_age_range"]["max_grade"] == 5
    
    @pytest.mark.asyncio
    async def test_get_curriculum_codes_by_topic_with_topic_code(self, alignment_service):
        """Test getting curriculum codes when topic has a Cambridge code"""
        alignment_service.curriculum_repo.get_by_id = AsyncMock(return_value={
            "topic_id": "test-topic-1",
            "cambridge_code": "3Ma1a"
        })
        alignment_service.objectives_repo.get_by_topic_id = AsyncMock(return_value=[
            {"cambridge_reference": "3Ma1b"},
            {"cambridge_reference": "3Ma1c"}
        ])
        
        codes = await alignment_service.get_curriculum_codes_by_topic("test-topic-1")
        
        assert "3Ma1a" in codes  # From topic
        assert "3Ma1b" in codes  # From objective
        assert "3Ma1c" in codes  # From objective
        assert len(codes) == 3
    
    @pytest.mark.asyncio
    async def test_get_curriculum_codes_by_topic_no_topic(self, alignment_service):
        """Test getting curriculum codes when topic doesn't exist"""
        alignment_service.curriculum_repo.get_by_id = AsyncMock(return_value=None)
        alignment_service.objectives_repo.get_by_topic_id = AsyncMock(return_value=[])
        
        codes = await alignment_service.get_curriculum_codes_by_topic("nonexistent-topic")
        
        assert codes == []
    
    def test_get_subject_from_code_valid(self, alignment_service):
        """Test extracting subject from valid Cambridge code"""
        assert alignment_service.get_subject_from_code("3Ma1a") == Subject.MATHEMATICS
        assert alignment_service.get_subject_from_code("2E3b") == Subject.ESL
        assert alignment_service.get_subject_from_code("4Sc2a") == Subject.SCIENCE
    
    def test_get_subject_from_code_invalid(self, alignment_service):
        """Test extracting subject from invalid Cambridge code"""
        assert alignment_service.get_subject_from_code("invalid") is None
        assert alignment_service.get_subject_from_code("") is None
    
    def test_generate_alignment_recommendations_invalid_codes(self, alignment_service):
        """Test recommendation generation for content with invalid codes"""
        alignment_report = {
            "invalid_codes": [{"code": "invalid1"}, {"code": "invalid2"}],
            "alignment_score": 0.3,
            "cambridge_codes": [],
            "topic_alignment": {"alignment_score": 0.2}
        }
        
        recommendations = alignment_service._generate_alignment_recommendations(alignment_report)
        
        assert len(recommendations) > 0
        assert any("invalid Cambridge codes" in rec for rec in recommendations)
        assert any("major revision needed" in rec for rec in recommendations)
    
    def test_generate_alignment_recommendations_no_codes(self, alignment_service):
        """Test recommendation generation for content with no Cambridge codes"""
        alignment_report = {
            "invalid_codes": [],
            "alignment_score": 0.0,
            "cambridge_codes": [],
            "topic_alignment": None
        }
        
        recommendations = alignment_service._generate_alignment_recommendations(alignment_report)
        
        assert any("Add Cambridge curriculum codes" in rec for rec in recommendations)
    
    def test_generate_alignment_recommendations_partial_alignment(self, alignment_service):
        """Test recommendation generation for partially aligned content"""
        alignment_report = {
            "invalid_codes": [],
            "alignment_score": 0.75,  # Below 0.8 threshold
            "cambridge_codes": ["3Ma1a"],
            "topic_alignment": {"alignment_score": 0.6}
        }
        
        recommendations = alignment_service._generate_alignment_recommendations(alignment_report)
        
        assert any("partially aligned" in rec for rec in recommendations)
        assert any("topic mapping" in rec for rec in recommendations)
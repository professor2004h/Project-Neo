"""
Unit tests for Content Service - Task 3.2
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch

from tutor.services.content_service import ContentService
from tutor.models.curriculum_models import Subject, DifficultyLevel


class TestContentService:
    """Test cases for content service search and validation functionality"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        return Mock()
    
    @pytest.fixture
    def mock_curriculum_repo(self):
        """Mock curriculum repository"""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.search_topics = AsyncMock()
        repo.get_by_cambridge_code = AsyncMock()
        return repo
    
    @pytest.fixture
    def mock_content_repo(self):
        """Mock content repository"""
        repo = AsyncMock()
        repo.get_by_id = AsyncMock()
        repo.get_by_topic_id = AsyncMock()
        repo.search_content = AsyncMock()
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
        service.validate_age_appropriateness = Mock()
        service.validate_curriculum_alignment = AsyncMock()
        service.get_curriculum_codes_by_topic = AsyncMock()
        return service
    
    @pytest.fixture
    def content_service(self, mock_db):
        """Create content service with mocked dependencies"""
        with patch('tutor.services.content_service.CurriculumTopicRepository') as mock_curriculum, \
             patch('tutor.services.content_service.LearningObjectiveRepository') as mock_objectives, \
             patch('tutor.services.content_service.ContentItemRepository') as mock_content, \
             patch('tutor.services.content_service.CambridgeAlignmentService') as mock_alignment:
            
            service = ContentService(mock_db)
            service.curriculum_repo = mock_curriculum.return_value
            service.objectives_repo = mock_objectives.return_value
            service.content_repo = mock_content.return_value
            service.alignment_service = mock_alignment.return_value
            return service
    
    @pytest.mark.asyncio
    async def test_get_lesson_content_success(self, content_service):
        """Test successful lesson content retrieval"""
        # Mock topic data
        topic_data = {
            "topic_id": "topic-1",
            "title": "Fractions",
            "description": "Introduction to fractions",
            "subject": "mathematics",
            "grade_level": 3,
            "cambridge_code": "3Ma1a",
            "difficulty_level": "elementary",
            "estimated_duration_minutes": 45
        }
        
        # Mock objectives data
        objectives_data = [
            {"description": "Understand what fractions are"},
            {"description": "Identify fraction parts"}
        ]
        
        # Mock content items data
        content_items_data = [
            {
                "content_id": "content-1",
                "title": "Fraction Video",
                "content_type": "video",
                "difficulty_level": "elementary"
            }
        ]
        
        # Setup mocks
        content_service.curriculum_repo.get_by_id.return_value = topic_data
        content_service.objectives_repo.get_by_topic_id.return_value = objectives_data
        content_service.content_repo.get_by_topic_id.return_value = content_items_data
        content_service.alignment_service.validate_age_appropriateness.return_value = {
            "is_appropriate": True
        }
        
        result = await content_service.get_lesson_content("topic-1", 3)
        
        assert result["topic_id"] == "topic-1"
        assert result["title"] == "Fractions"
        assert result["subject"] == "mathematics"
        assert result["grade_level"] == 3
        assert result["cambridge_code"] == "3Ma1a"
        assert len(result["learning_objectives"]) == 2
        assert len(result["content_items"]) == 1
        assert "Understand what fractions are" in result["learning_objectives"]
    
    @pytest.mark.asyncio
    async def test_get_lesson_content_topic_not_found(self, content_service):
        """Test lesson content retrieval when topic doesn't exist"""
        content_service.curriculum_repo.get_by_id.return_value = None
        
        with pytest.raises(ValueError) as exc_info:
            await content_service.get_lesson_content("nonexistent-topic", 3)
        
        assert "Topic not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_lesson_content_age_filtering(self, content_service):
        """Test that inappropriate content is filtered out"""
        topic_data = {
            "topic_id": "topic-1",
            "title": "Advanced Algebra",
            "subject": "mathematics",
            "grade_level": 6,
            "cambridge_code": "6Ma1a",
            "difficulty_level": "advanced"
        }
        
        content_items_data = [
            {
                "content_id": "content-1",
                "difficulty_level": "advanced"
            },
            {
                "content_id": "content-2",
                "difficulty_level": "expert"
            }
        ]
        
        content_service.curriculum_repo.get_by_id.return_value = topic_data
        content_service.objectives_repo.get_by_topic_id.return_value = []
        content_service.content_repo.get_by_topic_id.return_value = content_items_data
        
        # Mock age validation - first appropriate, second not
        content_service.alignment_service.validate_age_appropriateness.side_effect = [
            {"is_appropriate": True},
            {"is_appropriate": False}
        ]
        
        result = await content_service.get_lesson_content("topic-1", 3)  # Grade 3 user
        
        assert len(result["content_items"]) == 1  # Only appropriate content included
        assert result["content_items"][0]["content_id"] == "content-1"
    
    @pytest.mark.asyncio
    async def test_search_content_with_text_query(self, content_service):
        """Test content search with text query"""
        # Mock topic search results
        topic_results = [
            {
                "topic_id": "topic-1",
                "title": "Fraction Operations",
                "description": "Working with fractions",
                "subject": "mathematics",
                "grade_level": 3,
                "cambridge_code": "3Ma1a",
                "difficulty_level": "elementary"
            }
        ]
        
        # Mock content search results
        content_results = [
            {
                "content_id": "content-1",
                "topic_id": "topic-1",
                "title": "Fraction Video",
                "content_type": "video",
                "difficulty_level": "elementary"
            }
        ]
        
        # Mock objectives and content items for topics
        content_service.curriculum_repo.search_topics.return_value = topic_results
        content_service.content_repo.search_content.return_value = content_results
        content_service.content_repo.get_by_topic_id.return_value = [content_results[0]]
        content_service.objectives_repo.get_by_topic_id.return_value = [
            {"description": "Understand fractions"}
        ]
        content_service.alignment_service.validate_cambridge_code.return_value = {
            "is_valid": False
        }
        
        results = await content_service.search_content("fraction", {})
        
        assert len(results) >= 1
        assert any("Fraction" in result["title"] for result in results)
        assert any(result["type"] == "topic" for result in results)
        
        # Verify repositories were called
        content_service.curriculum_repo.search_topics.assert_called_once()
        content_service.content_repo.search_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_content_with_cambridge_code(self, content_service):
        """Test content search with Cambridge curriculum code"""
        cambridge_topic = {
            "topic_id": "topic-cambridge",
            "title": "Number Operations",
            "description": "Cambridge 3Ma1a content",
            "subject": "mathematics",
            "grade_level": 3,
            "cambridge_code": "3Ma1a",
            "difficulty_level": "elementary"
        }
        
        # Mock Cambridge code validation
        content_service.alignment_service.validate_cambridge_code.return_value = {
            "is_valid": True,
            "subject": Subject.MATHEMATICS,
            "grade_level": 3
        }
        content_service.curriculum_repo.get_by_cambridge_code.return_value = cambridge_topic
        content_service.curriculum_repo.search_topics.return_value = []
        content_service.content_repo.search_content.return_value = []
        content_service.objectives_repo.get_by_topic_id.return_value = [
            {"description": "Perform number operations"}
        ]
        
        results = await content_service.search_content("3Ma1a", {})
        
        assert len(results) >= 1
        cambridge_result = next((r for r in results if r["type"] == "cambridge_code_match"), None)
        assert cambridge_result is not None
        assert cambridge_result["cambridge_code"] == "3Ma1a"
        assert cambridge_result["match_score"] == 1.0  # Exact match
    
    @pytest.mark.asyncio
    async def test_search_content_with_filters(self, content_service):
        """Test content search with multiple filters"""
        filters = {
            "subject": "mathematics",
            "grade_level": 3,
            "difficulty_level": "elementary",
            "content_type": "video",
            "limit": 10
        }
        
        content_service.curriculum_repo.search_topics.return_value = []
        content_service.content_repo.search_content.return_value = []
        content_service.alignment_service.validate_cambridge_code.return_value = {
            "is_valid": False
        }
        
        await content_service.search_content("test query", filters)
        
        # Verify filters were passed to repositories
        curriculum_call_args = content_service.curriculum_repo.search_topics.call_args
        assert curriculum_call_args.kwargs["subject"] == Subject.MATHEMATICS
        assert curriculum_call_args.kwargs["grade_level"] == 3
        assert curriculum_call_args.kwargs["difficulty_level"] == DifficultyLevel.ELEMENTARY
        
        content_call_args = content_service.content_repo.search_content.call_args
        assert content_call_args.kwargs["content_type"] == "video"
        assert content_call_args.kwargs["difficulty_level"] == DifficultyLevel.ELEMENTARY
    
    @pytest.mark.asyncio
    async def test_search_content_invalid_enum_values(self, content_service):
        """Test content search handles invalid enum values gracefully"""
        filters = {
            "subject": "invalid_subject",
            "difficulty_level": "invalid_difficulty"
        }
        
        content_service.curriculum_repo.search_topics.return_value = []
        content_service.content_repo.search_content.return_value = []
        content_service.alignment_service.validate_cambridge_code.return_value = {
            "is_valid": False
        }
        
        # Should not raise exception
        results = await content_service.search_content("test", filters)
        
        assert isinstance(results, list)
        
        # Verify None values were passed for invalid enums
        curriculum_call_args = content_service.curriculum_repo.search_topics.call_args
        assert curriculum_call_args.kwargs["subject"] is None
        
        content_call_args = content_service.content_repo.search_content.call_args
        assert content_call_args.kwargs["difficulty_level"] is None
    
    @pytest.mark.asyncio
    async def test_search_content_deduplication(self, content_service):
        """Test that search results are properly deduplicated"""
        # Mock topic that has content items
        topic_with_content = {
            "topic_id": "topic-1",
            "title": "Fractions",
            "subject": "mathematics",
            "grade_level": 3,
            "cambridge_code": "3Ma1a",
            "difficulty_level": "elementary"
        }
        
        # Content item that belongs to the topic
        content_item = {
            "content_id": "content-1",
            "topic_id": "topic-1",
            "title": "Fraction Video",
            "content_type": "video",
            "difficulty_level": "elementary"
        }
        
        content_service.curriculum_repo.search_topics.return_value = [topic_with_content]
        content_service.content_repo.search_content.return_value = [content_item]
        content_service.content_repo.get_by_topic_id.return_value = [content_item]
        content_service.objectives_repo.get_by_topic_id.return_value = []
        content_service.alignment_service.validate_cambridge_code.return_value = {
            "is_valid": False
        }
        
        results = await content_service.search_content("fraction", {})
        
        # Should not have duplicate content items
        content_ids = []
        for result in results:
            if result.get("content_id"):
                content_ids.append(result["content_id"])
            for item in result.get("content_items", []):
                content_ids.append(item["content_id"])
        
        assert len(content_ids) == len(set(content_ids))  # No duplicates
    
    @pytest.mark.asyncio
    async def test_validate_curriculum_alignment_success(self, content_service):
        """Test successful curriculum alignment validation"""
        content_item = {
            "content_id": "content-1",
            "topic_id": "topic-1",
            "difficulty_level": "elementary",
            "content_type": "video"
        }
        
        topic_data = {
            "cambridge_code": "3Ma1a"
        }
        
        alignment_report = {
            "content_id": "content-1",
            "is_aligned": True,
            "alignment_score": 0.95,
            "cambridge_codes": ["3Ma1a"],
            "recommendations": []
        }
        
        content_service.content_repo.get_by_id.return_value = content_item
        content_service.curriculum_repo.get_by_id.return_value = topic_data
        content_service.alignment_service.get_curriculum_codes_by_topic.return_value = ["3Ma1b"]
        content_service.alignment_service.validate_curriculum_alignment.return_value = alignment_report
        
        result = await content_service.validate_curriculum_alignment("content-1")
        
        assert result["is_aligned"] is True
        assert result["alignment_score"] == 0.95
        assert "3Ma1a" in result["cambridge_codes"]
        
        # Verify alignment service was called with correct data
        call_args = content_service.alignment_service.validate_curriculum_alignment.call_args
        content_data = call_args[0][0]
        assert content_data["content_id"] == "content-1"
        assert "3Ma1a" in content_data["cambridge_codes"]
        assert "3Ma1b" in content_data["cambridge_codes"]
    
    @pytest.mark.asyncio
    async def test_validate_curriculum_alignment_content_not_found(self, content_service):
        """Test curriculum alignment validation when content doesn't exist"""
        content_service.content_repo.get_by_id.return_value = None
        
        result = await content_service.validate_curriculum_alignment("nonexistent-content")
        
        assert result["is_aligned"] is False
        assert result["alignment_score"] == 0.0
        assert "Content not found" in result["error"]
    
    @pytest.mark.asyncio
    async def test_validate_curriculum_alignment_no_topic(self, content_service):
        """Test curriculum alignment validation when content has no topic"""
        content_item = {
            "content_id": "content-1",
            "topic_id": None,
            "difficulty_level": "elementary"
        }
        
        alignment_report = {
            "content_id": "content-1",
            "is_aligned": False,
            "alignment_score": 0.0,
            "cambridge_codes": []
        }
        
        content_service.content_repo.get_by_id.return_value = content_item
        content_service.alignment_service.validate_curriculum_alignment.return_value = alignment_report
        
        result = await content_service.validate_curriculum_alignment("content-1")
        
        assert result["alignment_score"] == 0.0
        
        # Verify alignment service was called with empty cambridge_codes
        call_args = content_service.alignment_service.validate_curriculum_alignment.call_args
        content_data = call_args[0][0]
        assert content_data["cambridge_codes"] == []
    
    def test_calculate_match_score_exact_title_match(self, content_service):
        """Test match score calculation for exact title match"""
        topic = {
            "title": "Fraction Operations",
            "cambridge_code": "3Ma1a",
            "description": "Working with fractions"
        }
        
        score = content_service._calculate_match_score("fraction", topic, {})
        
        assert score >= 0.4  # Title match weight
    
    def test_calculate_match_score_cambridge_code_match(self, content_service):
        """Test match score calculation for Cambridge code match"""
        topic = {
            "title": "Number Operations",
            "cambridge_code": "3Ma1a",
            "description": "Basic operations"
        }
        
        score = content_service._calculate_match_score("3ma1a", topic, {})
        
        assert score >= 0.3  # Cambridge code match weight
    
    def test_calculate_match_score_with_filters(self, content_service):
        """Test match score calculation with matching filters"""
        topic = {
            "title": "Algebra Basics",
            "cambridge_code": "4Ma2a",
            "subject": "mathematics",
            "description": "Introduction to algebra"
        }
        
        filters = {"subject": "mathematics"}
        score = content_service._calculate_match_score("algebra", topic, filters)
        
        # Should get points for title match and subject filter match
        assert score >= 0.5
    
    def test_calculate_content_match_score(self, content_service):
        """Test content item match score calculation"""
        content_item = {
            "title": "Fraction Video Tutorial",
            "content_type": "video",
            "difficulty_level": "elementary"
        }
        
        filters = {
            "content_type": "video",
            "difficulty_level": "elementary"
        }
        
        score = content_service._calculate_content_match_score("fraction", content_item, filters)
        
        # Should get points for title, content_type, and difficulty_level matches
        assert score >= 0.8
    
    def test_calculate_match_score_no_query(self, content_service):
        """Test match score calculation with no query"""
        topic = {"title": "Test Topic", "cambridge_code": "1Ma1a"}
        
        score = content_service._calculate_match_score("", topic, {})
        
        assert score == 0.5  # Default score for no query
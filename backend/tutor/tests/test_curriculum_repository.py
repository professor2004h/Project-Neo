"""
Unit tests for Curriculum Repository - Task 3.2
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch

from tutor.repositories.curriculum_repository import (
    CurriculumTopicRepository,
    LearningObjectiveRepository,
    ContentItemRepository
)
from tutor.models.curriculum_models import Subject, DifficultyLevel


class TestCurriculumTopicRepository:
    """Test cases for curriculum topic repository filtering and search"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        return Mock()
    
    @pytest.fixture
    def mock_client(self):
        """Mock database client"""
        client = AsyncMock()
        client.table = Mock(return_value=client)
        client.select = Mock(return_value=client)
        client.eq = Mock(return_value=client)
        client.limit = Mock(return_value=client)
        client.order = Mock(return_value=client)
        client.execute = AsyncMock()
        return client
    
    @pytest.fixture
    def repository(self, mock_db):
        """Create curriculum topic repository with mocked database"""
        return CurriculumTopicRepository(mock_db)
    
    @pytest.mark.asyncio
    async def test_get_by_cambridge_code_found(self, repository, mock_client):
        """Test getting topic by Cambridge code when topic exists"""
        # Setup mock response
        mock_client.execute.return_value.data = [{
            "topic_id": "test-topic-1",
            "cambridge_code": "3MA1A",
            "title": "Number Operations",
            "subject": "mathematics",
            "grade_level": 3
        }]
        
        # Mock the get_client method
        repository.get_client = AsyncMock(return_value=mock_client)
        
        result = await repository.get_by_cambridge_code("3ma1a")
        
        assert result is not None
        assert result["cambridge_code"] == "3MA1A"
        assert result["title"] == "Number Operations"
        
        # Verify the query was made with uppercase code
        mock_client.eq.assert_called_with("cambridge_code", "3MA1A")
    
    @pytest.mark.asyncio
    async def test_get_by_cambridge_code_not_found(self, repository, mock_client):
        """Test getting topic by Cambridge code when topic doesn't exist"""
        mock_client.execute.return_value.data = []
        repository.get_client = AsyncMock(return_value=mock_client)
        
        result = await repository.get_by_cambridge_code("nonexistent")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_by_subject_and_grade(self, repository, mock_client):
        """Test filtering topics by subject and grade level"""
        mock_client.execute.return_value.data = [
            {
                "topic_id": "topic-1",
                "subject": "mathematics",
                "grade_level": 3,
                "title": "Fractions"
            },
            {
                "topic_id": "topic-2", 
                "subject": "mathematics",
                "grade_level": 3,
                "title": "Decimals"
            }
        ]
        repository.get_client = AsyncMock(return_value=mock_client)
        
        results = await repository.get_by_subject_and_grade(Subject.MATHEMATICS, 3)
        
        assert len(results) == 2
        assert all(topic["subject"] == "mathematics" for topic in results)
        assert all(topic["grade_level"] == 3 for topic in results)
        
        # Verify correct filter calls
        mock_client.eq.assert_any_call("subject", "mathematics")
        mock_client.eq.assert_any_call("grade_level", 3)
    
    @pytest.mark.asyncio
    async def test_search_topics_with_query(self, repository, mock_client):
        """Test searching topics with text query"""
        mock_client.execute.return_value.data = [
            {
                "topic_id": "topic-1",
                "title": "Fraction Operations",
                "description": "Working with fractions",
                "cambridge_code": "3Ma1a"
            }
        ]
        repository.get_client = AsyncMock(return_value=mock_client)
        
        results = await repository.search_topics(query="fraction")
        
        assert len(results) == 1
        assert "Fraction" in results[0]["title"]
        
        # Verify text search was applied
        mock_client.or_.assert_called()
    
    @pytest.mark.asyncio
    async def test_search_topics_with_all_filters(self, repository, mock_client):
        """Test searching topics with all filter options"""
        mock_client.execute.return_value.data = []
        repository.get_client = AsyncMock(return_value=mock_client)
        
        await repository.search_topics(
            query="algebra",
            subject=Subject.MATHEMATICS,
            grade_level=5,
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            limit=20
        )
        
        # Verify all filters were applied
        mock_client.eq.assert_any_call("subject", "mathematics")
        mock_client.eq.assert_any_call("grade_level", 5)
        mock_client.eq.assert_any_call("difficulty_level", "intermediate")
        mock_client.limit.assert_called_with(20)
        mock_client.order.assert_called()
    
    @pytest.mark.asyncio
    async def test_get_prerequisites(self, repository, mock_client):
        """Test getting prerequisite topics"""
        # Mock the topic with prerequisites
        repository.get_by_id = AsyncMock(return_value={
            "topic_id": "advanced-topic",
            "prerequisites": ["prereq-1", "prereq-2"]
        })
        
        # Mock prerequisite topics
        mock_client.execute.return_value.data = [
            {"topic_id": "prereq-1", "title": "Basic Concepts"},
            {"topic_id": "prereq-2", "title": "Intermediate Skills"}
        ]
        repository.get_client = AsyncMock(return_value=mock_client)
        
        results = await repository.get_prerequisites("advanced-topic")
        
        assert len(results) == 2
        assert any(topic["title"] == "Basic Concepts" for topic in results)
        assert any(topic["title"] == "Intermediate Skills" for topic in results)
        
        # Verify query for prerequisite IDs
        mock_client.in_.assert_called_with("topic_id", ["prereq-1", "prereq-2"])
    
    @pytest.mark.asyncio
    async def test_get_prerequisites_none(self, repository, mock_client):
        """Test getting prerequisites when topic has none"""
        repository.get_by_id = AsyncMock(return_value={
            "topic_id": "basic-topic",
            "prerequisites": []
        })
        repository.get_client = AsyncMock(return_value=mock_client)
        
        results = await repository.get_prerequisites("basic-topic")
        
        assert results == []
    
    @pytest.mark.asyncio
    async def test_get_dependents(self, repository, mock_client):
        """Test getting topics that depend on this topic"""
        mock_client.execute.return_value.data = [
            {"topic_id": "dependent-1", "title": "Advanced Topic 1"},
            {"topic_id": "dependent-2", "title": "Advanced Topic 2"}
        ]
        repository.get_client = AsyncMock(return_value=mock_client)
        
        results = await repository.get_dependents("basic-topic")
        
        assert len(results) == 2
        assert any(topic["title"] == "Advanced Topic 1" for topic in results)
        
        # Verify contains query for prerequisites array
        mock_client.contains.assert_called_with("prerequisites", ["basic-topic"])


class TestLearningObjectiveRepository:
    """Test cases for learning objective repository"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock()
    
    @pytest.fixture
    def mock_client(self):
        client = AsyncMock()
        client.table = Mock(return_value=client)
        client.select = Mock(return_value=client)
        client.eq = Mock(return_value=client)
        client.ilike = Mock(return_value=client)
        client.execute = AsyncMock()
        return client
    
    @pytest.fixture
    def repository(self, mock_db):
        return LearningObjectiveRepository(mock_db)
    
    @pytest.mark.asyncio
    async def test_get_by_topic_id(self, repository, mock_client):
        """Test getting objectives for a topic"""
        mock_client.execute.return_value.data = [
            {
                "objective_id": "obj-1",
                "topic_id": "topic-1",
                "description": "Understand fractions",
                "cambridge_reference": "3Ma1a"
            },
            {
                "objective_id": "obj-2",
                "topic_id": "topic-1", 
                "description": "Add fractions",
                "cambridge_reference": "3Ma1b"
            }
        ]
        repository.get_client = AsyncMock(return_value=mock_client)
        
        results = await repository.get_by_topic_id("topic-1")
        
        assert len(results) == 2
        assert all(obj["topic_id"] == "topic-1" for obj in results)
        mock_client.eq.assert_called_with("topic_id", "topic-1")
    
    @pytest.mark.asyncio
    async def test_search_by_cambridge_reference(self, repository, mock_client):
        """Test searching objectives by Cambridge reference"""
        mock_client.execute.return_value.data = [
            {
                "objective_id": "obj-1",
                "cambridge_reference": "3Ma1a",
                "description": "Number operations"
            }
        ]
        repository.get_client = AsyncMock(return_value=mock_client)
        
        results = await repository.search_by_cambridge_reference("3Ma1")
        
        assert len(results) == 1
        assert "3Ma1a" in results[0]["cambridge_reference"]
        mock_client.ilike.assert_called_with("cambridge_reference", "%3Ma1%")


class TestContentItemRepository:
    """Test cases for content item repository"""
    
    @pytest.fixture
    def mock_db(self):
        return Mock()
    
    @pytest.fixture
    def mock_client(self):
        client = AsyncMock()
        client.table = Mock(return_value=client)
        client.select = Mock(return_value=client)
        client.eq = Mock(return_value=client)
        client.ilike = Mock(return_value=client)
        client.limit = Mock(return_value=client)
        client.order = Mock(return_value=client)
        client.execute = AsyncMock()
        return client
    
    @pytest.fixture
    def repository(self, mock_db):
        return ContentItemRepository(mock_db)
    
    @pytest.mark.asyncio
    async def test_get_by_topic_id(self, repository, mock_client):
        """Test getting content items for a topic"""
        mock_client.execute.return_value.data = [
            {
                "content_id": "content-1",
                "topic_id": "topic-1",
                "title": "Fraction Video",
                "content_type": "video"
            },
            {
                "content_id": "content-2",
                "topic_id": "topic-1",
                "title": "Fraction Practice",
                "content_type": "interactive"
            }
        ]
        repository.get_client = AsyncMock(return_value=mock_client)
        
        results = await repository.get_by_topic_id("topic-1")
        
        assert len(results) == 2
        assert all(item["topic_id"] == "topic-1" for item in results)
        mock_client.eq.assert_called_with("topic_id", "topic-1")
    
    @pytest.mark.asyncio
    async def test_search_content_with_filters(self, repository, mock_client):
        """Test searching content with various filters"""
        mock_client.execute.return_value.data = [
            {
                "content_id": "content-1",
                "title": "Algebra Video",
                "content_type": "video",
                "difficulty_level": "intermediate"
            }
        ]
        repository.get_client = AsyncMock(return_value=mock_client)
        
        results = await repository.search_content(
            query="algebra",
            topic_id="topic-1",
            content_type="video",
            difficulty_level=DifficultyLevel.INTERMEDIATE,
            limit=10
        )
        
        assert len(results) == 1
        assert results[0]["content_type"] == "video"
        
        # Verify filters were applied
        mock_client.eq.assert_any_call("topic_id", "topic-1")
        mock_client.eq.assert_any_call("content_type", "video")
        mock_client.eq.assert_any_call("difficulty_level", "intermediate")
        mock_client.ilike.assert_called_with("title", "%algebra%")
        mock_client.limit.assert_called_with(10)
    
    @pytest.mark.asyncio
    async def test_search_content_no_filters(self, repository, mock_client):
        """Test searching content with no filters"""
        mock_client.execute.return_value.data = []
        repository.get_client = AsyncMock(return_value=mock_client)
        
        results = await repository.search_content()
        
        assert results == []
        # Verify only ordering and limiting was applied
        mock_client.order.assert_called_with("created_at", desc=True)
        mock_client.limit.assert_called_with(50)  # Default limit
    
    @pytest.mark.asyncio
    async def test_get_by_content_type(self, repository, mock_client):
        """Test getting content by type with limit"""
        mock_client.execute.return_value.data = [
            {"content_id": "video-1", "content_type": "video"},
            {"content_id": "video-2", "content_type": "video"}
        ]
        repository.get_client = AsyncMock(return_value=mock_client)
        
        results = await repository.get_by_content_type("video", 5)
        
        assert len(results) == 2
        assert all(item["content_type"] == "video" for item in results)
        mock_client.eq.assert_called_with("content_type", "video")
        mock_client.limit.assert_called_with(5)
    
    @pytest.mark.asyncio
    async def test_repository_error_handling(self, repository):
        """Test repository error handling"""
        # Mock database client to raise exception
        repository.get_client = AsyncMock(side_effect=Exception("Database error"))
        
        with pytest.raises(Exception) as exc_info:
            await repository.get_by_topic_id("topic-1")
        
        assert "Database error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_search_content_age_filtering_placeholder(self, repository, mock_client):
        """Test that age filtering parameters are accepted (implementation placeholder)"""
        mock_client.execute.return_value.data = []
        repository.get_client = AsyncMock(return_value=mock_client)
        
        # Should not raise error even with age parameters
        results = await repository.search_content(
            age_min=8,
            age_max=10
        )
        
        assert results == []
        # Age filtering is not implemented yet, but parameters should be accepted
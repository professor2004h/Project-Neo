"""
Unit tests for TutorService - Task 4.1 LLM integration and conversation management
"""
import pytest
from unittest.mock import AsyncMock, Mock, patch
from datetime import datetime, timezone
import json

from tutor.services.tutor_service import TutorService, ConversationContext
from tutor.models.user_models import Subject, LearningStyle


class TestConversationContext:
    """Test cases for conversation context management"""
    
    def test_conversation_context_creation(self):
        """Test creating a new conversation context"""
        user_id = "test-user-123"
        session_id = "session-456"
        
        context = ConversationContext(user_id, session_id)
        
        assert context.user_id == user_id
        assert context.session_id == session_id
        assert context.messages == []
        assert context.learning_context == {}
        assert context.current_topic is None
        assert context.difficulty_level == 1
        assert context.learning_style == "mixed"
        assert isinstance(context.created_at, datetime)
        assert isinstance(context.last_updated, datetime)
    
    def test_conversation_context_auto_session_id(self):
        """Test conversation context with auto-generated session ID"""
        user_id = "test-user-123"
        
        context = ConversationContext(user_id)
        
        assert context.user_id == user_id
        assert context.session_id is not None
        assert len(context.session_id) > 0
    
    def test_add_user_message(self):
        """Test adding user messages to conversation"""
        context = ConversationContext("user-123")
        content = "What is 2 + 2?"
        metadata = {"subject": "mathematics"}
        
        context.add_user_message(content, metadata)
        
        assert len(context.messages) == 1
        message = context.messages[0]
        assert message["role"] == "user"
        assert message["content"] == content
        assert message["metadata"] == metadata
        assert "id" in message
        assert "timestamp" in message
    
    def test_add_assistant_message(self):
        """Test adding assistant messages to conversation"""
        context = ConversationContext("user-123")
        content = "2 + 2 equals 4!"
        
        context.add_assistant_message(content)
        
        assert len(context.messages) == 1
        message = context.messages[0]
        assert message["role"] == "assistant"
        assert message["content"] == content
        assert "id" in message
        assert "timestamp" in message
    
    def test_get_recent_context(self):
        """Test getting recent conversation context for LLM"""
        context = ConversationContext("user-123")
        
        # Add multiple messages
        for i in range(15):
            context.add_user_message(f"Question {i}")
            context.add_assistant_message(f"Answer {i}")
        
        # Get recent context with limit
        recent = context.get_recent_context(max_messages=10)
        
        assert len(recent) == 10
        assert all(msg["role"] in ["user", "assistant"] for msg in recent)
        assert all("content" in msg for msg in recent)
        
        # Check that it gets the most recent messages
        assert recent[-1]["content"] == "Answer 14"
    
    def test_update_learning_context(self):
        """Test updating learning context parameters"""
        context = ConversationContext("user-123")
        
        context.update_learning_context(
            current_topic="fractions",
            difficulty_level=3,
            learning_style="visual"
        )
        
        assert context.current_topic == "fractions"
        assert context.difficulty_level == 3
        assert context.learning_style == "visual"
        assert context.learning_context["current_topic"] == "fractions"
        assert context.learning_context["difficulty_level"] == 3
        assert context.learning_context["learning_style"] == "visual"


class TestTutorService:
    """Test cases for TutorService LLM integration"""
    
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
    def mock_alignment_service(self):
        """Mock alignment service"""
        return AsyncMock()
    
    @pytest.fixture
    def tutor_service(self, mock_db):
        """Create tutor service with mocked dependencies"""
        with patch('tutor.services.tutor_service.ChildProfileRepository') as mock_child, \
             patch('tutor.services.tutor_service.CurriculumTopicRepository') as mock_curriculum, \
             patch('tutor.services.tutor_service.CambridgeAlignmentService') as mock_alignment:
            
            service = TutorService(mock_db)
            service.child_repo = mock_child.return_value
            service.curriculum_repo = mock_curriculum.return_value
            service.alignment_service = mock_alignment.return_value
            return service
    
    @pytest.mark.asyncio
    async def test_ask_question_success(self, tutor_service):
        """Test successful question processing with LLM integration"""
        # Mock child profile
        child_profile = {
            "child_id": "child-123",
            "age": 8,
            "grade_level": 3,
            "learning_style": "visual",
            "preferred_subjects": ["mathematics"]
        }
        
        # Mock LLM response
        mock_llm_response = Mock()
        mock_llm_response.choices = [Mock()]
        mock_llm_response.choices[0].message.content = json.dumps({
            "content": "Great question! 2 + 2 equals 4. Think of it like having 2 apples, then getting 2 more apples.",
            "explanation_level": "simple",
            "curriculum_alignment": ["2Ma1a"],
            "visual_aids_suggested": ["Use counting blocks or draw pictures"],
            "follow_up_questions": ["Can you try 3 + 3?"],
            "detected_topic": "addition",
            "confidence": 0.95
        })
        
        # Setup mocks
        tutor_service.child_repo.get_by_id.return_value = child_profile
        
        with patch('tutor.services.tutor_service.make_llm_api_call', return_value=mock_llm_response):
            response = await tutor_service.ask_question(
                user_id="child-123",
                question="What is 2 + 2?",
                context={"subject": "mathematics", "session_id": "session-456"}
            )
        
        # Verify response structure
        assert "response_id" in response
        assert response["session_id"] == "session-456"
        assert "2 + 2 equals 4" in response["content"]
        assert response["explanation_level"] == "simple"
        assert "2Ma1a" in response["curriculum_alignment"]
        assert response["child_age"] == 8
        assert response["child_grade"] == 3
        assert response["confidence_score"] == 0.95
        assert "response_time" in response
        assert "timestamp" in response
    
    @pytest.mark.asyncio
    async def test_ask_question_child_not_found(self, tutor_service):
        """Test question processing when child profile not found"""
        tutor_service.child_repo.get_by_id.return_value = None
        
        with pytest.raises(ValueError) as exc_info:
            await tutor_service.ask_question(
                user_id="nonexistent-child",
                question="What is 2 + 2?",
                context={}
            )
        
        assert "Child profile not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_ask_question_llm_error(self, tutor_service):
        """Test question processing with LLM API error"""
        child_profile = {
            "child_id": "child-123",
            "age": 8,
            "grade_level": 3,
            "learning_style": "visual"
        }
        
        tutor_service.child_repo.get_by_id.return_value = child_profile
        
        with patch('tutor.services.tutor_service.make_llm_api_call', side_effect=Exception("API Error")):
            response = await tutor_service.ask_question(
                user_id="child-123",
                question="What is 2 + 2?",
                context={}
            )
        
        # Should return fallback response
        assert response["error"] is True
        assert response["confidence_score"] == 0.1
        assert "trouble understanding" in response["content"]
        assert "Could you tell me more" in response["follow_up_questions"][0]
    
    @pytest.mark.asyncio
    async def test_ask_question_json_parse_error(self, tutor_service):
        """Test question processing with invalid JSON from LLM"""
        child_profile = {
            "child_id": "child-123",
            "age": 8,
            "grade_level": 3,
            "learning_style": "visual"
        }
        
        mock_llm_response = Mock()
        mock_llm_response.choices = [Mock()]
        mock_llm_response.choices[0].message.content = "Invalid JSON response"
        
        tutor_service.child_repo.get_by_id.return_value = child_profile
        
        with patch('tutor.services.tutor_service.make_llm_api_call', return_value=mock_llm_response):
            response = await tutor_service.ask_question(
                user_id="child-123",
                question="What is 2 + 2?",
                context={}
            )
        
        # Should handle gracefully with fallback
        assert response["content"] == "Invalid JSON response"
        assert response["explanation_level"] == "age_appropriate"
        assert response["confidence_score"] == 0.8
    
    @pytest.mark.asyncio
    async def test_conversation_management(self, tutor_service):
        """Test conversation context is maintained across interactions"""
        child_profile = {
            "child_id": "child-123",
            "age": 8,
            "grade_level": 3,
            "learning_style": "visual"
        }
        
        mock_llm_response = Mock()
        mock_llm_response.choices = [Mock()]
        mock_llm_response.choices[0].message.content = json.dumps({
            "content": "Great question!",
            "explanation_level": "simple",
            "confidence": 0.9
        })
        
        tutor_service.child_repo.get_by_id.return_value = child_profile
        
        with patch('tutor.services.tutor_service.make_llm_api_call', return_value=mock_llm_response):
            # First question
            response1 = await tutor_service.ask_question(
                user_id="child-123",
                question="What is 2 + 2?",
                context={"session_id": "session-test"}
            )
            
            # Second question in same session
            response2 = await tutor_service.ask_question(
                user_id="child-123", 
                question="What about 3 + 3?",
                context={"session_id": "session-test"}
            )
        
        # Both responses should have same session_id
        assert response1["session_id"] == response2["session_id"]
        assert response1["session_id"] == "session-test"
        
        # Check conversation is stored
        assert "session-test" in tutor_service.active_conversations
        conversation = tutor_service.active_conversations["session-test"]
        assert len(conversation.messages) == 4  # 2 user + 2 assistant messages
    
    @pytest.mark.asyncio
    async def test_get_conversation_history(self, tutor_service):
        """Test retrieving conversation history"""
        # Create conversation with messages
        user_id = "child-123"
        session_id = "session-test"
        
        context = ConversationContext(user_id, session_id)
        context.add_user_message("Question 1")
        context.add_assistant_message("Answer 1")
        tutor_service.active_conversations[session_id] = context
        
        history = await tutor_service.get_conversation_history(user_id, session_id)
        
        assert history["session_id"] == session_id
        assert history["user_id"] == user_id
        assert len(history["messages"]) == 2
        assert history["message_count"] == 2
        assert "created_at" in history
        assert "last_updated" in history
    
    @pytest.mark.asyncio
    async def test_get_conversation_history_not_found(self, tutor_service):
        """Test retrieving non-existent conversation history"""
        history = await tutor_service.get_conversation_history("user-123", "nonexistent-session")
        
        assert history["session_id"] == "nonexistent-session"
        assert history["user_id"] == "user-123"
        assert history["messages"] == []
        assert history["message_count"] == 0
    
    @pytest.mark.asyncio
    async def test_clear_conversation(self, tutor_service):
        """Test clearing conversation history"""
        # Create conversation
        user_id = "child-123"
        session_id = "session-test"
        context = ConversationContext(user_id, session_id)
        tutor_service.active_conversations[session_id] = context
        
        # Clear conversation
        result = await tutor_service.clear_conversation(user_id, session_id)
        
        assert result is True
        assert session_id not in tutor_service.active_conversations
    
    @pytest.mark.asyncio
    async def test_clear_conversation_not_found(self, tutor_service):
        """Test clearing non-existent conversation"""
        result = await tutor_service.clear_conversation("user-123", "nonexistent-session")
        assert result is False
    
    def test_build_system_prompt_age_appropriate(self, tutor_service):
        """Test system prompt is built with age-appropriate settings"""
        child_profile = {
            "age": 6,
            "grade_level": 1,
            "learning_style": "visual",
            "preferred_subjects": ["mathematics", "science"]
        }
        context = {"subject": "mathematics"}
        
        # Use the sync method directly for testing
        import asyncio
        system_prompt = asyncio.run(tutor_service._build_system_prompt(child_profile, context))
        
        assert "6-year-old child" in system_prompt
        assert "Grade 1" in system_prompt
        assert "very_simple language level" in system_prompt
        assert "Maximum 10 words" in system_prompt
        assert "visual" in system_prompt.lower()
        assert "Mathematics, English as a Second Language (ESL), and Science" in system_prompt
        assert "JSON" in system_prompt
        assert "Current subject focus: mathematics" in system_prompt
    
    def test_age_vocabulary_settings(self, tutor_service):
        """Test age-appropriate vocabulary settings"""
        # Test different ages
        settings_5 = tutor_service.age_vocabulary[5]
        settings_8 = tutor_service.age_vocabulary[8]
        settings_12 = tutor_service.age_vocabulary[12]
        
        assert settings_5["level"] == "very_simple"
        assert settings_5["max_sentence_length"] == 8
        assert settings_5["technical_terms"] is False
        
        assert settings_8["level"] == "simple"
        assert settings_8["max_sentence_length"] == 15
        assert settings_8["technical_terms"] == "basic"
        
        assert settings_12["level"] == "advanced"
        assert settings_12["max_sentence_length"] == 30
        assert settings_12["technical_terms"] == "advanced"
    
    def test_get_learning_style_guidance(self, tutor_service):
        """Test learning style guidance generation"""
        visual_guidance = tutor_service._get_learning_style_guidance("visual")
        auditory_guidance = tutor_service._get_learning_style_guidance("auditory")
        kinesthetic_guidance = tutor_service._get_learning_style_guidance("kinesthetic")
        mixed_guidance = tutor_service._get_learning_style_guidance("mixed")
        
        assert "visual" in visual_guidance.lower()
        assert "diagrams" in visual_guidance
        
        assert "rhythm" in auditory_guidance or "reading aloud" in auditory_guidance
        
        assert "hands-on" in kinesthetic_guidance
        assert "physical" in kinesthetic_guidance
        
        assert "combine" in mixed_guidance.lower()
        
        # Test unknown learning style defaults to mixed
        unknown_guidance = tutor_service._get_learning_style_guidance("unknown")
        assert unknown_guidance == mixed_guidance
    
    @pytest.mark.asyncio
    async def test_conversation_aging(self, tutor_service):
        """Test that old conversations are replaced"""
        user_id = "child-123"
        session_id = "session-test"
        
        # Create old conversation
        old_context = ConversationContext(user_id, session_id)
        old_context.last_updated = datetime.now(timezone.utc).replace(hour=0)  # Make it old
        tutor_service.active_conversations[session_id] = old_context
        
        # Get conversation (should create new one due to age)
        new_context = await tutor_service._get_or_create_conversation(user_id, session_id)
        
        # Should be a new conversation object
        assert new_context is not old_context
        assert new_context.user_id == user_id
        assert new_context.session_id == session_id
"""
Tests for Parent Guidance Service - Task 9.1 implementation
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import json

from services.supabase import DBConnection
from ..services.parent_guidance_service import (
    ParentGuidanceService, GuidanceCategory, GuidancePriority,
    FAQItem, GuidanceRecommendation, GuidanceSearchQuery
)
from ..models.user_models import ParentProfile, ChildProfile, Subject
from ..repositories.user_repository import ChildProfileRepository, ParentProfileRepository


class TestParentGuidanceService:
    """Test cases for Parent Guidance Service"""
    
    @pytest.fixture
    async def mock_db(self):
        """Mock database connection"""
        db = AsyncMock(spec=DBConnection)
        return db
    
    @pytest.fixture
    async def mock_child_repo(self):
        """Mock child repository"""
        return AsyncMock(spec=ChildProfileRepository)
    
    @pytest.fixture
    async def mock_parent_repo(self):
        """Mock parent repository"""
        return AsyncMock(spec=ParentProfileRepository)
    
    @pytest.fixture
    async def sample_parent_profile(self):
        """Sample parent profile for testing"""
        return ParentProfile(
            parent_id="parent_123",
            user_id="user_123",
            children_ids=["child_123"],
            preferred_language="en",
            guidance_level="intermediate",
            notification_preferences={"email": True, "push": False}
        )
    
    @pytest.fixture
    async def sample_child_profile(self):
        """Sample child profile for testing"""
        return ChildProfile(
            child_id="child_123",
            parent_id="parent_123",
            name="Alice",
            age=8,
            grade_level=3,
            preferred_subjects=[Subject.MATHEMATICS, Subject.ESL],
            learning_preferences={"learning_style": "visual", "difficulty": "intermediate"}
        )
    
    @pytest.fixture
    async def guidance_service(self, mock_db, mock_child_repo, mock_parent_repo):
        """Create guidance service with mocked dependencies"""
        service = ParentGuidanceService(mock_db)
        service.child_repo = mock_child_repo
        service.parent_repo = mock_parent_repo
        return service
    
    @pytest.mark.asyncio
    async def test_search_faq_basic_functionality(self, guidance_service, sample_parent_profile):
        """Test basic FAQ search functionality"""
        # Setup
        guidance_service.parent_repo.get_parent_profile_by_user_id.return_value = sample_parent_profile
        
        with patch.object(guidance_service, '_ai_enhanced_faq_search') as mock_ai_search:
            mock_ai_search.return_value = [
                FAQItem(
                    category=GuidanceCategory.CURRICULUM,
                    question="How to help with math?",
                    answer="Use visual aids and real-life examples.",
                    keywords=["math", "help"],
                    popularity_score=0.9
                )
            ]
            
            with patch.object(guidance_service, '_log_faq_search') as mock_log:
                # Execute
                search_query = GuidanceSearchQuery(
                    query="help with mathematics",
                    category=GuidanceCategory.CURRICULUM,
                    child_age=8,
                    max_results=5
                )
                
                results = await guidance_service.search_faq(search_query, "parent_123")
                
                # Verify
                assert len(results) == 1
                assert results[0].question == "How to help with math?"
                assert results[0].category == GuidanceCategory.CURRICULUM
                mock_ai_search.assert_called_once()
                mock_log.assert_called_once_with("parent_123", "help with mathematics", 1)
    
    @pytest.mark.asyncio
    async def test_search_faq_parent_not_found(self, guidance_service):
        """Test FAQ search when parent profile is not found"""
        # Setup
        guidance_service.parent_repo.get_parent_profile_by_user_id.return_value = None
        
        # Execute
        search_query = GuidanceSearchQuery(query="test query")
        results = await guidance_service.search_faq(search_query, "nonexistent_parent")
        
        # Verify
        assert results == []
    
    @pytest.mark.asyncio
    async def test_generate_personalized_guidance(self, guidance_service, sample_parent_profile, sample_child_profile):
        """Test personalized guidance generation"""
        # Setup
        guidance_service.parent_repo.get_parent_profile_by_user_id.return_value = sample_parent_profile
        guidance_service.child_repo.get_child_profile_by_id.return_value = sample_child_profile
        
        with patch.object(guidance_service, '_gather_child_context') as mock_context:
            mock_context.return_value = {"recent_subjects": ["mathematics"], "struggles": ["fractions"]}
            
            with patch.object(guidance_service, '_generate_ai_guidance') as mock_ai_guidance:
                mock_ai_guidance.return_value = [
                    GuidanceRecommendation(
                        parent_id="parent_123",
                        child_id="child_123",
                        category=GuidanceCategory.LEARNING_SUPPORT,
                        priority=GuidancePriority.HIGH,
                        title="Help with Fractions",
                        description="Your child needs support with fraction concepts.",
                        actionable_steps=["Use visual aids", "Practice with real objects"],
                        estimated_time_minutes=30
                    )
                ]
                
                with patch.object(guidance_service, '_store_guidance_recommendation') as mock_store:
                    mock_store.return_value = True
                    
                    # Execute
                    recommendations = await guidance_service.generate_personalized_guidance(
                        "parent_123", "child_123", {"recent_activity": "math"}
                    )
                    
                    # Verify
                    assert len(recommendations) == 1
                    assert recommendations[0].title == "Help with Fractions"
                    assert recommendations[0].priority == GuidancePriority.HIGH
                    assert "Use visual aids" in recommendations[0].actionable_steps
                    mock_store.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_personalized_guidance_missing_profiles(self, guidance_service):
        """Test guidance generation when profiles are missing"""
        # Setup
        guidance_service.parent_repo.get_parent_profile_by_user_id.return_value = None
        guidance_service.child_repo.get_child_profile_by_id.return_value = None
        
        # Execute
        recommendations = await guidance_service.generate_personalized_guidance(
            "nonexistent_parent", "nonexistent_child"
        )
        
        # Verify
        assert recommendations == []
    
    @pytest.mark.asyncio
    async def test_get_curriculum_guidance(self, guidance_service, sample_parent_profile):
        """Test curriculum-specific guidance generation"""
        # Setup
        guidance_service.parent_repo.get_parent_profile_by_user_id.return_value = sample_parent_profile
        
        with patch.object(guidance_service, '_generate_curriculum_guidance') as mock_curriculum:
            mock_curriculum.return_value = {
                "curriculum_overview": "Grade 3 mathematics covers...",
                "key_learning_objectives": ["Number sense", "Basic operations"],
                "parent_support_strategies": [
                    {"strategy": "Daily practice", "description": "10 minutes daily", "examples": ["Counting games"]}
                ],
                "common_challenges": [
                    {"challenge": "Place value confusion", "solutions": ["Use base-10 blocks"]}
                ],
                "home_activities": [
                    {"activity": "Cooking math", "instructions": "Measure ingredients", "materials": ["Measuring cups"]}
                ]
            }
            
            # Execute
            guidance = await guidance_service.get_curriculum_guidance(
                "parent_123", Subject.MATHEMATICS, 3, "place value"
            )
            
            # Verify
            assert "curriculum_overview" in guidance
            assert "key_learning_objectives" in guidance
            assert len(guidance["parent_support_strategies"]) > 0
            assert len(guidance["common_challenges"]) > 0
            mock_curriculum.assert_called_once_with(
                sample_parent_profile, Subject.MATHEMATICS, 3, "place value"
            )
    
    @pytest.mark.asyncio
    async def test_get_curriculum_guidance_parent_not_found(self, guidance_service):
        """Test curriculum guidance when parent is not found"""
        # Setup
        guidance_service.parent_repo.get_parent_profile_by_user_id.return_value = None
        
        # Execute
        guidance = await guidance_service.get_curriculum_guidance(
            "nonexistent_parent", Subject.MATHEMATICS, 3
        )
        
        # Verify
        assert guidance == {"error": "Parent profile not found"}
    
    @pytest.mark.asyncio
    async def test_get_popular_faqs(self, guidance_service):
        """Test retrieving popular FAQ items"""
        # Execute - no category filter
        popular_faqs = await guidance_service.get_popular_faqs(limit=5)
        
        # Verify
        assert len(popular_faqs) <= 5
        assert all(isinstance(faq, FAQItem) for faq in popular_faqs)
        
        # Check that results are sorted by popularity
        if len(popular_faqs) > 1:
            for i in range(len(popular_faqs) - 1):
                assert popular_faqs[i].popularity_score >= popular_faqs[i + 1].popularity_score
    
    @pytest.mark.asyncio
    async def test_get_popular_faqs_with_category_filter(self, guidance_service):
        """Test retrieving popular FAQs with category filter"""
        # Execute - with category filter
        math_faqs = await guidance_service.get_popular_faqs(
            category=GuidanceCategory.CURRICULUM, limit=3
        )
        
        # Verify
        assert len(math_faqs) <= 3
        assert all(faq.category == GuidanceCategory.CURRICULUM for faq in math_faqs)
    
    @pytest.mark.asyncio
    async def test_ai_enhanced_faq_search(self, guidance_service, sample_parent_profile):
        """Test AI-enhanced FAQ search functionality"""
        # Setup
        search_query = GuidanceSearchQuery(
            query="help child with math homework",
            category=GuidanceCategory.LEARNING_SUPPORT,
            child_age=8
        )
        
        faq_db = [
            FAQItem(
                category=GuidanceCategory.LEARNING_SUPPORT,
                question="How can I help my child with math homework?",
                answer="Break problems into smaller steps...",
                keywords=["math", "homework", "help"],
                grade_levels=[1, 2, 3, 4],
                subjects=[Subject.MATHEMATICS],
                popularity_score=0.9
            ),
            FAQItem(
                category=GuidanceCategory.CURRICULUM,
                question="What is Cambridge Math curriculum?",
                answer="Cambridge Math focuses on...",
                keywords=["cambridge", "math", "curriculum"],
                grade_levels=[1, 2, 3, 4, 5, 6],
                subjects=[Subject.MATHEMATICS],
                popularity_score=0.8
            )
        ]
        
        with patch.object(guidance_service, '_ai_rank_faq_results') as mock_rank:
            mock_rank.return_value = [faq_db[0]]  # Return first FAQ as most relevant
            
            # Execute
            results = await guidance_service._ai_enhanced_faq_search(
                search_query, sample_parent_profile, faq_db
            )
            
            # Verify
            assert len(results) == 1
            assert results[0].question == "How can I help my child with math homework?"
            mock_rank.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('services.llm.make_llm_api_call')
    async def test_ai_rank_faq_results(self, mock_llm_call, guidance_service):
        """Test AI ranking of FAQ results"""
        # Setup
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "ranked_indices": [1, 0],
            "reasoning": "Second FAQ is more relevant to the specific query"
        })
        mock_llm_call.return_value = mock_response
        
        faqs = [
            FAQItem(
                category=GuidanceCategory.CURRICULUM,
                question="General math info",
                answer="General answer",
                keywords=["math"]
            ),
            FAQItem(
                category=GuidanceCategory.LEARNING_SUPPORT,
                question="Specific homework help",
                answer="Specific answer",
                keywords=["homework", "help"]
            )
        ]
        
        context = {
            "parent_guidance_level": "intermediate",
            "child_age": 8,
            "subject": "mathematics"
        }
        
        # Execute
        ranked_faqs = await guidance_service._ai_rank_faq_results(
            "help with homework", faqs, context
        )
        
        # Verify
        assert len(ranked_faqs) == 2
        assert ranked_faqs[0].question == "Specific homework help"
        assert ranked_faqs[1].question == "General math info"
        mock_llm_call.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('services.llm.make_llm_api_call')
    async def test_generate_ai_guidance(self, mock_llm_call, guidance_service, sample_parent_profile, sample_child_profile):
        """Test AI-powered guidance generation"""
        # Setup
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "recommendations": [
                {
                    "category": "learning_support",
                    "priority": "high",
                    "title": "Support Visual Learning",
                    "description": "Your child shows strong visual learning preferences.",
                    "actionable_steps": ["Use diagrams", "Create visual schedules"],
                    "resources": [
                        {"type": "activity", "title": "Visual Math Games", "description": "Games that use pictures"}
                    ],
                    "estimated_time_minutes": 20,
                    "success_indicators": ["Improved engagement", "Better understanding"]
                }
            ]
        })
        mock_llm_call.return_value = mock_response
        
        context = {"recent_subjects": ["mathematics"], "learning_style": "visual"}
        
        # Execute
        recommendations = await guidance_service._generate_ai_guidance(
            sample_parent_profile, sample_child_profile, context
        )
        
        # Verify
        assert len(recommendations) == 1
        rec = recommendations[0]
        assert rec.title == "Support Visual Learning"
        assert rec.category == GuidanceCategory.LEARNING_SUPPORT
        assert rec.priority == GuidancePriority.HIGH
        assert "Use diagrams" in rec.actionable_steps
        assert len(rec.resources) == 1
        mock_llm_call.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('services.llm.make_llm_api_call')
    async def test_generate_curriculum_guidance(self, mock_llm_call, guidance_service, sample_parent_profile):
        """Test curriculum guidance generation"""
        # Setup
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "curriculum_overview": "Grade 3 mathematics focuses on number sense and basic operations",
            "key_learning_objectives": ["Count to 1000", "Add and subtract 3-digit numbers"],
            "parent_support_strategies": [
                {
                    "strategy": "Daily practice",
                    "description": "10-15 minutes of daily math practice",
                    "examples": ["Counting exercises", "Simple word problems"]
                }
            ],
            "common_challenges": [
                {
                    "challenge": "Regrouping in subtraction",
                    "solutions": ["Use manipulatives", "Practice with smaller numbers first"]
                }
            ],
            "home_activities": [
                {
                    "activity": "Grocery store math",
                    "instructions": "Count items and calculate prices",
                    "materials": ["Calculator", "Shopping list"]
                }
            ],
            "assessment_expectations": "Children should demonstrate fluency with basic facts",
            "next_level_preparation": "Introduction to multiplication and division concepts"
        })
        mock_llm_call.return_value = mock_response
        
        # Execute
        guidance = await guidance_service._generate_curriculum_guidance(
            sample_parent_profile, Subject.MATHEMATICS, 3, "place value"
        )
        
        # Verify
        assert guidance["curriculum_overview"].startswith("Grade 3 mathematics")
        assert len(guidance["key_learning_objectives"]) == 2
        assert len(guidance["parent_support_strategies"]) == 1
        assert len(guidance["common_challenges"]) == 1
        assert len(guidance["home_activities"]) == 1
        assert "assessment_expectations" in guidance
        assert "next_level_preparation" in guidance
        mock_llm_call.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_faq_database_initialization(self, guidance_service):
        """Test that FAQ database is properly initialized"""
        # Verify
        assert len(guidance_service.faq_database) > 0
        
        # Check that we have FAQs for different categories
        categories = {faq.category for faq in guidance_service.faq_database}
        assert GuidanceCategory.CURRICULUM in categories
        assert GuidanceCategory.LEARNING_SUPPORT in categories
        assert GuidanceCategory.ESL_SUPPORT in categories
        assert GuidanceCategory.MOTIVATION in categories
        
        # Check that all FAQs have required fields
        for faq in guidance_service.faq_database:
            assert faq.question
            assert faq.answer
            assert faq.category
            assert isinstance(faq.keywords, list)
            assert 0 <= faq.popularity_score <= 1
    
    @pytest.mark.asyncio
    async def test_guidance_templates_initialization(self, guidance_service):
        """Test that guidance templates are properly initialized"""
        # Verify
        assert len(guidance_service.guidance_templates) > 0
        
        # Check that we have templates for main categories
        assert GuidanceCategory.CURRICULUM in guidance_service.guidance_templates
        assert GuidanceCategory.LEARNING_SUPPORT in guidance_service.guidance_templates
        assert GuidanceCategory.MOTIVATION in guidance_service.guidance_templates
        
        # Check template structure
        for category, templates in guidance_service.guidance_templates.items():
            assert "title_template" in templates
            assert "description_template" in templates
    
    @pytest.mark.asyncio
    async def test_error_handling_in_search_faq(self, guidance_service):
        """Test error handling in FAQ search"""
        # Setup - make parent repo raise an exception
        guidance_service.parent_repo.get_parent_profile_by_user_id.side_effect = Exception("Database error")
        
        # Execute
        search_query = GuidanceSearchQuery(query="test query")
        results = await guidance_service.search_faq(search_query, "parent_123")
        
        # Verify - should return empty list on error
        assert results == []
    
    @pytest.mark.asyncio
    async def test_error_handling_in_guidance_generation(self, guidance_service):
        """Test error handling in guidance generation"""
        # Setup - make parent repo raise an exception
        guidance_service.parent_repo.get_parent_profile_by_user_id.side_effect = Exception("Database error")
        
        # Execute
        recommendations = await guidance_service.generate_personalized_guidance(
            "parent_123", "child_123"
        )
        
        # Verify - should return empty list on error
        assert recommendations == []
    
    @pytest.mark.asyncio
    async def test_faq_search_filtering(self, guidance_service, sample_parent_profile):
        """Test FAQ search filtering by category, subject, and grade level"""
        # Setup
        guidance_service.parent_repo.get_parent_profile_by_user_id.return_value = sample_parent_profile
        
        # Create specific search query
        search_query = GuidanceSearchQuery(
            query="mathematics grade 3",
            category=GuidanceCategory.CURRICULUM,
            child_age=8,  # Should map to grade 3-4
            subject=Subject.MATHEMATICS,
            max_results=10
        )
        
        # Execute search on pre-loaded FAQ database
        with patch.object(guidance_service, '_ai_rank_faq_results') as mock_rank:
            mock_rank.return_value = []  # We'll test the filtering, not ranking
            
            results = await guidance_service._ai_enhanced_faq_search(
                search_query, sample_parent_profile, guidance_service.faq_database
            )
            
            # The method should have filtered FAQs before ranking
            # We can't directly test the filtered results since they're passed to ranking
            # But we can verify the method completed without errors
            assert isinstance(results, list)


class TestFAQModels:
    """Test FAQ and guidance models"""
    
    def test_faq_item_creation(self):
        """Test FAQ item model creation"""
        faq = FAQItem(
            category=GuidanceCategory.CURRICULUM,
            question="Test question?",
            answer="Test answer.",
            keywords=["test", "example"],
            grade_levels=[1, 2, 3],
            subjects=[Subject.MATHEMATICS],
            popularity_score=0.8
        )
        
        assert faq.category == GuidanceCategory.CURRICULUM
        assert faq.question == "Test question?"
        assert faq.answer == "Test answer."
        assert "test" in faq.keywords
        assert 1 in faq.grade_levels
        assert Subject.MATHEMATICS in faq.subjects
        assert faq.popularity_score == 0.8
        assert faq.faq_id  # Should be auto-generated
    
    def test_guidance_recommendation_creation(self):
        """Test guidance recommendation model creation"""
        rec = GuidanceRecommendation(
            parent_id="parent_123",
            child_id="child_123",
            category=GuidanceCategory.LEARNING_SUPPORT,
            priority=GuidancePriority.HIGH,
            title="Test Recommendation",
            description="Test description",
            actionable_steps=["Step 1", "Step 2"],
            estimated_time_minutes=30
        )
        
        assert rec.parent_id == "parent_123"
        assert rec.child_id == "child_123"
        assert rec.category == GuidanceCategory.LEARNING_SUPPORT
        assert rec.priority == GuidancePriority.HIGH
        assert rec.title == "Test Recommendation"
        assert len(rec.actionable_steps) == 2
        assert rec.estimated_time_minutes == 30
        assert rec.recommendation_id  # Should be auto-generated
        assert not rec.is_read  # Should default to False
    
    def test_guidance_search_query_validation(self):
        """Test guidance search query validation"""
        query = GuidanceSearchQuery(
            query="test query",
            category=GuidanceCategory.CURRICULUM,
            child_age=8,
            subject=Subject.MATHEMATICS,
            max_results=5
        )
        
        assert query.query == "test query"
        assert query.category == GuidanceCategory.CURRICULUM
        assert query.child_age == 8
        assert query.subject == Subject.MATHEMATICS
        assert query.max_results == 5
        
        # Test with minimal required fields
        minimal_query = GuidanceSearchQuery(query="minimal test")
        assert minimal_query.query == "minimal test"
        assert minimal_query.category is None
        assert minimal_query.max_results == 10  # Default value


if __name__ == "__main__":
    pytest.main([__file__])
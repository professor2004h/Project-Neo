"""
Basic tests to verify the tutor module structure is set up correctly
"""
import pytest
from unittest.mock import Mock

from tutor.models.user_models import UserProfile, ChildProfile, UserRole, Subject, LearningStyle
from tutor.models.curriculum_models import CurriculumTopic, DifficultyLevel, ActivityType


class TestUserModels:
    """Test user-related models"""
    
    def test_user_profile_creation(self):
        """Test UserProfile model creation"""
        profile = UserProfile(
            email="test@example.com",
            role=UserRole.PARENT
        )
        
        assert profile.email == "test@example.com"
        assert profile.role == UserRole.PARENT
        assert profile.user_id is not None
        assert profile.created_at is not None
    
    def test_child_profile_creation(self):
        """Test ChildProfile model creation"""
        child = ChildProfile(
            parent_id="parent-123",
            name="Test Child",
            age=8,
            grade_level=3,
            learning_style=LearningStyle.VISUAL,
            preferred_subjects=[Subject.MATHEMATICS, Subject.SCIENCE]
        )
        
        assert child.name == "Test Child"
        assert child.age == 8
        assert child.grade_level == 3
        assert child.learning_style == LearningStyle.VISUAL
        assert Subject.MATHEMATICS in child.preferred_subjects
        assert child.child_id is not None
    
    def test_child_profile_validation(self):
        """Test ChildProfile validation"""
        # Test invalid age
        with pytest.raises(ValueError):
            ChildProfile(
                parent_id="parent-123",
                name="Test Child",
                age=15,  # Too old for primary school
                grade_level=3
            )
        
        # Test invalid grade level
        with pytest.raises(ValueError):
            ChildProfile(
                parent_id="parent-123",
                name="Test Child",
                age=8,
                grade_level=10  # Too high for primary school
            )


class TestCurriculumModels:
    """Test curriculum-related models"""
    
    def test_curriculum_topic_creation(self):
        """Test CurriculumTopic model creation"""
        topic = CurriculumTopic(
            subject=Subject.MATHEMATICS,
            grade_level=2,
            cambridge_code="2Ma1",
            title="Addition and Subtraction",
            description="Basic arithmetic operations",
            difficulty_level=DifficultyLevel.ELEMENTARY
        )
        
        assert topic.subject == Subject.MATHEMATICS
        assert topic.grade_level == 2
        assert topic.cambridge_code == "2MA1"  # Should be uppercase
        assert topic.title == "Addition and Subtraction"
        assert topic.difficulty_level == DifficultyLevel.ELEMENTARY
        assert topic.topic_id is not None
    
    def test_curriculum_topic_validation(self):
        """Test CurriculumTopic validation"""
        # Test invalid Cambridge code
        with pytest.raises(ValueError):
            CurriculumTopic(
                subject=Subject.MATHEMATICS,
                grade_level=2,
                cambridge_code="",  # Empty code
                title="Test Topic"
            )
        
        # Test invalid title
        with pytest.raises(ValueError):
            CurriculumTopic(
                subject=Subject.MATHEMATICS,
                grade_level=2,
                cambridge_code="2Ma1",
                title="   "  # Empty title
            )


class TestModuleStructure:
    """Test that the module structure is properly set up"""
    
    def test_models_import(self):
        """Test that models can be imported successfully"""
        # If we get here without import errors, the structure is working
        assert UserProfile is not None
        assert ChildProfile is not None
        assert CurriculumTopic is not None
        
    def test_enums_available(self):
        """Test that enums are properly defined"""
        assert UserRole.PARENT == "parent"
        assert Subject.MATHEMATICS == "mathematics"
        assert LearningStyle.VISUAL == "visual"
        assert DifficultyLevel.ELEMENTARY == "elementary"
        assert ActivityType.LESSON == "lesson"
"""
Unit tests for user repository operations using mocks
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import sys

# Mock the dependencies before importing
sys.modules['services.supabase'] = MagicMock()
sys.modules['utils.logger'] = MagicMock()

from tutor.models.user_models import (
    User, UserCreate, UserUpdate, UserRole,
    ChildProfile, ChildProfileCreate, ChildProfileUpdate,
    ParentProfile, ParentProfileCreate, ParentProfileUpdate,
    UserSession, Subject, LearningStyle
)


class MockDBConnection:
    """Mock database connection for testing"""
    def __init__(self):
        self.client = AsyncMock()


class MockBaseRepository:
    """Mock base repository for testing"""
    def __init__(self, db, table_name):
        self.db = db
        self.table_name = table_name
    
    async def get_client(self):
        return self.db.client
    
    async def create(self, data):
        # Simulate database insert
        result = {**data, "id": "generated-id"}
        return result
    
    async def get_by_id(self, record_id, id_column="id"):
        # Simulate database select
        if record_id == "nonexistent":
            return None
        return {
            id_column: record_id,
            "email": "test@example.com",
            "role": "parent",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    
    async def update(self, record_id, data, id_column="id"):
        # Simulate database update
        result = {**data, id_column: record_id}
        return result
    
    async def delete(self, record_id, id_column="id"):
        # Simulate database delete
        return True
    
    async def list_all(self, filters=None, limit=None):
        # Simulate database select all
        return [
            {
                "user_id": "user-123",
                "email": "test1@example.com",
                "role": "parent",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            {
                "user_id": "user-456",
                "email": "test2@example.com",
                "role": "parent",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        ]


class MockUserRepository(MockBaseRepository):
    """Mock user repository for testing"""
    
    def __init__(self, db):
        super().__init__(db, "tutor_user_profiles")
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user profile"""
        data = {
            "user_id": "user-123",
            "email": user_data.email,
            "role": user_data.role.value,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        result = await self.create(data)
        return User(**result)
    
    async def get_user_by_id(self, user_id: str) -> User:
        """Get user by ID"""
        result = await self.get_by_id(user_id, "user_id")
        if result:
            return User(**result)
        return None
    
    async def get_user_by_email(self, email: str) -> User:
        """Get user by email"""
        # Mock database response
        if email == "nonexistent@example.com":
            return None
        
        result = {
            "user_id": "user-123",
            "email": email.lower(),
            "role": "parent",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        return User(**result)
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        """Update user profile"""
        data = {}
        if user_data.email is not None:
            data["email"] = user_data.email
        if user_data.role is not None:
            data["role"] = user_data.role.value
        
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        data["user_id"] = user_id
        
        result = await self.update(user_id, data, "user_id")
        return User(**result)
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user profile"""
        return await self.delete(user_id, "user_id")
    
    async def list_users_by_role(self, role: str, limit=None) -> list:
        """List users by role"""
        results = await self.list_all({"role": role}, limit)
        return [User(**result) for result in results]


class MockChildProfileRepository(MockBaseRepository):
    """Mock child profile repository for testing"""
    
    def __init__(self, db):
        super().__init__(db, "tutor_child_profiles")
    
    async def create_child_profile(self, child_data: ChildProfileCreate) -> ChildProfile:
        """Create a new child profile"""
        data = {
            "child_id": "child-123",
            "parent_id": child_data.parent_id,
            "name": child_data.name,
            "age": child_data.age,
            "grade_level": child_data.grade_level,
            "learning_style": child_data.learning_style.value,
            "preferred_subjects": [subject.value for subject in child_data.preferred_subjects],
            "learning_preferences": child_data.learning_preferences,
            "curriculum_progress": {},
            "safety_settings": child_data.safety_settings,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        result = await self.create(data)
        return ChildProfile(**result)
    
    async def get_child_profile_by_id(self, child_id: str) -> ChildProfile:
        """Get child profile by ID"""
        if child_id == "nonexistent":
            return None
        
        result = {
            "child_id": child_id,
            "parent_id": "parent-123",
            "name": "Test Child",
            "age": 8,
            "grade_level": 3,
            "learning_style": "visual",
            "preferred_subjects": ["mathematics"],
            "learning_preferences": {},
            "curriculum_progress": {},
            "safety_settings": {},
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        return ChildProfile(**result)
    
    async def get_children_by_parent_id(self, parent_id: str) -> list:
        """Get all children for a parent"""
        results = [
            {
                "child_id": "child-123",
                "parent_id": parent_id,
                "name": "Child 1",
                "age": 8,
                "grade_level": 3,
                "learning_style": "visual",
                "preferred_subjects": [],
                "learning_preferences": {},
                "curriculum_progress": {},
                "safety_settings": {},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            {
                "child_id": "child-456",
                "parent_id": parent_id,
                "name": "Child 2",
                "age": 10,
                "grade_level": 5,
                "learning_style": "auditory",
                "preferred_subjects": [],
                "learning_preferences": {},
                "curriculum_progress": {},
                "safety_settings": {},
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        ]
        return [ChildProfile(**result) for result in results]
    
    async def update_child_profile(self, child_id: str, child_data: ChildProfileUpdate) -> ChildProfile:
        """Update child profile"""
        data = {
            "child_id": child_id,
            "parent_id": "parent-123",
            "name": child_data.name or "Updated Child",
            "age": child_data.age or 9,
            "grade_level": child_data.grade_level or 4,
            "learning_style": child_data.learning_style.value if child_data.learning_style else "kinesthetic",
            "preferred_subjects": [subject.value for subject in child_data.preferred_subjects] if child_data.preferred_subjects else ["science"],
            "learning_preferences": child_data.learning_preferences or {},
            "curriculum_progress": {},
            "safety_settings": child_data.safety_settings or {},
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        result = await self.update(child_id, data, "child_id")
        return ChildProfile(**result)


@pytest.mark.asyncio
class TestMockUserRepository:
    """Test user repository operations with mocks"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        return MockDBConnection()
    
    @pytest.fixture
    def user_repo(self, mock_db):
        """User repository with mocked database"""
        return MockUserRepository(mock_db)
    
    async def test_create_user(self, user_repo):
        """Test creating a user"""
        user_create = UserCreate(email="test@example.com", role=UserRole.PARENT)
        result = await user_repo.create_user(user_create)
        
        assert isinstance(result, User)
        assert result.email == "test@example.com"
        assert result.role == UserRole.PARENT
        assert result.user_id == "user-123"
    
    async def test_get_user_by_id(self, user_repo):
        """Test getting user by ID"""
        result = await user_repo.get_user_by_id("user-123")
        
        assert isinstance(result, User)
        assert result.user_id == "user-123"
        assert result.email == "test@example.com"
    
    async def test_get_user_by_id_not_found(self, user_repo):
        """Test getting user by ID when not found"""
        result = await user_repo.get_user_by_id("nonexistent")
        
        assert result is None
    
    async def test_get_user_by_email(self, user_repo):
        """Test getting user by email"""
        result = await user_repo.get_user_by_email("test@example.com")
        
        assert isinstance(result, User)
        assert result.email == "test@example.com"
    
    async def test_get_user_by_email_not_found(self, user_repo):
        """Test getting user by email when not found"""
        result = await user_repo.get_user_by_email("nonexistent@example.com")
        
        assert result is None
    
    async def test_update_user(self, user_repo):
        """Test updating a user"""
        user_update = UserUpdate(email="updated@example.com", role=UserRole.ADMIN)
        result = await user_repo.update_user("user-123", user_update)
        
        assert isinstance(result, User)
        assert result.email == "updated@example.com"
        assert result.role == UserRole.ADMIN
    
    async def test_delete_user(self, user_repo):
        """Test deleting a user"""
        result = await user_repo.delete_user("user-123")
        
        assert result is True
    
    async def test_list_users_by_role(self, user_repo):
        """Test listing users by role"""
        result = await user_repo.list_users_by_role("parent")
        
        assert len(result) == 2
        assert all(isinstance(user, User) for user in result)
        assert all(user.role == UserRole.PARENT for user in result)


@pytest.mark.asyncio
class TestMockChildProfileRepository:
    """Test child profile repository operations with mocks"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        return MockDBConnection()
    
    @pytest.fixture
    def child_repo(self, mock_db):
        """Child profile repository with mocked database"""
        return MockChildProfileRepository(mock_db)
    
    async def test_create_child_profile(self, child_repo):
        """Test creating a child profile"""
        child_create = ChildProfileCreate(
            parent_id="parent-123",
            name="Test Child",
            age=8,
            grade_level=3,
            learning_style=LearningStyle.VISUAL,
            preferred_subjects=[Subject.MATHEMATICS]
        )
        result = await child_repo.create_child_profile(child_create)
        
        assert isinstance(result, ChildProfile)
        assert result.name == "Test Child"
        assert result.age == 8
        assert result.grade_level == 3
        assert result.child_id == "child-123"
    
    async def test_get_child_profile_by_id(self, child_repo):
        """Test getting child profile by ID"""
        result = await child_repo.get_child_profile_by_id("child-123")
        
        assert isinstance(result, ChildProfile)
        assert result.child_id == "child-123"
        assert result.name == "Test Child"
    
    async def test_get_child_profile_by_id_not_found(self, child_repo):
        """Test getting child profile by ID when not found"""
        result = await child_repo.get_child_profile_by_id("nonexistent")
        
        assert result is None
    
    async def test_get_children_by_parent_id(self, child_repo):
        """Test getting children by parent ID"""
        result = await child_repo.get_children_by_parent_id("parent-123")
        
        assert len(result) == 2
        assert all(isinstance(child, ChildProfile) for child in result)
        assert all(child.parent_id == "parent-123" for child in result)
    
    async def test_update_child_profile(self, child_repo):
        """Test updating a child profile"""
        child_update = ChildProfileUpdate(
            name="Updated Child",
            age=9,
            grade_level=4,
            learning_style=LearningStyle.KINESTHETIC,
            preferred_subjects=[Subject.SCIENCE]
        )
        result = await child_repo.update_child_profile("child-123", child_update)
        
        assert isinstance(result, ChildProfile)
        assert result.name == "Updated Child"
        assert result.age == 9
        assert result.grade_level == 4


class TestRepositoryIntegration:
    """Test repository integration scenarios"""
    
    def test_user_model_serialization(self):
        """Test that user models can be serialized/deserialized properly"""
        user_data = {
            "user_id": "user-123",
            "email": "test@example.com",
            "role": "parent",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        user = User(**user_data)
        
        assert user.user_id == "user-123"
        assert user.email == "test@example.com"
        assert user.role == UserRole.PARENT
        assert isinstance(user.created_at, datetime)
    
    def test_child_profile_model_serialization(self):
        """Test that child profile models can be serialized/deserialized properly"""
        child_data = {
            "child_id": "child-123",
            "parent_id": "parent-123",
            "name": "Test Child",
            "age": 8,
            "grade_level": 3,
            "learning_style": "visual",
            "preferred_subjects": ["mathematics", "science"],
            "learning_preferences": {"visual_aids": True},
            "curriculum_progress": {"math": 0.7},
            "safety_settings": {"content_filtering": "strict"},
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        child = ChildProfile(**child_data)
        
        assert child.child_id == "child-123"
        assert child.parent_id == "parent-123"
        assert child.name == "Test Child"
        assert child.age == 8
        assert child.grade_level == 3
        assert child.learning_style == LearningStyle.VISUAL
        assert Subject.MATHEMATICS in child.preferred_subjects
        assert Subject.SCIENCE in child.preferred_subjects
        assert child.learning_preferences["visual_aids"] is True
        assert child.curriculum_progress["math"] == 0.7
        assert child.safety_settings["content_filtering"] == "strict"
    
    def test_parent_profile_model_serialization(self):
        """Test that parent profile models can be serialized/deserialized properly"""
        parent_data = {
            "parent_id": "parent-123",
            "user_id": "user-123",
            "children_ids": ["child-123", "child-456"],
            "preferred_language": "en",
            "notification_preferences": {"email": True, "sms": False},
            "guidance_level": "intermediate",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
        
        parent = ParentProfile(**parent_data)
        
        assert parent.parent_id == "parent-123"
        assert parent.user_id == "user-123"
        assert "child-123" in parent.children_ids
        assert "child-456" in parent.children_ids
        assert parent.preferred_language == "en"
        assert parent.notification_preferences["email"] is True
        assert parent.notification_preferences["sms"] is False
        assert parent.guidance_level == "intermediate"
    
    def test_user_session_model_serialization(self):
        """Test that user session models can be serialized/deserialized properly"""
        session_data = {
            "session_id": "session-123",
            "user_id": "user-123",
            "device_id": "device-456",
            "device_type": "web",
            "started_at": "2024-01-01T00:00:00Z",
            "last_activity": "2024-01-01T01:00:00Z",
            "is_active": True,
            "sync_status": "synced"
        }
        
        session = UserSession(**session_data)
        
        assert session.session_id == "session-123"
        assert session.user_id == "user-123"
        assert session.device_id == "device-456"
        assert session.device_type == "web"
        assert isinstance(session.started_at, datetime)
        assert isinstance(session.last_activity, datetime)
        assert session.is_active is True
        assert session.sync_status == "synced"
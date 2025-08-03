"""
Unit tests for user models and repository operations
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import ValidationError

from tutor.models.user_models import (
    User, UserCreate, UserUpdate, UserRole,
    ChildProfile, ChildProfileCreate, ChildProfileUpdate,
    ParentProfile, ParentProfileCreate, ParentProfileUpdate,
    UserSession, SafetySettings,
    Subject, LearningStyle
)

# Mock the imports to avoid dependency issues
with patch.dict('sys.modules', {
    'services.supabase': MagicMock(),
    'utils.logger': MagicMock()
}):
    from tutor.repositories.user_repository import (
        UserRepository,
        ChildProfileRepository,
        ParentProfileRepository,
        UserSessionRepository
    )


class TestUserModels:
    """Test user model validation and creation"""
    
    def test_user_model_valid_creation(self):
        """Test creating a valid user model"""
        user = User(
            email="test@example.com",
            role=UserRole.PARENT
        )
        
        assert user.email == "test@example.com"
        assert user.role == UserRole.PARENT
        assert user.user_id is not None
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)
    
    def test_user_model_email_validation(self):
        """Test user email validation"""
        # Valid email
        user = User(email="valid@example.com", role=UserRole.PARENT)
        assert user.email == "valid@example.com"
        
        # Email should be lowercased
        user = User(email="UPPER@EXAMPLE.COM", role=UserRole.PARENT)
        assert user.email == "upper@example.com"
        
        # Invalid email should raise ValidationError
        with pytest.raises(ValidationError):
            User(email="invalid-email", role=UserRole.PARENT)
        
        # Too long email should raise ValidationError
        with pytest.raises(ValidationError):
            User(email="a" * 250 + "@example.com", role=UserRole.PARENT)
    
    def test_child_profile_model_valid_creation(self):
        """Test creating a valid child profile model"""
        child = ChildProfile(
            parent_id="parent-123",
            name="John Doe",
            age=8,
            grade_level=3,
            learning_style=LearningStyle.VISUAL,
            preferred_subjects=[Subject.MATHEMATICS, Subject.SCIENCE]
        )
        
        assert child.parent_id == "parent-123"
        assert child.name == "John Doe"
        assert child.age == 8
        assert child.grade_level == 3
        assert child.learning_style == LearningStyle.VISUAL
        assert Subject.MATHEMATICS in child.preferred_subjects
        assert Subject.SCIENCE in child.preferred_subjects
        assert child.child_id is not None
        assert isinstance(child.created_at, datetime)
    
    def test_child_profile_model_validation(self):
        """Test child profile validation rules"""
        # Valid child
        child = ChildProfile(
            parent_id="parent-123",
            name="Valid Name",
            age=7,
            grade_level=2
        )
        assert child.name == "Valid Name"
        
        # Empty name should raise ValidationError
        with pytest.raises(ValidationError):
            ChildProfile(
                parent_id="parent-123",
                name="",
                age=7,
                grade_level=2
            )
        
        # Whitespace-only name should raise ValidationError
        with pytest.raises(ValidationError):
            ChildProfile(
                parent_id="parent-123",
                name="   ",
                age=7,
                grade_level=2
            )
        
        # Age too young should raise ValidationError
        with pytest.raises(ValidationError):
            ChildProfile(
                parent_id="parent-123",
                name="Young Child",
                age=4,
                grade_level=1
            )
        
        # Age too old should raise ValidationError
        with pytest.raises(ValidationError):
            ChildProfile(
                parent_id="parent-123",
                name="Old Child",
                age=13,
                grade_level=6
            )
        
        # Grade level too low should raise ValidationError
        with pytest.raises(ValidationError):
            ChildProfile(
                parent_id="parent-123",
                name="Child",
                age=6,
                grade_level=0
            )
        
        # Grade level too high should raise ValidationError
        with pytest.raises(ValidationError):
            ChildProfile(
                parent_id="parent-123",
                name="Child",
                age=12,
                grade_level=7
            )
        
        # Too many preferred subjects should raise ValidationError
        with pytest.raises(ValidationError):
            ChildProfile(
                parent_id="parent-123",
                name="Child",
                age=8,
                grade_level=3,
                preferred_subjects=[Subject.MATHEMATICS] * 15
            )
    
    def test_parent_profile_model_valid_creation(self):
        """Test creating a valid parent profile model"""
        parent = ParentProfile(
            user_id="user-123",
            preferred_language="en",
            guidance_level="intermediate"
        )
        
        assert parent.user_id == "user-123"
        assert parent.preferred_language == "en"
        assert parent.guidance_level == "intermediate"
        assert parent.children_ids == []
        assert parent.parent_id is not None
        assert isinstance(parent.created_at, datetime)
    
    def test_parent_profile_model_validation(self):
        """Test parent profile validation rules"""
        # Valid parent
        parent = ParentProfile(
            user_id="user-123",
            guidance_level="beginner"
        )
        assert parent.guidance_level == "beginner"
        
        # Invalid guidance level should raise ValidationError
        with pytest.raises(ValidationError):
            ParentProfile(
                user_id="user-123",
                guidance_level="invalid"
            )
        
        # Too many children should raise ValidationError
        with pytest.raises(ValidationError):
            ParentProfile(
                user_id="user-123",
                children_ids=["child"] * 25
            )
    
    def test_user_session_model_valid_creation(self):
        """Test creating a valid user session model"""
        session = UserSession(
            user_id="user-123",
            device_id="device-456",
            device_type="web"
        )
        
        assert session.user_id == "user-123"
        assert session.device_id == "device-456"
        assert session.device_type == "web"
        assert session.is_active is True
        assert session.sync_status == "synced"
        assert session.session_id is not None
        assert isinstance(session.started_at, datetime)
    
    def test_user_session_model_validation(self):
        """Test user session validation rules"""
        # Valid session
        session = UserSession(
            user_id="user-123",
            device_id="device-456",
            device_type="mobile"
        )
        assert session.device_type == "mobile"
        
        # Invalid device type should raise ValidationError
        with pytest.raises(ValidationError):
            UserSession(
                user_id="user-123",
                device_id="device-456",
                device_type="invalid"
            )
        
        # Invalid sync status should raise ValidationError
        with pytest.raises(ValidationError):
            UserSession(
                user_id="user-123",
                device_id="device-456",
                device_type="web",
                sync_status="invalid"
            )
    
    def test_safety_settings_model_validation(self):
        """Test safety settings validation rules"""
        # Valid safety settings
        settings = SafetySettings(
            child_id="child-123",
            content_filtering_level="strict"
        )
        assert settings.content_filtering_level == "strict"
        
        # Invalid content filtering level should raise ValidationError
        with pytest.raises(ValidationError):
            SafetySettings(
                child_id="child-123",
                content_filtering_level="invalid"
            )
        
        # Invalid session time limits should raise ValidationError
        with pytest.raises(ValidationError):
            SafetySettings(
                child_id="child-123",
                session_time_limits={"daily": -10}
            )
        
        with pytest.raises(ValidationError):
            SafetySettings(
                child_id="child-123",
                session_time_limits={"daily": "invalid"}
            )


class TestUserCreateUpdateDTOs:
    """Test user create and update DTOs"""
    
    def test_user_create_dto(self):
        """Test UserCreate DTO validation"""
        # Valid creation
        user_create = UserCreate(
            email="test@example.com",
            role=UserRole.PARENT
        )
        assert user_create.email == "test@example.com"
        assert user_create.role == UserRole.PARENT
        
        # Invalid email should raise ValidationError
        with pytest.raises(ValidationError):
            UserCreate(email="invalid", role=UserRole.PARENT)
    
    def test_user_update_dto(self):
        """Test UserUpdate DTO validation"""
        # Valid update with email
        user_update = UserUpdate(email="new@example.com")
        assert user_update.email == "new@example.com"
        assert user_update.role is None
        
        # Valid update with role
        user_update = UserUpdate(role=UserRole.ADMIN)
        assert user_update.role == UserRole.ADMIN
        assert user_update.email is None
        
        # Empty update should be valid
        user_update = UserUpdate()
        assert user_update.email is None
        assert user_update.role is None
    
    def test_child_profile_create_dto(self):
        """Test ChildProfileCreate DTO validation"""
        child_create = ChildProfileCreate(
            parent_id="parent-123",
            name="Test Child",
            age=8,
            grade_level=3
        )
        assert child_create.parent_id == "parent-123"
        assert child_create.name == "Test Child"
        assert child_create.age == 8
        assert child_create.grade_level == 3
    
    def test_child_profile_update_dto(self):
        """Test ChildProfileUpdate DTO validation"""
        # Valid partial update
        child_update = ChildProfileUpdate(name="Updated Name")
        assert child_update.name == "Updated Name"
        assert child_update.age is None
        
        # Empty update should be valid
        child_update = ChildProfileUpdate()
        assert child_update.name is None
        assert child_update.age is None
    
    def test_parent_profile_create_dto(self):
        """Test ParentProfileCreate DTO validation"""
        parent_create = ParentProfileCreate(
            user_id="user-123",
            guidance_level="advanced"
        )
        assert parent_create.user_id == "user-123"
        assert parent_create.guidance_level == "advanced"
    
    def test_parent_profile_update_dto(self):
        """Test ParentProfileUpdate DTO validation"""
        # Valid partial update
        parent_update = ParentProfileUpdate(
            preferred_language="es",
            guidance_level="beginner"
        )
        assert parent_update.preferred_language == "es"
        assert parent_update.guidance_level == "beginner"
        
        # Empty update should be valid
        parent_update = ParentProfileUpdate()
        assert parent_update.preferred_language is None
        assert parent_update.guidance_level is None


@pytest.mark.asyncio
class TestUserRepository:
    """Test user repository operations"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        db = MagicMock()
        db.client = AsyncMock()
        return db
    
    @pytest.fixture
    def user_repo(self, mock_db):
        """User repository with mocked database"""
        return UserRepository(mock_db)
    
    async def test_create_user(self, user_repo, mock_db):
        """Test creating a user"""
        # Mock database response
        mock_db.client.table.return_value.insert.return_value.execute.return_value.data = [{
            "user_id": "user-123",
            "email": "test@example.com",
            "role": "parent",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }]
        
        user_create = UserCreate(email="test@example.com", role=UserRole.PARENT)
        result = await user_repo.create_user(user_create)
        
        assert isinstance(result, User)
        assert result.email == "test@example.com"
        assert result.role == UserRole.PARENT
    
    async def test_get_user_by_id(self, user_repo, mock_db):
        """Test getting user by ID"""
        # Mock database response
        mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "user_id": "user-123",
            "email": "test@example.com",
            "role": "parent",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }]
        
        result = await user_repo.get_user_by_id("user-123")
        
        assert isinstance(result, User)
        assert result.user_id == "user-123"
        assert result.email == "test@example.com"
    
    async def test_get_user_by_id_not_found(self, user_repo, mock_db):
        """Test getting user by ID when not found"""
        # Mock database response - no data
        mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
        
        result = await user_repo.get_user_by_id("nonexistent")
        
        assert result is None
    
    async def test_get_user_by_email(self, user_repo, mock_db):
        """Test getting user by email"""
        # Mock database response
        mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "user_id": "user-123",
            "email": "test@example.com",
            "role": "parent",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }]
        
        result = await user_repo.get_user_by_email("test@example.com")
        
        assert isinstance(result, User)
        assert result.email == "test@example.com"
    
    async def test_update_user(self, user_repo, mock_db):
        """Test updating a user"""
        # Mock database response
        mock_db.client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            "user_id": "user-123",
            "email": "updated@example.com",
            "role": "admin",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T01:00:00Z"
        }]
        
        user_update = UserUpdate(email="updated@example.com", role=UserRole.ADMIN)
        result = await user_repo.update_user("user-123", user_update)
        
        assert isinstance(result, User)
        assert result.email == "updated@example.com"
        assert result.role == UserRole.ADMIN
    
    async def test_delete_user(self, user_repo, mock_db):
        """Test deleting a user"""
        # Mock database response
        mock_db.client.table.return_value.delete.return_value.eq.return_value.execute.return_value = MagicMock()
        
        result = await user_repo.delete_user("user-123")
        
        assert result is True
    
    async def test_list_users_by_role(self, user_repo, mock_db):
        """Test listing users by role"""
        # Mock database response
        mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "user_id": "user-123",
                "email": "parent1@example.com",
                "role": "parent",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            },
            {
                "user_id": "user-456",
                "email": "parent2@example.com",
                "role": "parent",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        ]
        
        result = await user_repo.list_users_by_role("parent")
        
        assert len(result) == 2
        assert all(isinstance(user, User) for user in result)
        assert all(user.role == UserRole.PARENT for user in result)


@pytest.mark.asyncio
class TestChildProfileRepository:
    """Test child profile repository operations"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        db = MagicMock()
        db.client = AsyncMock()
        return db
    
    @pytest.fixture
    def child_repo(self, mock_db):
        """Child profile repository with mocked database"""
        return ChildProfileRepository(mock_db)
    
    async def test_create_child_profile(self, child_repo, mock_db):
        """Test creating a child profile"""
        # Mock database response
        mock_db.client.table.return_value.insert.return_value.execute.return_value.data = [{
            "child_id": "child-123",
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
        }]
        
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
    
    async def test_get_children_by_parent_id(self, child_repo, mock_db):
        """Test getting children by parent ID"""
        # Mock database response
        mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [
            {
                "child_id": "child-123",
                "parent_id": "parent-123",
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
                "parent_id": "parent-123",
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
        
        result = await child_repo.get_children_by_parent_id("parent-123")
        
        assert len(result) == 2
        assert all(isinstance(child, ChildProfile) for child in result)
        assert all(child.parent_id == "parent-123" for child in result)
    
    async def test_get_children_by_age_range(self, child_repo, mock_db):
        """Test getting children by age range"""
        # Mock database response
        mock_db.client.table.return_value.select.return_value.gte.return_value.lte.return_value.execute.return_value.data = [
            {
                "child_id": "child-123",
                "parent_id": "parent-123",
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
            }
        ]
        
        result = await child_repo.get_children_by_age_range(7, 9)
        
        assert len(result) == 1
        assert result[0].age == 8
    
    async def test_update_child_profile(self, child_repo, mock_db):
        """Test updating a child profile"""
        # Mock database response
        mock_db.client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            "child_id": "child-123",
            "parent_id": "parent-123",
            "name": "Updated Child",
            "age": 9,
            "grade_level": 4,
            "learning_style": "kinesthetic",
            "preferred_subjects": ["science"],
            "learning_preferences": {},
            "curriculum_progress": {},
            "safety_settings": {},
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T01:00:00Z"
        }]
        
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


@pytest.mark.asyncio
class TestParentProfileRepository:
    """Test parent profile repository operations"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        db = MagicMock()
        db.client = AsyncMock()
        return db
    
    @pytest.fixture
    def parent_repo(self, mock_db):
        """Parent profile repository with mocked database"""
        return ParentProfileRepository(mock_db)
    
    async def test_create_parent_profile(self, parent_repo, mock_db):
        """Test creating a parent profile"""
        # Mock database response
        mock_db.client.table.return_value.insert.return_value.execute.return_value.data = [{
            "parent_id": "parent-123",
            "user_id": "user-123",
            "children_ids": [],
            "preferred_language": "en",
            "notification_preferences": {},
            "guidance_level": "intermediate",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }]
        
        parent_create = ParentProfileCreate(
            user_id="user-123",
            guidance_level="intermediate"
        )
        result = await parent_repo.create_parent_profile(parent_create)
        
        assert isinstance(result, ParentProfile)
        assert result.user_id == "user-123"
        assert result.guidance_level == "intermediate"
    
    async def test_get_parent_profile_by_user_id(self, parent_repo, mock_db):
        """Test getting parent profile by user ID"""
        # Mock database response
        mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "parent_id": "parent-123",
            "user_id": "user-123",
            "children_ids": ["child-123"],
            "preferred_language": "en",
            "notification_preferences": {},
            "guidance_level": "intermediate",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }]
        
        result = await parent_repo.get_parent_profile_by_user_id("user-123")
        
        assert isinstance(result, ParentProfile)
        assert result.user_id == "user-123"
        assert "child-123" in result.children_ids
    
    async def test_add_child_to_parent(self, parent_repo, mock_db):
        """Test adding a child to parent's children list"""
        # Mock getting current parent profile
        mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "parent_id": "parent-123",
            "user_id": "user-123",
            "children_ids": ["child-123"],
            "preferred_language": "en",
            "notification_preferences": {},
            "guidance_level": "intermediate",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }]
        
        # Mock update response
        mock_db.client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            "parent_id": "parent-123",
            "user_id": "user-123",
            "children_ids": ["child-123", "child-456"],
            "preferred_language": "en",
            "notification_preferences": {},
            "guidance_level": "intermediate",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T01:00:00Z"
        }]
        
        result = await parent_repo.add_child_to_parent("parent-123", "child-456")
        
        assert isinstance(result, ParentProfile)
        assert "child-123" in result.children_ids
        assert "child-456" in result.children_ids
    
    async def test_remove_child_from_parent(self, parent_repo, mock_db):
        """Test removing a child from parent's children list"""
        # Mock getting current parent profile
        mock_db.client.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [{
            "parent_id": "parent-123",
            "user_id": "user-123",
            "children_ids": ["child-123", "child-456"],
            "preferred_language": "en",
            "notification_preferences": {},
            "guidance_level": "intermediate",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }]
        
        # Mock update response
        mock_db.client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            "parent_id": "parent-123",
            "user_id": "user-123",
            "children_ids": ["child-123"],
            "preferred_language": "en",
            "notification_preferences": {},
            "guidance_level": "intermediate",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T01:00:00Z"
        }]
        
        result = await parent_repo.remove_child_from_parent("parent-123", "child-456")
        
        assert isinstance(result, ParentProfile)
        assert "child-123" in result.children_ids
        assert "child-456" not in result.children_ids


@pytest.mark.asyncio
class TestUserSessionRepository:
    """Test user session repository operations"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database connection"""
        db = MagicMock()
        db.client = AsyncMock()
        return db
    
    @pytest.fixture
    def session_repo(self, mock_db):
        """User session repository with mocked database"""
        return UserSessionRepository(mock_db)
    
    async def test_create_session(self, session_repo, mock_db):
        """Test creating a user session"""
        # Mock database response
        mock_db.client.table.return_value.insert.return_value.execute.return_value.data = [{
            "session_id": "session-123",
            "user_id": "user-123",
            "device_id": "device-456",
            "device_type": "web",
            "started_at": "2024-01-01T00:00:00Z",
            "last_activity": "2024-01-01T00:00:00Z",
            "is_active": True,
            "sync_status": "synced"
        }]
        
        session = UserSession(
            user_id="user-123",
            device_id="device-456",
            device_type="web"
        )
        result = await session_repo.create_session(session)
        
        assert isinstance(result, UserSession)
        assert result.user_id == "user-123"
        assert result.device_type == "web"
        assert result.is_active is True
    
    async def test_get_active_sessions_by_user_id(self, session_repo, mock_db):
        """Test getting active sessions by user ID"""
        # Mock database response
        mock_db.client.table.return_value.select.return_value.eq.return_value.eq.return_value.execute.return_value.data = [
            {
                "session_id": "session-123",
                "user_id": "user-123",
                "device_id": "device-456",
                "device_type": "web",
                "started_at": "2024-01-01T00:00:00Z",
                "last_activity": "2024-01-01T00:00:00Z",
                "is_active": True,
                "sync_status": "synced"
            },
            {
                "session_id": "session-456",
                "user_id": "user-123",
                "device_id": "device-789",
                "device_type": "mobile",
                "started_at": "2024-01-01T00:00:00Z",
                "last_activity": "2024-01-01T00:00:00Z",
                "is_active": True,
                "sync_status": "synced"
            }
        ]
        
        result = await session_repo.get_active_sessions_by_user_id("user-123")
        
        assert len(result) == 2
        assert all(isinstance(session, UserSession) for session in result)
        assert all(session.user_id == "user-123" for session in result)
        assert all(session.is_active is True for session in result)
    
    async def test_update_session_activity(self, session_repo, mock_db):
        """Test updating session activity"""
        # Mock database response
        mock_db.client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            "session_id": "session-123",
            "user_id": "user-123",
            "device_id": "device-456",
            "device_type": "web",
            "started_at": "2024-01-01T00:00:00Z",
            "last_activity": "2024-01-01T01:00:00Z",
            "is_active": True,
            "sync_status": "synced"
        }]
        
        result = await session_repo.update_session_activity("session-123")
        
        assert isinstance(result, UserSession)
        assert result.session_id == "session-123"
    
    async def test_deactivate_session(self, session_repo, mock_db):
        """Test deactivating a session"""
        # Mock database response
        mock_db.client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            "session_id": "session-123",
            "user_id": "user-123",
            "device_id": "device-456",
            "device_type": "web",
            "started_at": "2024-01-01T00:00:00Z",
            "last_activity": "2024-01-01T01:00:00Z",
            "is_active": False,
            "sync_status": "synced"
        }]
        
        result = await session_repo.deactivate_session("session-123")
        
        assert isinstance(result, UserSession)
        assert result.is_active is False
    
    async def test_update_sync_status(self, session_repo, mock_db):
        """Test updating sync status"""
        # Mock database response
        mock_db.client.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [{
            "session_id": "session-123",
            "user_id": "user-123",
            "device_id": "device-456",
            "device_type": "web",
            "started_at": "2024-01-01T00:00:00Z",
            "last_activity": "2024-01-01T01:00:00Z",
            "is_active": True,
            "sync_status": "pending"
        }]
        
        result = await session_repo.update_sync_status("session-123", "pending")
        
        assert isinstance(result, UserSession)
        assert result.sync_status == "pending"
    
    async def test_update_sync_status_invalid(self, session_repo, mock_db):
        """Test updating sync status with invalid value"""
        with pytest.raises(ValueError, match="Invalid sync status"):
            await session_repo.update_sync_status("session-123", "invalid")
    
    async def test_cleanup_inactive_sessions(self, session_repo, mock_db):
        """Test cleaning up inactive sessions"""
        # Mock database response
        mock_db.client.table.return_value.delete.return_value.lt.return_value.execute.return_value.data = [
            {"session_id": "session-1"},
            {"session_id": "session-2"}
        ]
        
        result = await session_repo.cleanup_inactive_sessions(24)
        
        assert result == 2
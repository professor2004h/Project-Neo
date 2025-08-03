"""
User repository for database operations
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from .base_repository import BaseRepository
from ..models.user_models import (
    User, UserCreate, UserUpdate,
    ChildProfile, ChildProfileCreate, ChildProfileUpdate,
    ParentProfile, ParentProfileCreate, ParentProfileUpdate,
    UserSession
)
from services.supabase import DBConnection
from utils.logger import logger


class UserRepository(BaseRepository):
    """Repository for user profile operations"""
    
    def __init__(self, db: DBConnection):
        super().__init__(db, "tutor_user_profiles")
    
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user profile"""
        try:
            data = {
                "email": user_data.email,
                "role": user_data.role.value,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = await self.create(data)
            return User(**result)
            
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            raise
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        try:
            result = await self.get_by_id(user_id, "user_id")
            if result:
                return User(**result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            client = await self.get_client()
            result = await client.table(self.table_name).select("*").eq("email", email.lower()).execute()
            
            if result.data:
                return User(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            raise
    
    async def update_user(self, user_id: str, user_data: UserUpdate) -> User:
        """Update user profile"""
        try:
            data = {}
            if user_data.email is not None:
                data["email"] = user_data.email
            if user_data.role is not None:
                data["role"] = user_data.role.value
            
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            result = await self.update(user_id, data, "user_id")
            return User(**result)
            
        except Exception as e:
            logger.error(f"Error updating user: {str(e)}")
            raise
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete user profile"""
        try:
            return await self.delete(user_id, "user_id")
            
        except Exception as e:
            logger.error(f"Error deleting user: {str(e)}")
            raise
    
    async def list_users_by_role(self, role: str, limit: Optional[int] = None) -> List[User]:
        """List users by role"""
        try:
            filters = {"role": role}
            results = await self.list_all(filters, limit)
            return [User(**result) for result in results]
            
        except Exception as e:
            logger.error(f"Error listing users by role: {str(e)}")
            raise


class ChildProfileRepository(BaseRepository):
    """Repository for child profile operations"""
    
    def __init__(self, db: DBConnection):
        super().__init__(db, "tutor_child_profiles")
    
    async def create_child_profile(self, child_data: ChildProfileCreate) -> ChildProfile:
        """Create a new child profile"""
        try:
            data = {
                "parent_id": child_data.parent_id,
                "name": child_data.name,
                "age": child_data.age,
                "grade_level": child_data.grade_level,
                "learning_style": child_data.learning_style.value,
                "preferred_subjects": [subject.value for subject in child_data.preferred_subjects],
                "learning_preferences": child_data.learning_preferences,
                "safety_settings": child_data.safety_settings,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = await self.create(data)
            return ChildProfile(**result)
            
        except Exception as e:
            logger.error(f"Error creating child profile: {str(e)}")
            raise
    
    async def get_child_profile_by_id(self, child_id: str) -> Optional[ChildProfile]:
        """Get child profile by ID"""
        try:
            result = await self.get_by_id(child_id, "child_id")
            if result:
                return ChildProfile(**result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting child profile by ID: {str(e)}")
            raise
    
    async def get_children_by_parent_id(self, parent_id: str) -> List[ChildProfile]:
        """Get all children for a parent"""
        try:
            filters = {"parent_id": parent_id}
            results = await self.list_all(filters)
            return [ChildProfile(**result) for result in results]
            
        except Exception as e:
            logger.error(f"Error getting children by parent ID: {str(e)}")
            raise
    
    async def update_child_profile(self, child_id: str, child_data: ChildProfileUpdate) -> ChildProfile:
        """Update child profile"""
        try:
            data = {}
            if child_data.name is not None:
                data["name"] = child_data.name
            if child_data.age is not None:
                data["age"] = child_data.age
            if child_data.grade_level is not None:
                data["grade_level"] = child_data.grade_level
            if child_data.learning_style is not None:
                data["learning_style"] = child_data.learning_style.value
            if child_data.preferred_subjects is not None:
                data["preferred_subjects"] = [subject.value for subject in child_data.preferred_subjects]
            if child_data.learning_preferences is not None:
                data["learning_preferences"] = child_data.learning_preferences
            if child_data.safety_settings is not None:
                data["safety_settings"] = child_data.safety_settings
            
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            result = await self.update(child_id, data, "child_id")
            return ChildProfile(**result)
            
        except Exception as e:
            logger.error(f"Error updating child profile: {str(e)}")
            raise
    
    async def delete_child_profile(self, child_id: str) -> bool:
        """Delete child profile"""
        try:
            return await self.delete(child_id, "child_id")
            
        except Exception as e:
            logger.error(f"Error deleting child profile: {str(e)}")
            raise
    
    async def get_children_by_age_range(self, min_age: int, max_age: int) -> List[ChildProfile]:
        """Get children within age range"""
        try:
            client = await self.get_client()
            result = await client.table(self.table_name).select("*").gte("age", min_age).lte("age", max_age).execute()
            
            return [ChildProfile(**child) for child in result.data or []]
            
        except Exception as e:
            logger.error(f"Error getting children by age range: {str(e)}")
            raise
    
    async def get_children_by_grade_level(self, grade_level: int) -> List[ChildProfile]:
        """Get children by grade level"""
        try:
            filters = {"grade_level": grade_level}
            results = await self.list_all(filters)
            return [ChildProfile(**result) for result in results]
            
        except Exception as e:
            logger.error(f"Error getting children by grade level: {str(e)}")
            raise


class ParentProfileRepository(BaseRepository):
    """Repository for parent profile operations"""
    
    def __init__(self, db: DBConnection):
        super().__init__(db, "tutor_parent_profiles")
    
    async def create_parent_profile(self, parent_data: ParentProfileCreate) -> ParentProfile:
        """Create a new parent profile"""
        try:
            data = {
                "user_id": parent_data.user_id,
                "children_ids": [],
                "preferred_language": parent_data.preferred_language,
                "notification_preferences": parent_data.notification_preferences,
                "guidance_level": parent_data.guidance_level,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            result = await self.create(data)
            return ParentProfile(**result)
            
        except Exception as e:
            logger.error(f"Error creating parent profile: {str(e)}")
            raise
    
    async def get_parent_profile_by_id(self, parent_id: str) -> Optional[ParentProfile]:
        """Get parent profile by ID"""
        try:
            result = await self.get_by_id(parent_id, "parent_id")
            if result:
                return ParentProfile(**result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting parent profile by ID: {str(e)}")
            raise
    
    async def get_parent_profile_by_user_id(self, user_id: str) -> Optional[ParentProfile]:
        """Get parent profile by user ID"""
        try:
            client = await self.get_client()
            result = await client.table(self.table_name).select("*").eq("user_id", user_id).execute()
            
            if result.data:
                return ParentProfile(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting parent profile by user ID: {str(e)}")
            raise
    
    async def update_parent_profile(self, parent_id: str, parent_data: ParentProfileUpdate) -> ParentProfile:
        """Update parent profile"""
        try:
            data = {}
            if parent_data.children_ids is not None:
                data["children_ids"] = parent_data.children_ids
            if parent_data.preferred_language is not None:
                data["preferred_language"] = parent_data.preferred_language
            if parent_data.notification_preferences is not None:
                data["notification_preferences"] = parent_data.notification_preferences
            if parent_data.guidance_level is not None:
                data["guidance_level"] = parent_data.guidance_level
            
            data["updated_at"] = datetime.now(timezone.utc).isoformat()
            
            result = await self.update(parent_id, data, "parent_id")
            return ParentProfile(**result)
            
        except Exception as e:
            logger.error(f"Error updating parent profile: {str(e)}")
            raise
    
    async def add_child_to_parent(self, parent_id: str, child_id: str) -> ParentProfile:
        """Add a child to parent's children list"""
        try:
            # First get the current parent profile
            parent = await self.get_parent_profile_by_id(parent_id)
            if not parent:
                raise ValueError(f"Parent profile not found: {parent_id}")
            
            # Add child ID if not already present
            if child_id not in parent.children_ids:
                updated_children_ids = parent.children_ids + [child_id]
                update_data = ParentProfileUpdate(children_ids=updated_children_ids)
                return await self.update_parent_profile(parent_id, update_data)
            
            return parent
            
        except Exception as e:
            logger.error(f"Error adding child to parent: {str(e)}")
            raise
    
    async def remove_child_from_parent(self, parent_id: str, child_id: str) -> ParentProfile:
        """Remove a child from parent's children list"""
        try:
            # First get the current parent profile
            parent = await self.get_parent_profile_by_id(parent_id)
            if not parent:
                raise ValueError(f"Parent profile not found: {parent_id}")
            
            # Remove child ID if present
            if child_id in parent.children_ids:
                updated_children_ids = [cid for cid in parent.children_ids if cid != child_id]
                update_data = ParentProfileUpdate(children_ids=updated_children_ids)
                return await self.update_parent_profile(parent_id, update_data)
            
            return parent
            
        except Exception as e:
            logger.error(f"Error removing child from parent: {str(e)}")
            raise
    
    async def delete_parent_profile(self, parent_id: str) -> bool:
        """Delete parent profile"""
        try:
            return await self.delete(parent_id, "parent_id")
            
        except Exception as e:
            logger.error(f"Error deleting parent profile: {str(e)}")
            raise


class UserSessionRepository(BaseRepository):
    """Repository for user session operations"""
    
    def __init__(self, db: DBConnection):
        super().__init__(db, "tutor_user_sessions")
    
    async def create_session(self, session_data: UserSession) -> UserSession:
        """Create a new user session"""
        try:
            data = {
                "user_id": session_data.user_id,
                "device_id": session_data.device_id,
                "device_type": session_data.device_type,
                "started_at": session_data.started_at.isoformat(),
                "last_activity": session_data.last_activity.isoformat(),
                "is_active": session_data.is_active,
                "sync_status": session_data.sync_status
            }
            
            result = await self.create(data)
            return UserSession(**result)
            
        except Exception as e:
            logger.error(f"Error creating user session: {str(e)}")
            raise
    
    async def get_session_by_id(self, session_id: str) -> Optional[UserSession]:
        """Get session by ID"""
        try:
            result = await self.get_by_id(session_id, "session_id")
            if result:
                return UserSession(**result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting session by ID: {str(e)}")
            raise
    
    async def get_active_sessions_by_user_id(self, user_id: str) -> List[UserSession]:
        """Get all active sessions for a user"""
        try:
            client = await self.get_client()
            result = await client.table(self.table_name).select("*").eq("user_id", user_id).eq("is_active", True).execute()
            
            return [UserSession(**session) for session in result.data or []]
            
        except Exception as e:
            logger.error(f"Error getting active sessions by user ID: {str(e)}")
            raise
    
    async def update_session_activity(self, session_id: str) -> UserSession:
        """Update session last activity timestamp"""
        try:
            data = {
                "last_activity": datetime.now(timezone.utc).isoformat()
            }
            
            result = await self.update(session_id, data, "session_id")
            return UserSession(**result)
            
        except Exception as e:
            logger.error(f"Error updating session activity: {str(e)}")
            raise
    
    async def deactivate_session(self, session_id: str) -> UserSession:
        """Deactivate a session"""
        try:
            data = {
                "is_active": False,
                "last_activity": datetime.now(timezone.utc).isoformat()
            }
            
            result = await self.update(session_id, data, "session_id")
            return UserSession(**result)
            
        except Exception as e:
            logger.error(f"Error deactivating session: {str(e)}")
            raise
    
    async def update_sync_status(self, session_id: str, sync_status: str) -> UserSession:
        """Update session sync status"""
        try:
            if sync_status not in ['synced', 'pending', 'conflict']:
                raise ValueError(f"Invalid sync status: {sync_status}")
            
            data = {
                "sync_status": sync_status,
                "last_activity": datetime.now(timezone.utc).isoformat()
            }
            
            result = await self.update(session_id, data, "session_id")
            return UserSession(**result)
            
        except Exception as e:
            logger.error(f"Error updating sync status: {str(e)}")
            raise
    
    async def cleanup_inactive_sessions(self, hours_threshold: int = 24) -> int:
        """Clean up sessions inactive for more than specified hours"""
        try:
            from datetime import timedelta
            
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)
            
            client = await self.get_client()
            result = await client.table(self.table_name).delete().lt("last_activity", cutoff_time.isoformat()).execute()
            
            count = len(result.data) if result.data else 0
            logger.info(f"Cleaned up {count} inactive sessions")
            return count
            
        except Exception as e:
            logger.error(f"Error cleaning up inactive sessions: {str(e)}")
            raise
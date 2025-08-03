"""
Curriculum Repository - Data access layer for curriculum topics and content
"""
from typing import Dict, List, Optional, Any
from datetime import datetime

from .base_repository import BaseRepository
from ..models.curriculum_models import Subject, DifficultyLevel
from utils.logger import logger


class CurriculumTopicRepository(BaseRepository):
    """Repository for curriculum topics"""
    
    def __init__(self, db):
        super().__init__(db, "tutor_curriculum_topics")
    
    async def get_by_cambridge_code(self, cambridge_code: str) -> Optional[Dict[str, Any]]:
        """Get a curriculum topic by Cambridge code"""
        try:
            client = await self.get_client()
            result = await client.table(self.table_name).select("*").eq("cambridge_code", cambridge_code.upper()).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting topic by Cambridge code: {str(e)}")
            raise
    
    async def get_by_subject_and_grade(self, subject: Subject, grade_level: int) -> List[Dict[str, Any]]:
        """Get topics by subject and grade level"""
        try:
            client = await self.get_client()
            result = await client.table(self.table_name).select("*").eq("subject", subject.value).eq("grade_level", grade_level).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting topics by subject and grade: {str(e)}")
            raise
    
    async def search_topics(self, 
                          query: str = None,
                          subject: Subject = None,
                          grade_level: int = None,
                          difficulty_level: DifficultyLevel = None,
                          limit: int = 50) -> List[Dict[str, Any]]:
        """Search topics with various filters"""
        try:
            client = await self.get_client()
            db_query = client.table(self.table_name).select("*")
            
            # Apply filters
            if subject:
                db_query = db_query.eq("subject", subject.value)
            if grade_level:
                db_query = db_query.eq("grade_level", grade_level)
            if difficulty_level:
                db_query = db_query.eq("difficulty_level", difficulty_level.value)
            
            # Text search in title and description
            if query:
                db_query = db_query.or_(f"title.ilike.%{query}%,description.ilike.%{query}%,cambridge_code.ilike.%{query}%")
            
            if limit:
                db_query = db_query.limit(limit)
            
            db_query = db_query.order("grade_level", desc=False).order("title", desc=False)
            
            result = await db_query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error searching topics: {str(e)}")
            raise
    
    async def get_prerequisites(self, topic_id: str) -> List[Dict[str, Any]]:
        """Get prerequisite topics for a given topic"""
        try:
            # First get the topic to find its prerequisites
            topic = await self.get_by_id(topic_id, "topic_id")
            if not topic or not topic.get("prerequisites"):
                return []
            
            # Get the prerequisite topics
            prerequisite_ids = topic["prerequisites"]
            if not prerequisite_ids:
                return []
            
            client = await self.get_client()
            result = await client.table(self.table_name).select("*").in_("topic_id", prerequisite_ids).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting prerequisites: {str(e)}")
            raise
    
    async def get_dependents(self, topic_id: str) -> List[Dict[str, Any]]:
        """Get topics that depend on this topic as a prerequisite"""
        try:
            client = await self.get_client()
            # PostgreSQL array contains operation
            result = await client.table(self.table_name).select("*").contains("prerequisites", [topic_id]).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting dependent topics: {str(e)}")
            raise


class LearningObjectiveRepository(BaseRepository):
    """Repository for learning objectives"""
    
    def __init__(self, db):
        super().__init__(db, "tutor_learning_objectives")
    
    async def get_by_topic_id(self, topic_id: str) -> List[Dict[str, Any]]:
        """Get all learning objectives for a topic"""
        try:
            client = await self.get_client()
            result = await client.table(self.table_name).select("*").eq("topic_id", topic_id).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting objectives by topic: {str(e)}")
            raise
    
    async def search_by_cambridge_reference(self, cambridge_ref: str) -> List[Dict[str, Any]]:
        """Search objectives by Cambridge reference"""
        try:
            client = await self.get_client()
            result = await client.table(self.table_name).select("*").ilike("cambridge_reference", f"%{cambridge_ref}%").execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error searching objectives by Cambridge reference: {str(e)}")
            raise


class ContentItemRepository(BaseRepository):
    """Repository for content items"""
    
    def __init__(self, db):
        super().__init__(db, "tutor_content_items")
    
    async def get_by_topic_id(self, topic_id: str) -> List[Dict[str, Any]]:
        """Get all content items for a topic"""
        try:
            client = await self.get_client()
            result = await client.table(self.table_name).select("*").eq("topic_id", topic_id).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting content by topic: {str(e)}")
            raise
    
    async def search_content(self,
                           query: str = None,
                           topic_id: str = None,
                           content_type: str = None,
                           difficulty_level: DifficultyLevel = None,
                           age_min: int = None,
                           age_max: int = None,
                           limit: int = 50) -> List[Dict[str, Any]]:
        """Search content items with various filters"""
        try:
            client = await self.get_client()
            db_query = client.table(self.table_name).select("*")
            
            # Apply filters
            if topic_id:
                db_query = db_query.eq("topic_id", topic_id)
            if content_type:
                db_query = db_query.eq("content_type", content_type)
            if difficulty_level:
                db_query = db_query.eq("difficulty_level", difficulty_level.value)
            
            # Text search in title
            if query:
                db_query = db_query.ilike("title", f"%{query}%")
            
            # Age appropriateness filtering would require more complex JSONB queries
            # For now, we'll implement basic filtering and enhance later
            
            if limit:
                db_query = db_query.limit(limit)
            
            db_query = db_query.order("created_at", desc=True)
            
            result = await db_query.execute()
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error searching content: {str(e)}")
            raise
    
    async def get_by_content_type(self, content_type: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get content items by type"""
        try:
            client = await self.get_client()
            result = await client.table(self.table_name).select("*").eq("content_type", content_type).limit(limit).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting content by type: {str(e)}")
            raise
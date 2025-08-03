"""
Content Management Service - Handles curriculum-aligned educational content
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
import uuid

from utils.logger import logger
from services.supabase import DBConnection
from ..repositories.curriculum_repository import (
    CurriculumTopicRepository, 
    LearningObjectiveRepository, 
    ContentItemRepository
)
from ..models.curriculum_models import Subject, DifficultyLevel
from .cambridge_alignment_service import CambridgeAlignmentService


class ContentService:
    """Manages curriculum-aligned educational content"""
    
    def __init__(self, db: DBConnection):
        self.db = db
        self.curriculum_repo = CurriculumTopicRepository(db)
        self.objectives_repo = LearningObjectiveRepository(db)
        self.content_repo = ContentItemRepository(db)
        self.alignment_service = CambridgeAlignmentService(db)
        
    async def get_lesson_content(self, lesson_id: str, user_level: int) -> Dict[str, Any]:
        """
        Retrieve lesson content adapted for user level
        
        Args:
            lesson_id: ID of the lesson (topic_id)
            user_level: User's current level (grade level)
            
        Returns:
            Dictionary containing lesson content
        """
        try:
            # Get the curriculum topic
            topic = await self.curriculum_repo.get_by_id(lesson_id, "topic_id")
            if not topic:
                raise ValueError(f"Topic not found: {lesson_id}")
            
            # Get learning objectives for this topic
            objectives = await self.objectives_repo.get_by_topic_id(lesson_id)
            
            # Get content items for this topic
            content_items = await self.content_repo.get_by_topic_id(lesson_id)
            
            # Filter content by difficulty level appropriate for user level
            appropriate_content = []
            for item in content_items:
                age_validation = self.alignment_service.validate_age_appropriateness(
                    {
                        "content_id": item["content_id"],
                        "difficulty_level": item["difficulty_level"],
                        "grade_level": user_level
                    },
                    5 + user_level - 1  # Convert grade to approximate age
                )
                
                if age_validation["is_appropriate"]:
                    appropriate_content.append(item)
            
            content = {
                "lesson_id": lesson_id,
                "topic_id": topic["topic_id"],
                "title": topic["title"],
                "description": topic.get("description", ""),
                "subject": topic["subject"],
                "grade_level": topic["grade_level"],
                "cambridge_code": topic["cambridge_code"],
                "difficulty_level": topic["difficulty_level"],
                "estimated_duration_minutes": topic.get("estimated_duration_minutes", 30),
                "learning_objectives": [obj["description"] for obj in objectives],
                "content_items": appropriate_content,
                "prerequisites": topic.get("prerequisites", [])
            }
            
            logger.info(f"Lesson content retrieved for topic {lesson_id}")
            return content
            
        except Exception as e:
            logger.error(f"Error retrieving lesson content: {str(e)}")
            raise
    
    async def search_content(self, query: str, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for educational content with curriculum code and topic-based queries
        
        Args:
            query: Search query (can be Cambridge code, topic name, or general text)
            filters: Search filters (subject, grade_level, difficulty_level, content_type, etc.)
            
        Returns:
            List of matching content items with topic information
        """
        try:
            # Parse filters
            subject = filters.get("subject")
            if subject and isinstance(subject, str):
                try:
                    subject = Subject(subject.lower())
                except ValueError:
                    subject = None
            
            grade_level = filters.get("grade_level")
            difficulty_level = filters.get("difficulty_level")
            if difficulty_level and isinstance(difficulty_level, str):
                try:
                    difficulty_level = DifficultyLevel(difficulty_level.lower())
                except ValueError:
                    difficulty_level = None
            
            content_type = filters.get("content_type")
            limit = filters.get("limit", 50)
            
            # Step 1: Search curriculum topics first
            topic_results = await self.curriculum_repo.search_topics(
                query=query,
                subject=subject,
                grade_level=grade_level,
                difficulty_level=difficulty_level,
                limit=limit
            )
            
            # Step 2: Search content items
            content_results = await self.content_repo.search_content(
                query=query,
                content_type=content_type,
                difficulty_level=difficulty_level,
                limit=limit
            )
            
            # Step 3: Check if query might be a Cambridge code
            cambridge_code_results = []
            if query and len(query) >= 3:
                validation = self.alignment_service.validate_cambridge_code(query)
                if validation["is_valid"]:
                    # Search for topics with this Cambridge code
                    code_topic = await self.curriculum_repo.get_by_cambridge_code(query)
                    if code_topic:
                        cambridge_code_results.append(code_topic)
            
            # Step 4: Combine and format results
            combined_results = []
            
            # Add topic-based results
            for topic in topic_results:
                # Get content items for this topic
                topic_content_items = await self.content_repo.get_by_topic_id(topic["topic_id"])
                
                # Apply content type filter if specified
                if content_type:
                    topic_content_items = [
                        item for item in topic_content_items 
                        if item.get("content_type") == content_type
                    ]
                
                # Get learning objectives
                objectives = await self.objectives_repo.get_by_topic_id(topic["topic_id"])
                
                combined_results.append({
                    "type": "topic",
                    "topic_id": topic["topic_id"],
                    "content_id": None,
                    "title": topic["title"],
                    "description": topic.get("description", ""),
                    "subject": topic["subject"],
                    "grade_level": topic["grade_level"],
                    "cambridge_code": topic["cambridge_code"],
                    "difficulty_level": topic["difficulty_level"],
                    "content_items_count": len(topic_content_items),
                    "content_items": topic_content_items[:5],  # Limit preview
                    "learning_objectives": [obj["description"] for obj in objectives[:3]],  # Limit preview
                    "match_score": self._calculate_match_score(query, topic, filters)
                })
            
            # Add content item results that weren't already included via topics
            included_content_ids = set()
            for result in combined_results:
                for item in result.get("content_items", []):
                    included_content_ids.add(item["content_id"])
            
            for content_item in content_results:
                if content_item["content_id"] not in included_content_ids:
                    # Get the topic for this content item
                    topic = await self.curriculum_repo.get_by_id(content_item["topic_id"], "topic_id")
                    
                    combined_results.append({
                        "type": "content_item",
                        "topic_id": content_item["topic_id"],
                        "content_id": content_item["content_id"],
                        "title": content_item["title"],
                        "description": topic.get("description", "") if topic else "",
                        "subject": topic["subject"] if topic else "unknown",
                        "grade_level": topic["grade_level"] if topic else 0,
                        "cambridge_code": topic["cambridge_code"] if topic else "",
                        "difficulty_level": content_item["difficulty_level"],
                        "content_type": content_item["content_type"],
                        "content_data": content_item.get("content_data", {}),
                        "match_score": self._calculate_content_match_score(query, content_item, filters)
                    })
            
            # Add Cambridge code specific results
            for topic in cambridge_code_results:
                if not any(r["topic_id"] == topic["topic_id"] for r in combined_results):
                    objectives = await self.objectives_repo.get_by_topic_id(topic["topic_id"])
                    content_items = await self.content_repo.get_by_topic_id(topic["topic_id"])
                    
                    combined_results.append({
                        "type": "cambridge_code_match",
                        "topic_id": topic["topic_id"],
                        "content_id": None,
                        "title": topic["title"],
                        "description": topic.get("description", ""),
                        "subject": topic["subject"],
                        "grade_level": topic["grade_level"],
                        "cambridge_code": topic["cambridge_code"],
                        "difficulty_level": topic["difficulty_level"],
                        "content_items_count": len(content_items),
                        "learning_objectives": [obj["description"] for obj in objectives],
                        "match_score": 1.0  # Exact Cambridge code match
                    })
            
            # Sort by match score and limit results
            combined_results.sort(key=lambda x: x["match_score"], reverse=True)
            final_results = combined_results[:limit]
            
            logger.info(f"Content search performed: '{query}' - found {len(final_results)} results")
            return final_results
            
        except Exception as e:
            logger.error(f"Error searching content: {str(e)}")
            raise
    
    async def generate_adaptive_content(self, user_id: str, topic: str) -> Dict[str, Any]:
        """
        Generate adaptive content for a user and topic
        
        Args:
            user_id: ID of the user
            topic: Topic to generate content for
            
        Returns:
            Dictionary containing adaptive content
        """
        try:
            # TODO: Implement adaptive content generation
            # This will be implemented in task 4.3
            
            content = {
                "content_id": str(uuid.uuid4()),
                "user_id": user_id,
                "topic": topic,
                "content": "Placeholder adaptive content",
                "difficulty_level": 1,
                "personalization_factors": []
            }
            
            logger.info(f"Adaptive content generated for user {user_id}")
            return content
            
        except Exception as e:
            logger.error(f"Error generating adaptive content: {str(e)}")
            raise
    
    async def validate_curriculum_alignment(self, content_id: str) -> Dict[str, Any]:
        """
        Validate that content aligns with Cambridge curriculum standards
        
        Args:
            content_id: ID of the content to validate
            
        Returns:
            Dictionary containing alignment report
        """
        try:
            # Get the content item
            content_item = await self.content_repo.get_by_id(content_id, "content_id")
            if not content_item:
                return {
                    "content_id": content_id,
                    "is_aligned": False,
                    "alignment_score": 0.0,
                    "error": "Content not found"
                }
            
            # Get the associated topic
            topic = None
            cambridge_codes = []
            if content_item.get("topic_id"):
                topic = await self.curriculum_repo.get_by_id(content_item["topic_id"], "topic_id")
                if topic:
                    cambridge_codes.append(topic["cambridge_code"])
                
                # Get additional codes from learning objectives
                additional_codes = await self.alignment_service.get_curriculum_codes_by_topic(
                    content_item["topic_id"]
                )
                cambridge_codes.extend(additional_codes)
            
            # Prepare content data for validation
            content_data = {
                "content_id": content_id,
                "topic_id": content_item.get("topic_id"),
                "cambridge_codes": list(set(cambridge_codes)),  # Remove duplicates
                "difficulty_level": content_item.get("difficulty_level"),
                "content_type": content_item.get("content_type"),
                "age_appropriateness": content_item.get("age_appropriateness", {}),
                "curriculum_alignment": content_item.get("curriculum_alignment", {})
            }
            
            # Validate curriculum alignment
            alignment_report = await self.alignment_service.validate_curriculum_alignment(content_data)
            
            logger.info(f"Curriculum alignment validated for {content_id}: {alignment_report['alignment_score']:.2f}")
            return alignment_report
            
        except Exception as e:
            logger.error(f"Error validating curriculum alignment: {str(e)}")
            return {
                "content_id": content_id,
                "is_aligned": False,
                "alignment_score": 0.0,
                "error": str(e)
            }
    
    def _calculate_match_score(self, query: str, topic: Dict[str, Any], filters: Dict[str, Any]) -> float:
        """Calculate relevance score for a topic based on query and filters"""
        score = 0.0
        
        if not query:
            return 0.5  # Default score for no query
        
        query_lower = query.lower()
        
        # Title match (highest weight)
        if query_lower in topic["title"].lower():
            score += 0.4
        
        # Cambridge code exact match
        if query.upper() == topic["cambridge_code"].upper():
            score += 0.3
        
        # Description match
        if topic.get("description") and query_lower in topic["description"].lower():
            score += 0.2
        
        # Subject match from filters
        if filters.get("subject") and filters["subject"] == topic["subject"]:
            score += 0.1
        
        return min(score, 1.0)
    
    def _calculate_content_match_score(self, query: str, content_item: Dict[str, Any], filters: Dict[str, Any]) -> float:
        """Calculate relevance score for a content item"""
        score = 0.0
        
        if not query:
            return 0.4  # Lower default for content items
        
        query_lower = query.lower()
        
        # Title match
        if query_lower in content_item["title"].lower():
            score += 0.5
        
        # Content type match from filters
        if filters.get("content_type") and filters["content_type"] == content_item["content_type"]:
            score += 0.2
        
        # Difficulty level match
        if filters.get("difficulty_level") and filters["difficulty_level"] == content_item["difficulty_level"]:
            score += 0.1
        
        return min(score, 1.0)
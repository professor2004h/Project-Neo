"""
Parent Guidance Service - Comprehensive support system for parents
Task 9.1 implementation - FAQ system and guidance generation
"""
import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum
from pydantic import BaseModel, Field
import uuid

from utils.logger import logger
from services.supabase import DBConnection
from services.llm import make_llm_api_call
from ..repositories.user_repository import (
    ChildProfileRepository, ParentProfileRepository
)
from ..models.user_models import (
    ChildProfile, ParentProfile, Subject
)


class GuidanceCategory(str, Enum):
    """Categories for parent guidance topics"""
    CURRICULUM = "curriculum"
    LEARNING_SUPPORT = "learning_support"
    TECHNOLOGY = "technology"
    MOTIVATION = "motivation"
    ASSESSMENT = "assessment"
    SAFETY = "safety"
    ESL_SUPPORT = "esl_support"
    SPECIAL_NEEDS = "special_needs"


class GuidancePriority(str, Enum):
    """Priority levels for guidance recommendations"""
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class FAQItem(BaseModel):
    """Model for FAQ items"""
    faq_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category: GuidanceCategory
    question: str = Field(max_length=200)
    answer: str = Field(max_length=2000)
    keywords: List[str] = Field(default_factory=list)
    grade_levels: List[int] = Field(default_factory=list)
    subjects: List[Subject] = Field(default_factory=list)
    popularity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
    class Config:
        from_attributes = True


class GuidanceRecommendation(BaseModel):
    """Model for personalized guidance recommendations"""
    recommendation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    parent_id: str
    child_id: str
    category: GuidanceCategory
    priority: GuidancePriority
    title: str = Field(max_length=100)
    description: str = Field(max_length=500)
    actionable_steps: List[str] = Field(default_factory=list)
    resources: List[Dict[str, str]] = Field(default_factory=list)
    estimated_time_minutes: Optional[int] = None
    success_indicators: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: Optional[datetime] = None
    is_read: bool = Field(default=False)
    
    class Config:
        from_attributes = True


class GuidanceSearchQuery(BaseModel):
    """Model for FAQ search queries"""
    query: str = Field(max_length=200)
    category: Optional[GuidanceCategory] = None
    child_age: Optional[int] = None
    subject: Optional[Subject] = None
    max_results: int = Field(default=10, ge=1, le=50)


class ParentGuidanceService:
    """
    Comprehensive guidance service for parents with FAQ system and personalized recommendations
    """
    
    def __init__(self, db: DBConnection):
        self.db = db
        self.child_repo = ChildProfileRepository(db)
        self.parent_repo = ParentProfileRepository(db)
        
        # Pre-loaded FAQ database
        self.faq_database = self._initialize_faq_database()
        
        # Guidance templates by category
        self.guidance_templates = self._initialize_guidance_templates()
    
    async def search_faq(self, search_query: GuidanceSearchQuery, parent_id: str) -> List[FAQItem]:
        """
        Search FAQ database with intelligent matching
        
        Args:
            search_query: Search parameters
            parent_id: ID of the parent requesting guidance
            
        Returns:
            List of relevant FAQ items
        """
        try:
            # Get parent context for personalization
            parent = await self.parent_repo.get_parent_profile_by_user_id(parent_id)
            if not parent:
                logger.warning(f"Parent profile not found for FAQ search: {parent_id}")
                return []
            
            # Use AI to enhance search relevance
            enhanced_results = await self._ai_enhanced_faq_search(
                search_query, parent, self.faq_database
            )
            
            # Log the search for analytics
            await self._log_faq_search(parent_id, search_query.query, len(enhanced_results))
            
            return enhanced_results[:search_query.max_results]
            
        except Exception as e:
            logger.error(f"Error searching FAQ: {str(e)}")
            return []
    
    async def generate_personalized_guidance(self, parent_id: str, child_id: str, 
                                           context: Dict[str, Any] = None) -> List[GuidanceRecommendation]:
        """
        Generate personalized guidance recommendations for a parent
        
        Args:
            parent_id: ID of the parent
            child_id: ID of the child
            context: Additional context (e.g., recent struggles, achievements)
            
        Returns:
            List of personalized guidance recommendations
        """
        try:
            # Get parent and child profiles
            parent = await self.parent_repo.get_parent_profile_by_user_id(parent_id)
            child = await self.child_repo.get_child_profile_by_id(child_id)
            
            if not parent or not child:
                logger.error(f"Parent or child profile not found: {parent_id}, {child_id}")
                return []
            
            # Get recent progress data for context
            recent_context = await self._gather_child_context(child_id, context or {})
            
            # Generate AI-powered guidance recommendations
            recommendations = await self._generate_ai_guidance(parent, child, recent_context)
            
            # Store recommendations for future reference
            for rec in recommendations:
                await self._store_guidance_recommendation(rec)
            
            logger.info(f"Generated {len(recommendations)} guidance recommendations for parent {parent_id}")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating personalized guidance: {str(e)}")
            return []
    
    async def get_curriculum_guidance(self, parent_id: str, subject: Subject, 
                                    grade_level: int, topic: str = None) -> Dict[str, Any]:
        """
        Get curriculum-specific guidance for parents
        
        Args:
            parent_id: ID of the parent
            subject: Subject area
            grade_level: Child's grade level
            topic: Specific topic (optional)
            
        Returns:
            Dictionary containing curriculum guidance
        """
        try:
            parent = await self.parent_repo.get_parent_profile_by_user_id(parent_id)
            if not parent:
                return {"error": "Parent profile not found"}
            
            # Build curriculum guidance using AI
            guidance_data = await self._generate_curriculum_guidance(
                parent, subject, grade_level, topic
            )
            
            return guidance_data
            
        except Exception as e:
            logger.error(f"Error getting curriculum guidance: {str(e)}")
            return {"error": "Failed to generate curriculum guidance"}
    
    async def get_popular_faqs(self, category: GuidanceCategory = None, 
                              limit: int = 10) -> List[FAQItem]:
        """
        Get most popular FAQ items
        
        Args:
            category: Optional category filter
            limit: Maximum number of results
            
        Returns:
            List of popular FAQ items
        """
        try:
            faqs = self.faq_database
            
            # Filter by category if specified
            if category:
                faqs = [faq for faq in faqs if faq.category == category]
            
            # Sort by popularity score
            faqs.sort(key=lambda x: x.popularity_score, reverse=True)
            
            return faqs[:limit]
            
        except Exception as e:
            logger.error(f"Error getting popular FAQs: {str(e)}")
            return []
    
    async def _ai_enhanced_faq_search(self, query: GuidanceSearchQuery, 
                                    parent: ParentProfile, 
                                    faq_db: List[FAQItem]) -> List[FAQItem]:
        """Use AI to enhance FAQ search relevance"""
        try:
            # Build search context
            search_context = {
                "query": query.query,
                "parent_guidance_level": parent.guidance_level,
                "parent_language": parent.preferred_language,
                "child_age": query.child_age,
                "subject": query.subject.value if query.subject else None,
                "category": query.category.value if query.category else None
            }
            
            # Filter FAQs by basic criteria first
            relevant_faqs = []
            for faq in faq_db:
                # Category filter
                if query.category and faq.category != query.category:
                    continue
                
                # Subject filter
                if query.subject and query.subject not in faq.subjects and faq.subjects:
                    continue
                
                # Grade level filter
                if query.child_age and faq.grade_levels:
                    grade_level = min(12, max(1, query.child_age - 4))  # Age to grade conversion
                    if grade_level not in faq.grade_levels:
                        continue
                
                # Keyword matching
                query_lower = query.query.lower()
                if (query_lower in faq.question.lower() or 
                    query_lower in faq.answer.lower() or
                    any(keyword.lower() in query_lower for keyword in faq.keywords)):
                    relevant_faqs.append(faq)
            
            # Use AI for semantic ranking if we have multiple results
            if len(relevant_faqs) > 1:
                ranked_faqs = await self._ai_rank_faq_results(query.query, relevant_faqs, search_context)
                return ranked_faqs
            
            return relevant_faqs
            
        except Exception as e:
            logger.error(f"Error in AI-enhanced FAQ search: {str(e)}")
            return relevant_faqs[:query.max_results] if 'relevant_faqs' in locals() else []
    
    async def _ai_rank_faq_results(self, query: str, faqs: List[FAQItem], 
                                 context: Dict[str, Any]) -> List[FAQItem]:
        """Use AI to rank FAQ results by relevance"""
        try:
            # Prepare FAQ data for AI ranking
            faq_summaries = []
            for i, faq in enumerate(faqs):
                summary = {
                    "index": i,
                    "question": faq.question,
                    "answer": faq.answer[:200] + "..." if len(faq.answer) > 200 else faq.answer,
                    "category": faq.category.value,
                    "keywords": faq.keywords[:5]  # Limit keywords
                }
                faq_summaries.append(summary)
            
            system_prompt = f"""You are an expert at ranking FAQ results for parents seeking educational guidance.

SEARCH CONTEXT:
- Query: "{query}"
- Parent guidance level: {context.get('parent_guidance_level', 'intermediate')}
- Child age: {context.get('child_age', 'not specified')}
- Subject focus: {context.get('subject', 'not specified')}

TASK: Rank the following FAQ items by relevance to the parent's query. Consider:
1. Direct relevance to the question
2. Appropriateness for the parent's guidance level
3. Age/grade level appropriateness
4. Practical usefulness

RESPONSE FORMAT (JSON):
{{
    "ranked_indices": [2, 0, 1, 3, ...],
    "reasoning": "Brief explanation of ranking criteria used"
}}

FAQ ITEMS:
{json.dumps(faq_summaries, indent=2)}"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please rank these FAQ items for the query: {query}"}
            ]
            
            response = await make_llm_api_call(
                messages=messages,
                model_name="gpt-4",
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"}
            )
            
            ranking_result = json.loads(response.choices[0].message.content)
            ranked_indices = ranking_result.get("ranked_indices", list(range(len(faqs))))
            
            # Return FAQs in ranked order
            return [faqs[i] for i in ranked_indices if i < len(faqs)]
            
        except Exception as e:
            logger.error(f"Error ranking FAQ results: {str(e)}")
            return faqs  # Return original order if ranking fails
    
    async def _generate_ai_guidance(self, parent: ParentProfile, child: ChildProfile, 
                                  context: Dict[str, Any]) -> List[GuidanceRecommendation]:
        """Generate AI-powered guidance recommendations"""
        try:
            system_prompt = f"""You are an expert educational consultant providing personalized guidance for parents supporting their child's Cambridge curriculum learning.

PARENT PROFILE:
- Guidance level: {parent.guidance_level}
- Preferred language: {parent.preferred_language}
- Number of children: {len(parent.children_ids)}

CHILD PROFILE:
- Age: {child.age} years
- Grade level: {child.grade_level}
- Preferred subjects: {[s.value for s in child.preferred_subjects]}
- Learning preferences: {child.learning_preferences}

RECENT CONTEXT:
{json.dumps(context, indent=2)}

TASK: Generate 3-5 personalized guidance recommendations for this parent. Focus on:
1. Specific, actionable steps the parent can take
2. Age-appropriate activities and support strategies
3. Cambridge curriculum alignment
4. Building on the child's strengths and addressing challenges

RESPONSE FORMAT (JSON):
{{
    "recommendations": [
        {{
            "category": "learning_support|curriculum|motivation|assessment|esl_support",
            "priority": "high|medium|low",
            "title": "Clear, actionable title (max 100 chars)",
            "description": "Detailed explanation (max 500 chars)",
            "actionable_steps": ["Step 1", "Step 2", "Step 3"],
            "resources": [
                {{"type": "article", "title": "Resource title", "url": "example.com"}},
                {{"type": "activity", "title": "Activity name", "description": "How to do it"}}
            ],
            "estimated_time_minutes": 15,
            "success_indicators": ["How to know it's working", "What to look for"]
        }}
    ]
}}"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Please generate personalized guidance recommendations for this parent-child pair."}
            ]
            
            response = await make_llm_api_call(
                messages=messages,
                model_name="gpt-4",
                temperature=0.4,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            ai_result = json.loads(response.choices[0].message.content)
            recommendations = []
            
            for rec_data in ai_result.get("recommendations", []):
                try:
                    recommendation = GuidanceRecommendation(
                        parent_id=parent.parent_id,
                        child_id=child.child_id,
                        category=GuidanceCategory(rec_data.get("category", "learning_support")),
                        priority=GuidancePriority(rec_data.get("priority", "medium")),
                        title=rec_data.get("title", "Guidance Recommendation"),
                        description=rec_data.get("description", ""),
                        actionable_steps=rec_data.get("actionable_steps", []),
                        resources=rec_data.get("resources", []),
                        estimated_time_minutes=rec_data.get("estimated_time_minutes"),
                        success_indicators=rec_data.get("success_indicators", [])
                    )
                    recommendations.append(recommendation)
                except Exception as e:
                    logger.warning(f"Error creating recommendation: {str(e)}")
                    continue
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating AI guidance: {str(e)}")
            return []
    
    async def _gather_child_context(self, child_id: str, base_context: Dict[str, Any]) -> Dict[str, Any]:
        """Gather recent context about the child for guidance generation"""
        try:
            context = base_context.copy()
            
            # Add recent learning activities (this would integrate with other services)
            context.update({
                "recent_subjects_practiced": [],  # Would be populated from activity tracking
                "recent_achievements": [],        # Would be populated from gamification service
                "areas_of_struggle": [],         # Would be populated from progress tracking
                "parent_reported_concerns": [],   # Could be from parent input
                "upcoming_assessments": []       # Cambridge curriculum schedule
            })
            
            return context
            
        except Exception as e:
            logger.error(f"Error gathering child context: {str(e)}")
            return base_context
    
    async def _generate_curriculum_guidance(self, parent: ParentProfile, subject: Subject, 
                                          grade_level: int, topic: str = None) -> Dict[str, Any]:
        """Generate curriculum-specific guidance"""
        try:
            system_prompt = f"""You are a Cambridge curriculum expert providing guidance for parents.

PARENT CONTEXT:
- Guidance level: {parent.guidance_level}
- Language preference: {parent.preferred_language}

CURRICULUM CONTEXT:
- Subject: {subject.value}
- Grade level: {grade_level}
- Specific topic: {topic or 'General curriculum overview'}

TASK: Provide comprehensive curriculum guidance including:
1. What children learn at this level
2. How parents can support learning at home
3. Key skills and knowledge expectations
4. Common challenges and how to address them
5. Progression to next level

RESPONSE FORMAT (JSON):
{{
    "curriculum_overview": "What children learn in {subject.value} at grade {grade_level}",
    "key_learning_objectives": ["Objective 1", "Objective 2", "Objective 3"],
    "parent_support_strategies": [
        {{"strategy": "Strategy name", "description": "How to implement", "examples": ["Example 1", "Example 2"]}}
    ],
    "common_challenges": [
        {{"challenge": "Challenge description", "solutions": ["Solution 1", "Solution 2"]}}
    ],
    "home_activities": [
        {{"activity": "Activity name", "instructions": "How to do it", "materials": ["Material 1", "Material 2"]}}
    ],
    "assessment_expectations": "What children should be able to do",
    "next_level_preparation": "How to prepare for the next grade level"
}}"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please provide curriculum guidance for {subject.value} at grade {grade_level}" + (f" focusing on {topic}" if topic else "")}
            ]
            
            response = await make_llm_api_call(
                messages=messages,
                model_name="gpt-4",
                temperature=0.3,
                max_tokens=1200,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Error generating curriculum guidance: {str(e)}")
            return {"error": "Failed to generate curriculum guidance"}
    
    async def _store_guidance_recommendation(self, recommendation: GuidanceRecommendation) -> bool:
        """Store guidance recommendation in database"""
        try:
            # This would store in a dedicated guidance_recommendations table
            # For now, we'll log it
            logger.info(f"Storing guidance recommendation: {recommendation.title} for parent {recommendation.parent_id}")
            return True
        except Exception as e:
            logger.error(f"Error storing guidance recommendation: {str(e)}")
            return False
    
    async def _log_faq_search(self, parent_id: str, query: str, results_count: int) -> None:
        """Log FAQ search for analytics"""
        try:
            logger.info(f"FAQ search by {parent_id}: '{query}' -> {results_count} results")
        except Exception as e:
            logger.error(f"Error logging FAQ search: {str(e)}")
    
    def _initialize_faq_database(self) -> List[FAQItem]:
        """Initialize the FAQ database with common questions"""
        return [
            # Curriculum FAQs
            FAQItem(
                category=GuidanceCategory.CURRICULUM,
                question="What should my child know in Cambridge Math Grade 3?",
                answer="Grade 3 Cambridge Math covers: number and place value up to 1000, addition and subtraction with 3-digit numbers, multiplication tables 2-10, fractions (halves, quarters, thirds), basic geometry shapes, and simple data handling. Children should be able to solve word problems and explain their thinking.",
                keywords=["math", "grade 3", "curriculum", "expectations", "skills"],
                grade_levels=[3],
                subjects=[Subject.MATHEMATICS],
                popularity_score=0.9
            ),
            FAQItem(
                category=GuidanceCategory.LEARNING_SUPPORT,
                question="How can I help my child with Cambridge Math at home?",
                answer="Support math learning through: daily practice with number facts, using real-life examples (cooking, shopping), playing math games, encouraging problem-solving discussions, using visual aids and manipulatives, celebrating mistakes as learning opportunities, and connecting math to their interests.",
                keywords=["math", "home support", "practice", "activities", "parent help"],
                grade_levels=[1, 2, 3, 4, 5, 6],
                subjects=[Subject.MATHEMATICS],
                popularity_score=0.95
            ),
            FAQItem(
                category=GuidanceCategory.ESL_SUPPORT,
                question="How can I support my child's English learning if it's not my first language?",
                answer="Even if English isn't your first language, you can help by: reading together in any language (develops literacy skills), encouraging your child to explain their learning to you, using educational apps and videos, connecting with English-speaking families, celebrating multilingual abilities, and focusing on encouragement rather than correction.",
                keywords=["ESL", "English", "second language", "parent support", "multilingual"],
                grade_levels=[1, 2, 3, 4, 5, 6],
                subjects=[Subject.ESL],
                popularity_score=0.85
            ),
            FAQItem(
                category=GuidanceCategory.MOTIVATION,
                question="My child has lost interest in learning. How can I re-engage them?",
                answer="Re-engage your child by: connecting learning to their interests, setting small achievable goals, celebrating progress not perfection, offering choices in how they learn, taking breaks when frustrated, using games and hands-on activities, and showing genuine interest in their thoughts and discoveries.",
                keywords=["motivation", "engagement", "interest", "encouragement", "learning"],
                grade_levels=[1, 2, 3, 4, 5, 6],
                subjects=[Subject.MATHEMATICS, Subject.ESL, Subject.SCIENCE],
                popularity_score=0.88
            ),
            FAQItem(
                category=GuidanceCategory.TECHNOLOGY,
                question="How much screen time is appropriate for educational apps?",
                answer="For primary children: Ages 5-7: 30-45 minutes daily, Ages 8-10: 45-60 minutes daily, Ages 11-12: 60-90 minutes daily. Focus on high-quality educational content, take regular breaks, balance with offline activities, and engage with your child about what they're learning online.",
                keywords=["screen time", "technology", "apps", "limits", "digital learning"],
                grade_levels=[1, 2, 3, 4, 5, 6],
                subjects=[Subject.MATHEMATICS, Subject.ESL, Subject.SCIENCE],
                popularity_score=0.82
            ),
            FAQItem(
                category=GuidanceCategory.ASSESSMENT,
                question="How can I prepare my child for Cambridge assessments?",
                answer="Prepare for assessments by: practicing past papers, understanding the format, building confidence through regular practice, focusing on understanding not memorization, teaching time management, discussing answers together, maintaining a positive attitude, and ensuring good rest and nutrition.",
                keywords=["assessment", "exams", "preparation", "practice", "cambridge"],
                grade_levels=[3, 4, 5, 6],
                subjects=[Subject.MATHEMATICS, Subject.ESL, Subject.SCIENCE],
                popularity_score=0.90
            ),
            FAQItem(
                category=GuidanceCategory.SAFETY,
                question="How can I ensure my child is safe while learning online?",
                answer="Ensure online safety by: using parental controls, monitoring online activity, teaching about appropriate online behavior, creating device-free zones, setting time limits, choosing age-appropriate content, keeping devices in common areas, and having regular conversations about online experiences.",
                keywords=["safety", "online", "internet", "protection", "supervision"],
                grade_levels=[1, 2, 3, 4, 5, 6],
                subjects=[Subject.MATHEMATICS, Subject.ESL, Subject.SCIENCE],
                popularity_score=0.87
            ),
            FAQItem(
                category=GuidanceCategory.CURRICULUM,
                question="What is the Cambridge Primary Science curriculum like?",
                answer="Cambridge Primary Science focuses on: thinking and working scientifically, biology (living things, habitats, life processes), chemistry (materials and their properties), physics (forces, light, sound, electricity). Children learn through investigation, observation, and hands-on experiments, developing scientific thinking skills.",
                keywords=["science", "curriculum", "biology", "chemistry", "physics", "experiments"],
                grade_levels=[1, 2, 3, 4, 5, 6],
                subjects=[Subject.SCIENCE],
                popularity_score=0.83
            ),
            FAQItem(
                category=GuidanceCategory.LEARNING_SUPPORT,
                question="My child struggles with reading comprehension. How can I help?",
                answer="Support reading comprehension by: reading together daily, asking questions about the story, discussing characters and plot, connecting to personal experiences, practicing prediction skills, retelling stories in their own words, using picture books for visual support, and being patient with progress.",
                keywords=["reading", "comprehension", "literacy", "support", "understanding"],
                grade_levels=[1, 2, 3, 4, 5, 6],
                subjects=[Subject.ESL],
                popularity_score=0.92
            ),
            FAQItem(
                category=GuidanceCategory.SPECIAL_NEEDS,
                question="How can I support my child if they have learning difficulties?",
                answer="Support children with learning difficulties by: breaking tasks into smaller steps, using multiple learning styles (visual, auditory, kinesthetic), celebrating small victories, being patient and encouraging, working closely with teachers, using assistive technology when helpful, and focusing on strengths while addressing challenges.",
                keywords=["special needs", "learning difficulties", "support", "accommodation", "individual"],
                grade_levels=[1, 2, 3, 4, 5, 6],
                subjects=[Subject.MATHEMATICS, Subject.ESL, Subject.SCIENCE],
                popularity_score=0.78
            )
        ]
    
    def _initialize_guidance_templates(self) -> Dict[GuidanceCategory, Dict[str, str]]:
        """Initialize guidance templates for different categories"""
        return {
            GuidanceCategory.CURRICULUM: {
                "title_template": "Cambridge {subject} Support for Grade {grade}",
                "description_template": "Specific guidance for supporting your child's {subject} learning at the Grade {grade} level"
            },
            GuidanceCategory.LEARNING_SUPPORT: {
                "title_template": "Supporting {child_name}'s Learning Journey",
                "description_template": "Personalized strategies to help {child_name} succeed in their studies"
            },
            GuidanceCategory.MOTIVATION: {
                "title_template": "Keeping {child_name} Motivated to Learn",
                "description_template": "Strategies to maintain engagement and enthusiasm for learning"
            },
            GuidanceCategory.ESL_SUPPORT: {
                "title_template": "English Language Support for {child_name}",
                "description_template": "Specific strategies for supporting English as a Second Language learning"
            }
        }
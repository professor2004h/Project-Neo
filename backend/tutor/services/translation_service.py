"""
Translation Service - Multilingual support for parents
Task 9.2 implementation - Translation service integration, multilingual content delivery, cultural adaptation
"""
import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone, timedelta
from enum import Enum
from pydantic import BaseModel, Field
import uuid
import hashlib

from utils.logger import logger
from services.supabase import DBConnection
from services.llm import make_llm_api_call
from ..repositories.user_repository import ParentProfileRepository
from ..models.user_models import ParentProfile


class SupportedLanguage(str, Enum):
    """Supported languages for translation"""
    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    ITALIAN = "it"
    PORTUGUESE = "pt"
    ARABIC = "ar"
    CHINESE_SIMPLIFIED = "zh-cn"
    CHINESE_TRADITIONAL = "zh-tw"
    JAPANESE = "ja"
    KOREAN = "ko"
    HINDI = "hi"
    RUSSIAN = "ru"
    DUTCH = "nl"
    SWEDISH = "sv"
    NORWEGIAN = "no"
    DANISH = "da"
    FINNISH = "fi"


class ContentType(str, Enum):
    """Types of content that can be translated"""
    PROGRESS_REPORT = "progress_report"
    GUIDANCE = "guidance"
    FAQ = "faq"
    NOTIFICATION = "notification"
    UI_TEXT = "ui_text"
    CURRICULUM_EXPLANATION = "curriculum_explanation"
    ACHIEVEMENT = "achievement"
    RECOMMENDATION = "recommendation"


class CulturalContext(str, Enum):
    """Cultural contexts for adaptation"""
    WESTERN = "western"
    EAST_ASIAN = "east_asian"
    MIDDLE_EASTERN = "middle_eastern"
    SOUTH_ASIAN = "south_asian"
    LATIN_AMERICAN = "latin_american"
    AFRICAN = "african"
    NORDIC = "nordic"


class TranslationRequest(BaseModel):
    """Model for translation requests"""
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = Field(max_length=5000)
    source_language: SupportedLanguage = Field(default=SupportedLanguage.ENGLISH)
    target_language: SupportedLanguage
    content_type: ContentType
    cultural_context: Optional[CulturalContext] = None
    preserve_formatting: bool = Field(default=True)
    child_age: Optional[int] = None
    parent_guidance_level: Optional[str] = None
    
    class Config:
        from_attributes = True


class TranslationResult(BaseModel):
    """Model for translation results"""
    request_id: str
    translated_content: str
    source_language: SupportedLanguage
    target_language: SupportedLanguage
    content_type: ContentType
    confidence_score: float = Field(ge=0.0, le=1.0)
    cultural_adaptations: List[str] = Field(default_factory=list)
    translation_notes: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cached: bool = Field(default=False)
    
    class Config:
        from_attributes = True


class CulturalAdaptation(BaseModel):
    """Model for cultural adaptation recommendations"""
    adaptation_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_content: str
    target_language: SupportedLanguage
    cultural_context: CulturalContext
    adaptations: List[Dict[str, str]] = Field(default_factory=list)
    reasoning: str = Field(default="")
    confidence_score: float = Field(ge=0.0, le=1.0)
    
    class Config:
        from_attributes = True


class TranslationCache(BaseModel):
    """Model for translation caching"""
    cache_key: str
    content_hash: str
    source_language: SupportedLanguage
    target_language: SupportedLanguage
    content_type: ContentType
    translated_content: str
    cultural_adaptations: List[str] = Field(default_factory=list)
    access_count: int = Field(default=0)
    last_accessed: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    
    class Config:
        from_attributes = True


class TranslationService:
    """
    Comprehensive translation and multilingual support service for parents
    """
    
    def __init__(self, db: DBConnection):
        self.db = db
        self.parent_repo = ParentProfileRepository(db)
        
        # Translation cache (in production, this would use Redis)
        self.translation_cache: Dict[str, TranslationCache] = {}
        
        # Language mappings and cultural contexts
        self.language_cultural_mapping = self._initialize_language_cultural_mapping()
        self.ui_translations = self._initialize_ui_translations()
        
        # Quality thresholds
        self.min_confidence_score = 0.7
        self.cache_duration_hours = 24
    
    async def translate_content(self, request: TranslationRequest) -> TranslationResult:
        """
        Translate content with cultural adaptation
        
        Args:
            request: Translation request details
            
        Returns:
            Translation result with cultural adaptations
        """
        try:
            # Check cache first
            cache_key = self._generate_cache_key(request)
            cached_result = await self._get_cached_translation(cache_key)
            
            if cached_result:
                logger.info(f"Using cached translation for {request.content_type}")
                return TranslationResult(
                    request_id=request.request_id,
                    translated_content=cached_result.translated_content,
                    source_language=request.source_language,
                    target_language=request.target_language,
                    content_type=request.content_type,
                    confidence_score=0.95,  # High confidence for cached content
                    cultural_adaptations=cached_result.cultural_adaptations,
                    cached=True
                )
            
            # Determine cultural context if not provided
            cultural_context = request.cultural_context
            if not cultural_context:
                cultural_context = self._infer_cultural_context(request.target_language)
            
            # Perform AI-powered translation with cultural adaptation
            translation_result = await self._ai_translate_with_cultural_adaptation(
                request, cultural_context
            )
            
            # Cache the result if quality is sufficient
            if translation_result.confidence_score >= self.min_confidence_score:
                await self._cache_translation(cache_key, request, translation_result)
            
            logger.info(f"Translated {request.content_type} from {request.source_language} to {request.target_language}")
            return translation_result
            
        except Exception as e:
            logger.error(f"Error translating content: {str(e)}")
            # Return fallback result
            return TranslationResult(
                request_id=request.request_id,
                translated_content=request.content,  # Return original if translation fails
                source_language=request.source_language,
                target_language=request.target_language,
                content_type=request.content_type,
                confidence_score=0.0,
                translation_notes="Translation failed, showing original content"
            )
    
    async def translate_for_parent(self, parent_id: str, content: str, 
                                 content_type: ContentType, child_age: int = None) -> str:
        """
        Translate content specifically for a parent based on their profile
        
        Args:
            parent_id: ID of the parent
            content: Content to translate
            content_type: Type of content
            child_age: Age of child (for context)
            
        Returns:
            Translated content string
        """
        try:
            # Get parent profile
            parent = await self.parent_repo.get_parent_profile_by_user_id(parent_id)
            if not parent:
                logger.warning(f"Parent profile not found: {parent_id}")
                return content
            
            # If already in preferred language, return as-is
            if parent.preferred_language == SupportedLanguage.ENGLISH.value:
                return content
            
            # Check if target language is supported
            try:
                target_language = SupportedLanguage(parent.preferred_language)
            except ValueError:
                logger.warning(f"Unsupported language: {parent.preferred_language}")
                return content
            
            # Create translation request
            request = TranslationRequest(
                content=content,
                target_language=target_language,
                content_type=content_type,
                child_age=child_age,
                parent_guidance_level=parent.guidance_level
            )
            
            # Translate
            result = await self.translate_content(request)
            return result.translated_content
            
        except Exception as e:
            logger.error(f"Error translating for parent {parent_id}: {str(e)}")
            return content
    
    async def get_ui_translations(self, language: SupportedLanguage) -> Dict[str, str]:
        """
        Get UI translations for a specific language
        
        Args:
            language: Target language
            
        Returns:
            Dictionary of UI translations
        """
        try:
            if language == SupportedLanguage.ENGLISH:
                return self.ui_translations[SupportedLanguage.ENGLISH]
            
            # Check cache for UI translations
            cache_key = f"ui_translations_{language.value}"
            if cache_key in self.translation_cache:
                cached = self.translation_cache[cache_key]
                if cached.expires_at > datetime.now(timezone.utc):
                    return json.loads(cached.translated_content)
            
            # Translate UI elements
            english_ui = self.ui_translations[SupportedLanguage.ENGLISH]
            translated_ui = {}
            
            for key, english_text in english_ui.items():
                request = TranslationRequest(
                    content=english_text,
                    target_language=language,
                    content_type=ContentType.UI_TEXT
                )
                result = await self.translate_content(request)
                translated_ui[key] = result.translated_content
            
            # Cache UI translations
            cache_entry = TranslationCache(
                cache_key=cache_key,
                content_hash=hashlib.md5(json.dumps(english_ui).encode()).hexdigest(),
                source_language=SupportedLanguage.ENGLISH,
                target_language=language,
                content_type=ContentType.UI_TEXT,
                translated_content=json.dumps(translated_ui),
                expires_at=datetime.now(timezone.utc) + timedelta(days=7)  # UI translations cached longer
            )
            self.translation_cache[cache_key] = cache_entry
            
            return translated_ui
            
        except Exception as e:
            logger.error(f"Error getting UI translations for {language}: {str(e)}")
            return self.ui_translations[SupportedLanguage.ENGLISH]
    
    async def get_cultural_adaptation_suggestions(self, content: str, 
                                                target_language: SupportedLanguage,
                                                content_type: ContentType) -> CulturalAdaptation:
        """
        Get cultural adaptation suggestions for content
        
        Args:
            content: Content to adapt
            target_language: Target language
            content_type: Type of content
            
        Returns:
            Cultural adaptation suggestions
        """
        try:
            cultural_context = self._infer_cultural_context(target_language)
            
            # Use AI to generate cultural adaptation suggestions
            adaptation = await self._generate_cultural_adaptations(
                content, target_language, cultural_context, content_type
            )
            
            return adaptation
            
        except Exception as e:
            logger.error(f"Error generating cultural adaptations: {str(e)}")
            return CulturalAdaptation(
                source_content=content,
                target_language=target_language,
                cultural_context=CulturalContext.WESTERN,
                confidence_score=0.0
            )
    
    async def _ai_translate_with_cultural_adaptation(self, request: TranslationRequest, 
                                                   cultural_context: CulturalContext) -> TranslationResult:
        """Use AI to translate content with cultural adaptation"""
        try:
            # Build context for AI translation
            context_info = {
                "target_language": request.target_language.value,
                "cultural_context": cultural_context.value,
                "content_type": request.content_type.value,
                "child_age": request.child_age,
                "parent_guidance_level": request.parent_guidance_level
            }
            
            system_prompt = f"""You are an expert translator specializing in educational content for parents. Your task is to translate content while adapting it culturally for the target audience.

TARGET LANGUAGE: {request.target_language.value}
CULTURAL CONTEXT: {cultural_context.value}
CONTENT TYPE: {request.content_type.value}
CHILD AGE: {request.child_age or 'not specified'}
PARENT GUIDANCE LEVEL: {request.parent_guidance_level or 'intermediate'}

TRANSLATION REQUIREMENTS:
1. Translate accurately while maintaining meaning and tone
2. Adapt cultural references to be appropriate for the target culture
3. Use parent-friendly language appropriate for the guidance level
4. Maintain educational context and terminology accuracy
5. Consider cultural attitudes toward education and parenting

RESPONSE FORMAT (JSON):
{{
    "translated_content": "The translated and culturally adapted content",
    "confidence_score": 0.95,
    "cultural_adaptations": [
        "Explanation of cultural adaptation 1",
        "Explanation of cultural adaptation 2"
    ],
    "translation_notes": "Any important notes about the translation choices"
}}

CONTENT TO TRANSLATE:
{request.content}"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please translate and culturally adapt this content for {request.target_language.value} speakers."}
            ]
            
            response = await make_llm_api_call(
                messages=messages,
                model_name="gpt-4",
                temperature=0.3,
                max_tokens=1500,
                response_format={"type": "json_object"}
            )
            
            ai_result = json.loads(response.choices[0].message.content)
            
            return TranslationResult(
                request_id=request.request_id,
                translated_content=ai_result.get("translated_content", request.content),
                source_language=request.source_language,
                target_language=request.target_language,
                content_type=request.content_type,
                confidence_score=ai_result.get("confidence_score", 0.8),
                cultural_adaptations=ai_result.get("cultural_adaptations", []),
                translation_notes=ai_result.get("translation_notes")
            )
            
        except Exception as e:
            logger.error(f"Error in AI translation: {str(e)}")
            raise
    
    async def _generate_cultural_adaptations(self, content: str, target_language: SupportedLanguage,
                                           cultural_context: CulturalContext, 
                                           content_type: ContentType) -> CulturalAdaptation:
        """Generate cultural adaptation suggestions using AI"""
        try:
            system_prompt = f"""You are a cultural adaptation expert for educational content. Analyze the provided content and suggest cultural adaptations for the target audience.

TARGET LANGUAGE: {target_language.value}
CULTURAL CONTEXT: {cultural_context.value}
CONTENT TYPE: {content_type.value}

TASK: Analyze the content and suggest specific cultural adaptations that would make it more appropriate and effective for the target cultural context. Consider:
1. Educational values and approaches in the target culture
2. Parent-child relationship dynamics
3. Communication styles and preferences
4. Cultural attitudes toward learning and achievement
5. Family structures and roles

RESPONSE FORMAT (JSON):
{{
    "adaptations": [
        {{
            "type": "cultural_reference|communication_style|educational_approach|family_dynamic",
            "original": "Original content that needs adaptation",
            "adapted": "Culturally adapted version",
            "reasoning": "Why this adaptation is important for the target culture"
        }}
    ],
    "reasoning": "Overall reasoning for the cultural adaptations",
    "confidence_score": 0.85
}}

CONTENT TO ANALYZE:
{content}"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Please analyze this content for cultural adaptation to {cultural_context.value} context."}
            ]
            
            response = await make_llm_api_call(
                messages=messages,
                model_name="gpt-4",
                temperature=0.4,
                max_tokens=800,
                response_format={"type": "json_object"}
            )
            
            ai_result = json.loads(response.choices[0].message.content)
            
            return CulturalAdaptation(
                source_content=content,
                target_language=target_language,
                cultural_context=cultural_context,
                adaptations=ai_result.get("adaptations", []),
                reasoning=ai_result.get("reasoning", ""),
                confidence_score=ai_result.get("confidence_score", 0.8)
            )
            
        except Exception as e:
            logger.error(f"Error generating cultural adaptations: {str(e)}")
            raise
    
    def _generate_cache_key(self, request: TranslationRequest) -> str:
        """Generate cache key for translation request"""
        content_hash = hashlib.md5(request.content.encode()).hexdigest()
        return f"trans_{request.source_language.value}_{request.target_language.value}_{request.content_type.value}_{content_hash[:12]}"
    
    async def _get_cached_translation(self, cache_key: str) -> Optional[TranslationCache]:
        """Get cached translation if available and not expired"""
        try:
            if cache_key in self.translation_cache:
                cached = self.translation_cache[cache_key]
                if cached.expires_at > datetime.now(timezone.utc):
                    # Update access statistics
                    cached.access_count += 1
                    cached.last_accessed = datetime.now(timezone.utc)
                    return cached
                else:
                    # Remove expired cache entry
                    del self.translation_cache[cache_key]
            return None
        except Exception as e:
            logger.error(f"Error getting cached translation: {str(e)}")
            return None
    
    async def _cache_translation(self, cache_key: str, request: TranslationRequest, 
                               result: TranslationResult) -> None:
        """Cache translation result"""
        try:
            cache_entry = TranslationCache(
                cache_key=cache_key,
                content_hash=hashlib.md5(request.content.encode()).hexdigest(),
                source_language=request.source_language,
                target_language=request.target_language,
                content_type=request.content_type,
                translated_content=result.translated_content,
                cultural_adaptations=result.cultural_adaptations,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=self.cache_duration_hours)
            )
            
            self.translation_cache[cache_key] = cache_entry
            
            # Cleanup old cache entries periodically
            if len(self.translation_cache) > 1000:
                await self._cleanup_cache()
                
        except Exception as e:
            logger.error(f"Error caching translation: {str(e)}")
    
    async def _cleanup_cache(self) -> None:
        """Clean up expired cache entries"""
        try:
            now = datetime.now(timezone.utc)
            expired_keys = [
                key for key, cache_entry in self.translation_cache.items()
                if cache_entry.expires_at <= now
            ]
            
            for key in expired_keys:
                del self.translation_cache[key]
            
            logger.info(f"Cleaned up {len(expired_keys)} expired cache entries")
            
        except Exception as e:
            logger.error(f"Error cleaning up cache: {str(e)}")
    
    def _infer_cultural_context(self, language: SupportedLanguage) -> CulturalContext:
        """Infer cultural context from language"""
        return self.language_cultural_mapping.get(language, CulturalContext.WESTERN)
    
    def _initialize_language_cultural_mapping(self) -> Dict[SupportedLanguage, CulturalContext]:
        """Initialize language to cultural context mapping"""
        return {
            SupportedLanguage.ENGLISH: CulturalContext.WESTERN,
            SupportedLanguage.SPANISH: CulturalContext.LATIN_AMERICAN,
            SupportedLanguage.FRENCH: CulturalContext.WESTERN,
            SupportedLanguage.GERMAN: CulturalContext.WESTERN,
            SupportedLanguage.ITALIAN: CulturalContext.WESTERN,
            SupportedLanguage.PORTUGUESE: CulturalContext.LATIN_AMERICAN,
            SupportedLanguage.ARABIC: CulturalContext.MIDDLE_EASTERN,
            SupportedLanguage.CHINESE_SIMPLIFIED: CulturalContext.EAST_ASIAN,
            SupportedLanguage.CHINESE_TRADITIONAL: CulturalContext.EAST_ASIAN,
            SupportedLanguage.JAPANESE: CulturalContext.EAST_ASIAN,
            SupportedLanguage.KOREAN: CulturalContext.EAST_ASIAN,
            SupportedLanguage.HINDI: CulturalContext.SOUTH_ASIAN,
            SupportedLanguage.RUSSIAN: CulturalContext.WESTERN,
            SupportedLanguage.DUTCH: CulturalContext.WESTERN,
            SupportedLanguage.SWEDISH: CulturalContext.NORDIC,
            SupportedLanguage.NORWEGIAN: CulturalContext.NORDIC,
            SupportedLanguage.DANISH: CulturalContext.NORDIC,
            SupportedLanguage.FINNISH: CulturalContext.NORDIC,
        }
    
    def _initialize_ui_translations(self) -> Dict[SupportedLanguage, Dict[str, str]]:
        """Initialize base UI translations"""
        return {
            SupportedLanguage.ENGLISH: {
                "dashboard_title": "Parent Dashboard",
                "progress_report": "Progress Report",
                "recommendations": "Recommendations",
                "child_activities": "Child Activities",
                "learning_insights": "Learning Insights",
                "safety_settings": "Safety Settings",
                "guidance": "Guidance",
                "faq": "Frequently Asked Questions",
                "support": "Support",
                "settings": "Settings",
                "notifications": "Notifications",
                "achievements": "Achievements",
                "curriculum": "Curriculum",
                "subjects": "Subjects",
                "mathematics": "Mathematics",
                "english": "English",
                "science": "Science",
                "grade_level": "Grade Level",
                "age": "Age",
                "learning_time": "Learning Time",
                "session_duration": "Session Duration",
                "daily_usage": "Daily Usage",
                "weekly_progress": "Weekly Progress",
                "strengths": "Strengths",
                "areas_for_improvement": "Areas for Improvement",
                "next_steps": "Next Steps",
                "parent_guidance": "Parent Guidance",
                "help_your_child": "How to Help Your Child",
                "learning_activities": "Learning Activities",
                "at_home_support": "At-Home Support"
            }
        }
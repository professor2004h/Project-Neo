"""
Tests for Translation Service - Task 9.2 implementation
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta
import json
import hashlib

from services.supabase import DBConnection
from ..services.translation_service import (
    TranslationService, SupportedLanguage, ContentType, CulturalContext,
    TranslationRequest, TranslationResult, CulturalAdaptation, TranslationCache
)
from ..models.user_models import ParentProfile
from ..repositories.user_repository import ParentProfileRepository


class TestTranslationService:
    """Test cases for Translation Service"""
    
    @pytest.fixture
    async def mock_db(self):
        """Mock database connection"""
        db = AsyncMock(spec=DBConnection)
        return db
    
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
            preferred_language="es",  # Spanish
            guidance_level="intermediate",
            notification_preferences={"email": True, "push": False}
        )
    
    @pytest.fixture
    async def translation_service(self, mock_db, mock_parent_repo):
        """Create translation service with mocked dependencies"""
        service = TranslationService(mock_db)
        service.parent_repo = mock_parent_repo
        return service
    
    @pytest.fixture
    async def sample_translation_request(self):
        """Sample translation request"""
        return TranslationRequest(
            content="Your child has made excellent progress in mathematics this week.",
            target_language=SupportedLanguage.SPANISH,
            content_type=ContentType.PROGRESS_REPORT,
            child_age=8,
            parent_guidance_level="intermediate"
        )
    
    @pytest.mark.asyncio
    async def test_translate_content_basic_functionality(self, translation_service, sample_translation_request):
        """Test basic content translation functionality"""
        # Setup
        with patch.object(translation_service, '_get_cached_translation') as mock_cache_get:
            mock_cache_get.return_value = None  # No cached result
            
            with patch.object(translation_service, '_ai_translate_with_cultural_adaptation') as mock_ai_translate:
                mock_ai_translate.return_value = TranslationResult(
                    request_id=sample_translation_request.request_id,
                    translated_content="Su hijo ha hecho un excelente progreso en matemáticas esta semana.",
                    source_language=SupportedLanguage.ENGLISH,
                    target_language=SupportedLanguage.SPANISH,
                    content_type=ContentType.PROGRESS_REPORT,
                    confidence_score=0.92,
                    cultural_adaptations=["Adapted formal tone for Spanish parents"]
                )
                
                with patch.object(translation_service, '_cache_translation') as mock_cache_set:
                    # Execute
                    result = await translation_service.translate_content(sample_translation_request)
                    
                    # Verify
                    assert result.translated_content.startswith("Su hijo ha hecho")
                    assert result.target_language == SupportedLanguage.SPANISH
                    assert result.confidence_score == 0.92
                    assert len(result.cultural_adaptations) == 1
                    assert not result.cached
                    
                    # Verify AI translation was called
                    mock_ai_translate.assert_called_once()
                    # Verify caching was attempted (high confidence score)
                    mock_cache_set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_translate_content_cached_result(self, translation_service, sample_translation_request):
        """Test translation using cached result"""
        # Setup - mock cached result
        cached_translation = TranslationCache(
            cache_key="test_key",
            content_hash="test_hash",
            source_language=SupportedLanguage.ENGLISH,
            target_language=SupportedLanguage.SPANISH,
            content_type=ContentType.PROGRESS_REPORT,
            translated_content="Su hijo ha hecho un excelente progreso en matemáticas esta semana.",
            cultural_adaptations=["Cached adaptation"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
        )
        
        with patch.object(translation_service, '_get_cached_translation') as mock_cache_get:
            mock_cache_get.return_value = cached_translation
            
            # Execute
            result = await translation_service.translate_content(sample_translation_request)
            
            # Verify
            assert result.cached
            assert result.translated_content == "Su hijo ha hecho un excelente progreso en matemáticas esta semana."
            assert result.confidence_score == 0.95  # High confidence for cached content
            assert result.cultural_adaptations == ["Cached adaptation"]
    
    @pytest.mark.asyncio
    async def test_translate_for_parent_basic(self, translation_service, sample_parent_profile):
        """Test translation for a specific parent"""
        # Setup
        translation_service.parent_repo.get_parent_profile_by_user_id.return_value = sample_parent_profile
        
        with patch.object(translation_service, 'translate_content') as mock_translate:
            mock_translate.return_value = TranslationResult(
                request_id="test_id",
                translated_content="Contenido traducido",
                source_language=SupportedLanguage.ENGLISH,
                target_language=SupportedLanguage.SPANISH,
                content_type=ContentType.GUIDANCE,
                confidence_score=0.9
            )
            
            # Execute
            result = await translation_service.translate_for_parent(
                "parent_123", "Test content", ContentType.GUIDANCE, child_age=8
            )
            
            # Verify
            assert result == "Contenido traducido"
            mock_translate.assert_called_once()
            
            # Check the translation request was properly formed
            call_args = mock_translate.call_args[0][0]
            assert call_args.content == "Test content"
            assert call_args.target_language == SupportedLanguage.SPANISH
            assert call_args.content_type == ContentType.GUIDANCE
            assert call_args.child_age == 8
    
    @pytest.mark.asyncio
    async def test_translate_for_parent_english_language(self, translation_service):
        """Test translation for parent with English preference"""
        # Setup - parent with English preference
        english_parent = ParentProfile(
            parent_id="parent_124",
            user_id="user_124",
            children_ids=["child_124"],
            preferred_language="en",  # English
            guidance_level="beginner"
        )
        
        translation_service.parent_repo.get_parent_profile_by_user_id.return_value = english_parent
        
        # Execute
        result = await translation_service.translate_for_parent(
            "parent_124", "Test content", ContentType.GUIDANCE
        )
        
        # Verify - should return original content for English
        assert result == "Test content"
    
    @pytest.mark.asyncio
    async def test_translate_for_parent_unsupported_language(self, translation_service):
        """Test translation for parent with unsupported language"""
        # Setup - parent with unsupported language
        unsupported_parent = ParentProfile(
            parent_id="parent_125",
            user_id="user_125",
            children_ids=["child_125"],
            preferred_language="xyz",  # Unsupported language
            guidance_level="advanced"
        )
        
        translation_service.parent_repo.get_parent_profile_by_user_id.return_value = unsupported_parent
        
        # Execute
        result = await translation_service.translate_for_parent(
            "parent_125", "Test content", ContentType.GUIDANCE
        )
        
        # Verify - should return original content for unsupported language
        assert result == "Test content"
    
    @pytest.mark.asyncio
    async def test_translate_for_parent_not_found(self, translation_service):
        """Test translation when parent profile is not found"""
        # Setup
        translation_service.parent_repo.get_parent_profile_by_user_id.return_value = None
        
        # Execute
        result = await translation_service.translate_for_parent(
            "nonexistent_parent", "Test content", ContentType.GUIDANCE
        )
        
        # Verify - should return original content
        assert result == "Test content"
    
    @pytest.mark.asyncio
    async def test_get_ui_translations_english(self, translation_service):
        """Test getting UI translations for English"""
        # Execute
        ui_translations = await translation_service.get_ui_translations(SupportedLanguage.ENGLISH)
        
        # Verify
        assert "dashboard_title" in ui_translations
        assert ui_translations["dashboard_title"] == "Parent Dashboard"
        assert "progress_report" in ui_translations
        assert "mathematics" in ui_translations
    
    @pytest.mark.asyncio
    async def test_get_ui_translations_non_english(self, translation_service):
        """Test getting UI translations for non-English language"""
        # Setup - mock translation for each UI element
        with patch.object(translation_service, 'translate_content') as mock_translate:
            def translate_side_effect(request):
                # Simple mock translation
                return TranslationResult(
                    request_id=request.request_id,
                    translated_content=f"ES_{request.content}",  # Prefix with ES_
                    source_language=SupportedLanguage.ENGLISH,
                    target_language=SupportedLanguage.SPANISH,
                    content_type=ContentType.UI_TEXT,
                    confidence_score=0.9
                )
            
            mock_translate.side_effect = translate_side_effect
            
            # Execute
            ui_translations = await translation_service.get_ui_translations(SupportedLanguage.SPANISH)
            
            # Verify
            assert "dashboard_title" in ui_translations
            assert ui_translations["dashboard_title"] == "ES_Parent Dashboard"
            assert "progress_report" in ui_translations
            assert ui_translations["progress_report"] == "ES_Progress Report"
    
    @pytest.mark.asyncio
    async def test_get_cultural_adaptation_suggestions(self, translation_service):
        """Test getting cultural adaptation suggestions"""
        # Setup
        with patch.object(translation_service, '_generate_cultural_adaptations') as mock_generate:
            mock_generate.return_value = CulturalAdaptation(
                source_content="Your child needs to work harder.",
                target_language=SupportedLanguage.SPANISH,
                cultural_context=CulturalContext.LATIN_AMERICAN,
                adaptations=[
                    {
                        "type": "communication_style",
                        "original": "work harder",
                        "adapted": "practice more consistently",
                        "reasoning": "Softer approach preferred in Latin American cultures"
                    }
                ],
                reasoning="Adapted for more supportive communication style",
                confidence_score=0.85
            )
            
            # Execute
            adaptation = await translation_service.get_cultural_adaptation_suggestions(
                "Your child needs to work harder.",
                SupportedLanguage.SPANISH,
                ContentType.GUIDANCE
            )
            
            # Verify
            assert adaptation.target_language == SupportedLanguage.SPANISH
            assert adaptation.cultural_context == CulturalContext.LATIN_AMERICAN
            assert len(adaptation.adaptations) == 1
            assert adaptation.adaptations[0]["adapted"] == "practice more consistently"
            assert adaptation.confidence_score == 0.85
    
    @pytest.mark.asyncio
    @patch('services.llm.make_llm_api_call')
    async def test_ai_translate_with_cultural_adaptation(self, mock_llm_call, translation_service, sample_translation_request):
        """Test AI translation with cultural adaptation"""
        # Setup
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "translated_content": "Su hijo ha hecho un excelente progreso en matemáticas esta semana.",
            "confidence_score": 0.92,
            "cultural_adaptations": [
                "Used formal 'su hijo' instead of informal 'tu hijo'",
                "Emphasized positive progress typical in Latin American educational communication"
            ],
            "translation_notes": "Adapted for formal parent-teacher communication style"
        })
        mock_llm_call.return_value = mock_response
        
        # Execute
        result = await translation_service._ai_translate_with_cultural_adaptation(
            sample_translation_request, CulturalContext.LATIN_AMERICAN
        )
        
        # Verify
        assert result.translated_content == "Su hijo ha hecho un excelente progreso en matemáticas esta semana."
        assert result.confidence_score == 0.92
        assert len(result.cultural_adaptations) == 2
        assert "formal 'su hijo'" in result.cultural_adaptations[0]
        assert result.translation_notes == "Adapted for formal parent-teacher communication style"
        mock_llm_call.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('services.llm.make_llm_api_call')
    async def test_generate_cultural_adaptations(self, mock_llm_call, translation_service):
        """Test cultural adaptation generation"""
        # Setup
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = json.dumps({
            "adaptations": [
                {
                    "type": "communication_style",
                    "original": "Your child should practice more",
                    "adapted": "It would be beneficial for your child to have additional practice opportunities",
                    "reasoning": "More respectful and collaborative tone preferred in East Asian cultures"
                }
            ],
            "reasoning": "Adapted communication style to be more respectful and less direct",
            "confidence_score": 0.88
        })
        mock_llm_call.return_value = mock_response
        
        # Execute
        adaptation = await translation_service._generate_cultural_adaptations(
            "Your child should practice more",
            SupportedLanguage.CHINESE_SIMPLIFIED,
            CulturalContext.EAST_ASIAN,
            ContentType.GUIDANCE
        )
        
        # Verify
        assert adaptation.target_language == SupportedLanguage.CHINESE_SIMPLIFIED
        assert adaptation.cultural_context == CulturalContext.EAST_ASIAN
        assert len(adaptation.adaptations) == 1
        assert adaptation.adaptations[0]["type"] == "communication_style"
        assert "respectful and collaborative" in adaptation.adaptations[0]["reasoning"]
        assert adaptation.confidence_score == 0.88
        mock_llm_call.assert_called_once()
    
    def test_generate_cache_key(self, translation_service, sample_translation_request):
        """Test cache key generation"""
        # Execute
        cache_key = translation_service._generate_cache_key(sample_translation_request)
        
        # Verify
        assert cache_key.startswith("trans_en_es_progress_report_")
        assert len(cache_key) > 30  # Should include content hash
        
        # Test that same request generates same key
        cache_key2 = translation_service._generate_cache_key(sample_translation_request)
        assert cache_key == cache_key2
    
    @pytest.mark.asyncio
    async def test_cache_translation_and_retrieval(self, translation_service, sample_translation_request):
        """Test caching and retrieving translations"""
        # Setup
        cache_key = "test_cache_key"
        translation_result = TranslationResult(
            request_id=sample_translation_request.request_id,
            translated_content="Cached content",
            source_language=SupportedLanguage.ENGLISH,
            target_language=SupportedLanguage.SPANISH,
            content_type=ContentType.PROGRESS_REPORT,
            confidence_score=0.9,
            cultural_adaptations=["Test adaptation"]
        )
        
        # Cache the translation
        await translation_service._cache_translation(cache_key, sample_translation_request, translation_result)
        
        # Retrieve from cache
        cached_result = await translation_service._get_cached_translation(cache_key)
        
        # Verify
        assert cached_result is not None
        assert cached_result.translated_content == "Cached content"
        assert cached_result.cultural_adaptations == ["Test adaptation"]
        assert cached_result.access_count == 1  # Should increment on access
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, translation_service, sample_translation_request):
        """Test cache expiration functionality"""
        # Setup - create expired cache entry
        cache_key = "expired_key"
        expired_cache = TranslationCache(
            cache_key=cache_key,
            content_hash="test_hash",
            source_language=SupportedLanguage.ENGLISH,
            target_language=SupportedLanguage.SPANISH,
            content_type=ContentType.GUIDANCE,
            translated_content="Expired content",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1)  # Expired
        )
        
        translation_service.translation_cache[cache_key] = expired_cache
        
        # Execute
        cached_result = await translation_service._get_cached_translation(cache_key)
        
        # Verify
        assert cached_result is None
        assert cache_key not in translation_service.translation_cache  # Should be removed
    
    def test_infer_cultural_context(self, translation_service):
        """Test cultural context inference from language"""
        # Test various language mappings
        assert translation_service._infer_cultural_context(SupportedLanguage.SPANISH) == CulturalContext.LATIN_AMERICAN
        assert translation_service._infer_cultural_context(SupportedLanguage.CHINESE_SIMPLIFIED) == CulturalContext.EAST_ASIAN
        assert translation_service._infer_cultural_context(SupportedLanguage.ARABIC) == CulturalContext.MIDDLE_EASTERN
        assert translation_service._infer_cultural_context(SupportedLanguage.HINDI) == CulturalContext.SOUTH_ASIAN
        assert translation_service._infer_cultural_context(SupportedLanguage.SWEDISH) == CulturalContext.NORDIC
        assert translation_service._infer_cultural_context(SupportedLanguage.FRENCH) == CulturalContext.WESTERN
    
    def test_language_cultural_mapping_initialization(self, translation_service):
        """Test language to cultural context mapping initialization"""
        # Verify mapping exists and is comprehensive
        mapping = translation_service.language_cultural_mapping
        
        assert len(mapping) > 0
        assert SupportedLanguage.ENGLISH in mapping
        assert SupportedLanguage.SPANISH in mapping
        assert SupportedLanguage.CHINESE_SIMPLIFIED in mapping
        
        # Verify all supported languages have mappings
        for language in SupportedLanguage:
            assert language in mapping
            assert isinstance(mapping[language], CulturalContext)
    
    def test_ui_translations_initialization(self, translation_service):
        """Test UI translations initialization"""
        # Verify English UI translations exist
        english_ui = translation_service.ui_translations[SupportedLanguage.ENGLISH]
        
        assert len(english_ui) > 0
        assert "dashboard_title" in english_ui
        assert "progress_report" in english_ui
        assert "mathematics" in english_ui
        assert "subjects" in english_ui
        
        # Verify all translations are strings
        for key, value in english_ui.items():
            assert isinstance(key, str)
            assert isinstance(value, str)
            assert len(value) > 0
    
    @pytest.mark.asyncio
    async def test_error_handling_in_translation(self, translation_service, sample_translation_request):
        """Test error handling in translation process"""
        # Setup - make AI translation fail
        with patch.object(translation_service, '_get_cached_translation') as mock_cache_get:
            mock_cache_get.return_value = None
            
            with patch.object(translation_service, '_ai_translate_with_cultural_adaptation') as mock_ai_translate:
                mock_ai_translate.side_effect = Exception("AI service error")
                
                # Execute
                result = await translation_service.translate_content(sample_translation_request)
                
                # Verify - should return fallback result
                assert result.translated_content == sample_translation_request.content  # Original content
                assert result.confidence_score == 0.0
                assert "Translation failed" in result.translation_notes
    
    @pytest.mark.asyncio
    async def test_low_confidence_translation_not_cached(self, translation_service, sample_translation_request):
        """Test that low confidence translations are not cached"""
        # Setup
        with patch.object(translation_service, '_get_cached_translation') as mock_cache_get:
            mock_cache_get.return_value = None
            
            with patch.object(translation_service, '_ai_translate_with_cultural_adaptation') as mock_ai_translate:
                mock_ai_translate.return_value = TranslationResult(
                    request_id=sample_translation_request.request_id,
                    translated_content="Low quality translation",
                    source_language=SupportedLanguage.ENGLISH,
                    target_language=SupportedLanguage.SPANISH,
                    content_type=ContentType.PROGRESS_REPORT,
                    confidence_score=0.5  # Below minimum threshold (0.7)
                )
                
                with patch.object(translation_service, '_cache_translation') as mock_cache_set:
                    # Execute
                    result = await translation_service.translate_content(sample_translation_request)
                    
                    # Verify
                    assert result.confidence_score == 0.5
                    # Should not cache low confidence translation
                    mock_cache_set.assert_not_called()


class TestTranslationModels:
    """Test translation service models"""
    
    def test_translation_request_creation(self):
        """Test translation request model creation"""
        request = TranslationRequest(
            content="Test content",
            target_language=SupportedLanguage.FRENCH,
            content_type=ContentType.GUIDANCE,
            cultural_context=CulturalContext.WESTERN,
            child_age=10,
            parent_guidance_level="advanced"
        )
        
        assert request.content == "Test content"
        assert request.source_language == SupportedLanguage.ENGLISH  # Default
        assert request.target_language == SupportedLanguage.FRENCH
        assert request.content_type == ContentType.GUIDANCE
        assert request.cultural_context == CulturalContext.WESTERN
        assert request.child_age == 10
        assert request.parent_guidance_level == "advanced"
        assert request.preserve_formatting  # Default True
        assert request.request_id  # Should be auto-generated
    
    def test_translation_result_creation(self):
        """Test translation result model creation"""
        result = TranslationResult(
            request_id="test_request_123",
            translated_content="Contenu traduit",
            source_language=SupportedLanguage.ENGLISH,
            target_language=SupportedLanguage.FRENCH,
            content_type=ContentType.FAQ,
            confidence_score=0.85,
            cultural_adaptations=["Adapted for French culture"],
            translation_notes="High quality translation"
        )
        
        assert result.request_id == "test_request_123"
        assert result.translated_content == "Contenu traduit"
        assert result.source_language == SupportedLanguage.ENGLISH
        assert result.target_language == SupportedLanguage.FRENCH
        assert result.content_type == ContentType.FAQ
        assert result.confidence_score == 0.85
        assert len(result.cultural_adaptations) == 1
        assert result.translation_notes == "High quality translation"
        assert not result.cached  # Default False
        assert result.created_at  # Should be auto-generated
    
    def test_cultural_adaptation_creation(self):
        """Test cultural adaptation model creation"""
        adaptation = CulturalAdaptation(
            source_content="Original content",
            target_language=SupportedLanguage.JAPANESE,
            cultural_context=CulturalContext.EAST_ASIAN,
            adaptations=[
                {
                    "type": "communication_style",
                    "original": "You should",
                    "adapted": "It would be respectful if you could",
                    "reasoning": "More polite form preferred in Japanese culture"
                }
            ],
            reasoning="Adapted for Japanese politeness culture",
            confidence_score=0.9
        )
        
        assert adaptation.source_content == "Original content"
        assert adaptation.target_language == SupportedLanguage.JAPANESE
        assert adaptation.cultural_context == CulturalContext.EAST_ASIAN
        assert len(adaptation.adaptations) == 1
        assert adaptation.adaptations[0]["type"] == "communication_style"
        assert adaptation.reasoning == "Adapted for Japanese politeness culture"
        assert adaptation.confidence_score == 0.9
        assert adaptation.adaptation_id  # Should be auto-generated
    
    def test_translation_cache_creation(self):
        """Test translation cache model creation"""
        cache = TranslationCache(
            cache_key="test_cache_key",
            content_hash="abc123",
            source_language=SupportedLanguage.ENGLISH,
            target_language=SupportedLanguage.GERMAN,
            content_type=ContentType.NOTIFICATION,
            translated_content="Übersetzte Inhalte",
            cultural_adaptations=["German adaptation"],
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24)
        )
        
        assert cache.cache_key == "test_cache_key"
        assert cache.content_hash == "abc123"
        assert cache.source_language == SupportedLanguage.ENGLISH
        assert cache.target_language == SupportedLanguage.GERMAN
        assert cache.content_type == ContentType.NOTIFICATION
        assert cache.translated_content == "Übersetzte Inhalte"
        assert len(cache.cultural_adaptations) == 1
        assert cache.access_count == 0  # Default
        assert cache.last_accessed  # Should be auto-generated
        assert cache.expires_at > datetime.now(timezone.utc)
    
    def test_supported_language_enum(self):
        """Test supported language enum"""
        # Test that all major languages are supported
        assert SupportedLanguage.ENGLISH == "en"
        assert SupportedLanguage.SPANISH == "es"
        assert SupportedLanguage.FRENCH == "fr"
        assert SupportedLanguage.CHINESE_SIMPLIFIED == "zh-cn"
        assert SupportedLanguage.CHINESE_TRADITIONAL == "zh-tw"
        assert SupportedLanguage.ARABIC == "ar"
        assert SupportedLanguage.HINDI == "hi"
        
        # Test that we have a good variety of languages
        all_languages = list(SupportedLanguage)
        assert len(all_languages) >= 15  # Should support at least 15 languages
    
    def test_content_type_enum(self):
        """Test content type enum"""
        # Test all content types
        assert ContentType.PROGRESS_REPORT == "progress_report"
        assert ContentType.GUIDANCE == "guidance"
        assert ContentType.FAQ == "faq"
        assert ContentType.NOTIFICATION == "notification"
        assert ContentType.UI_TEXT == "ui_text"
        assert ContentType.CURRICULUM_EXPLANATION == "curriculum_explanation"
        assert ContentType.ACHIEVEMENT == "achievement"
        assert ContentType.RECOMMENDATION == "recommendation"
    
    def test_cultural_context_enum(self):
        """Test cultural context enum"""
        # Test all cultural contexts
        assert CulturalContext.WESTERN == "western"
        assert CulturalContext.EAST_ASIAN == "east_asian"
        assert CulturalContext.MIDDLE_EASTERN == "middle_eastern"
        assert CulturalContext.SOUTH_ASIAN == "south_asian"
        assert CulturalContext.LATIN_AMERICAN == "latin_american"
        assert CulturalContext.AFRICAN == "african"
        assert CulturalContext.NORDIC == "nordic"


if __name__ == "__main__":
    pytest.main([__file__])
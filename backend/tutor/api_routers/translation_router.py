"""
Translation API Router - Multilingual support for parents
Task 10.1 implementation - Requirements: 6.2, 6.5
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

from services.supabase import DBConnection
from utils.auth_utils import get_current_user_id_from_jwt
from utils.logger import logger
from ..services.translation_service import (
    TranslationService, SupportedLanguage, ContentType,
    TranslationRequest, TranslationResult
)

router = APIRouter(prefix="/translation", tags=["Translation"])

# Pydantic models for API requests/responses
class TranslateContentRequest(BaseModel):
    """Request model for content translation"""
    content: str = Field(min_length=1, max_length=5000, description="Content to translate")
    target_language: SupportedLanguage = Field(description="Target language")
    content_type: ContentType = Field(description="Type of content")
    child_age: Optional[int] = Field(None, ge=5, le=12, description="Child's age for context")

# Dependency to get initialized services
async def get_translation_service() -> TranslationService:
    """Get initialized translation service"""
    from ..api import db
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return TranslationService(db)

# API Endpoints
@router.post("/translate", response_model=TranslationResult)
async def translate_content(
    request: TranslateContentRequest,
    user_id: str = Depends(get_current_user_id_from_jwt),
    translation_service: TranslationService = Depends(get_translation_service)
):
    """
    Translate content with cultural adaptation
    Requirement 6.2: Offer translations and multilingual support for parent interfaces
    """
    try:
        translation_request = TranslationRequest(
            content=request.content,
            target_language=request.target_language,
            content_type=request.content_type,
            child_age=request.child_age
        )
        
        result = await translation_service.translate_content(translation_request)
        return result
        
    except Exception as e:
        logger.error(f"Error translating content for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to translate content")

@router.get("/ui/{language}", response_model=Dict[str, str])
async def get_ui_translations(
    language: SupportedLanguage,
    translation_service: TranslationService = Depends(get_translation_service)
):
    """Get UI translations for a specific language"""
    try:
        translations = await translation_service.get_ui_translations(language)
        return translations
        
    except Exception as e:
        logger.error(f"Error getting UI translations for {language}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get UI translations")

@router.get("/health")
async def translation_health_check():
    """Health check endpoint for translation service"""
    return {
        "status": "ok",
        "service": "translation",
        "timestamp": "datetime.now(timezone.utc).isoformat()",
        "capabilities": ["content_translation", "cultural_adaptation", "ui_translation"]
    }
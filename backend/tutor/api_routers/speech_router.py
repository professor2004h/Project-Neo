"""
Speech API Router - Voice and multimodal interaction
Task 10.1 implementation - Requirements: 7.1, 7.2, 7.5
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from services.supabase import DBConnection
from utils.auth_utils import get_current_user_id_from_jwt
from utils.logger import logger
from ..services.speech_service import SpeechService

router = APIRouter(prefix="/speech", tags=["Speech"])

# Pydantic models for API requests/responses
class SpeechRecognitionResponse(BaseModel):
    """Response model for speech recognition"""
    text: str = Field(description="Recognized text")
    confidence: float = Field(description="Recognition confidence")
    language: str = Field(description="Detected language")

class TextToSpeechRequest(BaseModel):
    """Request model for text-to-speech"""
    text: str = Field(min_length=1, max_length=1000, description="Text to synthesize")
    voice: Optional[str] = Field(None, description="Voice preference")
    speed: Optional[float] = Field(1.0, ge=0.5, le=2.0, description="Speech speed")

# Dependency to get initialized services
async def get_speech_service() -> SpeechService:
    """Get initialized speech service"""
    from ..api import db
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return SpeechService(db)

# API Endpoints
@router.post("/recognize", response_model=SpeechRecognitionResponse)
async def recognize_speech(
    audio_file: UploadFile = File(...),
    user_id: str = Depends(get_current_user_id_from_jwt),
    speech_service: SpeechService = Depends(get_speech_service)
):
    """
    Recognize speech from audio file
    Requirement 7.1: Accurately recognize speech and provide appropriate responses
    """
    try:
        result = await speech_service.recognize_speech(audio_file, user_id)
        return SpeechRecognitionResponse(
            text=result.get("text", ""),
            confidence=result.get("confidence", 0.0),
            language=result.get("language", "en")
        )
        
    except Exception as e:
        logger.error(f"Error recognizing speech for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to recognize speech")

@router.post("/synthesize")
async def synthesize_speech(
    request: TextToSpeechRequest,
    user_id: str = Depends(get_current_user_id_from_jwt),
    speech_service: SpeechService = Depends(get_speech_service)
):
    """
    Convert text to speech
    Requirement 7.2: Provide feedback on speech clarity and accuracy
    """
    try:
        audio_data = await speech_service.synthesize_speech(
            request.text, request.voice, request.speed, user_id
        )
        return {"audio_url": audio_data.get("audio_url")}
        
    except Exception as e:
        logger.error(f"Error synthesizing speech for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to synthesize speech")

@router.get("/health")
async def speech_health_check():
    """Health check endpoint for speech service"""
    return {
        "status": "ok",
        "service": "speech",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "capabilities": ["speech_recognition", "text_to_speech", "pronunciation_feedback"]
    }
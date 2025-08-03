"""
Gamification API Router - Achievement and reward system
Task 10.1 implementation - Requirements: 5.1, 5.2, 5.3
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from services.supabase import DBConnection
from utils.auth_utils import get_current_user_id_from_jwt
from utils.logger import logger
from ..services.gamification_service import GamificationService
from ..services.adaptive_gamification_service import AdaptiveGamificationService

router = APIRouter(prefix="/gamification", tags=["Gamification"])

# Pydantic models for API requests/responses
class AchievementRequest(BaseModel):
    """Request model for tracking achievements"""
    achievement_type: str = Field(description="Type of achievement")
    activity_data: Dict[str, Any] = Field(description="Activity data")

# Dependency to get initialized services
async def get_gamification_service() -> GamificationService:
    """Get initialized gamification service"""
    from ..api import db
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return GamificationService(db)

# API Endpoints
@router.post("/achievements")
async def track_achievement(
    request: AchievementRequest,
    user_id: str = Depends(get_current_user_id_from_jwt),
    gamification_service: GamificationService = Depends(get_gamification_service)
):
    """
    Track achievement progress
    Requirement 5.1: Award points, badges, and achievements
    """
    try:
        result = await gamification_service.track_achievement(
            user_id, request.achievement_type, request.activity_data
        )
        return result
        
    except Exception as e:
        logger.error(f"Error tracking achievement for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to track achievement")

@router.get("/profile/{child_id}")
async def get_gamification_profile(
    child_id: str,
    user_id: str = Depends(get_current_user_id_from_jwt),
    gamification_service: GamificationService = Depends(get_gamification_service)
):
    """Get gamification profile for a child"""
    try:
        profile = await gamification_service.get_gamification_profile(child_id)
        return profile
        
    except Exception as e:
        logger.error(f"Error getting gamification profile: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get gamification profile")

@router.get("/health")
async def gamification_health_check():
    """Health check endpoint for gamification service"""
    return {
        "status": "ok",
        "service": "gamification",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "capabilities": ["achievements", "rewards", "engagement_tracking"]
    }
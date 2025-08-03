from fastapi import APIRouter
from services.supabase import DBConnection
from utils.logger import logger

# Import all API routers
from .api_routers import (
    tutor_router,
    progress_router,
    content_router,
    sync_router,
    guidance_router,
    translation_router,
    gamification_router,
    speech_router,
    auth_router
)
from .api_routers.websocket_router import router as websocket_router

# Create main router
router = APIRouter()

# Global database connection
db = None

def initialize(database: DBConnection):
    """Initialize the tutor API with database connection"""
    global db
    db = database
    logger.info("Cambridge AI Tutor API initialized with comprehensive routers")

# Include all sub-routers
router.include_router(tutor_router, tags=["AI Tutor"])
router.include_router(progress_router, tags=["Progress Tracking"])
router.include_router(content_router, tags=["Content Management"])
router.include_router(sync_router, tags=["Synchronization"])
router.include_router(guidance_router, tags=["Parent Guidance"])
router.include_router(translation_router, tags=["Translation"])
router.include_router(gamification_router, tags=["Gamification"])
router.include_router(speech_router, tags=["Speech"])
router.include_router(auth_router, tags=["Authentication"])
router.include_router(websocket_router, tags=["WebSocket"])

@router.get("/health")
async def tutor_health_check():
    """Health check endpoint for Cambridge AI Tutor service"""
    return {
        "status": "ok",
        "service": "cambridge_ai_tutor",
        "version": "1.0.0",
        "components": {
            "ai_tutor": "active",
            "progress_tracking": "active",
            "content_management": "active",
            "synchronization": "active",
            "parent_guidance": "active",
            "translation": "active",
            "gamification": "active",
            "speech": "active",
            "authentication": "active",
            "websocket": "active"
        },
        "capabilities": [
            "personalized_ai_tutoring",
            "real_time_progress_tracking",
            "curriculum_aligned_content",
            "cross_platform_synchronization",
            "parent_guidance_system",
            "multilingual_support",
            "gamified_learning",
            "voice_interaction",
            "child_safety_controls",
            "real_time_websocket_communication"
        ],
        "timestamp": "2025-01-03T00:00:00Z"
    }
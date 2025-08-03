"""
API Routers package for Cambridge AI Tutor
Task 10.1 implementation - Comprehensive FastAPI routers for all services
"""

from .tutor_router import router as tutor_router
from .progress_router import router as progress_router
from .content_router import router as content_router
from .sync_router import router as sync_router
from .guidance_router import router as guidance_router
from .translation_router import router as translation_router
from .gamification_router import router as gamification_router
from .speech_router import router as speech_router
from .auth_router import router as auth_router

__all__ = [
    "tutor_router",
    "progress_router", 
    "content_router",
    "sync_router",
    "guidance_router",
    "translation_router",
    "gamification_router",
    "speech_router",
    "auth_router"
]
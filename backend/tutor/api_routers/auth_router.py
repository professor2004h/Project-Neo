"""
Authentication API Router - User authentication and authorization
Task 10.1 implementation - Requirements: 8.1, 8.2
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from services.supabase import DBConnection
from utils.auth_utils import get_current_user_id_from_jwt
from utils.logger import logger
from ..services.safety_service import SafetyService
from ..services.session_management_service import SessionManagementService

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Pydantic models for API requests/responses
class ParentalConsentRequest(BaseModel):
    """Request model for parental consent"""
    child_id: str = Field(description="Child's user ID")
    consent_type: str = Field(description="Type of consent")
    action: str = Field(description="Action requiring consent")

# Dependency to get initialized services
async def get_safety_service() -> SafetyService:
    """Get initialized safety service"""
    from ..api import db
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return SafetyService(db)

# API Endpoints
@router.post("/consent/verify")
async def verify_parental_consent(
    request: ParentalConsentRequest,
    user_id: str = Depends(get_current_user_id_from_jwt),
    safety_service: SafetyService = Depends(get_safety_service)
):
    """
    Verify parental consent for actions
    Requirement 8.1: Comply with COPPA and GDPR regulations
    """
    try:
        consent_verified = await safety_service.verify_parental_consent(
            user_id, request.child_id, request.consent_type
        )
        return {"consent_verified": consent_verified}
        
    except Exception as e:
        logger.error(f"Error verifying parental consent for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to verify parental consent")

@router.get("/dashboard/{parent_id}")
async def get_parental_dashboard(
    parent_id: str,
    user_id: str = Depends(get_current_user_id_from_jwt),
    safety_service: SafetyService = Depends(get_safety_service)
):
    """Get parental oversight dashboard"""
    try:
        dashboard = await safety_service.get_parental_oversight_dashboard(parent_id)
        return dashboard
        
    except Exception as e:
        logger.error(f"Error getting parental dashboard: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get parental dashboard")

@router.get("/health")
async def auth_health_check():
    """Health check endpoint for authentication service"""
    return {
        "status": "ok",
        "service": "authentication",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "capabilities": ["parental_consent", "child_safety", "session_management"]
    }
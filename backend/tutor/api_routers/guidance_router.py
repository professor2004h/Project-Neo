"""
Parent Guidance API Router - Parent support and FAQ system
Task 10.1 implementation - Requirements: 6.1, 6.3, 6.4
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid
from datetime import datetime, timezone

from services.supabase import DBConnection
from utils.auth_utils import get_current_user_id_from_jwt
from utils.logger import logger
from ..services.parent_guidance_service import (
    ParentGuidanceService, GuidanceCategory, GuidancePriority,
    FAQItem, GuidanceRecommendation, GuidanceSearchQuery
)
from ..models.user_models import Subject

router = APIRouter(prefix="/guidance", tags=["Parent Guidance"])

# Pydantic models for API requests/responses
class FAQSearchRequest(BaseModel):
    """Request model for FAQ search"""
    query: str = Field(min_length=1, max_length=200, description="Search query")
    category: Optional[GuidanceCategory] = Field(None, description="Category filter")
    child_age: Optional[int] = Field(None, ge=5, le=12, description="Child's age")
    subject: Optional[Subject] = Field(None, description="Subject filter")
    max_results: int = Field(default=10, ge=1, le=50, description="Maximum results")

class GuidanceRequest(BaseModel):
    """Request model for personalized guidance"""
    child_id: str = Field(description="Child's user ID")
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")

class CurriculumGuidanceRequest(BaseModel):
    """Request model for curriculum guidance"""
    subject: Subject = Field(description="Subject area")
    grade_level: int = Field(ge=1, le=12, description="Grade level")
    topic: Optional[str] = Field(None, description="Specific topic")

# Dependency to get initialized services
async def get_guidance_service() -> ParentGuidanceService:
    """Get initialized parent guidance service"""
    from ..api import db
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return ParentGuidanceService(db)

# API Endpoints
@router.post("/faq/search", response_model=List[FAQItem])
async def search_faq(
    request: FAQSearchRequest,
    user_id: str = Depends(get_current_user_id_from_jwt),
    guidance_service: ParentGuidanceService = Depends(get_guidance_service)
):
    """
    Search FAQ database with intelligent matching
    Requirement 6.4: Provide FAQs and guidance resources
    """
    try:
        logger.info(f"FAQ search by user {user_id}: {request.query}")
        
        search_query = GuidanceSearchQuery(
            query=request.query,
            category=request.category,
            child_age=request.child_age,
            subject=request.subject,
            max_results=request.max_results
        )
        
        results = await guidance_service.search_faq(search_query, user_id)
        
        logger.info(f"FAQ search completed for user {user_id}: {len(results)} results")
        return results
        
    except Exception as e:
        logger.error(f"Error searching FAQ for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to search FAQ")

@router.post("/personalized", response_model=List[GuidanceRecommendation])
async def get_personalized_guidance(
    request: GuidanceRequest,
    user_id: str = Depends(get_current_user_id_from_jwt),
    guidance_service: ParentGuidanceService = Depends(get_guidance_service)
):
    """
    Generate personalized guidance recommendations
    Requirement 6.1: Provide simplified explanations and teaching tips
    Requirement 6.3: Include specific suggestions for home support activities
    """
    try:
        logger.info(f"Generating personalized guidance for user {user_id}, child {request.child_id}")
        
        recommendations = await guidance_service.generate_personalized_guidance(
            user_id, request.child_id, request.context
        )
        
        logger.info(f"Personalized guidance generated for user {user_id}")
        return recommendations
        
    except Exception as e:
        logger.error(f"Error generating personalized guidance for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate personalized guidance")

@router.post("/curriculum", response_model=Dict[str, Any])
async def get_curriculum_guidance(
    request: CurriculumGuidanceRequest,
    user_id: str = Depends(get_current_user_id_from_jwt),
    guidance_service: ParentGuidanceService = Depends(get_guidance_service)
):
    """
    Get curriculum-specific guidance for parents
    """
    try:
        logger.info(f"Getting curriculum guidance for user {user_id}")
        
        guidance = await guidance_service.get_curriculum_guidance(
            user_id, request.subject, request.grade_level, request.topic
        )
        
        logger.info(f"Curriculum guidance provided for user {user_id}")
        return guidance
        
    except Exception as e:
        logger.error(f"Error getting curriculum guidance for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get curriculum guidance")

@router.get("/faq/popular", response_model=List[FAQItem])
async def get_popular_faqs(
    category: Optional[GuidanceCategory] = Query(None, description="Category filter"),
    limit: int = Query(default=10, ge=1, le=20, description="Number of results"),
    guidance_service: ParentGuidanceService = Depends(get_guidance_service)
):
    """Get most popular FAQ items"""
    try:
        results = await guidance_service.get_popular_faqs(category, limit)
        return results
    except Exception as e:
        logger.error(f"Error getting popular FAQs: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get popular FAQs")

@router.get("/health")
async def guidance_health_check():
    """Health check endpoint for parent guidance service"""
    return {
        "status": "ok",
        "service": "parent_guidance",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "capabilities": ["faq_search", "personalized_guidance", "curriculum_guidance"]
    }
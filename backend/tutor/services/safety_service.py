"""
Child safety and parental controls service for the Cambridge AI Tutor
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import uuid

from ..models.user_models import (
    ChildProfile, ChildProfileCreate, ParentProfile, UserSession,
    SafetySettings, UserRole
)
from ..models.safety_models import (
    ConsentType, SafetyViolationType, ParentalConsentRecord, SafetyViolationRecord, SessionTimeLimit
)
from ..repositories.user_repository import (
    ChildProfileRepository, ParentProfileRepository, UserSessionRepository
)
from services.supabase import DBConnection
import logging

logger = logging.getLogger(__name__)





class SafetyService:
    """Service for managing child safety and parental controls"""
    
    def __init__(self, db: DBConnection):
        self.db = db
        self.child_repo = ChildProfileRepository(db)
        self.parent_repo = ParentProfileRepository(db)
        self.session_repo = UserSessionRepository(db)
        # Import repositories here to avoid circular imports
        from ..repositories.safety_repository import (
            ParentalConsentRepository, SafetyViolationRepository, 
            SessionTimeTrackingRepository, DailyUsageSummaryRepository
        )
        self.consent_repo = ParentalConsentRepository(db)
        self.violation_repo = SafetyViolationRepository(db)
        self.time_tracking_repo = SessionTimeTrackingRepository(db)
        self.usage_summary_repo = DailyUsageSummaryRepository(db)
    
    async def verify_parental_consent(
        self,
        parent_id: str,
        child_id: str,
        consent_type: ConsentType,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        """
        Verify and record parental consent for specific actions
        
        Args:
            parent_id: ID of the parent giving consent
            child_id: ID of the child the consent is for
            consent_type: Type of consent being requested
            ip_address: IP address of the consent request
            user_agent: User agent of the consent request
            
        Returns:
            bool: True if consent is granted and valid
        """
        try:
            # Verify parent-child relationship
            child = await self.child_repo.get_child_profile_by_id(child_id)
            if not child or child.parent_id != parent_id:
                logger.warning(f"Invalid parent-child relationship: {parent_id} -> {child_id}")
                return False
            
            # Check for existing valid consent
            existing_consent = await self._get_existing_consent(parent_id, child_id, consent_type)
            if existing_consent and self._is_consent_valid(existing_consent):
                return True
            
            # Record new consent (in a real implementation, this would be granted through UI)
            consent_record = ParentalConsentRecord(
                parent_id=parent_id,
                child_id=child_id,
                consent_type=consent_type,
                granted=True,  # Assuming consent is granted for this implementation
                ip_address=ip_address,
                user_agent=user_agent,
                expires_at=datetime.now(timezone.utc) + timedelta(days=365)  # 1 year expiry
            )
            
            await self._store_consent_record(consent_record)
            logger.info(f"Parental consent granted: {parent_id} -> {child_id} for {consent_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error verifying parental consent: {str(e)}")
            return False
    
    async def create_child_profile_with_safety(
        self,
        parent_id: str,
        child_data: ChildProfileCreate,
        safety_settings: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Optional[ChildProfile]:
        """
        Create a child profile with safety settings and age verification
        
        Args:
            parent_id: ID of the parent creating the profile
            child_data: Child profile data
            safety_settings: Custom safety settings
            ip_address: IP address of the request
            user_agent: User agent of the request
            
        Returns:
            ChildProfile: Created child profile or None if failed
        """
        try:
            # Verify parental consent for profile creation
            consent_granted = await self.verify_parental_consent(
                parent_id,
                "temp_child_id",  # Temporary ID for consent verification
                ConsentType.PROFILE_CREATION,
                ip_address,
                user_agent
            )
            
            if not consent_granted:
                logger.warning(f"Parental consent not granted for profile creation: {parent_id}")
                return None
            
            # Age verification - ensure child is within primary school age range
            if child_data.age < 5 or child_data.age > 12:
                logger.warning(f"Invalid age for child profile: {child_data.age}")
                return None
            
            # Set default safety settings based on age
            default_safety_settings = self._get_default_safety_settings(child_data.age)
            
            # Merge with custom safety settings if provided
            if safety_settings:
                default_safety_settings.update(safety_settings)
            
            # Update child data with safety settings
            child_data.safety_settings = default_safety_settings
            
            # Create the child profile
            child_profile = await self.child_repo.create_child_profile(child_data)
            
            # Add child to parent's children list
            await self.parent_repo.add_child_to_parent(parent_id, child_profile.child_id)
            
            # Record consent for data collection
            await self.verify_parental_consent(
                parent_id,
                child_profile.child_id,
                ConsentType.DATA_COLLECTION,
                ip_address,
                user_agent
            )
            
            logger.info(f"Child profile created with safety settings: {child_profile.child_id}")
            return child_profile
            
        except Exception as e:
            logger.error(f"Error creating child profile with safety: {str(e)}")
            return None
    
    async def validate_session_safety(
        self,
        child_id: str,
        device_id: str,
        device_type: str
    ) -> Dict[str, Any]:
        """
        Validate if a child can start a new session based on safety rules
        
        Args:
            child_id: ID of the child
            device_id: Device identifier
            device_type: Type of device (web, mobile, extension)
            
        Returns:
            Dict containing validation result and details
        """
        try:
            child = await self.child_repo.get_child_profile_by_id(child_id)
            if not child:
                return {"allowed": False, "reason": "Child profile not found"}
            
            safety_settings = child.safety_settings
            
            # Check time limits
            time_check = await self._check_time_limits(child_id, safety_settings)
            if not time_check["allowed"]:
                return time_check
            
            # Check quiet hours
            quiet_hours_check = self._check_quiet_hours(safety_settings)
            if not quiet_hours_check["allowed"]:
                return quiet_hours_check
            
            # Check device restrictions
            device_check = self._check_device_restrictions(device_type, safety_settings)
            if not device_check["allowed"]:
                return device_check
            
            # Check parental oversight requirements
            oversight_check = await self._check_parental_oversight(child_id, safety_settings)
            if not oversight_check["allowed"]:
                return oversight_check
            
            return {"allowed": True, "reason": "Session validation passed"}
            
        except Exception as e:
            logger.error(f"Error validating session safety: {str(e)}")
            return {"allowed": False, "reason": "Validation error"}
    
    async def monitor_session_activity(
        self,
        session_id: str,
        activity_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Monitor ongoing session for safety violations
        
        Args:
            session_id: ID of the session to monitor
            activity_data: Activity data to analyze
            
        Returns:
            Dict containing monitoring results and any violations
        """
        try:
            session = await self.session_repo.get_session_by_id(session_id)
            if not session:
                return {"status": "error", "message": "Session not found"}
            
            child = await self.child_repo.get_child_profile_by_id(session.user_id)
            if not child:
                return {"status": "error", "message": "Child profile not found"}
            
            violations = []
            
            # Check session duration
            session_duration = datetime.now(timezone.utc) - session.started_at
            max_duration = timedelta(minutes=child.safety_settings.get("max_consecutive_minutes", 30))
            
            if session_duration > max_duration:
                violation = SafetyViolationRecord(
                    child_id=child.child_id,
                    violation_type=SafetyViolationType.EXCESSIVE_SESSION_TIME,
                    description=f"Session exceeded maximum duration: {session_duration.total_seconds() / 60:.1f} minutes",
                    severity="medium"
                )
                violations.append(violation)
            
            # Check content appropriateness (placeholder for content analysis)
            if activity_data.get("content_flagged"):
                violation = SafetyViolationRecord(
                    child_id=child.child_id,
                    violation_type=SafetyViolationType.INAPPROPRIATE_CONTENT,
                    description="Inappropriate content detected in session",
                    severity="high"
                )
                violations.append(violation)
            
            # Store violations and notify parent if needed
            for violation in violations:
                await self._store_safety_violation(violation)
                if violation.severity in ["high", "critical"]:
                    await self._notify_parent_of_violation(child.parent_id, violation)
            
            return {
                "status": "monitored",
                "violations_count": len(violations),
                "violations": [v.dict() for v in violations]
            }
            
        except Exception as e:
            logger.error(f"Error monitoring session activity: {str(e)}")
            return {"status": "error", "message": "Monitoring error"}
    
    async def get_parental_oversight_dashboard(
        self,
        parent_id: str
    ) -> Dict[str, Any]:
        """
        Get parental oversight dashboard with child activity and safety information
        
        Args:
            parent_id: ID of the parent
            
        Returns:
            Dict containing dashboard data
        """
        try:
            parent = await self.parent_repo.get_parent_profile_by_user_id(parent_id)
            if not parent:
                return {"error": "Parent profile not found"}
            
            dashboard_data = {
                "parent_id": parent_id,
                "children": [],
                "recent_violations": [],
                "consent_status": {}
            }
            
            # Get data for each child
            for child_id in parent.children_ids:
                child = await self.child_repo.get_child_profile_by_id(child_id)
                if not child:
                    continue
                
                # Get active sessions
                active_sessions = await self.session_repo.get_active_sessions_by_user_id(child_id)
                
                # Get recent violations (last 7 days)
                recent_violations = await self._get_recent_violations(child_id, days=7)
                
                # Calculate daily usage
                daily_usage = await self._calculate_daily_usage(child_id)
                
                child_data = {
                    "child_id": child_id,
                    "name": child.name,
                    "age": child.age,
                    "active_sessions": len(active_sessions),
                    "daily_usage_minutes": daily_usage,
                    "recent_violations": len(recent_violations),
                    "safety_settings": child.safety_settings
                }
                
                dashboard_data["children"].append(child_data)
                dashboard_data["recent_violations"].extend(recent_violations)
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting parental oversight dashboard: {str(e)}")
            return {"error": "Dashboard error"}
    
    def _get_default_safety_settings(self, age: int) -> Dict[str, Any]:
        """Get default safety settings based on child's age"""
        if age <= 7:
            return {
                "content_filtering_level": "strict",
                "parental_oversight_required": True,
                "session_time_limits": {
                    "daily_limit_minutes": 30,
                    "weekly_limit_minutes": 150,
                    "max_consecutive_minutes": 15
                },
                "allowed_subjects": ["mathematics"],
                "blocked_topics": ["advanced_topics", "complex_science"],
                "data_sharing_consent": False,
                "voice_interaction_enabled": False,
                "quiet_hours": {"start": "19:00", "end": "08:00"}
            }
        elif age <= 10:
            return {
                "content_filtering_level": "moderate",
                "parental_oversight_required": True,
                "session_time_limits": {
                    "daily_limit_minutes": 45,
                    "weekly_limit_minutes": 225,
                    "max_consecutive_minutes": 25
                },
                "allowed_subjects": ["mathematics", "esl"],
                "blocked_topics": ["advanced_science"],
                "data_sharing_consent": False,
                "voice_interaction_enabled": True,
                "quiet_hours": {"start": "20:00", "end": "07:00"}
            }
        else:  # age > 10
            return {
                "content_filtering_level": "moderate",
                "parental_oversight_required": False,
                "session_time_limits": {
                    "daily_limit_minutes": 60,
                    "weekly_limit_minutes": 300,
                    "max_consecutive_minutes": 30
                },
                "allowed_subjects": ["mathematics", "esl", "science"],
                "blocked_topics": [],
                "data_sharing_consent": False,
                "voice_interaction_enabled": True,
                "quiet_hours": {"start": "21:00", "end": "07:00"}
            }
    
    async def _check_time_limits(self, child_id: str, safety_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Check if child has exceeded time limits"""
        try:
            time_limits = safety_settings.get("session_time_limits", {})
            daily_limit = time_limits.get("daily_limit_minutes", 60)
            
            # Calculate today's usage
            daily_usage = await self._calculate_daily_usage(child_id)
            
            if daily_usage >= daily_limit:
                return {
                    "allowed": False,
                    "reason": f"Daily time limit exceeded ({daily_usage}/{daily_limit} minutes)"
                }
            
            return {"allowed": True}
            
        except Exception as e:
            logger.error(f"Error checking time limits: {str(e)}")
            return {"allowed": False, "reason": "Time limit check error"}
    
    def _check_quiet_hours(self, safety_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Check if current time is within quiet hours"""
        try:
            quiet_hours = safety_settings.get("quiet_hours", {})
            if not quiet_hours:
                return {"allowed": True}
            
            now = datetime.now(timezone.utc).time()
            start_time = datetime.strptime(quiet_hours.get("start", "22:00"), "%H:%M").time()
            end_time = datetime.strptime(quiet_hours.get("end", "06:00"), "%H:%M").time()
            
            # Handle overnight quiet hours
            if start_time > end_time:
                if now >= start_time or now <= end_time:
                    return {"allowed": False, "reason": "Current time is within quiet hours"}
            else:
                if start_time <= now <= end_time:
                    return {"allowed": False, "reason": "Current time is within quiet hours"}
            
            return {"allowed": True}
            
        except Exception as e:
            logger.error(f"Error checking quiet hours: {str(e)}")
            return {"allowed": True}  # Allow on error
    
    def _check_device_restrictions(self, device_type: str, safety_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Check if device type is allowed"""
        allowed_devices = safety_settings.get("allowed_devices", ["web", "mobile", "extension"])
        
        if device_type not in allowed_devices:
            return {"allowed": False, "reason": f"Device type '{device_type}' not allowed"}
        
        return {"allowed": True}
    
    async def _check_parental_oversight(self, child_id: str, safety_settings: Dict[str, Any]) -> Dict[str, Any]:
        """Check if parental oversight is required and available"""
        if not safety_settings.get("parental_oversight_required", False):
            return {"allowed": True}
        
        # In a real implementation, this would check if parent is actively monitoring
        # For now, we'll assume oversight is available during reasonable hours
        now = datetime.now(timezone.utc).time()
        oversight_hours_start = datetime.strptime("08:00", "%H:%M").time()
        oversight_hours_end = datetime.strptime("20:00", "%H:%M").time()
        
        if oversight_hours_start <= now <= oversight_hours_end:
            return {"allowed": True}
        else:
            return {"allowed": False, "reason": "Parental oversight required but not available"}
    
    async def _calculate_daily_usage(self, child_id: str) -> int:
        """Calculate child's usage for today in minutes"""
        try:
            return await self.time_tracking_repo.get_daily_usage(child_id)
            
        except Exception as e:
            logger.error(f"Error calculating daily usage: {str(e)}")
            return 0
    
    async def _get_existing_consent(
        self,
        parent_id: str,
        child_id: str,
        consent_type: ConsentType
    ) -> Optional[ParentalConsentRecord]:
        """Get existing consent record"""
        try:
            return await self.consent_repo.get_consent_record(parent_id, child_id, consent_type)
        except Exception as e:
            logger.error(f"Error getting existing consent: {str(e)}")
            return None
    
    def _is_consent_valid(self, consent: ParentalConsentRecord) -> bool:
        """Check if consent record is still valid"""
        if not consent.granted:
            return False
        
        if consent.expires_at and datetime.now(timezone.utc) > consent.expires_at:
            return False
        
        return True
    
    async def _store_consent_record(self, consent: ParentalConsentRecord) -> None:
        """Store consent record in database"""
        try:
            await self.consent_repo.create_consent_record(consent)
            logger.info(f"Stored consent record: {consent.consent_id}")
        except Exception as e:
            logger.error(f"Error storing consent record: {str(e)}")
            raise
    
    async def _store_safety_violation(self, violation: SafetyViolationRecord) -> None:
        """Store safety violation record in database"""
        try:
            await self.violation_repo.create_violation_record(violation)
            logger.warning(f"Safety violation recorded: {violation.violation_id} - {violation.description}")
        except Exception as e:
            logger.error(f"Error storing safety violation: {str(e)}")
            raise
    
    async def _notify_parent_of_violation(self, parent_id: str, violation: SafetyViolationRecord) -> None:
        """Notify parent of safety violation"""
        # This would send notification to parent (email, push notification, etc.)
        # For now, just log it
        logger.info(f"Notifying parent {parent_id} of violation: {violation.violation_id}")
    
    async def _get_recent_violations(self, child_id: str, days: int = 7) -> List[SafetyViolationRecord]:
        """Get recent safety violations for a child"""
        try:
            return await self.violation_repo.get_violations_for_child(child_id, days=days)
        except Exception as e:
            logger.error(f"Error getting recent violations: {str(e)}")
            return []
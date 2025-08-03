"""
Session management service with multi-device support and parental oversight
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, timedelta
from enum import Enum

from ..models.user_models import UserSession, ChildProfile
from ..repositories.user_repository import ChildProfileRepository, UserSessionRepository
from ..repositories.safety_repository import SessionTimeTrackingRepository
from ..services.safety_service import SafetyService
from services.supabase import DBConnection
import logging

logger = logging.getLogger(__name__)


class SessionStatus(str, Enum):
    """Session status enumeration"""
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
    SUSPENDED = "suspended"  # Suspended due to safety violation


class SessionManagementService:
    """Service for managing user sessions with safety controls"""
    
    def __init__(self, db: DBConnection):
        self.db = db
        self.child_repo = ChildProfileRepository(db)
        self.session_repo = UserSessionRepository(db)
        self.time_tracking_repo = SessionTimeTrackingRepository(db)
        self.safety_service = SafetyService(db)
    
    async def start_session(
        self,
        child_id: str,
        device_id: str,
        device_type: str,
        parent_supervision: bool = False
    ) -> Dict[str, Any]:
        """
        Start a new session for a child with safety validation
        
        Args:
            child_id: ID of the child starting the session
            device_id: Unique device identifier
            device_type: Type of device (web, mobile, extension)
            parent_supervision: Whether parent is actively supervising
            
        Returns:
            Dict containing session start result and session info
        """
        try:
            # Validate session safety
            safety_check = await self.safety_service.validate_session_safety(
                child_id, device_id, device_type
            )
            
            if not safety_check["allowed"]:
                return {
                    "success": False,
                    "reason": safety_check["reason"],
                    "session_id": None
                }
            
            # Check for existing active sessions on this device
            existing_sessions = await self.session_repo.get_active_sessions_by_user_id(child_id)
            device_sessions = [s for s in existing_sessions if s.device_id == device_id]
            
            if device_sessions:
                # Resume existing session
                session = device_sessions[0]
                await self.session_repo.update_session_activity(session.session_id)
                
                return {
                    "success": True,
                    "reason": "Session resumed",
                    "session_id": session.session_id,
                    "resumed": True
                }
            
            # Create new session
            session_data = UserSession(
                user_id=child_id,
                device_id=device_id,
                device_type=device_type,
                started_at=datetime.now(timezone.utc),
                last_activity=datetime.now(timezone.utc),
                is_active=True,
                sync_status="synced"
            )
            
            session = await self.session_repo.create_session(session_data)
            
            # Log session start for parental oversight
            await self._log_session_event(
                session.session_id,
                "session_started",
                {"parent_supervision": parent_supervision}
            )
            
            logger.info(f"Session started: {session.session_id} for child {child_id}")
            
            return {
                "success": True,
                "reason": "Session started successfully",
                "session_id": session.session_id,
                "resumed": False
            }
            
        except Exception as e:
            logger.error(f"Error starting session: {str(e)}")
            return {
                "success": False,
                "reason": "Session start error",
                "session_id": None
            }
    
    async def end_session(
        self,
        session_id: str,
        reason: str = "user_ended"
    ) -> Dict[str, Any]:
        """
        End a session and record usage time
        
        Args:
            session_id: ID of the session to end
            reason: Reason for ending session
            
        Returns:
            Dict containing session end result and usage info
        """
        try:
            session = await self.session_repo.get_session_by_id(session_id)
            if not session:
                return {"success": False, "reason": "Session not found"}
            
            if not session.is_active:
                return {"success": False, "reason": "Session already ended"}
            
            # Calculate session duration
            end_time = datetime.now(timezone.utc)
            duration = end_time - session.started_at
            duration_minutes = int(duration.total_seconds() / 60)
            
            # Deactivate session
            await self.session_repo.deactivate_session(session_id)
            
            # Record session time for tracking
            await self.time_tracking_repo.record_session_time(
                session.user_id,
                session_id,
                duration_minutes
            )
            
            # Log session end for parental oversight
            await self._log_session_event(
                session_id,
                "session_ended",
                {
                    "reason": reason,
                    "duration_minutes": duration_minutes
                }
            )
            
            logger.info(f"Session ended: {session_id}, duration: {duration_minutes} minutes")
            
            return {
                "success": True,
                "reason": "Session ended successfully",
                "duration_minutes": duration_minutes,
                "total_daily_usage": await self.time_tracking_repo.get_daily_usage(session.user_id)
            }
            
        except Exception as e:
            logger.error(f"Error ending session: {str(e)}")
            return {"success": False, "reason": "Session end error"}
    
    async def pause_session(
        self,
        session_id: str,
        reason: str = "user_paused"
    ) -> Dict[str, Any]:
        """
        Pause a session temporarily
        
        Args:
            session_id: ID of the session to pause
            reason: Reason for pausing
            
        Returns:
            Dict containing pause result
        """
        try:
            session = await self.session_repo.get_session_by_id(session_id)
            if not session:
                return {"success": False, "reason": "Session not found"}
            
            # Update sync status to indicate paused state
            await self.session_repo.update_sync_status(session_id, "pending")
            
            # Log pause event
            await self._log_session_event(
                session_id,
                "session_paused",
                {"reason": reason}
            )
            
            return {"success": True, "reason": "Session paused"}
            
        except Exception as e:
            logger.error(f"Error pausing session: {str(e)}")
            return {"success": False, "reason": "Session pause error"}
    
    async def resume_session(
        self,
        session_id: str
    ) -> Dict[str, Any]:
        """
        Resume a paused session
        
        Args:
            session_id: ID of the session to resume
            
        Returns:
            Dict containing resume result
        """
        try:
            session = await self.session_repo.get_session_by_id(session_id)
            if not session:
                return {"success": False, "reason": "Session not found"}
            
            # Validate session can be resumed (safety checks)
            safety_check = await self.safety_service.validate_session_safety(
                session.user_id, session.device_id, session.device_type
            )
            
            if not safety_check["allowed"]:
                return {
                    "success": False,
                    "reason": safety_check["reason"]
                }
            
            # Update session activity and sync status
            await self.session_repo.update_session_activity(session_id)
            await self.session_repo.update_sync_status(session_id, "synced")
            
            # Log resume event
            await self._log_session_event(
                session_id,
                "session_resumed",
                {}
            )
            
            return {"success": True, "reason": "Session resumed"}
            
        except Exception as e:
            logger.error(f"Error resuming session: {str(e)}")
            return {"success": False, "reason": "Session resume error"}
    
    async def suspend_session(
        self,
        session_id: str,
        reason: str,
        violation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Suspend a session due to safety violation
        
        Args:
            session_id: ID of the session to suspend
            reason: Reason for suspension
            violation_id: ID of the safety violation causing suspension
            
        Returns:
            Dict containing suspension result
        """
        try:
            session = await self.session_repo.get_session_by_id(session_id)
            if not session:
                return {"success": False, "reason": "Session not found"}
            
            # Deactivate session
            await self.session_repo.deactivate_session(session_id)
            
            # Log suspension event
            await self._log_session_event(
                session_id,
                "session_suspended",
                {
                    "reason": reason,
                    "violation_id": violation_id
                }
            )
            
            # Notify parent of suspension
            child = await self.child_repo.get_child_profile_by_id(session.user_id)
            if child:
                await self._notify_parent_of_suspension(child.parent_id, session_id, reason)
            
            logger.warning(f"Session suspended: {session_id}, reason: {reason}")
            
            return {"success": True, "reason": "Session suspended due to safety violation"}
            
        except Exception as e:
            logger.error(f"Error suspending session: {str(e)}")
            return {"success": False, "reason": "Session suspension error"}
    
    async def get_active_sessions_for_child(self, child_id: str) -> List[Dict[str, Any]]:
        """
        Get all active sessions for a child
        
        Args:
            child_id: ID of the child
            
        Returns:
            List of active session information
        """
        try:
            sessions = await self.session_repo.get_active_sessions_by_user_id(child_id)
            
            session_info = []
            for session in sessions:
                # Calculate current session duration
                duration = datetime.now(timezone.utc) - session.started_at
                duration_minutes = int(duration.total_seconds() / 60)
                
                session_info.append({
                    "session_id": session.session_id,
                    "device_id": session.device_id,
                    "device_type": session.device_type,
                    "started_at": session.started_at.isoformat(),
                    "duration_minutes": duration_minutes,
                    "sync_status": session.sync_status
                })
            
            return session_info
            
        except Exception as e:
            logger.error(f"Error getting active sessions: {str(e)}")
            return []
    
    async def sync_session_data(
        self,
        session_id: str,
        data_updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Sync session data across devices
        
        Args:
            session_id: ID of the session to sync
            data_updates: Data updates to sync
            
        Returns:
            Dict containing sync result
        """
        try:
            session = await self.session_repo.get_session_by_id(session_id)
            if not session:
                return {"success": False, "reason": "Session not found"}
            
            # Update session activity
            await self.session_repo.update_session_activity(session_id)
            
            # In a real implementation, this would sync data to other devices
            # For now, just update sync status
            await self.session_repo.update_sync_status(session_id, "synced")
            
            # Log sync event
            await self._log_session_event(
                session_id,
                "data_synced",
                {"updates_count": len(data_updates)}
            )
            
            return {"success": True, "reason": "Data synced successfully"}
            
        except Exception as e:
            logger.error(f"Error syncing session data: {str(e)}")
            return {"success": False, "reason": "Data sync error"}
    
    async def get_parental_oversight_info(self, parent_id: str) -> Dict[str, Any]:
        """
        Get parental oversight information for all children
        
        Args:
            parent_id: ID of the parent
            
        Returns:
            Dict containing oversight information
        """
        try:
            # Get parent's children
            from ..repositories.user_repository import ParentProfileRepository
            parent_repo = ParentProfileRepository(self.db)
            parent = await parent_repo.get_parent_profile_by_user_id(parent_id)
            
            if not parent:
                return {"error": "Parent profile not found"}
            
            oversight_info = {
                "parent_id": parent_id,
                "children_sessions": [],
                "total_active_sessions": 0
            }
            
            for child_id in parent.children_ids:
                child = await self.child_repo.get_child_profile_by_id(child_id)
                if not child:
                    continue
                
                active_sessions = await self.get_active_sessions_for_child(child_id)
                daily_usage = await self.time_tracking_repo.get_daily_usage(child_id)
                
                child_info = {
                    "child_id": child_id,
                    "name": child.name,
                    "active_sessions": active_sessions,
                    "daily_usage_minutes": daily_usage,
                    "safety_settings": child.safety_settings
                }
                
                oversight_info["children_sessions"].append(child_info)
                oversight_info["total_active_sessions"] += len(active_sessions)
            
            return oversight_info
            
        except Exception as e:
            logger.error(f"Error getting parental oversight info: {str(e)}")
            return {"error": "Oversight info error"}
    
    async def cleanup_inactive_sessions(self, hours_threshold: int = 24) -> int:
        """
        Clean up inactive sessions older than threshold
        
        Args:
            hours_threshold: Hours after which to consider session inactive
            
        Returns:
            Number of sessions cleaned up
        """
        try:
            return await self.session_repo.cleanup_inactive_sessions(hours_threshold)
            
        except Exception as e:
            logger.error(f"Error cleaning up inactive sessions: {str(e)}")
            return 0
    
    async def _log_session_event(
        self,
        session_id: str,
        event_type: str,
        metadata: Dict[str, Any]
    ) -> None:
        """Log session event for audit and parental oversight"""
        try:
            # In a real implementation, this would log to an audit table
            # For now, just log to application logs
            logger.info(f"Session event: {session_id} - {event_type} - {metadata}")
            
        except Exception as e:
            logger.error(f"Error logging session event: {str(e)}")
    
    async def _notify_parent_of_suspension(
        self,
        parent_id: str,
        session_id: str,
        reason: str
    ) -> None:
        """Notify parent of session suspension"""
        try:
            # In a real implementation, this would send notification to parent
            # For now, just log the notification
            logger.info(f"Notifying parent {parent_id} of session suspension: {session_id} - {reason}")
            
        except Exception as e:
            logger.error(f"Error notifying parent of suspension: {str(e)}")
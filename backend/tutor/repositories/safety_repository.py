"""
Repository for safety and parental consent operations
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone, date, timedelta

from .base_repository import BaseRepository
from ..models.safety_models import (
    ParentalConsentRecord, SafetyViolationRecord, ConsentType, SafetyViolationType
)
from services.supabase import DBConnection
import logging

logger = logging.getLogger(__name__)


class ParentalConsentRepository(BaseRepository):
    """Repository for parental consent operations"""
    
    def __init__(self, db: DBConnection):
        super().__init__(db, "tutor_parental_consent")
    
    async def create_consent_record(self, consent: ParentalConsentRecord) -> ParentalConsentRecord:
        """Create a new parental consent record"""
        try:
            data = {
                "parent_id": consent.parent_id,
                "child_id": consent.child_id,
                "consent_type": consent.consent_type.value,
                "granted": consent.granted,
                "granted_at": consent.granted_at.isoformat(),
                "expires_at": consent.expires_at.isoformat() if consent.expires_at else None,
                "ip_address": consent.ip_address,
                "user_agent": consent.user_agent,
                "metadata": consent.metadata
            }
            
            result = await self.create(data)
            return ParentalConsentRecord(**result)
            
        except Exception as e:
            logger.error(f"Error creating consent record: {str(e)}")
            raise
    
    async def get_consent_record(
        self,
        parent_id: str,
        child_id: str,
        consent_type: ConsentType
    ) -> Optional[ParentalConsentRecord]:
        """Get consent record for specific parent, child, and consent type"""
        try:
            client = await self.get_client()
            result = await client.table(self.table_name).select("*").eq(
                "parent_id", parent_id
            ).eq(
                "child_id", child_id
            ).eq(
                "consent_type", consent_type.value
            ).execute()
            
            if result.data:
                return ParentalConsentRecord(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting consent record: {str(e)}")
            raise
    
    async def get_all_consents_for_child(self, child_id: str) -> List[ParentalConsentRecord]:
        """Get all consent records for a child"""
        try:
            filters = {"child_id": child_id}
            results = await self.list_all(filters)
            return [ParentalConsentRecord(**result) for result in results]
            
        except Exception as e:
            logger.error(f"Error getting consents for child: {str(e)}")
            raise
    
    async def update_consent_record(
        self,
        consent_id: str,
        updates: Dict[str, Any]
    ) -> ParentalConsentRecord:
        """Update a consent record"""
        try:
            result = await self.update(consent_id, updates, "consent_id")
            return ParentalConsentRecord(**result)
            
        except Exception as e:
            logger.error(f"Error updating consent record: {str(e)}")
            raise
    
    async def revoke_consent(
        self,
        parent_id: str,
        child_id: str,
        consent_type: ConsentType
    ) -> bool:
        """Revoke a specific consent"""
        try:
            client = await self.get_client()
            result = await client.table(self.table_name).update({
                "granted": False,
                "expires_at": datetime.now(timezone.utc).isoformat()
            }).eq(
                "parent_id", parent_id
            ).eq(
                "child_id", child_id
            ).eq(
                "consent_type", consent_type.value
            ).execute()
            
            return len(result.data) > 0 if result.data else False
            
        except Exception as e:
            logger.error(f"Error revoking consent: {str(e)}")
            raise
    
    async def get_expired_consents(self) -> List[ParentalConsentRecord]:
        """Get all expired consent records"""
        try:
            client = await self.get_client()
            now = datetime.now(timezone.utc).isoformat()
            result = await client.table(self.table_name).select("*").lt(
                "expires_at", now
            ).eq("granted", True).execute()
            
            return [ParentalConsentRecord(**record) for record in result.data or []]
            
        except Exception as e:
            logger.error(f"Error getting expired consents: {str(e)}")
            raise


class SafetyViolationRepository(BaseRepository):
    """Repository for safety violation operations"""
    
    def __init__(self, db: DBConnection):
        super().__init__(db, "tutor_safety_violations")
    
    async def create_violation_record(self, violation: SafetyViolationRecord) -> SafetyViolationRecord:
        """Create a new safety violation record"""
        try:
            data = {
                "child_id": violation.child_id,
                "violation_type": violation.violation_type.value,
                "description": violation.description,
                "severity": violation.severity,
                "detected_at": violation.detected_at.isoformat(),
                "resolved": violation.resolved,
                "resolved_at": violation.resolved_at.isoformat() if violation.resolved_at else None,
                "parent_notified": violation.parent_notified,
                "metadata": violation.metadata
            }
            
            result = await self.create(data)
            return SafetyViolationRecord(**result)
            
        except Exception as e:
            logger.error(f"Error creating violation record: {str(e)}")
            raise
    
    async def get_violation_by_id(self, violation_id: str) -> Optional[SafetyViolationRecord]:
        """Get violation record by ID"""
        try:
            result = await self.get_by_id(violation_id, "violation_id")
            if result:
                return SafetyViolationRecord(**result)
            return None
            
        except Exception as e:
            logger.error(f"Error getting violation by ID: {str(e)}")
            raise
    
    async def get_violations_for_child(
        self,
        child_id: str,
        days: Optional[int] = None,
        severity: Optional[str] = None
    ) -> List[SafetyViolationRecord]:
        """Get violations for a specific child with optional filters"""
        try:
            client = await self.get_client()
            query = client.table(self.table_name).select("*").eq("child_id", child_id)
            
            if days:
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
                query = query.gte("detected_at", cutoff_date.isoformat())
            
            if severity:
                query = query.eq("severity", severity)
            
            result = await query.order("detected_at", desc=True).execute()
            
            return [SafetyViolationRecord(**record) for record in result.data or []]
            
        except Exception as e:
            logger.error(f"Error getting violations for child: {str(e)}")
            raise
    
    async def get_unresolved_violations(self) -> List[SafetyViolationRecord]:
        """Get all unresolved violations"""
        try:
            filters = {"resolved": False}
            results = await self.list_all(filters)
            return [SafetyViolationRecord(**result) for result in results]
            
        except Exception as e:
            logger.error(f"Error getting unresolved violations: {str(e)}")
            raise
    
    async def resolve_violation(
        self,
        violation_id: str,
        resolution_notes: Optional[str] = None
    ) -> SafetyViolationRecord:
        """Mark a violation as resolved"""
        try:
            updates = {
                "resolved": True,
                "resolved_at": datetime.now(timezone.utc).isoformat()
            }
            
            if resolution_notes:
                updates["metadata"] = {"resolution_notes": resolution_notes}
            
            result = await self.update(violation_id, updates, "violation_id")
            return SafetyViolationRecord(**result)
            
        except Exception as e:
            logger.error(f"Error resolving violation: {str(e)}")
            raise
    
    async def mark_parent_notified(self, violation_id: str) -> SafetyViolationRecord:
        """Mark that parent has been notified of violation"""
        try:
            updates = {"parent_notified": True}
            result = await self.update(violation_id, updates, "violation_id")
            return SafetyViolationRecord(**result)
            
        except Exception as e:
            logger.error(f"Error marking parent notified: {str(e)}")
            raise
    
    async def get_violation_statistics(
        self,
        child_id: Optional[str] = None,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get violation statistics for analysis"""
        try:
            client = await self.get_client()
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            query = client.table(self.table_name).select("*").gte(
                "detected_at", cutoff_date.isoformat()
            )
            
            if child_id:
                query = query.eq("child_id", child_id)
            
            result = await query.execute()
            violations = result.data or []
            
            # Calculate statistics
            total_violations = len(violations)
            by_severity = {}
            by_type = {}
            resolved_count = 0
            
            for violation in violations:
                severity = violation.get("severity", "medium")
                violation_type = violation.get("violation_type", "unknown")
                
                by_severity[severity] = by_severity.get(severity, 0) + 1
                by_type[violation_type] = by_type.get(violation_type, 0) + 1
                
                if violation.get("resolved", False):
                    resolved_count += 1
            
            return {
                "total_violations": total_violations,
                "resolved_violations": resolved_count,
                "unresolved_violations": total_violations - resolved_count,
                "by_severity": by_severity,
                "by_type": by_type,
                "resolution_rate": resolved_count / total_violations if total_violations > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting violation statistics: {str(e)}")
            raise


class SessionTimeTrackingRepository(BaseRepository):
    """Repository for session time tracking operations"""
    
    def __init__(self, db: DBConnection):
        super().__init__(db, "tutor_session_time_tracking")
    
    async def record_session_time(
        self,
        child_id: str,
        session_id: str,
        duration_minutes: int,
        session_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """Record session time for a child"""
        try:
            if session_date is None:
                session_date = date.today()
            
            data = {
                "child_id": child_id,
                "session_id": session_id,
                "date": session_date.isoformat(),
                "duration_minutes": duration_minutes
            }
            
            result = await self.create(data)
            return result
            
        except Exception as e:
            logger.error(f"Error recording session time: {str(e)}")
            raise
    
    async def get_daily_usage(self, child_id: str, target_date: Optional[date] = None) -> int:
        """Get total daily usage for a child"""
        try:
            if target_date is None:
                target_date = date.today()
            
            client = await self.get_client()
            result = await client.table(self.table_name).select(
                "duration_minutes"
            ).eq("child_id", child_id).eq("date", target_date.isoformat()).execute()
            
            total_minutes = sum(record["duration_minutes"] for record in result.data or [])
            return total_minutes
            
        except Exception as e:
            logger.error(f"Error getting daily usage: {str(e)}")
            raise
    
    async def get_weekly_usage(self, child_id: str, start_date: Optional[date] = None) -> int:
        """Get total weekly usage for a child"""
        try:
            if start_date is None:
                start_date = date.today() - timedelta(days=6)  # Last 7 days
            
            end_date = start_date + timedelta(days=6)
            
            client = await self.get_client()
            result = await client.table(self.table_name).select(
                "duration_minutes"
            ).eq("child_id", child_id).gte(
                "date", start_date.isoformat()
            ).lte("date", end_date.isoformat()).execute()
            
            total_minutes = sum(record["duration_minutes"] for record in result.data or [])
            return total_minutes
            
        except Exception as e:
            logger.error(f"Error getting weekly usage: {str(e)}")
            raise
    
    async def get_usage_history(
        self,
        child_id: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get usage history for a child"""
        try:
            start_date = date.today() - timedelta(days=days-1)
            
            client = await self.get_client()
            result = await client.table(self.table_name).select("*").eq(
                "child_id", child_id
            ).gte("date", start_date.isoformat()).order("date", desc=True).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting usage history: {str(e)}")
            raise


class DailyUsageSummaryRepository(BaseRepository):
    """Repository for daily usage summary operations"""
    
    def __init__(self, db: DBConnection):
        super().__init__(db, "tutor_daily_usage_summary")
    
    async def get_daily_summary(
        self,
        child_id: str,
        target_date: Optional[date] = None
    ) -> Optional[Dict[str, Any]]:
        """Get daily usage summary for a child"""
        try:
            if target_date is None:
                target_date = date.today()
            
            client = await self.get_client()
            result = await client.table(self.table_name).select("*").eq(
                "child_id", child_id
            ).eq("date", target_date.isoformat()).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Error getting daily summary: {str(e)}")
            raise
    
    async def get_weekly_summaries(
        self,
        child_id: str,
        start_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Get weekly usage summaries for a child"""
        try:
            if start_date is None:
                start_date = date.today() - timedelta(days=6)
            
            end_date = start_date + timedelta(days=6)
            
            client = await self.get_client()
            result = await client.table(self.table_name).select("*").eq(
                "child_id", child_id
            ).gte("date", start_date.isoformat()).lte(
                "date", end_date.isoformat()
            ).order("date", desc=True).execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting weekly summaries: {str(e)}")
            raise
    
    async def get_usage_trends(
        self,
        child_id: str,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get usage trends and analytics for a child"""
        try:
            start_date = date.today() - timedelta(days=days-1)
            
            client = await self.get_client()
            result = await client.table(self.table_name).select("*").eq(
                "child_id", child_id
            ).gte("date", start_date.isoformat()).order("date", desc=False).execute()
            
            summaries = result.data or []
            
            if not summaries:
                return {"total_days": 0, "average_daily_minutes": 0, "trend": "no_data"}
            
            total_minutes = sum(s["total_minutes"] for s in summaries)
            total_sessions = sum(s["session_count"] for s in summaries)
            total_violations = sum(s["violations_count"] for s in summaries)
            
            average_daily_minutes = total_minutes / len(summaries)
            average_sessions_per_day = total_sessions / len(summaries)
            
            # Calculate trend (simple linear trend)
            if len(summaries) >= 7:
                recent_avg = sum(s["total_minutes"] for s in summaries[-7:]) / 7
                earlier_avg = sum(s["total_minutes"] for s in summaries[:7]) / 7
                
                if recent_avg > earlier_avg * 1.1:
                    trend = "increasing"
                elif recent_avg < earlier_avg * 0.9:
                    trend = "decreasing"
                else:
                    trend = "stable"
            else:
                trend = "insufficient_data"
            
            return {
                "total_days": len(summaries),
                "total_minutes": total_minutes,
                "total_sessions": total_sessions,
                "total_violations": total_violations,
                "average_daily_minutes": round(average_daily_minutes, 1),
                "average_sessions_per_day": round(average_sessions_per_day, 1),
                "trend": trend
            }
            
        except Exception as e:
            logger.error(f"Error getting usage trends: {str(e)}")
            raise
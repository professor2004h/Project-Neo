"""
Data Versioning and Merge Strategies Service
Task 8.1 implementation
"""
import json
import hashlib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from enum import Enum

from utils.logger import logger
from services.supabase import DBConnection
from ..models.sync_models import (
    DataVersion,
    SyncData,
    DataConflict,
    DataType,
    ConflictResolution,
    SyncOperation
)


class MergeStrategy(str, Enum):
    """Merge strategy enumeration"""
    LAST_WRITER_WINS = "last_writer_wins"
    FIELD_LEVEL_MERGE = "field_level_merge"
    SEMANTIC_MERGE = "semantic_merge"
    UNION_MERGE = "union_merge"
    CUSTOM_MERGE = "custom_merge"


class VersionControlService:
    """
    Handles data versioning and conflict detection
    """
    
    def __init__(self, db: DBConnection):
        self.db = db
        
        # Version storage (in production, this would be database tables)
        self.version_store: Dict[str, List[DataVersion]] = {}  # data_id -> versions
        self.data_store: Dict[str, Dict[str, Any]] = {}  # version_id -> data
        
        # Conflict detection rules
        self.conflict_rules = self._initialize_conflict_rules()
    
    async def create_version(self, data_id: str, data_type: DataType, 
                           content: Dict[str, Any], device_id: str, 
                           user_id: str, changes: List[str] = None) -> DataVersion:
        """
        Create a new version of data
        
        Args:
            data_id: ID of the data
            data_type: Type of data
            content: Data content
            device_id: Device that created the version
            user_id: User ID
            changes: List of changed fields
            
        Returns:
            New data version
        """
        try:
            # Get current version number
            current_versions = self.version_store.get(data_id, [])
            version_number = len(current_versions) + 1
            
            # Calculate checksum
            checksum = self._calculate_checksum(content)
            
            # Get previous version
            previous_version = current_versions[-1].version_id if current_versions else None
            
            # Create new version
            version = DataVersion(
                data_id=data_id,
                data_type=data_type,
                version_number=version_number,
                device_id=device_id,
                user_id=user_id,
                checksum=checksum,
                changes=changes or [],
                previous_version=previous_version
            )
            
            # Store version and data
            if data_id not in self.version_store:
                self.version_store[data_id] = []
            
            self.version_store[data_id].append(version)
            self.data_store[version.version_id] = content.copy()
            
            logger.debug(f"Created version {version.version_number} for data {data_id}")
            
            return version
            
        except Exception as e:
            logger.error(f"Error creating version: {str(e)}")
            raise
    
    async def get_version(self, version_id: str) -> Optional[Tuple[DataVersion, Dict[str, Any]]]:
        """Get a specific version and its data"""
        try:
            # Find version
            for data_id, versions in self.version_store.items():
                for version in versions:
                    if version.version_id == version_id:
                        content = self.data_store.get(version_id, {})
                        return version, content
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting version {version_id}: {str(e)}")
            return None
    
    async def get_latest_version(self, data_id: str) -> Optional[Tuple[DataVersion, Dict[str, Any]]]:
        """Get the latest version of data"""
        try:
            versions = self.version_store.get(data_id, [])
            if not versions:
                return None
            
            latest_version = versions[-1]
            content = self.data_store.get(latest_version.version_id, {})
            
            return latest_version, content
            
        except Exception as e:
            logger.error(f"Error getting latest version for {data_id}: {str(e)}")
            return None
    
    async def get_version_history(self, data_id: str, limit: int = 10) -> List[DataVersion]:
        """Get version history for data"""
        try:
            versions = self.version_store.get(data_id, [])
            return versions[-limit:] if limit > 0 else versions
            
        except Exception as e:
            logger.error(f"Error getting version history: {str(e)}")
            return []
    
    async def detect_conflicts(self, data_id: str, new_version: DataVersion,
                             new_content: Dict[str, Any]) -> Optional[DataConflict]:
        """
        Detect conflicts when creating a new version
        
        Args:
            data_id: Data ID
            new_version: New version being created
            new_content: New content
            
        Returns:
            Conflict if detected, None otherwise
        """
        try:
            # Get current latest version
            result = await self.get_latest_version(data_id)
            if not result:
                return None  # No existing version, no conflict
            
            current_version, current_content = result
            
            # Check if versions conflict
            conflicted_fields = await self._find_conflicted_fields(
                current_content, new_content, new_version.data_type
            )
            
            if not conflicted_fields:
                return None  # No conflicts
            
            # Check if versions are concurrent (not one after another)
            if not await self._are_versions_concurrent(current_version, new_version):
                return None  # Sequential update, no conflict
            
            # Create conflict
            conflict = DataConflict(
                data_id=data_id,
                data_type=new_version.data_type,
                user_id=new_version.user_id,
                server_version=current_version,
                client_version=new_version,
                conflicted_fields=conflicted_fields,
                conflict_description=f"Concurrent modifications to fields: {', '.join(conflicted_fields)}",
                severity=await self._assess_conflict_severity(conflicted_fields, new_version.data_type)
            )
            
            logger.info(f"Detected conflict for data {data_id}: {len(conflicted_fields)} fields")
            
            return conflict
            
        except Exception as e:
            logger.error(f"Error detecting conflicts: {str(e)}")
            return None
    
    async def _find_conflicted_fields(self, content1: Dict[str, Any], 
                                    content2: Dict[str, Any],
                                    data_type: DataType) -> List[str]:
        """Find fields that conflict between two versions"""
        conflicted_fields = []
        
        # Get conflict detection rules for this data type
        rules = self.conflict_rules.get(data_type, {})
        
        # Check all fields that exist in either version
        all_fields = set(content1.keys()) | set(content2.keys())
        
        for field in all_fields:
            value1 = content1.get(field)
            value2 = content2.get(field)
            
            # Skip if values are the same
            if value1 == value2:
                continue
            
            # Check if field should be ignored for conflicts
            if field in rules.get("ignore_fields", []):
                continue
            
            # Check if field is metadata that can be auto-merged
            if field in rules.get("auto_merge_fields", []):
                continue
            
            # Field values differ, this is a conflict
            conflicted_fields.append(field)
        
        return conflicted_fields
    
    async def _are_versions_concurrent(self, version1: DataVersion, version2: DataVersion) -> bool:
        """Check if two versions are concurrent (created independently)"""
        # Versions are concurrent if neither is an ancestor of the other
        
        # If version2 has version1 as its previous version, they're sequential
        if version2.previous_version == version1.version_id:
            return False
        
        # If they have the same previous version, they're concurrent
        if version1.previous_version == version2.previous_version:
            return True
        
        # Check timestamp difference (less than 5 minutes might be concurrent)
        time_diff = abs((version1.timestamp - version2.timestamp).total_seconds())
        return time_diff < 300  # 5 minutes
    
    async def _assess_conflict_severity(self, conflicted_fields: List[str], 
                                      data_type: DataType) -> str:
        """Assess the severity of a conflict"""
        rules = self.conflict_rules.get(data_type, {})
        
        critical_fields = rules.get("critical_fields", [])
        important_fields = rules.get("important_fields", [])
        
        # Critical if any critical field is involved
        if any(field in critical_fields for field in conflicted_fields):
            return "critical"
        
        # High if multiple important fields or many fields
        if (any(field in important_fields for field in conflicted_fields) or 
            len(conflicted_fields) > 5):
            return "high"
        
        # Medium if few fields
        if len(conflicted_fields) <= 2:
            return "medium"
        
        return "low"
    
    def _calculate_checksum(self, content: Dict[str, Any]) -> str:
        """Calculate checksum for content"""
        # Create deterministic JSON representation
        content_str = json.dumps(content, sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(content_str.encode()).hexdigest()
    
    def _initialize_conflict_rules(self) -> Dict[DataType, Dict[str, List[str]]]:
        """Initialize conflict detection rules for different data types"""
        return {
            DataType.USER_PROFILE: {
                "ignore_fields": ["last_seen", "session_count", "login_count"],
                "auto_merge_fields": ["total_time", "total_activities"],
                "critical_fields": ["email", "password_hash", "parental_controls"],
                "important_fields": ["name", "age", "grade", "preferences"]
            },
            DataType.PROGRESS_RECORD: {
                "ignore_fields": ["updated_at", "sync_timestamp"],
                "auto_merge_fields": ["total_time", "activity_count", "last_practiced"],
                "critical_fields": ["skill_level", "confidence_score"],
                "important_fields": ["mastery_indicators", "improvement_areas"]
            },
            DataType.LEARNING_ACTIVITY: {
                "ignore_fields": ["started_at", "view_count"],
                "auto_merge_fields": ["duration", "attempts"],
                "critical_fields": ["status", "completed_at", "performance_data"],
                "important_fields": ["score", "accuracy", "engagement_score"]
            },
            DataType.ACHIEVEMENT: {
                "ignore_fields": ["viewed_at", "notification_sent"],
                "auto_merge_fields": ["progress_value", "milestone_count"],
                "critical_fields": ["is_completed", "completed_at"],
                "important_fields": ["current_progress", "milestones"]
            },
            DataType.SETTINGS: {
                "ignore_fields": ["last_updated"],
                "auto_merge_fields": [],
                "critical_fields": ["privacy_settings", "parental_controls"],
                "important_fields": ["language", "theme", "notifications"]
            }
        }


class MergeStrategyService:
    """
    Handles intelligent merging of conflicted data
    """
    
    def __init__(self):
        # Merge strategy implementations
        self.merge_strategies = {
            MergeStrategy.LAST_WRITER_WINS: self._merge_last_writer_wins,
            MergeStrategy.FIELD_LEVEL_MERGE: self._merge_field_level,
            MergeStrategy.SEMANTIC_MERGE: self._merge_semantic,
            MergeStrategy.UNION_MERGE: self._merge_union,
            MergeStrategy.CUSTOM_MERGE: self._merge_custom
        }
        
        # Data type specific merge configurations
        self.merge_configs = self._initialize_merge_configs()
    
    async def merge_data(self, conflict: DataConflict, server_content: Dict[str, Any],
                        client_content: Dict[str, Any], 
                        strategy: MergeStrategy = None) -> Dict[str, Any]:
        """
        Merge conflicted data using specified strategy
        
        Args:
            conflict: The conflict to resolve
            server_content: Server version content
            client_content: Client version content
            strategy: Merge strategy to use
            
        Returns:
            Merged content
        """
        try:
            # Choose strategy if not specified
            if strategy is None:
                strategy = self._choose_merge_strategy(conflict)
            
            # Get merge function
            merge_func = self.merge_strategies.get(strategy, self._merge_last_writer_wins)
            
            # Perform merge
            merged_content = await merge_func(
                conflict, server_content, client_content
            )
            
            logger.info(f"Merged data for conflict {conflict.conflict_id} using {strategy.value}")
            
            return merged_content
            
        except Exception as e:
            logger.error(f"Error merging data: {str(e)}")
            # Fallback to server content
            return server_content.copy()
    
    async def _merge_last_writer_wins(self, conflict: DataConflict,
                                    server_content: Dict[str, Any],
                                    client_content: Dict[str, Any]) -> Dict[str, Any]:
        """Simple last-writer-wins merge"""
        # Choose the version with the later timestamp
        if conflict.client_version.timestamp > conflict.server_version.timestamp:
            return client_content.copy()
        else:
            return server_content.copy()
    
    async def _merge_field_level(self, conflict: DataConflict,
                               server_content: Dict[str, Any],
                               client_content: Dict[str, Any]) -> Dict[str, Any]:
        """Field-level merge based on field priorities"""
        merged = server_content.copy()
        config = self.merge_configs.get(conflict.data_type, {})
        
        # Get field priorities
        client_priority_fields = config.get("client_priority_fields", [])
        server_priority_fields = config.get("server_priority_fields", [])
        
        for field in conflict.conflicted_fields:
            if field in client_priority_fields:
                # Client wins for this field
                if field in client_content:
                    merged[field] = client_content[field]
            elif field in server_priority_fields:
                # Server wins for this field (already in merged)
                pass
            else:
                # Use timestamp-based decision for this field
                if conflict.client_version.timestamp > conflict.server_version.timestamp:
                    if field in client_content:
                        merged[field] = client_content[field]
        
        return merged
    
    async def _merge_semantic(self, conflict: DataConflict,
                            server_content: Dict[str, Any],
                            client_content: Dict[str, Any]) -> Dict[str, Any]:
        """Semantic merge based on data type semantics"""
        merged = server_content.copy()
        
        # Data type specific semantic merging
        if conflict.data_type == DataType.PROGRESS_RECORD:
            # For progress records, take maximum values for numeric fields
            numeric_fields = ["skill_level", "confidence_score", "total_time", "total_activities"]
            
            for field in numeric_fields:
                if field in conflict.conflicted_fields:
                    server_val = server_content.get(field, 0)
                    client_val = client_content.get(field, 0)
                    
                    # Take maximum for progress metrics
                    if isinstance(server_val, (int, float)) and isinstance(client_val, (int, float)):
                        merged[field] = max(server_val, client_val)
        
        elif conflict.data_type == DataType.LEARNING_ACTIVITY:
            # For activities, prefer completed status and latest performance data
            if "status" in conflict.conflicted_fields:
                server_status = server_content.get("status", "")
                client_status = client_content.get("status", "")
                
                # Prefer completed status
                if client_status == "completed" or server_status != "completed":
                    merged["status"] = client_status
            
            # Take latest performance data
            if "performance_data" in conflict.conflicted_fields:
                if conflict.client_version.timestamp > conflict.server_version.timestamp:
                    merged["performance_data"] = client_content.get("performance_data", {})
        
        elif conflict.data_type == DataType.ACHIEVEMENT:
            # For achievements, prefer completed state and higher progress
            if "is_completed" in conflict.conflicted_fields:
                # If either version shows completed, use that
                if client_content.get("is_completed", False) or server_content.get("is_completed", False):
                    merged["is_completed"] = True
                    
                    # Use completion timestamp from the version that's completed
                    if client_content.get("is_completed", False):
                        merged["completed_at"] = client_content.get("completed_at")
                    else:
                        merged["completed_at"] = server_content.get("completed_at")
            
            # Take higher progress value
            if "current_progress" in conflict.conflicted_fields:
                server_progress = server_content.get("current_progress", 0)
                client_progress = client_content.get("current_progress", 0)
                merged["current_progress"] = max(server_progress, client_progress)
        
        return merged
    
    async def _merge_union(self, conflict: DataConflict,
                         server_content: Dict[str, Any],
                         client_content: Dict[str, Any]) -> Dict[str, Any]:
        """Union merge for array and set fields"""
        merged = server_content.copy()
        
        # Merge array fields by taking union
        array_fields = self.merge_configs.get(conflict.data_type, {}).get("array_fields", [])
        
        for field in array_fields:
            if field in conflict.conflicted_fields:
                server_items = set(server_content.get(field, []))
                client_items = set(client_content.get(field, []))
                merged[field] = list(server_items.union(client_items))
        
        # For non-array fields, use field-level merge
        non_array_fields = [f for f in conflict.conflicted_fields if f not in array_fields]
        if non_array_fields:
            # Create temporary conflict for non-array fields
            temp_conflict = DataConflict(
                data_id=conflict.data_id,
                data_type=conflict.data_type,
                user_id=conflict.user_id,
                server_version=conflict.server_version,
                client_version=conflict.client_version,
                conflicted_fields=non_array_fields
            )
            
            field_merged = await self._merge_field_level(temp_conflict, server_content, client_content)
            
            # Update merged content with field-level merged results
            for field in non_array_fields:
                if field in field_merged:
                    merged[field] = field_merged[field]
        
        return merged
    
    async def _merge_custom(self, conflict: DataConflict,
                          server_content: Dict[str, Any],
                          client_content: Dict[str, Any]) -> Dict[str, Any]:
        """Custom merge logic for specific data types"""
        # Get custom merge rules
        custom_rules = self.merge_configs.get(conflict.data_type, {}).get("custom_rules", {})
        
        if not custom_rules:
            # No custom rules, fall back to semantic merge
            return await self._merge_semantic(conflict, server_content, client_content)
        
        merged = server_content.copy()
        
        # Apply custom rules
        for field in conflict.conflicted_fields:
            field_rule = custom_rules.get(field)
            
            if field_rule == "max":
                # Take maximum value
                server_val = server_content.get(field, 0)
                client_val = client_content.get(field, 0)
                if isinstance(server_val, (int, float)) and isinstance(client_val, (int, float)):
                    merged[field] = max(server_val, client_val)
                    
            elif field_rule == "min":
                # Take minimum value
                server_val = server_content.get(field, float('inf'))
                client_val = client_content.get(field, float('inf'))
                if isinstance(server_val, (int, float)) and isinstance(client_val, (int, float)):
                    merged[field] = min(server_val, client_val)
                    
            elif field_rule == "concat":
                # Concatenate string values
                server_val = str(server_content.get(field, ""))
                client_val = str(client_content.get(field, ""))
                merged[field] = f"{server_val} {client_val}".strip()
                
            elif field_rule == "client_wins":
                # Client version wins
                if field in client_content:
                    merged[field] = client_content[field]
                    
            elif field_rule == "server_wins":
                # Server version wins (already in merged)
                pass
        
        return merged
    
    def _choose_merge_strategy(self, conflict: DataConflict) -> MergeStrategy:
        """Choose appropriate merge strategy based on conflict characteristics"""
        config = self.merge_configs.get(conflict.data_type, {})
        
        # Check if conflict has array fields
        array_fields = config.get("array_fields", [])
        has_arrays = any(field in array_fields for field in conflict.conflicted_fields)
        
        if has_arrays:
            return MergeStrategy.UNION_MERGE
        
        # Check if custom rules exist
        custom_rules = config.get("custom_rules", {})
        has_custom_rules = any(field in custom_rules for field in conflict.conflicted_fields)
        
        if has_custom_rules:
            return MergeStrategy.CUSTOM_MERGE
        
        # Check conflict severity
        if conflict.severity in ["critical", "high"]:
            return MergeStrategy.SEMANTIC_MERGE
        
        # Default to field-level merge
        return MergeStrategy.FIELD_LEVEL_MERGE
    
    def _initialize_merge_configs(self) -> Dict[DataType, Dict[str, Any]]:
        """Initialize merge configurations for different data types"""
        return {
            DataType.USER_PROFILE: {
                "client_priority_fields": ["language", "theme", "notifications", "privacy_settings"],
                "server_priority_fields": ["email", "created_at", "last_login"],
                "array_fields": ["favorite_subjects", "completed_tutorials"],
                "custom_rules": {
                    "total_time": "max",
                    "total_activities": "max",
                    "login_count": "max"
                }
            },
            DataType.PROGRESS_RECORD: {
                "client_priority_fields": ["last_practiced"],
                "server_priority_fields": ["created_at"],
                "array_fields": ["improvement_areas", "mastery_indicators"],
                "custom_rules": {
                    "skill_level": "max",
                    "confidence_score": "max",
                    "total_time": "max"
                }
            },
            DataType.LEARNING_ACTIVITY: {
                "client_priority_fields": ["performance_data", "completed_at", "status"],
                "server_priority_fields": ["created_at", "content"],
                "array_fields": ["attempts", "hints_used"],
                "custom_rules": {
                    "score": "max",
                    "accuracy": "max",
                    "duration": "max"
                }
            },
            DataType.ACHIEVEMENT: {
                "client_priority_fields": ["current_progress", "completed_at"],
                "server_priority_fields": ["created_at", "requirements"],
                "array_fields": ["milestones", "evidence"],
                "custom_rules": {
                    "current_progress": "max",
                    "is_completed": "max"  # True > False
                }
            },
            DataType.SETTINGS: {
                "client_priority_fields": ["user_preferences", "ui_settings"],
                "server_priority_fields": ["system_settings", "defaults"],
                "array_fields": ["enabled_features", "disabled_notifications"]
            }
        }


class DataVersioningService:
    """
    Main service combining version control and merge strategies
    """
    
    def __init__(self, db: DBConnection):
        self.db = db
        self.version_control = VersionControlService(db)
        self.merge_service = MergeStrategyService()
    
    async def create_version_with_conflict_detection(self, data_id: str, data_type: DataType,
                                                   content: Dict[str, Any], device_id: str,
                                                   user_id: str, changes: List[str] = None) -> Tuple[DataVersion, Optional[DataConflict]]:
        """
        Create a new version with automatic conflict detection
        
        Returns:
            Tuple of (new_version, conflict_if_any)
        """
        try:
            # Create new version
            new_version = await self.version_control.create_version(
                data_id, data_type, content, device_id, user_id, changes
            )
            
            # Detect conflicts
            conflict = await self.version_control.detect_conflicts(
                data_id, new_version, content
            )
            
            return new_version, conflict
            
        except Exception as e:
            logger.error(f"Error creating version with conflict detection: {str(e)}")
            raise
    
    async def resolve_conflict_with_merge(self, conflict: DataConflict,
                                        strategy: MergeStrategy = None) -> Dict[str, Any]:
        """
        Resolve a conflict using intelligent merging
        
        Args:
            conflict: The conflict to resolve
            strategy: Merge strategy to use (optional)
            
        Returns:
            Merged content
        """
        try:
            # Get version contents
            server_result = await self.version_control.get_version(conflict.server_version.version_id)
            client_result = await self.version_control.get_version(conflict.client_version.version_id)
            
            if not server_result or not client_result:
                raise ValueError("Cannot retrieve version data for conflict resolution")
            
            _, server_content = server_result
            _, client_content = client_result
            
            # Perform merge
            merged_content = await self.merge_service.merge_data(
                conflict, server_content, client_content, strategy
            )
            
            # Create new merged version
            merged_version = await self.version_control.create_version(
                conflict.data_id,
                conflict.data_type,
                merged_content,
                "system_merge",
                conflict.user_id,
                changes=["merged_conflict"]
            )
            
            logger.info(f"Resolved conflict {conflict.conflict_id} with merge strategy")
            
            return merged_content
            
        except Exception as e:
            logger.error(f"Error resolving conflict with merge: {str(e)}")
            raise
    
    async def get_merge_preview(self, conflict: DataConflict,
                              strategy: MergeStrategy = None) -> Dict[str, Any]:
        """
        Get a preview of what the merge result would be without applying it
        
        Args:
            conflict: The conflict to preview merge for
            strategy: Merge strategy to use
            
        Returns:
            Preview of merged content
        """
        try:
            # Get version contents
            server_result = await self.version_control.get_version(conflict.server_version.version_id)
            client_result = await self.version_control.get_version(conflict.client_version.version_id)
            
            if not server_result or not client_result:
                return {}
            
            _, server_content = server_result
            _, client_content = client_result
            
            # Perform merge preview (without creating version)
            merged_content = await self.merge_service.merge_data(
                conflict, server_content, client_content, strategy
            )
            
            return {
                "merged_content": merged_content,
                "strategy_used": strategy.value if strategy else "auto",
                "server_content": server_content,
                "client_content": client_content,
                "conflicted_fields": conflict.conflicted_fields
            }
            
        except Exception as e:
            logger.error(f"Error generating merge preview: {str(e)}")
            return {}
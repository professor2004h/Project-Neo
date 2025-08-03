"""
Synchronization API Router - Cross-platform data synchronization
Task 10.1 implementation - Requirements: 2.1, 2.3, 8.1, 8.2
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import uuid
from datetime import datetime, timezone

from services.supabase import DBConnection
from utils.auth_utils import get_current_user_id_from_jwt
from utils.logger import logger
from ..services.sync_service import SyncService
from ..services.offline_service import OfflineService
from ..models.sync_models import DataType, SyncStatus, DeviceInfo

router = APIRouter(prefix="/sync", tags=["Synchronization"])

# Pydantic models for API requests/responses
class SyncRequest(BaseModel):
    """Request model for data synchronization"""
    device_id: str = Field(description="Unique device identifier")
    device_info: Dict[str, Any] = Field(description="Device information")
    last_sync_timestamp: Optional[datetime] = Field(None, description="Last successful sync timestamp")
    data_types: Optional[List[DataType]] = Field(None, description="Specific data types to sync")
    include_offline_queue: bool = Field(default=True, description="Include offline queue processing")

class OfflineOperationRequest(BaseModel):
    """Request model for queuing offline operations"""
    device_id: str = Field(description="Device identifier")
    operations: List[Dict[str, Any]] = Field(description="Operations to queue")
    operation_type: str = Field(description="Type of operations")

class DeviceRegistrationRequest(BaseModel):
    """Request model for device registration"""
    device_id: str = Field(description="Unique device identifier")
    device_type: str = Field(description="Type of device (web, mobile, extension)")
    device_name: Optional[str] = Field(None, description="User-friendly device name")
    platform_info: Dict[str, Any] = Field(description="Platform and version information")

class SyncResponse(BaseModel):
    """Response model for synchronization operations"""
    sync_id: str = Field(description="Unique sync operation identifier")
    device_id: str = Field(description="Device that performed sync")
    sync_status: SyncStatus = Field(description="Status of sync operation")
    synced_data_types: List[DataType] = Field(description="Data types that were synchronized")
    sync_timestamp: datetime = Field(description="When sync completed")
    conflicts_resolved: int = Field(description="Number of conflicts resolved")
    operations_processed: int = Field(description="Number of operations processed")
    next_sync_recommended: datetime = Field(description="Recommended next sync time")
    sync_summary: Dict[str, Any] = Field(description="Summary of sync results")

class OfflineStatusResponse(BaseModel):
    """Response model for offline status"""
    device_id: str = Field(description="Device identifier")
    is_offline: bool = Field(description="Whether device is currently offline")
    queued_operations: int = Field(description="Number of queued offline operations")
    last_sync: Optional[datetime] = Field(None, description="Last successful sync")
    cached_content_size: int = Field(description="Size of cached content in bytes")
    available_offline_features: List[str] = Field(description="Features available offline")
    sync_required: bool = Field(description="Whether sync is required")

class DeviceStatusResponse(BaseModel):
    """Response model for device status"""
    device_id: str = Field(description="Device identifier")
    device_type: str = Field(description="Device type")
    is_registered: bool = Field(description="Whether device is registered")
    last_seen: Optional[datetime] = Field(None, description="Last activity timestamp")
    sync_status: str = Field(description="Current sync status")
    data_version: int = Field(description="Current data version")
    pending_updates: int = Field(description="Number of pending updates")

# Dependency to get initialized services
async def get_sync_service() -> SyncService:
    """Get initialized sync service"""
    from ..api import db
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return SyncService(db)

async def get_offline_service() -> OfflineService:
    """Get initialized offline service"""
    from ..api import db
    if not db:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return OfflineService(db)

# API Endpoints
@router.post("/sync", response_model=SyncResponse)
async def sync_user_data(
    request: SyncRequest,
    user_id: str = Depends(get_current_user_id_from_jwt),
    sync_service: SyncService = Depends(get_sync_service)
):
    """
    Synchronize user data across devices
    Requirement 2.1: Sync progress and preferences across web, mobile, and Chrome extension
    Requirement 2.3: Maintain session continuity and current learning context
    """
    try:
        logger.info(f"Starting data sync for user {user_id}, device {request.device_id}")
        
        # Perform data synchronization
        sync_result = await sync_service.sync_user_data(
            user_id=user_id,
            device_id=request.device_id,
            device_info=request.device_info,
            last_sync_timestamp=request.last_sync_timestamp,
            data_types=request.data_types,
            include_offline_queue=request.include_offline_queue
        )
        
        # Convert to API response
        response = SyncResponse(
            sync_id=sync_result.get("sync_id", str(uuid.uuid4())),
            device_id=request.device_id,
            sync_status=SyncStatus(sync_result.get("status", "completed")),
            synced_data_types=sync_result.get("synced_data_types", []),
            sync_timestamp=datetime.now(timezone.utc),
            conflicts_resolved=sync_result.get("conflicts_resolved", 0),
            operations_processed=sync_result.get("operations_processed", 0),
            next_sync_recommended=sync_result.get("next_sync_recommended", 
                                                datetime.now(timezone.utc)),
            sync_summary=sync_result.get("summary", {})
        )
        
        logger.info(f"Data sync completed for user {user_id}, device {request.device_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error syncing data for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to synchronize data")

@router.post("/offline/queue", response_model=Dict[str, Any])
async def queue_offline_operations(
    request: OfflineOperationRequest,
    user_id: str = Depends(get_current_user_id_from_jwt),
    offline_service: OfflineService = Depends(get_offline_service)
):
    """
    Queue operations for offline processing
    Requirement 2.4: Queue interactions and sync when connection is restored
    Requirement 8.2: Offline functionality and caching
    """
    try:
        logger.info(f"Queuing offline operations for user {user_id}, device {request.device_id}")
        
        # Queue operations
        queue_result = await offline_service.queue_operations(
            user_id=user_id,
            device_id=request.device_id,
            operations=request.operations,
            operation_type=request.operation_type
        )
        
        logger.info(f"Offline operations queued for user {user_id}")
        return {
            "queue_id": queue_result.get("queue_id", str(uuid.uuid4())),
            "operations_queued": len(request.operations),
            "queue_size": queue_result.get("total_queue_size", 0),
            "estimated_sync_time": queue_result.get("estimated_sync_time"),
            "queued_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error queuing offline operations for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to queue offline operations")

@router.post("/devices/register", response_model=Dict[str, Any])
async def register_device(
    request: DeviceRegistrationRequest,
    user_id: str = Depends(get_current_user_id_from_jwt),
    sync_service: SyncService = Depends(get_sync_service)
):
    """
    Register a new device for synchronization
    """
    try:
        logger.info(f"Registering device {request.device_id} for user {user_id}")
        
        # Register device
        registration_result = await sync_service.register_device(
            user_id=user_id,
            device_id=request.device_id,
            device_type=request.device_type,
            device_name=request.device_name,
            platform_info=request.platform_info
        )
        
        logger.info(f"Device registered successfully for user {user_id}")
        return {
            "device_id": request.device_id,
            "registration_status": "success",
            "device_token": registration_result.get("device_token"),
            "sync_enabled": True,
            "registered_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error registering device for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to register device")

@router.get("/offline/status", response_model=OfflineStatusResponse)
async def get_offline_status(
    device_id: str = Query(description="Device identifier"),
    user_id: str = Depends(get_current_user_id_from_jwt),
    offline_service: OfflineService = Depends(get_offline_service)
):
    """
    Get offline status for a device
    """
    try:
        logger.info(f"Getting offline status for user {user_id}, device {device_id}")
        
        # Get offline status
        status_data = await offline_service.get_offline_status(user_id, device_id)
        
        response = OfflineStatusResponse(
            device_id=device_id,
            is_offline=status_data.get("is_offline", False),
            queued_operations=status_data.get("queued_operations", 0),
            last_sync=status_data.get("last_sync"),
            cached_content_size=status_data.get("cached_content_size", 0),
            available_offline_features=status_data.get("available_offline_features", []),
            sync_required=status_data.get("sync_required", False)
        )
        
        logger.info(f"Offline status retrieved for user {user_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error getting offline status for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get offline status")

@router.get("/devices", response_model=List[DeviceStatusResponse])
async def get_user_devices(
    user_id: str = Depends(get_current_user_id_from_jwt),
    sync_service: SyncService = Depends(get_sync_service)
):
    """
    Get all registered devices for a user
    """
    try:
        logger.info(f"Getting devices for user {user_id}")
        
        # Get user devices
        devices_data = await sync_service.get_user_devices(user_id)
        
        devices = []
        for device_data in devices_data.get("devices", []):
            device = DeviceStatusResponse(
                device_id=device_data.get("device_id", ""),
                device_type=device_data.get("device_type", "unknown"),
                is_registered=device_data.get("is_registered", False),
                last_seen=device_data.get("last_seen"),
                sync_status=device_data.get("sync_status", "unknown"),
                data_version=device_data.get("data_version", 0),
                pending_updates=device_data.get("pending_updates", 0)
            )
            devices.append(device)
        
        logger.info(f"Retrieved {len(devices)} devices for user {user_id}")
        return devices
        
    except Exception as e:
        logger.error(f"Error getting devices for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get user devices")

@router.delete("/devices/{device_id}")
async def unregister_device(
    device_id: str,
    user_id: str = Depends(get_current_user_id_from_jwt),
    sync_service: SyncService = Depends(get_sync_service)
):
    """
    Unregister a device from synchronization
    """
    try:
        logger.info(f"Unregistering device {device_id} for user {user_id}")
        
        # Unregister device
        await sync_service.unregister_device(user_id, device_id)
        
        logger.info(f"Device unregistered successfully for user {user_id}")
        return {
            "device_id": device_id,
            "status": "unregistered",
            "unregistered_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error unregistering device for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to unregister device")

@router.post("/conflicts/resolve")
async def resolve_sync_conflicts(
    conflicts: List[Dict[str, Any]],
    resolution_strategy: str = Query(description="Resolution strategy"),
    user_id: str = Depends(get_current_user_id_from_jwt),
    sync_service: SyncService = Depends(get_sync_service)
):
    """
    Resolve synchronization conflicts
    """
    try:
        logger.info(f"Resolving sync conflicts for user {user_id}")
        
        # Resolve conflicts
        resolution_result = await sync_service.resolve_conflicts(
            user_id=user_id,
            conflicts=conflicts,
            resolution_strategy=resolution_strategy
        )
        
        logger.info(f"Sync conflicts resolved for user {user_id}")
        return {
            "conflicts_resolved": len(conflicts),
            "resolution_strategy": resolution_strategy,
            "resolution_summary": resolution_result.get("summary", {}),
            "resolved_at": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error resolving sync conflicts for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to resolve sync conflicts")

@router.get("/health")
async def sync_health_check():
    """Health check endpoint for synchronization service"""
    return {
        "status": "ok",
        "service": "synchronization",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "capabilities": [
            "cross_platform_sync",
            "offline_queue_management",
            "device_registration",
            "conflict_resolution",
            "real_time_updates"
        ]
    }
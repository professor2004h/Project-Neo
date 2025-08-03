"""
WebSocket API Router - Real-time communication and updates
Task 10.2 implementation - Requirements: 2.1, 2.3, 4.1
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException, Query
from typing import Dict, List, Optional, Any
import json
import asyncio
import uuid
from datetime import datetime, timezone
import logging

from services.supabase import DBConnection
from utils.auth_utils import get_current_user_id_from_jwt_websocket
from utils.logger import logger
from ..services.realtime_sync_service import RealtimeSyncService, WebSocketConnectionManager
from ..services.progress_reporting_service import ProgressReportingService
from ..services.tutor_service import TutorService

router = APIRouter(prefix="/ws", tags=["WebSocket"])

# Global connection managers
connection_manager = WebSocketConnectionManager()
# Note: RealtimeSyncService will be initialized in endpoints with proper DB connection

# WebSocket message types
class MessageType:
    # Tutoring session messages
    TUTOR_QUESTION = "tutor_question"
    TUTOR_RESPONSE = "tutor_response"
    CONCEPT_EXPLANATION = "concept_explanation"
    
    # Progress updates
    ACTIVITY_COMPLETED = "activity_completed"
    PROGRESS_UPDATE = "progress_update"
    ACHIEVEMENT_EARNED = "achievement_earned"
    
    # Synchronization messages
    DATA_SYNC = "data_sync"
    DEVICE_SYNC = "device_sync"
    CONFLICT_DETECTED = "conflict_detected"
    
    # Real-time notifications
    PARENT_NOTIFICATION = "parent_notification"
    LEARNING_REMINDER = "learning_reminder"
    
    # Connection management
    HEARTBEAT = "heartbeat"
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    ERROR = "error"

class WebSocketMessage:
    """Structure for WebSocket messages"""
    
    def __init__(self, message_type: str, data: Dict[str, Any], 
                 user_id: str = None, session_id: str = None):
        self.message_type = message_type
        self.data = data
        self.user_id = user_id
        self.session_id = session_id
        self.timestamp = datetime.now(timezone.utc)
        self.message_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "message_type": self.message_type,
            "data": self.data,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat()
        }

async def get_user_from_websocket_token(token: str) -> Optional[str]:
    """Extract user ID from WebSocket token"""
    try:
        # This would use the same JWT validation as REST endpoints
        user_id = await get_current_user_id_from_jwt_websocket(token)
        return user_id
    except Exception as e:
        logger.error(f"Error validating WebSocket token: {str(e)}")
        return None

async def broadcast_to_user_devices(user_id: str, message: WebSocketMessage, exclude_device: str = None):
    """Broadcast message to all devices of a user"""
    try:
        await connection_manager.broadcast_to_user(
            user_id, message.to_dict(), exclude_device_id=exclude_device
        )
    except Exception as e:
        logger.error(f"Error broadcasting to user devices: {str(e)}")

async def handle_tutor_interaction(websocket: WebSocket, message_data: Dict[str, Any], 
                                 user_id: str, session_id: str):
    """Handle real-time tutoring interactions"""
    try:
        from ..api import db
        tutor_service = TutorService(db)
        
        if message_data.get("type") == "question":
            # Process tutor question in real-time
            question = message_data.get("question", "")
            context = message_data.get("context", {})
            context.update({
                "user_id": user_id,
                "session_id": session_id,
                "real_time": True
            })
            
            # Send acknowledgment
            ack_message = WebSocketMessage(
                MessageType.TUTOR_RESPONSE,
                {
                    "status": "processing",
                    "message": "Processing your question...",
                    "question_id": message_data.get("question_id")
                },
                user_id,
                session_id
            )
            await websocket.send_text(json.dumps(ack_message.to_dict()))
            
            # Process the question
            response = await tutor_service.ask_question(user_id, question, context)
            
            # Send response
            response_message = WebSocketMessage(
                MessageType.TUTOR_RESPONSE,
                {
                    "status": "completed",
                    "response": response,
                    "question_id": message_data.get("question_id")
                },
                user_id,
                session_id
            )
            await websocket.send_text(json.dumps(response_message.to_dict()))
            
            # Broadcast to other devices
            await broadcast_to_user_devices(user_id, response_message, 
                                          exclude_device=message_data.get("device_id"))
            
        elif message_data.get("type") == "explanation_request":
            # Handle concept explanation requests
            concept_name = message_data.get("concept_name", "")
            explanation = await tutor_service.explain_concept(
                concept_id=message_data.get("concept_id"),
                concept_name=concept_name,
                difficulty_level=message_data.get("difficulty_level", 1),
                learning_style=message_data.get("learning_style", "visual"),
                age=message_data.get("age"),
                user_id=user_id
            )
            
            explanation_message = WebSocketMessage(
                MessageType.CONCEPT_EXPLANATION,
                {
                    "explanation": explanation,
                    "concept_name": concept_name,
                    "request_id": message_data.get("request_id")
                },
                user_id,
                session_id
            )
            await websocket.send_text(json.dumps(explanation_message.to_dict()))
            
    except Exception as e:
        logger.error(f"Error handling tutor interaction: {str(e)}")
        error_message = WebSocketMessage(
            MessageType.ERROR,
            {
                "error": "Failed to process tutor interaction",
                "details": str(e),
                "request_id": message_data.get("request_id") or message_data.get("question_id")
            },
            user_id,
            session_id
        )
        await websocket.send_text(json.dumps(error_message.to_dict()))

async def handle_progress_update(websocket: WebSocket, message_data: Dict[str, Any], 
                               user_id: str, session_id: str):
    """Handle real-time progress updates"""
    try:
        from ..api import db
        progress_service = ProgressReportingService(db)
        
        if message_data.get("type") == "activity_completed":
            # Track completed activity
            activity_data = message_data.get("activity_data", {})
            activity_data["user_id"] = user_id
            
            # Process activity tracking
            tracking_result = await progress_service.track_activity_completion(activity_data)
            
            # Send confirmation
            confirmation_message = WebSocketMessage(
                MessageType.ACTIVITY_COMPLETED,
                {
                    "status": "tracked",
                    "activity_id": tracking_result.get("activity_id"),
                    "performance_impact": tracking_result.get("performance_impact"),
                    "achievements_earned": tracking_result.get("achievements_earned", [])
                },
                user_id,
                session_id
            )
            await websocket.send_text(json.dumps(confirmation_message.to_dict()))
            
            # Broadcast progress update to parent devices
            if tracking_result.get("notify_parent"):
                parent_notification = WebSocketMessage(
                    MessageType.PARENT_NOTIFICATION,
                    {
                        "type": "activity_completed",
                        "child_id": user_id,
                        "activity_summary": tracking_result.get("activity_summary"),
                        "progress_update": tracking_result.get("progress_summary")
                    }
                )
                # This would broadcast to parent's devices
                await broadcast_to_user_devices(
                    tracking_result.get("parent_id"), parent_notification
                )
        
        elif message_data.get("type") == "progress_request":
            # Real-time progress report request
            timeframe = message_data.get("timeframe", "daily")
            progress_data = await progress_service.get_real_time_progress(user_id, timeframe)
            
            progress_message = WebSocketMessage(
                MessageType.PROGRESS_UPDATE,
                {
                    "progress_data": progress_data,
                    "timeframe": timeframe,
                    "request_id": message_data.get("request_id")
                },
                user_id,
                session_id
            )
            await websocket.send_text(json.dumps(progress_message.to_dict()))
            
    except Exception as e:
        logger.error(f"Error handling progress update: {str(e)}")
        error_message = WebSocketMessage(
            MessageType.ERROR,
            {
                "error": "Failed to process progress update",
                "details": str(e),
                "request_id": message_data.get("request_id")
            },
            user_id,
            session_id
        )
        await websocket.send_text(json.dumps(error_message.to_dict()))

async def handle_sync_operation(websocket: WebSocket, message_data: Dict[str, Any], 
                               user_id: str, session_id: str):
    """Handle real-time synchronization operations"""
    try:
        # Initialize database connection and realtime sync service
        db = DBConnection()
        await db.initialize()
        realtime_updater = RealtimeSyncService(db)
        
        if message_data.get("type") == "device_sync":
            # Real-time device synchronization
            device_id = message_data.get("device_id")
            sync_data = message_data.get("sync_data", {})
            
            # Process sync through realtime updater
            sync_result = await realtime_updater.process_real_time_sync(
                user_id, device_id, sync_data
            )
            
            # Send sync confirmation
            sync_message = WebSocketMessage(
                MessageType.DEVICE_SYNC,
                {
                    "status": "synced",
                    "sync_result": sync_result,
                    "device_id": device_id,
                    "sync_timestamp": datetime.now(timezone.utc).isoformat()
                },
                user_id,
                session_id
            )
            await websocket.send_text(json.dumps(sync_message.to_dict()))
            
            # Broadcast sync update to other devices
            await broadcast_to_user_devices(user_id, sync_message, exclude_device=device_id)
            
        elif message_data.get("type") == "conflict_resolution":
            # Handle sync conflicts in real-time
            conflicts = message_data.get("conflicts", [])
            resolution_strategy = message_data.get("resolution_strategy", "timestamp_based")
            
            resolution_result = await realtime_updater.resolve_sync_conflicts(
                user_id, conflicts, resolution_strategy
            )
            
            resolution_message = WebSocketMessage(
                MessageType.CONFLICT_DETECTED,
                {
                    "status": "resolved",
                    "resolution_result": resolution_result,
                    "conflicts_count": len(conflicts)
                },
                user_id,
                session_id
            )
            await websocket.send_text(json.dumps(resolution_message.to_dict()))
            
    except Exception as e:
        logger.error(f"Error handling sync operation: {str(e)}")
        error_message = WebSocketMessage(
            MessageType.ERROR,
            {
                "error": "Failed to process sync operation",
                "details": str(e),
                "request_id": message_data.get("request_id")
            },
            user_id,
            session_id
        )
        await websocket.send_text(json.dumps(error_message.to_dict()))

@router.websocket("/tutoring")
async def websocket_tutoring_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="Authentication token"),
    device_id: str = Query(..., description="Device identifier"),
    session_id: Optional[str] = Query(None, description="Tutoring session ID")
):
    """
    WebSocket endpoint for real-time tutoring sessions
    Requirement 2.1: Real-time updates across platforms
    Requirement 2.3: Maintain session continuity
    Requirement 4.1: Real-time progress tracking
    """
    # Validate user authentication
    user_id = await get_user_from_websocket_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Authentication failed")
        return
    
    # Accept WebSocket connection
    await websocket.accept()
    
    # Register connection
    device_info = {
        "device_id": device_id,
        "device_type": "websocket",
        "session_id": session_id or str(uuid.uuid4()),
        "connected_at": datetime.now(timezone.utc).isoformat()
    }
    
    connection_registered = await connection_manager.register_connection(
        websocket, user_id, device_id, device_info
    )
    
    if not connection_registered:
        await websocket.close(code=4002, reason="Failed to register connection")
        return
    
    logger.info(f"WebSocket tutoring connection established for user {user_id}, device {device_id}")
    
    try:
        # Send welcome message
        welcome_message = WebSocketMessage(
            MessageType.USER_JOINED,
            {
                "message": "Connected to tutoring session",
                "user_id": user_id,
                "session_id": session_id,
                "capabilities": [
                    "real_time_tutoring",
                    "progress_updates",
                    "device_sync",
                    "notifications"
                ]
            },
            user_id,
            session_id
        )
        await websocket.send_text(json.dumps(welcome_message.to_dict()))
        
        # Message handling loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                message_type = message_data.get("message_type")
                
                # Handle different message types
                if message_type in [MessageType.TUTOR_QUESTION, MessageType.CONCEPT_EXPLANATION]:
                    await handle_tutor_interaction(websocket, message_data, user_id, session_id)
                
                elif message_type in [MessageType.ACTIVITY_COMPLETED, MessageType.PROGRESS_UPDATE]:
                    await handle_progress_update(websocket, message_data, user_id, session_id)
                
                elif message_type in [MessageType.DATA_SYNC, MessageType.DEVICE_SYNC]:
                    await handle_sync_operation(websocket, message_data, user_id, session_id)
                
                elif message_type == MessageType.HEARTBEAT:
                    # Respond to heartbeat
                    heartbeat_response = WebSocketMessage(
                        MessageType.HEARTBEAT,
                        {
                            "status": "alive",
                            "server_time": datetime.now(timezone.utc).isoformat()
                        },
                        user_id,
                        session_id
                    )
                    await websocket.send_text(json.dumps(heartbeat_response.to_dict()))
                
                else:
                    # Unknown message type
                    error_message = WebSocketMessage(
                        MessageType.ERROR,
                        {
                            "error": f"Unknown message type: {message_type}",
                            "received_message": message_data
                        },
                        user_id,
                        session_id
                    )
                    await websocket.send_text(json.dumps(error_message.to_dict()))
                
            except json.JSONDecodeError:
                error_message = WebSocketMessage(
                    MessageType.ERROR,
                    {"error": "Invalid JSON format"},
                    user_id,
                    session_id
                )
                await websocket.send_text(json.dumps(error_message.to_dict()))
            
            except Exception as e:
                logger.error(f"Error processing WebSocket message: {str(e)}")
                error_message = WebSocketMessage(
                    MessageType.ERROR,
                    {
                        "error": "Failed to process message",
                        "details": str(e)
                    },
                    user_id,
                    session_id
                )
                await websocket.send_text(json.dumps(error_message.to_dict()))
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket tutoring connection closed for user {user_id}, device {device_id}")
    
    except Exception as e:
        logger.error(f"Unexpected error in WebSocket tutoring connection: {str(e)}")
    
    finally:
        # Unregister connection
        await connection_manager.unregister_connection(device_id)
        
        # Send disconnect notification to other devices
        disconnect_message = WebSocketMessage(
            MessageType.USER_LEFT,
            {
                "user_id": user_id,
                "device_id": device_id,
                "session_id": session_id,
                "disconnected_at": datetime.now(timezone.utc).isoformat()
            },
            user_id,
            session_id
        )
        await broadcast_to_user_devices(user_id, disconnect_message, exclude_device=device_id)

@router.websocket("/progress")
async def websocket_progress_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="Authentication token"),
    device_id: str = Query(..., description="Device identifier"),
    child_id: Optional[str] = Query(None, description="Child ID for parent connections")
):
    """
    WebSocket endpoint for real-time progress updates
    Requirement 4.1: Real-time progress tracking and notifications
    """
    # Validate user authentication
    user_id = await get_user_from_websocket_token(token)
    if not user_id:
        await websocket.close(code=4001, reason="Authentication failed")
        return
    
    await websocket.accept()
    
    # Register connection for progress updates
    device_info = {
        "device_id": device_id,
        "device_type": "progress_monitor",
        "child_id": child_id,
        "connected_at": datetime.now(timezone.utc).isoformat()
    }
    
    connection_registered = await connection_manager.register_connection(
        websocket, user_id, device_id, device_info
    )
    
    if not connection_registered:
        await websocket.close(code=4002, reason="Failed to register connection")
        return
    
    logger.info(f"WebSocket progress connection established for user {user_id}, device {device_id}")
    
    try:
        # Send welcome message with current progress
        from ..api import db
        progress_service = ProgressReportingService(db)
        
        current_progress = await progress_service.get_real_time_progress(
            child_id or user_id, "daily"
        )
        
        welcome_message = WebSocketMessage(
            MessageType.PROGRESS_UPDATE,
            {
                "message": "Connected to progress updates",
                "current_progress": current_progress,
                "monitoring": child_id or user_id
            },
            user_id
        )
        await websocket.send_text(json.dumps(welcome_message.to_dict()))
        
        # Keep connection alive and handle progress update requests
        while True:
            try:
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                if message_data.get("message_type") == "progress_request":
                    timeframe = message_data.get("timeframe", "daily")
                    target_user = child_id or user_id
                    
                    progress_data = await progress_service.get_real_time_progress(
                        target_user, timeframe
                    )
                    
                    progress_message = WebSocketMessage(
                        MessageType.PROGRESS_UPDATE,
                        {
                            "progress_data": progress_data,
                            "timeframe": timeframe,
                            "request_id": message_data.get("request_id")
                        },
                        user_id
                    )
                    await websocket.send_text(json.dumps(progress_message.to_dict()))
                
            except json.JSONDecodeError:
                continue
            except Exception as e:
                logger.error(f"Error in progress WebSocket: {str(e)}")
                break
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket progress connection closed for user {user_id}")
    
    finally:
        await connection_manager.unregister_connection(device_id)

# Background task for sending periodic updates
async def send_periodic_updates():
    """Send periodic updates to connected clients"""
    while True:
        try:
            # Send heartbeat to all connections
            await connection_manager.broadcast_heartbeat()
            
            # Send progress updates to parent connections
            await connection_manager.send_progress_updates()
            
            # Wait 30 seconds before next update cycle
            await asyncio.sleep(30)
            
        except Exception as e:
            logger.error(f"Error in periodic updates: {str(e)}")
            await asyncio.sleep(10)

# Note: Background task should be started in FastAPI startup event, not at module level
# asyncio.create_task(send_periodic_updates())
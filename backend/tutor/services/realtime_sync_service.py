"""
Real-time Synchronization Service - WebSocket and Redis integration for live updates
Task 8.1 implementation
"""
import asyncio
import json
import time
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timezone, timedelta
import redis.asyncio as redis
import websockets
from websockets.server import WebSocketServerProtocol
from collections import defaultdict

from utils.logger import logger
from services.supabase import DBConnection
from ..models.sync_models import (
    RealtimeUpdate,
    SyncStatus,
    DataType,
    DeviceInfo,
    SyncConfiguration
)


class WebSocketConnectionManager:
    """
    Manages WebSocket connections for real-time updates
    """
    
    def __init__(self):
        # Connection tracking
        self.connections: Dict[str, WebSocketServerProtocol] = {}  # device_id -> websocket
        self.user_devices: Dict[str, Set[str]] = defaultdict(set)  # user_id -> device_ids
        self.device_users: Dict[str, str] = {}  # device_id -> user_id
        
        # Connection metadata
        self.connection_info: Dict[str, Dict[str, Any]] = {}  # device_id -> info
        self.heartbeat_tasks: Dict[str, asyncio.Task] = {}  # device_id -> heartbeat task
        
        # Statistics
        self.connection_stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "connection_errors": 0
        }
    
    async def register_connection(self, websocket: WebSocketServerProtocol, 
                                user_id: str, device_id: str, device_info: Dict[str, Any]) -> bool:
        """
        Register a new WebSocket connection
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
            device_id: Device ID
            device_info: Device information
            
        Returns:
            True if successfully registered
        """
        try:
            # Close existing connection for this device if any
            await self._close_existing_connection(device_id)
            
            # Register new connection
            self.connections[device_id] = websocket
            self.user_devices[user_id].add(device_id)
            self.device_users[device_id] = user_id
            
            # Store connection info
            self.connection_info[device_id] = {
                "user_id": user_id,
                "device_info": device_info,
                "connected_at": datetime.now(timezone.utc),
                "last_heartbeat": datetime.now(timezone.utc),
                "message_count": 0
            }
            
            # Start heartbeat monitoring
            self.heartbeat_tasks[device_id] = asyncio.create_task(
                self._monitor_heartbeat(device_id)
            )
            
            # Update statistics
            self.connection_stats["total_connections"] += 1
            self.connection_stats["active_connections"] += 1
            
            logger.info(f"Registered WebSocket connection for user {user_id}, device {device_id}")
            
            # Send welcome message
            await self.send_message(device_id, {
                "type": "welcome",
                "user_id": user_id,
                "device_id": device_id,
                "server_time": datetime.now(timezone.utc).isoformat()
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Error registering WebSocket connection: {str(e)}")
            self.connection_stats["connection_errors"] += 1
            return False
    
    async def unregister_connection(self, device_id: str) -> None:
        """Unregister a WebSocket connection"""
        try:
            if device_id in self.connections:
                # Get user ID before removing
                user_id = self.device_users.get(device_id)
                
                # Close WebSocket connection
                websocket = self.connections[device_id]
                if not websocket.closed:
                    await websocket.close()
                
                # Remove from tracking
                del self.connections[device_id]
                if device_id in self.device_users:
                    del self.device_users[device_id]
                if user_id and device_id in self.user_devices[user_id]:
                    self.user_devices[user_id].remove(device_id)
                    if not self.user_devices[user_id]:  # No more devices for user
                        del self.user_devices[user_id]
                
                # Remove connection info
                if device_id in self.connection_info:
                    del self.connection_info[device_id]
                
                # Cancel heartbeat task
                if device_id in self.heartbeat_tasks:
                    self.heartbeat_tasks[device_id].cancel()
                    del self.heartbeat_tasks[device_id]
                
                # Update statistics
                self.connection_stats["active_connections"] -= 1
                
                logger.info(f"Unregistered WebSocket connection for device {device_id}")
                
        except Exception as e:
            logger.error(f"Error unregistering connection: {str(e)}")
    
    async def send_message(self, device_id: str, message: Dict[str, Any]) -> bool:
        """Send a message to a specific device"""
        try:
            if device_id not in self.connections:
                return False
            
            websocket = self.connections[device_id]
            if websocket.closed:
                await self.unregister_connection(device_id)
                return False
            
            # Add timestamp and message ID
            message["timestamp"] = datetime.now(timezone.utc).isoformat()
            message["message_id"] = f"msg_{int(time.time() * 1000)}"
            
            # Send message
            await websocket.send(json.dumps(message))
            
            # Update statistics
            self.connection_stats["messages_sent"] += 1
            if device_id in self.connection_info:
                self.connection_info[device_id]["message_count"] += 1
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending message to device {device_id}: {str(e)}")
            await self.unregister_connection(device_id)
            return False
    
    async def broadcast_to_user(self, user_id: str, message: Dict[str, Any], 
                              exclude_devices: List[str] = None) -> int:
        """
        Broadcast a message to all devices for a user
        
        Args:
            user_id: User ID to broadcast to
            message: Message to send
            exclude_devices: Device IDs to exclude from broadcast
            
        Returns:
            Number of devices message was sent to
        """
        exclude_devices = exclude_devices or []
        sent_count = 0
        
        if user_id in self.user_devices:
            for device_id in self.user_devices[user_id]:
                if device_id not in exclude_devices:
                    success = await self.send_message(device_id, message)
                    if success:
                        sent_count += 1
        
        return sent_count
    
    async def get_user_devices(self, user_id: str) -> List[str]:
        """Get list of connected devices for a user"""
        return list(self.user_devices.get(user_id, set()))
    
    async def is_device_connected(self, device_id: str) -> bool:
        """Check if a device is connected"""
        return device_id in self.connections and not self.connections[device_id].closed
    
    async def get_connection_stats(self) -> Dict[str, Any]:
        """Get connection statistics"""
        stats = self.connection_stats.copy()
        stats["devices_by_user"] = {user_id: len(devices) for user_id, devices in self.user_devices.items()}
        stats["uptime_by_device"] = {}
        
        for device_id, info in self.connection_info.items():
            uptime_seconds = (datetime.now(timezone.utc) - info["connected_at"]).total_seconds()
            stats["uptime_by_device"][device_id] = uptime_seconds
        
        return stats
    
    async def _close_existing_connection(self, device_id: str) -> None:
        """Close existing connection for device"""
        if device_id in self.connections:
            try:
                websocket = self.connections[device_id]
                if not websocket.closed:
                    await websocket.close()
                await self.unregister_connection(device_id)
            except Exception as e:
                logger.warning(f"Error closing existing connection: {str(e)}")
    
    async def _monitor_heartbeat(self, device_id: str) -> None:
        """Monitor heartbeat for a device connection"""
        try:
            while device_id in self.connections:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                if device_id not in self.connection_info:
                    break
                
                last_heartbeat = self.connection_info[device_id]["last_heartbeat"]
                time_since_heartbeat = (datetime.now(timezone.utc) - last_heartbeat).total_seconds()
                
                if time_since_heartbeat > 90:  # 90 seconds timeout
                    logger.warning(f"Heartbeat timeout for device {device_id}")
                    await self.unregister_connection(device_id)
                    break
                
                # Send ping
                await self.send_message(device_id, {"type": "ping"})
                
        except asyncio.CancelledError:
            # Task was cancelled, connection is being closed
            pass
        except Exception as e:
            logger.error(f"Error in heartbeat monitoring: {str(e)}")
    
    async def handle_heartbeat(self, device_id: str) -> None:
        """Handle heartbeat from device"""
        if device_id in self.connection_info:
            self.connection_info[device_id]["last_heartbeat"] = datetime.now(timezone.utc)


class RealtimeSyncService:
    """
    Real-time synchronization service using WebSockets and Redis
    """
    
    def __init__(self, db: DBConnection, redis_url: str = "redis://localhost:6379"):
        self.db = db
        
        # Initialize Redis for pub/sub
        self.redis = redis.from_url(redis_url, decode_responses=True)
        self.redis_pubsub = self.redis.pubsub()
        
        # WebSocket connection manager
        self.connection_manager = WebSocketConnectionManager()
        
        # Subscription tracking
        self.subscriptions: Dict[str, Set[str]] = defaultdict(set)  # channel -> device_ids
        
        # Message queues for offline devices
        self.offline_queues: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        
        # Background tasks
        self.pubsub_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self) -> None:
        """Start the real-time sync service"""
        try:
            # Start Redis pub/sub listener
            self.pubsub_task = asyncio.create_task(self._listen_to_redis())
            
            # Start cleanup task
            self.cleanup_task = asyncio.create_task(self._cleanup_offline_queues())
            
            logger.info("Real-time sync service started")
            
        except Exception as e:
            logger.error(f"Error starting real-time sync service: {str(e)}")
            raise
    
    async def stop(self) -> None:
        """Stop the real-time sync service"""
        try:
            # Cancel background tasks
            if self.pubsub_task:
                self.pubsub_task.cancel()
            if self.cleanup_task:
                self.cleanup_task.cancel()
            
            # Close Redis connections
            await self.redis_pubsub.close()
            await self.redis.close()
            
            logger.info("Real-time sync service stopped")
            
        except Exception as e:
            logger.error(f"Error stopping real-time sync service: {str(e)}")
    
    async def handle_websocket_connection(self, websocket: WebSocketServerProtocol, 
                                        user_id: str, device_id: str, 
                                        device_info: Dict[str, Any]) -> None:
        """
        Handle a new WebSocket connection
        
        Args:
            websocket: WebSocket connection
            user_id: User ID
            device_id: Device ID
            device_info: Device information
        """
        try:
            # Register connection
            success = await self.connection_manager.register_connection(
                websocket, user_id, device_id, device_info
            )
            
            if not success:
                await websocket.close()
                return
            
            # Subscribe to user channels
            await self._subscribe_device_to_channels(user_id, device_id)
            
            # Send any queued offline messages
            await self._send_offline_messages(device_id)
            
            # Handle incoming messages
            async for message in websocket:
                try:
                    await self._handle_websocket_message(device_id, message)
                except Exception as e:
                    logger.error(f"Error handling WebSocket message: {str(e)}")
            
        except Exception as e:
            logger.error(f"Error in WebSocket connection handler: {str(e)}")
        finally:
            # Unregister connection
            await self.connection_manager.unregister_connection(device_id)
            await self._unsubscribe_device_from_channels(device_id)
    
    async def publish_update(self, update: RealtimeUpdate) -> bool:
        """
        Publish a real-time update
        
        Args:
            update: The update to publish
            
        Returns:
            True if successfully published
        """
        try:
            # Publish to Redis channels
            channels = [
                f"user:{update.user_id}",
                f"global:updates"
            ]
            
            update_data = update.json()
            
            for channel in channels:
                await self.redis.publish(channel, update_data)
            
            # Send directly to connected devices
            if update.target_devices:
                # Send to specific devices
                for device_id in update.target_devices:
                    if device_id not in update.exclude_devices:
                        await self._send_update_to_device(device_id, update)
            else:
                # Broadcast to all user devices
                device_ids = await self.connection_manager.get_user_devices(update.user_id)
                for device_id in device_ids:
                    if device_id not in update.exclude_devices:
                        await self._send_update_to_device(device_id, update)
            
            logger.debug(f"Published update {update.update_id} for user {update.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error publishing update: {str(e)}")
            return False
    
    async def notify_data_change(self, user_id: str, data_type: DataType, 
                               data_id: str, operation: str, 
                               data_payload: Dict[str, Any] = None,
                               source_device: str = None) -> None:
        """
        Notify about a data change
        
        Args:
            user_id: User ID
            data_type: Type of data that changed
            data_id: ID of changed data
            operation: Operation performed (create, update, delete)
            data_payload: Changed data (optional)
            source_device: Device that made the change (optional)
        """
        update = RealtimeUpdate(
            user_id=user_id,
            update_type="data_change",
            data_type=data_type,
            data_id=data_id,
            data_payload={
                "operation": operation,
                "data": data_payload or {}
            },
            source_device=source_device,
            exclude_devices=[source_device] if source_device else [],
            priority=7  # High priority for data changes
        )
        
        await self.publish_update(update)
    
    async def notify_sync_progress(self, user_id: str, device_id: str, 
                                 progress: Dict[str, Any]) -> None:
        """Notify about sync progress"""
        update = RealtimeUpdate(
            user_id=user_id,
            update_type="sync_progress",
            data_payload=progress,
            source_device=device_id,
            priority=6
        )
        
        await self.publish_update(update)
    
    async def request_device_sync(self, user_id: str, requesting_device: str,
                                target_devices: List[str] = None) -> None:
        """Request other devices to sync"""
        update = RealtimeUpdate(
            user_id=user_id,
            update_type="sync_request",
            data_payload={
                "requesting_device": requesting_device,
                "timestamp": datetime.now(timezone.utc).isoformat()
            },
            source_device=requesting_device,
            target_devices=target_devices or [],
            exclude_devices=[requesting_device],
            priority=8
        )
        
        await self.publish_update(update)
    
    # Private helper methods
    
    async def _listen_to_redis(self) -> None:
        """Listen to Redis pub/sub messages"""
        try:
            # Subscribe to global update channel
            await self.redis_pubsub.subscribe("global:updates")
            
            async for message in self.redis_pubsub.listen():
                if message["type"] == "message":
                    try:
                        update_data = json.loads(message["data"])
                        update = RealtimeUpdate.parse_obj(update_data)
                        
                        # Route to appropriate devices
                        await self._route_update_to_devices(update)
                        
                    except Exception as e:
                        logger.error(f"Error processing Redis message: {str(e)}")
                        
        except asyncio.CancelledError:
            # Task was cancelled
            pass
        except Exception as e:
            logger.error(f"Error in Redis pub/sub listener: {str(e)}")
    
    async def _route_update_to_devices(self, update: RealtimeUpdate) -> None:
        """Route update to appropriate devices"""
        try:
            if update.target_devices:
                # Send to specific devices
                for device_id in update.target_devices:
                    if device_id not in update.exclude_devices:
                        await self._send_update_to_device(device_id, update)
            else:
                # Send to all devices for the user
                device_ids = await self.connection_manager.get_user_devices(update.user_id)
                for device_id in device_ids:
                    if device_id not in update.exclude_devices:
                        await self._send_update_to_device(device_id, update)
                        
        except Exception as e:
            logger.error(f"Error routing update to devices: {str(e)}")
    
    async def _send_update_to_device(self, device_id: str, update: RealtimeUpdate) -> None:
        """Send update to a specific device"""
        try:
            is_connected = await self.connection_manager.is_device_connected(device_id)
            
            if is_connected:
                # Send directly via WebSocket
                message = {
                    "type": "realtime_update",
                    "update_id": update.update_id,
                    "update_type": update.update_type,
                    "data_type": update.data_type.value if update.data_type else None,
                    "data_id": update.data_id,
                    "data_payload": update.data_payload,
                    "priority": update.priority,
                    "source_device": update.source_device
                }
                
                await self.connection_manager.send_message(device_id, message)
            else:
                # Queue for offline device
                await self._queue_message_for_offline_device(device_id, update)
                
        except Exception as e:
            logger.error(f"Error sending update to device {device_id}: {str(e)}")
    
    async def _queue_message_for_offline_device(self, device_id: str, update: RealtimeUpdate) -> None:
        """Queue message for offline device"""
        try:
            # Don't queue if expired
            if update.is_expired():
                return
            
            message = {
                "type": "realtime_update",
                "update_id": update.update_id,
                "update_type": update.update_type,
                "data_type": update.data_type.value if update.data_type else None,
                "data_id": update.data_id,
                "data_payload": update.data_payload,
                "priority": update.priority,
                "source_device": update.source_device,
                "queued_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Add to offline queue (limit size)
            self.offline_queues[device_id].append(message)
            
            # Keep only last 50 messages per device
            if len(self.offline_queues[device_id]) > 50:
                self.offline_queues[device_id] = self.offline_queues[device_id][-50:]
            
        except Exception as e:
            logger.error(f"Error queuing message for offline device: {str(e)}")
    
    async def _send_offline_messages(self, device_id: str) -> None:
        """Send queued messages to device that just came online"""
        try:
            if device_id in self.offline_queues:
                messages = self.offline_queues[device_id]
                
                for message in messages:
                    await self.connection_manager.send_message(device_id, message)
                
                # Clear queue
                del self.offline_queues[device_id]
                
                logger.info(f"Sent {len(messages)} offline messages to device {device_id}")
                
        except Exception as e:
            logger.error(f"Error sending offline messages: {str(e)}")
    
    async def _handle_websocket_message(self, device_id: str, message: str) -> None:
        """Handle incoming WebSocket message from device"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "pong":
                # Handle heartbeat response
                await self.connection_manager.handle_heartbeat(device_id)
                
            elif message_type == "sync_request":
                # Handle sync request
                user_id = self.connection_manager.device_users.get(device_id)
                if user_id:
                    await self.request_device_sync(user_id, device_id)
                    
            elif message_type == "data_change":
                # Handle data change notification
                user_id = self.connection_manager.device_users.get(device_id)
                if user_id:
                    await self.notify_data_change(
                        user_id=user_id,
                        data_type=DataType(data.get("data_type")),
                        data_id=data.get("data_id"),
                        operation=data.get("operation"),
                        data_payload=data.get("data_payload"),
                        source_device=device_id
                    )
            
            # Update message statistics
            self.connection_manager.connection_stats["messages_received"] += 1
            
        except Exception as e:
            logger.error(f"Error handling WebSocket message from {device_id}: {str(e)}")
    
    async def _subscribe_device_to_channels(self, user_id: str, device_id: str) -> None:
        """Subscribe device to relevant Redis channels"""
        try:
            channels = [
                f"user:{user_id}",
                f"device:{device_id}"
            ]
            
            for channel in channels:
                self.subscriptions[channel].add(device_id)
                # Subscribe to Redis channel if first device for this channel
                if len(self.subscriptions[channel]) == 1:
                    await self.redis_pubsub.subscribe(channel)
            
        except Exception as e:
            logger.error(f"Error subscribing device to channels: {str(e)}")
    
    async def _unsubscribe_device_from_channels(self, device_id: str) -> None:
        """Unsubscribe device from Redis channels"""
        try:
            channels_to_unsubscribe = []
            
            for channel, devices in self.subscriptions.items():
                if device_id in devices:
                    devices.remove(device_id)
                    # Unsubscribe from Redis if no more devices for this channel
                    if not devices:
                        channels_to_unsubscribe.append(channel)
            
            for channel in channels_to_unsubscribe:
                await self.redis_pubsub.unsubscribe(channel)
                del self.subscriptions[channel]
            
        except Exception as e:
            logger.error(f"Error unsubscribing device from channels: {str(e)}")
    
    async def _cleanup_offline_queues(self) -> None:
        """Periodically clean up expired offline message queues"""
        try:
            while True:
                await asyncio.sleep(300)  # Clean up every 5 minutes
                
                current_time = datetime.now(timezone.utc)
                devices_to_remove = []
                
                for device_id, messages in self.offline_queues.items():
                    # Remove expired messages
                    valid_messages = []
                    for message in messages:
                        try:
                            queued_at = datetime.fromisoformat(message["queued_at"].replace('Z', '+00:00'))
                            if (current_time - queued_at).total_seconds() < 24 * 60 * 60:  # 24 hours
                                valid_messages.append(message)
                        except Exception:
                            # Skip invalid messages
                            continue
                    
                    if valid_messages:
                        self.offline_queues[device_id] = valid_messages
                    else:
                        devices_to_remove.append(device_id)
                
                # Remove empty queues
                for device_id in devices_to_remove:
                    del self.offline_queues[device_id]
                
                if devices_to_remove:
                    logger.info(f"Cleaned up offline queues for {len(devices_to_remove)} devices")
                    
        except asyncio.CancelledError:
            # Task was cancelled
            pass
        except Exception as e:
            logger.error(f"Error in offline queue cleanup: {str(e)}")
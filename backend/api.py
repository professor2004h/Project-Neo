from fastapi import FastAPI, Request, HTTPException, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
import sentry # Keep this import here, right after fastapi imports
from contextlib import asynccontextmanager
from agentpress.thread_manager import ThreadManager
from services.supabase import DBConnection
from datetime import datetime, timezone
from dotenv import load_dotenv
from utils.config import config, EnvMode
import asyncio
from utils.logger import logger, structlog
import time
import os
from collections import OrderedDict
from typing import Dict, Any

from pydantic import BaseModel
import uuid
# Import the agent API module
from agent import api as agent_api
from sandbox import api as sandbox_api
from services import billing as billing_api
from flags import api as feature_flags_api
from services import transcription as transcription_api
from services.mcp_custom import discover_custom_tools
import sys
from services import email_api


load_dotenv()

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Initialize managers
db = DBConnection()
instance_id = "single"

# Rate limiter state
ip_tracker = OrderedDict()
MAX_CONCURRENT_IPS = 25

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting up FastAPI application with instance ID: {instance_id} in {config.ENV_MODE.value} mode")
    try:
        await db.initialize()
        
        agent_api.initialize(
            db,
            instance_id
        )
        
        sandbox_api.initialize(db)
        
        # Initialize Redis connection
        from services import redis
        try:
            await redis.initialize_async()
            logger.info("Redis connection initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            # Continue without Redis - the application will handle Redis failures gracefully
        
        # Start background tasks
        # asyncio.create_task(agent_api.restore_running_agent_runs())
        
        yield
        
        # Clean up agent resources
        logger.info("Cleaning up agent resources")
        await agent_api.cleanup()
        
        # Clean up Redis connection
        try:
            logger.info("Closing Redis connection")
            await redis.close()
            logger.info("Redis connection closed successfully")
        except Exception as e:
            logger.error(f"Error closing Redis connection: {e}")
        
        # Clean up database connection
        logger.info("Disconnecting from database")
        await db.disconnect()
    except Exception as e:
        logger.error(f"Error during application startup: {e}")
        raise

app = FastAPI(lifespan=lifespan)

@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    structlog.contextvars.clear_contextvars()

    request_id = str(uuid.uuid4())
    start_time = time.time()
    client_ip = request.client.host
    method = request.method
    path = request.url.path
    query_params = str(request.query_params)

    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        client_ip=client_ip,
        method=method,
        path=path,
        query_params=query_params
    )

    # Log the incoming request
    logger.info(f"Request started: {method} {path} from {client_ip} | Query: {query_params}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.debug(f"Request completed: {method} {path} | Status: {response.status_code} | Time: {process_time:.2f}s")
        return response
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"Request failed: {method} {path} | Error: {str(e)} | Time: {process_time:.2f}s")
        raise

# Define allowed origins based on environment
allowed_origins = [ "http://localhost:3000", "https://operator.becomeomni.com", "https://operator.staging.becomeomni.com", "https://dev1.operator.becomeomni.com", "https://huston.becomeomni.net", "https://mssc.becomeomni.net","https://coldchain.becomeomni.net"]
allow_origin_regex = None

# Add staging-specific origins
if config.ENV_MODE == EnvMode.STAGING:
    allowed_origins.append("https://staging.suna.so")
    allow_origin_regex = r"https://suna-.*-prjcts\.vercel\.app"

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=allow_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(agent_api.router, prefix="/api")

app.include_router(sandbox_api.router, prefix="/api")

app.include_router(billing_api.router, prefix="/api")

app.include_router(feature_flags_api.router, prefix="/api")

from mcp_local import api as mcp_api

app.include_router(mcp_api.router, prefix="/api")


app.include_router(transcription_api.router, prefix="/api")

app.include_router(email_api.router, prefix="/api")

@app.get("/api/health")
async def health_check():
    """Health check endpoint to verify API is working."""
    logger.info("Health check endpoint called")
    return {
        "status": "ok", 
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "instance_id": instance_id
    }

class CustomMCPDiscoverRequest(BaseModel):
    type: str
    config: Dict[str, Any]


@app.post("/api/mcp/discover-custom-tools")
async def discover_custom_mcp_tools(request: CustomMCPDiscoverRequest):
    try:
        return await discover_custom_tools(request.type, request.config)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error discovering custom MCP tools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# SSE connections storage for real-time updates
active_sse_connections = {}

async def broadcast_bot_update(bot_id: str, session_data: dict):
    """Broadcast bot status update to connected SSE clients"""
    import json
    message = f"data: {json.dumps({'bot_id': bot_id, **session_data})}\n\n"
    
    # Send to all connected clients for this bot
    if bot_id in active_sse_connections:
        disconnected = []
        for queue in active_sse_connections[bot_id]:
            try:
                await queue.put(message)
            except:
                disconnected.append(queue)
        
        # Clean up disconnected clients
        for queue in disconnected:
            active_sse_connections[bot_id].remove(queue)

@app.get("/api/meeting-bot/{bot_id}/events")
async def bot_status_events(bot_id: str):
    """Server-Sent Events stream for real-time bot status updates"""
    import asyncio
    from fastapi.responses import StreamingResponse
    
    async def event_publisher():
        queue = asyncio.Queue()
        
        # Add this client to active connections
        if bot_id not in active_sse_connections:
            active_sse_connections[bot_id] = []
        active_sse_connections[bot_id].append(queue)
        
        try:
            # Send initial status
            yield "data: {\"type\": \"connected\"}\n\n"
            
            # Stream real-time updates
            while True:
                try:
                    message = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield message
                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    yield "data: {\"type\": \"heartbeat\"}\n\n"
                    
        except Exception as e:
            print(f"[SSE] Client disconnected: {e}")
        finally:
            # Clean up connection
            if bot_id in active_sse_connections:
                if queue in active_sse_connections[bot_id]:
                    active_sse_connections[bot_id].remove(queue)
                if not active_sse_connections[bot_id]:
                    del active_sse_connections[bot_id]
    
    return StreamingResponse(
        event_publisher(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

# Meeting Bot Management Endpoints
@app.post("/api/meeting-bot/start")
async def start_meeting_bot(request: Request):
    """Start a meeting bot for the given URL"""
    try:
        logger.info("[MEETING BOT] Starting meeting bot request")
        
        data = await request.json()
        meeting_url = data.get('meeting_url')
        sandbox_id = data.get('sandbox_id')
        
        logger.info(f"[MEETING BOT] Request data: meeting_url={meeting_url}, sandbox_id={sandbox_id}")
        
        if not meeting_url:
            logger.error("[MEETING BOT] Missing meeting_url in request")
            return JSONResponse({"error": "meeting_url is required"}, status_code=400)
        
        # Check API key exists
        api_key = os.getenv('MEETINGBAAS_API_KEY')
        if not api_key:
            logger.error("[MEETING BOT] MEETINGBAAS_API_KEY environment variable not set")
            return JSONResponse({"error": "MeetingBaaS API key not configured"}, status_code=500)
        
        logger.info(f"[MEETING BOT] API key configured (first 10 chars): {api_key[:10]}...")
            
        # Import the tool
        try:
            from agent.tools.meeting_bot_tool import MeetingBotTool
            logger.info("[MEETING BOT] Successfully imported MeetingBotTool")
        except Exception as import_error:
            logger.error(f"[MEETING BOT] Failed to import MeetingBotTool: {str(import_error)}")
            return JSONResponse({"error": f"Failed to import tool: {str(import_error)}"}, status_code=500)
        
        try:
            tool = MeetingBotTool()
            logger.info("[MEETING BOT] Successfully initialized MeetingBotTool")
        except Exception as init_error:
            logger.error(f"[MEETING BOT] Failed to initialize MeetingBotTool: {str(init_error)}")
            return JSONResponse({"error": f"Failed to initialize tool: {str(init_error)}"}, status_code=500)
        
        # Start the bot with webhook URL for real-time updates
        webhook_url = f"{request.base_url}api/meeting-bot/webhook"
        logger.info(f"[MEETING BOT] Using webhook URL: {webhook_url}")
        
        try:
            result = await tool.start_meeting_bot(meeting_url, "AI Transcription Bot", webhook_url)
            logger.info(f"[MEETING BOT] Tool result: {result}")
        except Exception as tool_error:
            logger.error(f"[MEETING BOT] Tool execution failed: {str(tool_error)}")
            return JSONResponse({"error": f"Failed to start bot: {str(tool_error)}"}, status_code=500)
        
        if result.get('success'):
            bot_id = result['bot_id']
            
            # Store bot session for persistence
            bot_session = {
                'bot_id': bot_id,
                'meeting_url': meeting_url,
                'sandbox_id': sandbox_id,
                'status': 'joining',
                'started_at': time.time(),
                'last_updated': time.time()
            }
            
            # Store in simple file-based persistence (production would use Redis/DB)
            import json
            import os
            
            sessions_dir = '/tmp/meeting_bot_sessions'
            os.makedirs(sessions_dir, exist_ok=True)
            
            with open(f'{sessions_dir}/{bot_id}.json', 'w') as f:
                json.dump(bot_session, f)
            
            return JSONResponse({
                "success": True,
                "bot_id": bot_id,
                "status": "joining",
                "message": "Bot is joining the meeting..."
            })
        else:
            return JSONResponse({"error": result.get('error')}, status_code=400)
            
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/meeting-bot/{bot_id}/status")
async def get_meeting_bot_status(bot_id: str):
    """Get current status of a meeting bot"""
    try:
        from agent.tools.meeting_bot_tool import MeetingBotTool
        tool = MeetingBotTool()
        
        # Get live status from API
        result = await tool.get_bot_status(bot_id)
        
        if result.get('success'):
            status = result.get('status')
            
            # Update stored session
            import json
            sessions_dir = '/tmp/meeting_bot_sessions'
            session_file = f'{sessions_dir}/{bot_id}.json'
            
            if os.path.exists(session_file):
                with open(session_file, 'r') as f:
                    session = json.load(f)
                
                session['status'] = status
                session['last_updated'] = time.time()
                
                with open(session_file, 'w') as f:
                    json.dump(session, f)
            
            return JSONResponse({
                "success": True,
                "status": status,
                "transcript": result.get('transcript', ''),
                "participants": result.get('participants', []),
                "duration": result.get('duration', 0)
            })
        else:
            return JSONResponse({"error": result.get('error')}, status_code=400)
            
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/meeting-bot/{bot_id}/stop")
async def stop_meeting_bot(bot_id: str, request: Request):
    """Stop meeting bot and get final transcript"""
    try:
        data = await request.json()
        sandbox_id = data.get('sandbox_id')
        
        from agent.tools.meeting_bot_tool import MeetingBotTool
        tool = MeetingBotTool()
        
        # Stop the bot and get final transcript
        result = await tool.stop_meeting_bot(bot_id)
        
        if result.get('success'):
            transcript = result.get('transcript', '')
            
            if transcript:
                # Create transcript file
                import tempfile
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"meeting_transcript_{timestamp}.txt"
                
                # Format the transcript nicely
                content = f"Meeting Transcript\n"
                content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
                content += f"Duration: {result.get('duration', 0) // 60}m {result.get('duration', 0) % 60}s\n"
                content += f"Participants: {', '.join(result.get('participants', []))}\n\n"
                
                if result.get('summary'):
                    content += f"Summary:\n{result.get('summary')}\n\n"
                
                if result.get('action_items'):
                    content += f"Action Items:\n"
                    for item in result.get('action_items', []):
                        content += f"• {item}\n"
                    content += "\n"
                
                content += f"Full Transcript:\n{transcript}"
                
                # Save to sandbox files
                if sandbox_id:
                    # This would integrate with your existing file upload system
                    # For now, return the content to be handled by frontend
                    pass
                
                # Clean up session
                import os
                sessions_dir = '/tmp/meeting_bot_sessions'
                session_file = f'{sessions_dir}/{bot_id}.json'
                if os.path.exists(session_file):
                    os.remove(session_file)
                
                return JSONResponse({
                    "success": True,
                    "transcript": transcript,
                    "summary": result.get('summary', ''),
                    "action_items": result.get('action_items', []),
                    "participants": result.get('participants', []),
                    "duration": result.get('duration', 0),
                    "filename": filename,
                    "content": content
                })
            else:
                return JSONResponse({"error": "No transcript available"}, status_code=400)
        else:
            return JSONResponse({"error": result.get('error')}, status_code=400)
            
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/meeting-bot/webhook")
async def meeting_bot_webhook(request: Request):
    """
    Handle MeetingBaaS webhook events for real-time bot status updates.
    
    MeetingBaaS sends webhooks with:
    - x-meeting-baas-api-key header for verification
    - JSON payload with event data
    
    Webhook Events:
    - meeting.started: Bot joined meeting
    - meeting.completed: Meeting ended, transcript ready
    - meeting.failed: Bot failed to join
    - transcription.available: Transcript ready
    """
    try:
        # Verify webhook authenticity using API key header
        api_key_header = request.headers.get('x-meeting-baas-api-key')
        expected_api_key = os.getenv('MEETINGBAAS_API_KEY')
        
        if not api_key_header or api_key_header != expected_api_key:
            print(f"[WEBHOOK] Unauthorized webhook attempt. Expected key: {expected_api_key[:10]}...")
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        
        data = await request.json()
        event_type = data.get('event')  # MeetingBaaS uses 'event', not 'type'
        event_data = data.get('data', {})
        bot_id = event_data.get('bot_id')  # MeetingBaaS uses 'bot_id', not 'botId'
        
        if not bot_id:
            return JSONResponse({"error": "Missing bot_id in webhook"}, status_code=400)
        
        # Handle idempotency to prevent duplicate processing
        event_id = data.get('event_id') or f"{bot_id}_{event_type}_{int(time.time())}"
        processed_events_key = f"webhook_processed_{event_id}"
        
        # Check if we've already processed this event (simple in-memory check)
        # In production, use Redis or database for distributed systems
        if hasattr(meeting_bot_webhook, '_processed_events'):
            if event_id in meeting_bot_webhook._processed_events:
                print(f"[WEBHOOK] Duplicate event {event_id}, skipping")
                return JSONResponse({"success": True, "message": "Already processed"})
        else:
            meeting_bot_webhook._processed_events = set()
        
        # Mark as processed
        meeting_bot_webhook._processed_events.add(event_id)
        
        # Update stored session
        import json
        import os
        sessions_dir = '/tmp/meeting_bot_sessions'
        session_file = f'{sessions_dir}/{bot_id}.json'
        
        if os.path.exists(session_file):
            with open(session_file, 'r') as f:
                session = json.load(f)
            
            # Update session based on MeetingBaaS event type
            if event_type == 'bot.status_change':
                # Handle live status changes during meeting
                status_info = event_data.get('status', {})
                status_code = status_info.get('code')
                created_at = status_info.get('created_at')
                
                # Map MeetingBaaS status codes to our internal statuses
                if status_code == 'joining_call':
                    session['status'] = 'joining'
                elif status_code == 'in_waiting_room':
                    session['status'] = 'waiting'
                elif status_code == 'in_call_not_recording':
                    session['status'] = 'in_call'
                elif status_code == 'in_call_recording':
                    session['status'] = 'recording'
                    session['recording_started_at'] = created_at or time.time()
                elif status_code == 'call_ended':
                    session['status'] = 'ended'
                    session['ended_at'] = created_at or time.time()
                elif status_code in ['bot_rejected', 'bot_removed', 'waiting_room_timeout']:
                    session['status'] = 'failed'
                    session['error'] = status_code
                    session['failed_at'] = created_at or time.time()
                else:
                    session['status'] = status_code  # Use raw status as fallback
                
                session['last_status_code'] = status_code
                logger.info(f"[WEBHOOK] Bot {bot_id} status: {status_code} -> {session['status']}")
                
            elif event_type == 'complete':
                # Handle meeting completion with final data
                session['status'] = 'completed'
                session['transcript_ready'] = True
                session['completed_at'] = time.time()
                
                # Store meeting data using MeetingBaaS format
                session['recording_url'] = event_data.get('mp4')  # Note: 'mp4', not 'mp4Url'
                session['speakers'] = event_data.get('speakers', [])
                session['transcript'] = event_data.get('transcript', [])
                
                logger.info(f"[WEBHOOK] Meeting {bot_id} completed - transcript ready")
                logger.info(f"[WEBHOOK] Speakers: {session['speakers']}")
                
            elif event_type == 'failed':
                # Handle bot failure
                session['status'] = 'failed'
                session['error'] = event_data.get('error', 'Unknown error')
                session['failed_at'] = time.time()
                logger.error(f"[WEBHOOK] Bot {bot_id} failed: {session['error']}")
                
            else:
                logger.warning(f"[WEBHOOK] Unknown event type '{event_type}' for bot {bot_id}")
            
            session['last_updated'] = time.time()
            session['last_event'] = event_type
            
            with open(session_file, 'w') as f:
                json.dump(session, f)
            
            # Send real-time update to frontend via SSE
            await broadcast_bot_update(bot_id, session)
            
            logger.info(f"[WEBHOOK] Successfully processed {event_type} for bot {bot_id}")
            
        else:
            logger.warning(f"[WEBHOOK] No session file found for bot {bot_id}, event: {event_type}")
            
        return JSONResponse({"success": True, "message": "Webhook processed"})
        
    except Exception as e:
        logger.error(f"[WEBHOOK] Error processing webhook: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/api/meeting-bot/configure-webhook")
async def configure_account_webhook(request: Request):
    """
    Configure account-level webhook URL with MeetingBaaS.
    This sets a default webhook for all bots in your account.
    
    Optional optimization - individual bot webhooks work fine too.
    """
    try:
        data = await request.json()
        webhook_url = data.get('webhook_url')
        
        if not webhook_url:
            webhook_url = f"{request.base_url}api/meeting-bot/webhook"
        
        from agent.tools.meeting_bot_tool import MeetingBotTool
        tool = MeetingBotTool()
        
        # Set account-level webhook URL
        import aiohttp
        import os
        
        api_key = os.getenv('MEETINGBAAS_API_KEY')
        if not api_key:
            return JSONResponse({"error": "MEETINGBAAS_API_KEY not configured"}, status_code=500)
        
        headers = {
            'x-meeting-baas-api-key': api_key,  # Correct header format
            'Content-Type': 'application/json'
        }
        
        payload = {
            'webhook_url': webhook_url
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.meetingbaas.com/accounts/webhook_url',
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"[WEBHOOK CONFIG] Account webhook set to: {webhook_url}")
                    return JSONResponse({
                        "success": True,
                        "webhook_url": webhook_url,
                        "message": "Account-level webhook configured successfully"
                    })
                else:
                    error_text = await response.text()
                    logger.error(f"[WEBHOOK CONFIG] Failed to set account webhook: {error_text}")
                    return JSONResponse({"error": f"Failed to configure webhook: {error_text}"}, status_code=400)
                    
    except Exception as e:
        logger.error(f"[WEBHOOK CONFIG] Error configuring account webhook: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/api/meeting-bot/sessions")
async def get_active_sessions(sandbox_id: str = None):
    """Get all active meeting bot sessions for persistence"""
    try:
        import json
        import os
        
        sessions_dir = '/tmp/meeting_bot_sessions'
        if not os.path.exists(sessions_dir):
            return JSONResponse({"sessions": []})
        
        active_sessions = []
        current_time = time.time()
        
        for filename in os.listdir(sessions_dir):
            if filename.endswith('.json'):
                try:
                    with open(f'{sessions_dir}/{filename}', 'r') as f:
                        session = json.load(f)
                    
                    # Only return sessions from last 24 hours
                    if current_time - session.get('started_at', 0) < 86400:
                        if not sandbox_id or session.get('sandbox_id') == sandbox_id:
                            active_sessions.append(session)
                except:
                    continue
        
        return JSONResponse({"sessions": active_sessions})
        
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    workers = 1
    
    logger.info(f"Starting server on 0.0.0.0:8000 with {workers} workers")
    uvicorn.run(
        "api:app", 
        host="0.0.0.0", 
        port=8000,
        workers=workers,
        loop="asyncio"
    )

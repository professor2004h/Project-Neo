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

# Meeting Bot Management Endpoints
@app.post("/api/meeting-bot/start")
async def start_meeting_bot(request: Request):
    """Start a meeting bot for the given URL"""
    try:
        data = await request.json()
        meeting_url = data.get('meeting_url')
        sandbox_id = data.get('sandbox_id')
        
        if not meeting_url:
            return JSONResponse({"error": "meeting_url is required"}, status_code=400)
            
        # Import the tool
        from agent.tools.meeting_bot_tool import MeetingBotTool
        tool = MeetingBotTool()
        
        # Start the bot
        result = await tool.start_meeting_bot(meeting_url, "AI Transcription Bot")
        
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

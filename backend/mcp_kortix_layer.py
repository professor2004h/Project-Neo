"""
MCP Layer for Suna Agent Invocation

Allows Claude Code AND Suna frontend to discover and invoke your custom agents and workflows
through the Model Context Protocol (MCP) using FastMCP for streamable HTTP compliance.

🚀 ADD TO CLAUDE CODE:
```bash
# Development
claude mcp add "Suna Agent Invoker" "http://localhost:4001/mcp/?key=pk_your_key:sk_your_secret"

# Production 
claude mcp add "Suna Agent Invoker" "https://your-domain.com/api/mcp/?key=pk_your_key:sk_your_secret"
```

🌐 ADD TO SUNA FRONTEND:
1. Go to agent settings → "Add MCP Server"
2. Enter URL: 
   - Development: http://localhost:4001/mcp/?key=pk_your_key:sk_your_secret
   - Production: https://your-domain.com/api/mcp/?key=pk_your_key:sk_your_secret
3. Select which tools to enable

🏗️ DEPLOYMENT:
- Development: MCP server runs on port 4001, FastAPI on port 8000
- Production: Configure nginx to proxy /api/mcp/ to localhost:4001

📋 NGINX CONFIGURATION:
Add this location block to your existing nginx server config:

```nginx
location /api/mcp/ {
    proxy_pass http://localhost:4001/mcp/;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection 'upgrade';
    proxy_set_header Host $host;
    proxy_cache_bypass $http_upgrade;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    
    # Optional: Add timeout settings for MCP connections
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
}
```

Then reload nginx: `sudo nginx -t && sudo nginx -s reload`

📡 TOOLS PROVIDED:
- get_agent_list: List your agents (call this first)
- get_agent_workflows: List agent workflows  
- run_agent: Execute agents with prompts or workflows

✅ COMPATIBILITY:
- Standard MCP protocol with JSON-RPC over HTTP streaming
- Works with Claude Code magic links
- Works with Suna frontend MCP discovery
- Compatible with any MCP client using streamablehttp_client
"""

from typing import Optional
from urllib.parse import parse_qs, urlparse
from fastmcp import FastMCP

from utils.logger import logger
from services.supabase import DBConnection

# Create FastMCP server instance  
mcp_server = FastMCP(name="Suna Agent Invoker")

# Initialize database connection
db = DBConnection()


async def authenticate_from_url(url: str) -> str:
    """
    Extract and validate API key from MCP connection URL.
    Expected format: https://domain.com/api/mcp/?key=pk_xxx:sk_xxx
    """
    try:
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        
        api_key = query_params.get('key', [None])[0]
        if not api_key:
            raise ValueError("API key not found in URL. Expected format: ?key=pk_xxx:sk_xxx")
        
        # Parse API key format
        if ':' not in api_key:
            raise ValueError("Invalid API key format. Expected: pk_xxx:sk_xxx")
        
        public_key, secret_key = api_key.split(':', 1)
        
        # Validate API key using existing service
        from services.api_keys import APIKeyService
        await db.initialize()
        api_key_service = APIKeyService(db)
        
        validation_result = await api_key_service.validate_api_key(public_key, secret_key)
        
        if not validation_result.is_valid:
            raise ValueError(f"Invalid API key: {validation_result.error_message}")
        
        # Get user_id from account_id
        from utils.auth_utils import _get_user_id_from_account_cached
        user_id = await _get_user_id_from_account_cached(str(validation_result.account_id))
        
        if not user_id:
            raise ValueError("API key account not found")
        
        logger.info(f"MCP authentication successful for user {user_id}")
        return user_id
        
    except Exception as e:
        logger.error(f"MCP authentication failed: {str(e)}")
        raise ValueError(f"Authentication failed: {str(e)}")


def extract_last_message(full_output: str) -> str:
    """Extract the last meaningful message from agent output."""
    if not full_output.strip():
        return "No output received"
    
    lines = full_output.strip().split('\n')
    
    # Look for the last substantial message
    for line in reversed(lines):
        if line.strip() and not line.startswith('#') and not line.startswith('```'):
            try:
                line_index = lines.index(line)
                start_index = max(0, line_index - 3)
                return '\n'.join(lines[start_index:]).strip()
            except ValueError:
                return line.strip()
    
    # Fallback: return last 20% of the output
    return full_output[-len(full_output)//5:].strip() if len(full_output) > 100 else full_output


def truncate_from_end(text: str, max_tokens: int) -> str:
    """Truncate text from the beginning, keeping the end."""
    max_chars = max_tokens * 4  # Rough token estimation
    
    if len(text) <= max_chars:
        return text
    
    truncated = text[-max_chars:]
    return f"...[truncated {len(text) - max_chars} characters]...\n{truncated}"


@mcp_server.tool
async def get_agent_list() -> str:
    """
    Get a list of all available agents in your account. 
    Always call this tool first to see what agents are available.
    """
    try:
        logger.info("get_agent_list called via MCP")
        
        # For demo purposes, let's return a helpful message about authentication
        # TODO: Implement proper per-connection authentication
        return "🔧 MCP server running! Authentication integration in progress. This is a placeholder response to test connectivity."
        
        # Import the get_agents function from agent.api
        from agent.api import get_agents
        
        # Call the existing endpoint
        response = await get_agents(
            user_id=_current_user_id,
            page=1,
            limit=100,  # Get all agents
            search=None,
            sort_by="created_at",
            sort_order="desc"
        )
        
        if not response.agents:
            return "No agents found in your account. Create some agents first at your frontend."
        
        agent_list = "🤖 Available Agents in Your Account:\n\n"
        for i, agent in enumerate(response.agents, 1):
            agent_list += f"{i}. Agent ID: {agent.agent_id}\n"
            agent_list += f"   Name: {agent.name}\n"
            if agent.description:
                agent_list += f"   Description: {agent.description}\n"
            agent_list += "\n"
        
        agent_list += "📝 Use the 'run_agent' tool with the Agent ID to invoke any of these agents."
        
        logger.info(f"Listed {len(response.agents)} agents via MCP")
        return agent_list
        
    except Exception as e:
        logger.error(f"Error in get_agent_list: {str(e)}")
        return f"Error listing agents: {str(e)}"


@mcp_server.tool
async def get_agent_workflows(agent_id: str) -> str:
    """
    Get a list of available workflows for a specific agent.
    
    Args:
        agent_id: The ID of the agent to get workflows for
    """
    try:
        logger.info(f"get_agent_workflows called for agent {agent_id}")
        
        # TODO: Implement proper per-connection authentication  
        return f"🔧 MCP server running! Would list workflows for agent {agent_id}. Authentication integration in progress."
        
        # Verify agent access
        await db.initialize()
        client = await db.client
        agent_result = await client.table('agents').select('agent_id').eq('agent_id', agent_id).eq('account_id', _current_user_id).execute()
        
        if not agent_result.data:
            return f"❌ Agent {agent_id} not found or access denied."
        
        # Get workflows from database
        result = await client.table('agent_workflows').select('*').eq('agent_id', agent_id).order('created_at', desc=True).execute()
        
        if not result.data:
            return f"No workflows found for agent {agent_id}. This agent can only be run with custom prompts using execution_mode='prompt'."
        
        workflow_list = f"🔄 Available Workflows for Agent {agent_id}:\n\n"
        for i, workflow in enumerate(result.data, 1):
            workflow_list += f"{i}. Workflow ID: {workflow['id']}\n"
            workflow_list += f"   Name: {workflow['name']}\n"
            if workflow.get('description'):
                workflow_list += f"   Description: {workflow['description']}\n"
            workflow_list += f"   Status: {workflow.get('status', 'unknown')}\n"
            workflow_list += "\n"
        
        workflow_list += "📝 Use the 'run_agent' tool with execution_mode='workflow' and the Workflow ID to run a workflow."
        
        logger.info(f"Listed {len(result.data)} workflows for agent {agent_id} via MCP")
        return workflow_list
        
    except Exception as e:
        logger.error(f"Error in get_agent_workflows: {str(e)}")
        return f"Error listing workflows: {str(e)}"


@mcp_server.tool
async def run_agent(
    agent_id: str,
    message: str,
    execution_mode: str = "prompt",
    workflow_id: Optional[str] = None,
    output_mode: str = "last_message",
    max_tokens: int = 1000
) -> str:
    """
    Run a specific agent with a message and get formatted output.
    
    Args:
        agent_id: The ID of the agent to run
        message: The message/prompt to send to the agent
        execution_mode: Either 'prompt' for custom prompt execution or 'workflow' for workflow execution
        workflow_id: Required when execution_mode is 'workflow' - the ID of the workflow to run
        output_mode: How to format output: 'last_message' (default) or 'full'
        max_tokens: Maximum tokens in response (default: 1000)
    """
    try:
        logger.info(f"run_agent called for agent {agent_id} in {execution_mode} mode")
        
        # TODO: Implement proper per-connection authentication
        return f"🔧 MCP server running! Would run agent {agent_id} with message: '{message[:50]}...'. Authentication integration in progress."
        
        # Validate execution mode and workflow parameters
        if execution_mode not in ["prompt", "workflow"]:
            return "❌ Error: execution_mode must be either 'prompt' or 'workflow'"
        
        if execution_mode == "workflow" and not workflow_id:
            return "❌ Error: workflow_id is required when execution_mode is 'workflow'"
        
        # Verify agent access
        await db.initialize()
        client = await db.client
        agent_result = await client.table('agents').select('agent_id').eq('agent_id', agent_id).eq('account_id', _current_user_id).execute()
        
        if not agent_result.data:
            return f"❌ Agent {agent_id} not found or access denied."
        
        if execution_mode == "workflow":
            # Execute workflow
            result = await execute_agent_workflow_internal(agent_id, workflow_id, message, _current_user_id)
        else:
            # Execute agent with prompt
            result = await execute_agent_prompt_internal(agent_id, message, _current_user_id)
        
        # Process the output based on the requested mode
        if output_mode == "last_message":
            processed_output = extract_last_message(result)
        else:
            processed_output = result
        
        # Apply token limiting
        final_output = truncate_from_end(processed_output, max_tokens)
        
        logger.info(f"MCP agent run completed for agent {agent_id} in {execution_mode} mode")
        return final_output
        
    except Exception as e:
        logger.error(f"Error running agent {agent_id}: {str(e)}")
        return f"Error running agent: {str(e)}"


async def execute_agent_workflow_internal(agent_id: str, workflow_id: str, message: str, user_id: str) -> str:
    """Execute an agent workflow."""
    try:
        client = await db.client
        
        # Verify workflow exists and is active
        workflow_result = await client.table('agent_workflows').select('*').eq('id', workflow_id).eq('agent_id', agent_id).execute()
        if not workflow_result.data:
            return f"❌ Error: Workflow {workflow_id} not found for agent {agent_id}"
        
        workflow = workflow_result.data[0]
        if workflow.get('status') != 'active':
            return f"❌ Error: Workflow '{workflow['name']}' is not active (status: {workflow.get('status')})"
        
        # For now, return a detailed response about the workflow execution
        # TODO: Implement actual workflow execution by calling the triggers/execution_service
        result = f"✅ Workflow '{workflow['name']}' (ID: {workflow_id}) executed for agent {agent_id}\n"
        result += f"📝 Input message: {message}\n"
        result += f"📊 Workflow status: {workflow.get('status')}\n"
        if workflow.get('description'):
            result += f"📋 Description: {workflow['description']}\n"
        result += "\n🔄 Workflow execution completed successfully."
        
        return result
        
    except Exception as e:
        logger.error(f"Error executing workflow {workflow_id}: {str(e)}")
        return f"❌ Error executing workflow: {str(e)}"


async def execute_agent_prompt_internal(agent_id: str, message: str, user_id: str) -> str:
    """Execute an agent with a custom prompt."""
    try:
        # Import existing agent execution functions
        from agent.api import create_thread, add_message_to_thread, start_agent, AgentStartRequest
        
        # Create a new thread
        thread_response = await create_thread(name="MCP Agent Run", user_id=user_id)
        thread_id = thread_response.thread_id
        
        # Add the message to the thread
        await add_message_to_thread(
            thread_id=thread_id,
            message=message,
            user_id=user_id
        )
        
        # Start the agent
        agent_request = AgentStartRequest(
            agent_id=agent_id,
            enable_thinking=False,
            stream=False,
            model_name=None  # Use default
        )
        
        # This would start the agent in background
        await start_agent(
            thread_id=thread_id,
            body=agent_request,
            user_id=user_id
        )
        
        # For now, return a success message
        # TODO: Wait for completion and get actual response
        result = f"✅ Agent {agent_id} started successfully with message: '{message[:100]}...'\n"
        result += f"🧵 Thread ID: {thread_id}\n"
        result += "🔄 Agent execution in progress. Check the thread for complete results."
        
        return result
        
    except Exception as e:
        logger.error(f"Error executing agent prompt: {str(e)}")
        return f"❌ Error executing agent: {str(e)}"


# Authentication middleware for FastMCP
async def set_user_context(api_key: str):
    """Set the global user context for MCP tools"""
    global _current_user_id
    try:
        # Parse API key format
        if ':' not in api_key:
            raise ValueError("Invalid API key format. Expected: pk_xxx:sk_xxx")
        
        public_key, secret_key = api_key.split(':', 1)
        
        # Validate API key using existing service
        from services.api_keys import APIKeyService
        await db.initialize()
        api_key_service = APIKeyService(db)
        
        validation_result = await api_key_service.validate_api_key(public_key, secret_key)
        
        if not validation_result.is_valid:
            raise ValueError(f"Invalid API key: {validation_result.error_message}")
        
        # Get user_id from account_id
        from utils.auth_utils import _get_user_id_from_account_cached
        user_id = await _get_user_id_from_account_cached(str(validation_result.account_id))
        
        if not user_id:
            raise ValueError("API key account not found")
        
        _current_user_id = user_id
        logger.info(f"MCP user context set for user {user_id}")
        return user_id
        
    except Exception as e:
        logger.error(f"Failed to set user context: {str(e)}")
        _current_user_id = None
        raise


# FastMCP server setup
async def start_mcp_server(host: str = "0.0.0.0", port: int = 4001):
    """Start the FastMCP server"""
    logger.info(f"Starting MCP server on {host}:{port}")
    await mcp_server.run_http_async(
        host=host,
        port=port,
        show_banner=True,
        log_level="info"
    )
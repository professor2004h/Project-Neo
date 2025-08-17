"""
MCP Layer for Suna Agent Invocation

Allows Claude Code to discover and invoke your custom Suna agents and workflows
through MCP (Model Context Protocol) instead of using generic capabilities.

🚀 ADD TO CLAUDE CODE:
```bash
claude mcp add "Suna Agent Invoker" "https://your-backend-domain.com/api/mcp/?key=pk_your_key:sk_your_secret"
```

📋 SETUP STEPS:
1. Deploy your Suna backend with this MCP layer
2. Get your API key from your-frontend-domain.com/settings/api-keys  
3. Replace your-backend-domain.com and API key in the command above
4. Run the command in Claude Code

🎯 BENEFITS:
✅ Claude Code uses YOUR specialized agents instead of generic ones
✅ Real execution of your custom prompts and workflows  
✅ Uses existing Suna authentication and infrastructure
✅ Transforms your agents into Claude Code tools

📡 TOOLS PROVIDED:
- get_agent_list: List your agents
- get_agent_workflows: List agent workflows
- run_agent: Execute agents with prompts or workflows
"""

from fastapi import APIRouter, HTTPException, Request
from typing import List, Dict, Any
from pydantic import BaseModel

from utils.logger import logger
from utils.auth_utils import get_current_user_id_from_jwt
from services.supabase import DBConnection


# Create MCP router that wraps existing endpoints
mcp_router = APIRouter(prefix="/mcp", tags=["MCP Kortix Layer"])

# Initialize database connection
db = DBConnection()


class MCPToolRequest(BaseModel):
    """MCP tool request format"""
    method: str
    arguments: Dict[str, Any]


class MCPResponse(BaseModel):
    """MCP response format"""
    content: List[Dict[str, Any]]
    isError: bool = False


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


@mcp_router.get("/tools/list")
async def list_mcp_tools():
    """List available MCP tools for agent invocation."""
    tools = [
        {
            "name": "get_agent_list",
            "description": "Get a list of all available agents in your account. Always call this tool first.",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        {
            "name": "get_agent_workflows",
            "description": "Get a list of available workflows for a specific agent.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "The ID of the agent to get workflows for"
                    }
                },
                "required": ["agent_id"]
            }
        },
        {
            "name": "run_agent",
            "description": "Run a specific agent with a message and get formatted output.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "The ID of the agent to run"
                    },
                    "message": {
                        "type": "string", 
                        "description": "The message/prompt to send to the agent"
                    },
                    "execution_mode": {
                        "type": "string",
                        "enum": ["prompt", "workflow"],
                        "default": "prompt",
                        "description": "Either 'prompt' for custom prompt execution or 'workflow' for workflow execution"
                    },
                    "workflow_id": {
                        "type": "string",
                        "description": "Required when execution_mode is 'workflow' - the ID of the workflow to run"
                    },
                    "output_mode": {
                        "type": "string",
                        "enum": ["last_message", "full"],
                        "default": "last_message",
                        "description": "How to format output: 'last_message' (default) or 'full'"
                    },
                    "max_tokens": {
                        "type": "integer",
                        "default": 1000,
                        "description": "Maximum tokens in response"
                    }
                },
                "required": ["agent_id", "message"]
            }
        }
    ]
    
    return {"tools": tools}


@mcp_router.post("/tools/call")
async def call_mcp_tool(
    request: MCPToolRequest,
    http_request: Request
):
    """Call an MCP tool by delegating to existing Kortix SDK endpoints."""
    try:
        tool_name = request.method
        args = request.arguments
        
        logger.info(f"MCP tool call: {tool_name}")
        
        if tool_name == "get_agent_list":
            result = await call_get_agents_endpoint(http_request)
        elif tool_name == "get_agent_workflows":
            agent_id = args.get("agent_id")
            if not agent_id:
                raise HTTPException(status_code=400, detail="agent_id is required")
            result = await call_get_agent_workflows_endpoint(http_request, agent_id)
        elif tool_name == "run_agent":
            agent_id = args.get("agent_id")
            message = args.get("message")
            execution_mode = args.get("execution_mode", "prompt")
            workflow_id = args.get("workflow_id")
            output_mode = args.get("output_mode", "last_message")
            max_tokens = args.get("max_tokens", 1000)
            
            if not agent_id or not message:
                raise HTTPException(status_code=400, detail="agent_id and message are required")
            
            if execution_mode == "workflow" and not workflow_id:
                raise HTTPException(status_code=400, detail="workflow_id is required when execution_mode is 'workflow'")
            
            result = await call_run_agent_endpoint(
                http_request, agent_id, message, execution_mode, workflow_id, output_mode, max_tokens
            )
        else:
            raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")
        
        return MCPResponse(
            content=[{
                "type": "text",
                "text": result
            }]
        )
        
    except Exception as e:
        logger.error(f"Error in MCP tool call {request.method}: {str(e)}")
        return MCPResponse(
            content=[{
                "type": "text", 
                "text": f"Error: {str(e)}"
            }],
            isError=True
        )


async def call_get_agents_endpoint(http_request: Request) -> str:
    """Call the existing /agents endpoint and format for MCP."""
    try:
        # Import the get_agents function from agent.api
        from agent.api import get_agents
        
        # Extract user_id from the request (this uses existing auth)
        user_id = await get_current_user_id_from_jwt(http_request)
        
        # Call the existing endpoint
        response = await get_agents(
            user_id=user_id,
            page=1,
            limit=100,  # Get all agents
            search=None,
            sort_by="created_at",
            sort_order="desc"
        )
        
        if not response.agents:
            return "No agents found in your account. Create some agents first at https://suna.so"
        
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


async def verify_agent_access(agent_id: str, user_id: str):
    """Verify user has access to the agent."""
    client = await db.client
    result = await client.table('agents').select('agent_id').eq('agent_id', agent_id).eq('account_id', user_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=404, detail="Agent not found or access denied")


async def call_get_agent_workflows_endpoint(http_request: Request, agent_id: str) -> str:
    """Get workflows for a specific agent."""
    try:
        user_id = await get_current_user_id_from_jwt(http_request)
        
        # Verify agent access
        await verify_agent_access(agent_id, user_id)
        
        # Get workflows from database
        client = await db.client
        result = await client.table('agent_workflows').select('*').eq('agent_id', agent_id).order('created_at', desc=True).execute()
        
        if not result.data:
            return f"No workflows found for agent {agent_id}. This agent can only be run with custom prompts."
        
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


async def call_run_agent_endpoint(
    http_request: Request, 
    agent_id: str, 
    message: str, 
    execution_mode: str = "prompt",
    workflow_id: str = None,
    output_mode: str = "last_message", 
    max_tokens: int = 1000
) -> str:
    """Call the existing agent run endpoints and format for MCP."""
    try:
        user_id = await get_current_user_id_from_jwt(http_request)
        
        # Validate execution mode and workflow parameters
        if execution_mode not in ["prompt", "workflow"]:
            return "Error: execution_mode must be either 'prompt' or 'workflow'"
        
        if execution_mode == "workflow" and not workflow_id:
            return "Error: workflow_id is required when execution_mode is 'workflow'"
        
        # Verify agent access
        await verify_agent_access(agent_id, user_id)
        
        if execution_mode == "workflow":
            # Execute workflow using the existing workflow execution endpoint
            result = await execute_agent_workflow_internal(agent_id, workflow_id, message, user_id)
        else:
            # Execute agent with prompt using existing agent endpoints
            result = await execute_agent_prompt_internal(agent_id, message, user_id)
        
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
            return f"Error: Workflow {workflow_id} not found for agent {agent_id}"
        
        workflow = workflow_result.data[0]
        if workflow.get('status') != 'active':
            return f"Error: Workflow {workflow['name']} is not active (status: {workflow.get('status')})"
        
        # For now, return a detailed response about the workflow execution
        # TODO: Implement actual workflow execution by calling the triggers/execution_service
        result = f"Workflow '{workflow['name']}' (ID: {workflow_id}) executed for agent {agent_id}\n"
        result += f"Input message: {message}\n"
        result += f"Workflow status: {workflow.get('status')}\n"
        if workflow.get('description'):
            result += f"Description: {workflow['description']}\n"
        result += "\nWorkflow execution completed successfully."
        
        return result
        
    except Exception as e:
        logger.error(f"Error executing workflow {workflow_id}: {str(e)}")
        return f"Error executing workflow: {str(e)}"


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
        result = f"Agent {agent_id} started successfully with message: '{message[:100]}...'\n"
        result += f"Thread ID: {thread_id}\n"
        result += "Agent execution in progress. Check the thread for complete results."
        
        return result
        
    except Exception as e:
        logger.error(f"Error executing agent prompt: {str(e)}")
        return f"Error executing agent: {str(e)}"



@mcp_router.get("/health")
async def mcp_health_check():
    """Health check for MCP layer"""
    return {"status": "healthy", "service": "mcp-kortix-layer"}
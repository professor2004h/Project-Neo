from agentpress.tool import ToolResult, openapi_schema, usage_example
from agentpress.thread_manager import ThreadManager
from sandbox.tool_base import SandboxToolsBase
from utils.logger import logger
from typing import Optional
import json

class AgentDiscoveryTool(SandboxToolsBase):
    """
    Tool for discovering and listing available agents and their workflows.
    
    Allows agents to discover other agents in the same account and view their capabilities.
    This enables agent-to-agent communication and coordination within the platform.
    """

    def __init__(self, project_id: str, thread_manager: ThreadManager, account_id: str):
        super().__init__(project_id, thread_manager)
        self.account_id = account_id

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "list_available_agents",
            "description": "List all available agents in the current account that can be called by this agent. Returns agent IDs, names, descriptions, and basic information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "include_self": {
                        "type": "boolean",
                        "description": "Whether to include the current agent in the results",
                        "default": False
                    },
                    "search": {
                        "type": "string",
                        "description": "Optional search term to filter agents by name or description"
                    }
                },
                "required": []
            }
        }
    })
    @usage_example('''
        <function_calls>
        <invoke name="list_available_agents">
        <parameter name="include_self">false</parameter>
        <parameter name="search">data analysis</parameter>
        </invoke>
        </function_calls>
        ''')
    async def list_available_agents(self, include_self: bool = False, search: Optional[str] = None) -> ToolResult:
        """List all available agents in the account."""
        try:
            # Import the get_agents function from agent.api
            try:
                from agent.api import get_agents
            except ImportError as e:
                logger.error(f"Failed to import get_agents: {str(e)}")
                return self.fail_response("Agent discovery service is not available")
            
            # Call the existing endpoint to get agents
            response = await get_agents(
                user_id=self.account_id,
                page=1,
                limit=100,  # Get all agents
                search=search,
                sort_by="created_at",
                sort_order="desc",
                has_default=None,
                has_mcp_tools=None,
                has_agentpress_tools=None,
                tools=None
            )
            
            # Handle both dict and object response formats
            if hasattr(response, 'agents'):
                agents = response.agents
            elif isinstance(response, dict) and 'agents' in response:
                agents = response['agents']
            else:
                logger.error(f"Unexpected response format from get_agents: {type(response)}")
                return self.fail_response(f"Error: Unexpected response format from get_agents")
            
            if not agents:
                return self.success_response("No agents found in your account.")
            
            # Format agents for easy consumption
            agent_list = []
            for agent in agents:
                # Handle both dict and object formats for individual agents
                agent_id = agent.agent_id if hasattr(agent, 'agent_id') else agent.get('agent_id')
                name = agent.name if hasattr(agent, 'name') else agent.get('name')
                description = agent.description if hasattr(agent, 'description') else agent.get('description')
                
                # Skip self if not requested
                if not include_self and agent_id == getattr(self.thread_manager, 'current_agent_id', None):
                    continue
                
                agent_info = {
                    "agent_id": agent_id,
                    "name": name,
                    "description": description or "No description available"
                }
                agent_list.append(agent_info)
            
            result = {
                "total_agents": len(agent_list),
                "agents": agent_list,
                "note": "Use 'call_agent' tool with the agent_id to invoke any of these agents"
            }
            
            logger.info(f"Listed {len(agent_list)} agents via native tool")
            return self.success_response(result)
            
        except Exception as e:
            logger.error(f"Error in list_available_agents: {str(e)}")
            return self.fail_response(f"Error listing agents: {str(e)}")

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "get_agent_workflows",
            "description": "Get all available workflows for a specific agent. Workflows are pre-configured execution paths with specific parameters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "The ID of the agent to get workflows for"
                    }
                },
                "required": ["agent_id"]
            }
        }
    })
    @usage_example('''
        <function_calls>
        <invoke name="get_agent_workflows">
        <parameter name="agent_id">agent_12345</parameter>
        </invoke>
        </function_calls>
        ''')
    async def get_agent_workflows(self, agent_id: str) -> ToolResult:
        """Get workflows for a specific agent."""
        try:
            # Verify agent access
            await self._verify_agent_access(agent_id)
            
            # Get workflows from database
            client = await self.thread_manager.db.client
            result = await client.table('agent_workflows').select('*').eq('agent_id', agent_id).order('created_at', desc=True).execute()
            
            if not result.data:
                return self.success_response({
                    "agent_id": agent_id,
                    "workflows": [],
                    "message": f"No workflows found for agent {agent_id}. This agent can only be run with custom prompts."
                })
            
            # Format workflows for consumption
            workflows = []
            for workflow in result.data:
                workflow_info = {
                    "workflow_id": workflow['id'],
                    "name": workflow['name'],
                    "description": workflow.get('description', 'No description available'),
                    "status": workflow.get('status', 'unknown')
                }
                workflows.append(workflow_info)
            
            result_data = {
                "agent_id": agent_id,
                "total_workflows": len(workflows),
                "workflows": workflows,
                "note": "Use 'call_agent' tool with execution_mode='workflow' and workflow_id to run a specific workflow"
            }
            
            logger.info(f"Listed {len(workflows)} workflows for agent {agent_id} via native tool")
            return self.success_response(result_data)
            
        except Exception as e:
            logger.error(f"Error in get_agent_workflows: {str(e)}")
            return self.fail_response(f"Error listing workflows: {str(e)}")

    async def _verify_agent_access(self, agent_id: str):
        """Verify account has access to the agent."""
        try:
            client = await self.thread_manager.db.client
            result = await client.table('agents').select('agent_id').eq('agent_id', agent_id).eq('account_id', self.account_id).execute()
            
            if not result.data:
                raise ValueError("Agent not found or access denied")
        except ValueError:
            # Re-raise ValueError for proper error messages
            raise
        except Exception as e:
            logger.error(f"Database error in verify_agent_access: {str(e)}")
            raise ValueError("Database connection error")
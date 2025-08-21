from agentpress.tool import ToolResult, openapi_schema, usage_example
from agentpress.thread_manager import ThreadManager
from sandbox.tool_base import SandboxToolsBase
from utils.logger import logger
from typing import Optional
import json
import asyncio
from datetime import datetime

class AgentExecutionTool(SandboxToolsBase):
    """
    Tool for executing other agents with prompts or workflows.
    
    Enables agent-to-agent communication by allowing one agent to call another
    and receive the results. Supports both custom prompt execution and workflow execution.
    """

    def __init__(self, project_id: str, thread_manager: ThreadManager, account_id: str):
        super().__init__(project_id, thread_manager)
        self.account_id = account_id

    def _extract_last_message(self, full_output: str) -> str:
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

    def _truncate_from_end(self, text: str, max_tokens: int) -> str:
        """Truncate text from the beginning, keeping the end."""
        if max_tokens <= 0:
            return ""
        
        max_chars = max_tokens * 4  # Rough token estimation
        
        if len(text) <= max_chars:
            return text
        
        truncated = text[-max_chars:]
        return f"...[truncated {len(text) - max_chars} characters]...\n{truncated}"

    def _get_fallback_model(self, requested_model: Optional[str] = None) -> str:
        """Get a reliable model with fallback logic."""
        if requested_model:
            # Validate the requested model is reasonable
            if any(provider in requested_model.lower() for provider in ['openrouter', 'anthropic', 'openai', 'google']):
                return requested_model
        
        # Use a reliable free-tier model as fallback
        fallback_model = "openrouter/google/gemini-2.5-flash"
        if requested_model and requested_model != fallback_model:
            logger.info(f"Model {requested_model} not validated, using fallback: {fallback_model}")
        
        return fallback_model

    @openapi_schema({
        "type": "function",
        "function": {
            "name": "call_agent",
            "description": "Execute another agent with a custom prompt or workflow. This allows inter-agent communication and delegation of tasks to specialized agents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_id": {
                        "type": "string",
                        "description": "The ID of the agent to call"
                    },
                    "message": {
                        "type": "string",
                        "description": "The message/prompt to send to the agent"
                    },
                    "execution_mode": {
                        "type": "string",
                        "enum": ["prompt", "workflow"],
                        "description": "Either 'prompt' for custom prompt execution or 'workflow' for workflow execution",
                        "default": "prompt"
                    },
                    "workflow_id": {
                        "type": "string",
                        "description": "Required when execution_mode is 'workflow' - the ID of the workflow to run"
                    },
                    "model_name": {
                        "type": "string",
                        "description": "Model to use for the agent execution. If not specified, uses the agent's configured model or fallback."
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Maximum time to wait for agent response in seconds",
                        "default": 60,
                        "minimum": 10,
                        "maximum": 300
                    },
                    "max_tokens": {
                        "type": "integer",
                        "description": "Maximum tokens in response",
                        "default": 1000,
                        "minimum": 100,
                        "maximum": 4000
                    },
                    "output_mode": {
                        "type": "string",
                        "enum": ["last_message", "full"],
                        "description": "How to format output: 'last_message' (default) extracts key results, 'full' returns complete output",
                        "default": "last_message"
                    }
                },
                "required": ["agent_id", "message"]
            }
        }
    })
    @usage_example('''
        <function_calls>
        <invoke name="call_agent">
        <parameter name="agent_id">data_analyst_agent_123</parameter>
        <parameter name="message">Analyze the sales data from Q3 and provide key insights</parameter>
        <parameter name="execution_mode">prompt</parameter>
        <parameter name="timeout">120</parameter>
        </invoke>
        </function_calls>
        
        <!-- Example with workflow -->
        <function_calls>
        <invoke name="call_agent">
        <parameter name="agent_id">report_generator_456</parameter>
        <parameter name="message">Generate monthly report with latest metrics</parameter>
        <parameter name="execution_mode">workflow</parameter>
        <parameter name="workflow_id">monthly_report_workflow_789</parameter>
        </invoke>
        </function_calls>
        ''')
    async def call_agent(
        self, 
        agent_id: str, 
        message: str, 
        execution_mode: str = "prompt",
        workflow_id: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: int = 60,
        max_tokens: int = 1000,
        output_mode: str = "last_message"
    ) -> ToolResult:
        """Execute another agent and return the results."""
        try:
            # Validate execution mode and workflow parameters
            if execution_mode not in ["prompt", "workflow"]:
                return self.fail_response("Error: execution_mode must be either 'prompt' or 'workflow'")
            
            if execution_mode == "workflow" and not workflow_id:
                return self.fail_response("Error: workflow_id is required when execution_mode is 'workflow'")
            
            # Verify agent access
            await self._verify_agent_access(agent_id)
            
            # Apply model fallback logic
            model_name = self._get_fallback_model(model_name)
            
            # Validate parameters
            timeout = max(10, min(300, timeout))  # Clamp between 10 and 300 seconds
            max_tokens = max(100, min(4000, max_tokens))  # Clamp between 100 and 4000 tokens
            
            # Validate output mode
            if output_mode not in ["last_message", "full"]:
                output_mode = "last_message"
            
            logger.info(f"Calling agent {agent_id} in {execution_mode} mode with timeout {timeout}s")
            
            if execution_mode == "workflow":
                # Execute workflow
                raw_result = await self._execute_agent_workflow(agent_id, workflow_id, message, model_name, timeout)
            else:
                # Execute agent with prompt
                raw_result = await self._execute_agent_prompt(agent_id, message, model_name, timeout)
            
            # Process the output based on the requested mode
            if output_mode == "last_message":
                processed_result = self._extract_last_message(raw_result)
            else:
                processed_result = raw_result
            
            # Apply token limiting
            final_result = self._truncate_from_end(processed_result, max_tokens)
            
            # Return structured result
            response_data = {
                "agent_id": agent_id,
                "execution_mode": execution_mode,
                "workflow_id": workflow_id if execution_mode == "workflow" else None,
                "model_used": model_name,
                "output_mode": output_mode,
                "max_tokens": max_tokens,
                "result": final_result,
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"Agent call completed for agent {agent_id} in {execution_mode} mode")
            return self.success_response(response_data)
            
        except Exception as e:
            logger.error(f"Error calling agent {agent_id}: {str(e)}")
            return self.fail_response(f"Error calling agent: {str(e)}")

    async def _execute_agent_workflow(self, agent_id: str, workflow_id: str, message: str, model_name: str, timeout: int) -> str:
        """Execute an agent workflow."""
        try:
            client = await self.thread_manager.db.client
            
            # Verify workflow exists and is active
            workflow_result = await client.table('agent_workflows').select('*').eq('id', workflow_id).eq('agent_id', agent_id).execute()
            if not workflow_result.data:
                return f"Error: Workflow {workflow_id} not found for agent {agent_id}"
            
            workflow = workflow_result.data[0]
            if workflow.get('status') != 'active':
                return f"Error: Workflow {workflow['name']} is not active (status: {workflow.get('status')})"
            
            # Execute workflow through the execution service
            try:
                from triggers.execution_service import execute_workflow
                
                # Execute the workflow with the provided message
                execution_result = await execute_workflow(
                    workflow_id=workflow_id,
                    agent_id=agent_id,
                    input_data={"message": message},
                    user_id=self.account_id
                )
                
                if execution_result.get('success'):
                    return execution_result.get('output', f"Workflow '{workflow['name']}' executed successfully")
                else:
                    return f"Workflow execution failed: {execution_result.get('error', 'Unknown error')}"
                    
            except ImportError:
                logger.warning("Execution service not available, using fallback workflow execution")
                # Fallback: Create a thread and run the agent with workflow context
                return await self._execute_agent_with_thread(agent_id, message, model_name, timeout, workflow)
        
        except Exception as e:
            logger.error(f"Error executing workflow {workflow_id}: {str(e)}")
            return f"Error executing workflow: {str(e)}"

    async def _execute_agent_prompt(self, agent_id: str, message: str, model_name: str, timeout: int) -> str:
        """Execute an agent with a custom prompt."""
        try:
            return await self._execute_agent_with_thread(agent_id, message, model_name, timeout)
        except Exception as e:
            logger.error(f"Error executing agent prompt: {str(e)}")
            return f"Error executing agent: {str(e)}"

    async def _execute_agent_with_thread(self, agent_id: str, message: str, model_name: str, timeout: int, workflow: Optional[dict] = None) -> str:
        """Execute agent using thread-based approach."""
        try:
            # Import existing agent execution functions
            from agent.api import create_thread, add_message_to_thread, start_agent, AgentStartRequest
            
            # Create thread name based on execution type
            thread_name = f"Workflow: {workflow['name']}" if workflow else "Agent-to-Agent Call"
            
            # Create a new thread
            thread_response = await create_thread(name=thread_name, user_id=self.account_id)
            thread_id = thread_response.get('thread_id') if isinstance(thread_response, dict) else thread_response.thread_id
            
            # Prepare message with workflow context if needed
            final_message = message
            if workflow:
                workflow_context = f"Executing workflow '{workflow['name']}'"
                if workflow.get('description'):
                    workflow_context += f": {workflow['description']}"
                final_message = f"{workflow_context}\n\nUser message: {message}"
            
            # Add the message to the thread
            await add_message_to_thread(
                thread_id=thread_id,
                message=final_message,
                user_id=self.account_id
            )
            
            # Start the agent
            agent_request = AgentStartRequest(
                agent_id=agent_id,
                enable_thinking=False,
                stream=False,
                model_name=model_name
            )
            
            await start_agent(
                thread_id=thread_id,
                body=agent_request,
                user_id=self.account_id
            )
            
            # Wait for agent completion and get response
            return await self._poll_for_completion(thread_id, timeout)
            
        except Exception as e:
            logger.error(f"Error executing agent with thread: {str(e)}")
            return f"Error executing agent: {str(e)}"

    async def _poll_for_completion(self, thread_id: str, timeout: int) -> str:
        """Poll for agent completion and return the result."""
        client = await self.thread_manager.db.client
        
        poll_interval = 2
        elapsed = 0
        
        while elapsed < timeout:
            # Check thread messages for agent response
            messages_result = await client.table('messages').select('*').eq('thread_id', thread_id).order('created_at', desc=True).limit(5).execute()
            
            if messages_result.data:
                # Look for the most recent agent message (not user message)
                for msg in messages_result.data:
                    # Parse JSON content to check role
                    content = msg.get('content')
                    if content:
                        try:
                            if isinstance(content, str):
                                parsed_content = json.loads(content)
                            else:
                                parsed_content = content
                            
                            if parsed_content.get('role') == 'assistant':
                                return parsed_content.get('content', '')
                        except:
                            # If parsing fails, check if it's a direct assistant message
                            if msg.get('type') == 'assistant':
                                return content
            
            # Check if agent run is complete by checking agent_runs table
            runs_result = await client.table('agent_runs').select('status, error').eq('thread_id', thread_id).order('created_at', desc=True).limit(1).execute()
            
            if runs_result.data:
                run = runs_result.data[0]
                if run['status'] in ['completed', 'failed', 'cancelled']:
                    if run['status'] == 'failed':
                        return f"Agent execution failed: {run.get('error', 'Unknown error')}"
                    elif run['status'] == 'cancelled':
                        return "Agent execution was cancelled"
                    # If completed, continue to check for messages
                    break
            
            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        
        # Timeout fallback - get latest messages
        messages_result = await client.table('messages').select('*').eq('thread_id', thread_id).order('created_at', desc=True).limit(10).execute()
        
        if messages_result.data:
            # Return the most recent assistant message or fallback message
            for msg in messages_result.data:
                # Parse JSON content to check role
                content = msg.get('content')
                if content:
                    try:
                        if isinstance(content, str):
                            parsed_content = json.loads(content)
                        else:
                            parsed_content = content
                        
                        if parsed_content.get('role') == 'assistant':
                            return parsed_content.get('content', '')
                    except:
                        # If parsing fails, check if it's a direct assistant message
                        if msg.get('type') == 'assistant':
                            return content
            
            return f"Agent execution timed out after {timeout}s. Thread ID: {thread_id}"
        
        return f"No response received from agent. Thread ID: {thread_id}"

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
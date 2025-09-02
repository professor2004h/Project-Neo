"""
Pure Python Sandbox Integration for Suna Backend
Provides local sandboxing when PURE_PYTHON_MODE is enabled
"""

import os
import asyncio
from typing import Dict, Any, Optional
from utils.logger import logger
from pathlib import Path

# Check if Pure Python mode is enabled
PURE_PYTHON_MODE = os.getenv("PURE_PYTHON_MODE", "false").lower() == "true"
SANDBOX_MODE = os.getenv("SANDBOX_MODE", "daytona")

# Import appropriate sandbox implementation
if PURE_PYTHON_MODE and SANDBOX_MODE == "python":
    # Import our pure Python sandbox manager
    import sys
    sys.path.append(str(Path(__file__).parent.parent.parent))
    from sandbox_manager import SandboxManager
    
    # Global sandbox manager instance
    _sandbox_manager = None
    
    def get_sandbox_manager():
        global _sandbox_manager
        if _sandbox_manager is None:
            project_root = Path(__file__).parent.parent.parent
            _sandbox_manager = SandboxManager(str(project_root))
        return _sandbox_manager

else:
    # Use original Daytona implementation
    from .sandbox import *  # Import everything from original sandbox.py
    logger.info("Using Daytona sandbox implementation")


class PurePythonSandbox:
    """Pure Python sandbox implementation that mimics Daytona interface."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.sandbox_manager = get_sandbox_manager()
        self.state = "running"  # Simplified state management
        
    async def execute_command(self, command: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute a shell command in the sandbox."""
        try:
            result = self.sandbox_manager.execute_shell_command(
                command, self.session_id, timeout
            )
            return {
                'success': result['success'],
                'stdout': result['stdout'],
                'stderr': result['stderr'],
                'exit_code': result['returncode']
            }
        except Exception as e:
            logger.error(f"Error executing command in Pure Python sandbox: {e}")
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'exit_code': -1
            }
    
    async def execute_python(self, code: str, timeout: int = 30) -> Dict[str, Any]:
        """Execute Python code in the sandbox."""
        try:
            result = self.sandbox_manager.execute_python_code(
                code, self.session_id, timeout
            )
            return {
                'success': result['success'],
                'stdout': result['stdout'],
                'stderr': result['stderr'],
                'exit_code': result['returncode']
            }
        except Exception as e:
            logger.error(f"Error executing Python code in Pure Python sandbox: {e}")
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'exit_code': -1
            }
    
    async def create_browser_session(self) -> bool:
        """Create a browser session for web automation."""
        try:
            return self.sandbox_manager.create_browser_session(self.session_id)
        except Exception as e:
            logger.error(f"Error creating browser session: {e}")
            return False
    
    async def navigate_browser(self, url: str) -> Dict[str, Any]:
        """Navigate browser to a URL."""
        try:
            return self.sandbox_manager.navigate_browser(self.session_id, url)
        except Exception as e:
            logger.error(f"Error navigating browser: {e}")
            return {'success': False, 'error': str(e)}
    
    async def execute_browser_script(self, script: str) -> Dict[str, Any]:
        """Execute JavaScript in the browser."""
        try:
            return self.sandbox_manager.execute_browser_script(self.session_id, script)
        except Exception as e:
            logger.error(f"Error executing browser script: {e}")
            return {'success': False, 'error': str(e)}
    
    async def take_screenshot(self, full_page: bool = False) -> Dict[str, Any]:
        """Take a screenshot of the browser."""
        try:
            return self.sandbox_manager.take_screenshot(self.session_id, full_page)
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return {'success': False, 'error': str(e)}
    
    async def process_file(self, file_path: str) -> Dict[str, Any]:
        """Process a document file."""
        try:
            return self.sandbox_manager.process_document(file_path, self.session_id)
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            return {'success': False, 'error': str(e)}
    
    async def cleanup(self):
        """Clean up sandbox resources."""
        try:
            self.sandbox_manager.cleanup_session(self.session_id)
        except Exception as e:
            logger.error(f"Error cleaning up Pure Python sandbox: {e}")


async def get_or_start_sandbox(sandbox_id: str):
    """
    Get or start a sandbox. 
    In Pure Python mode, creates a PurePythonSandbox.
    In Daytona mode, uses the original implementation.
    """
    if PURE_PYTHON_MODE and SANDBOX_MODE == "python":
        logger.debug(f"Creating Pure Python sandbox with ID: {sandbox_id}")
        
        # Initialize browser automation if needed
        sandbox_manager = get_sandbox_manager()
        if not hasattr(sandbox_manager, 'browser_instance') or not sandbox_manager.browser_instance:
            await asyncio.to_thread(sandbox_manager.init_browser_automation)
        
        return PurePythonSandbox(sandbox_id)
    
    else:
        # Use original Daytona implementation
        logger.debug(f"Using Daytona sandbox with ID: {sandbox_id}")
        return await get_or_start_sandbox(sandbox_id)  # Call original function


async def create_sandbox_from_snapshot(snapshot_name: str, resources: Optional[Dict] = None) -> str:
    """
    Create a sandbox from snapshot.
    In Pure Python mode, generates a unique session ID.
    In Daytona mode, uses the original implementation.
    """
    if PURE_PYTHON_MODE and SANDBOX_MODE == "python":
        import uuid
        sandbox_id = f"pure_python_{uuid.uuid4().hex[:8]}"
        logger.debug(f"Creating Pure Python sandbox from snapshot {snapshot_name}: {sandbox_id}")
        
        # Initialize sandbox manager components
        sandbox_manager = get_sandbox_manager()
        if not sandbox_manager.check_dependencies():
            logger.warning("Some Pure Python sandbox dependencies are missing")
            
        return sandbox_id
    
    else:
        # Use original Daytona implementation - this would need to be imported
        # from the original sandbox.py if it exists
        logger.debug(f"Creating Daytona sandbox from snapshot: {snapshot_name}")
        # Implementation would depend on original Daytona code
        raise NotImplementedError("Daytona sandbox creation not implemented in this adapter")


def is_pure_python_mode() -> bool:
    """Check if Pure Python sandbox mode is enabled."""
    return PURE_PYTHON_MODE and SANDBOX_MODE == "python"


async def initialize_sandbox_system():
    """Initialize the sandbox system."""
    if is_pure_python_mode():
        logger.info("Initializing Pure Python sandbox system")
        sandbox_manager = get_sandbox_manager()
        
        # Check dependencies
        if not sandbox_manager.check_dependencies():
            logger.error("Pure Python sandbox dependencies not available")
            return False
        
        # Initialize browser automation
        if not await asyncio.to_thread(sandbox_manager.init_browser_automation):
            logger.warning("Browser automation not available in Pure Python sandbox")
        
        logger.info("Pure Python sandbox system initialized successfully")
        return True
    else:
        logger.info("Using Daytona sandbox system")
        return True


async def cleanup_sandbox_system():
    """Clean up the sandbox system."""
    if is_pure_python_mode():
        logger.info("Cleaning up Pure Python sandbox system")
        sandbox_manager = get_sandbox_manager()
        sandbox_manager.cleanup()
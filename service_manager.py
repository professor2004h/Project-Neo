#!/usr/bin/env python3
"""
Service Manager for Suna - Pure Python Implementation
Replaces Docker Compose functionality with native Python process management
"""

import os
import sys
import time
import signal
import subprocess
import platform
import threading
import json
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import tempfile

IS_WINDOWS = platform.system() == "Windows"

class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


class ServiceManager:
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).absolute()
        self.backend_dir = self.project_root / "backend"
        # Frontend is now at root level
        self.frontend_dir = self.project_root
        self.processes: Dict[str, subprocess.Popen] = {}
        self.service_logs: Dict[str, List[str]] = {}
        self.running = False
        self.redis_process = None
        self.redis_port = 6379
        self.redis_data_dir = self.project_root / "redis_data"
        
    def print_info(self, message: str):
        print(f"{Colors.CYAN}ℹ️  {message}{Colors.ENDC}")
        
    def print_success(self, message: str):
        print(f"{Colors.GREEN}✅  {message}{Colors.ENDC}")
        
    def print_warning(self, message: str):
        print(f"{Colors.YELLOW}⚠️  {message}{Colors.ENDC}")
        
    def print_error(self, message: str):
        print(f"{Colors.RED}❌  {message}{Colors.ENDC}")

    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed."""
        deps = {
            "python3": "Python 3.11+",
            "node": "Node.js 20+", 
            "npm": "npm",
        }
        
        # Try to use pip instead of uv for now
        try:
            subprocess.run(["pip", "--version"], capture_output=True, check=True)
            deps["pip"] = "Python package manager (pip)"
            self.print_info("Using pip instead of uv for Python package management")
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.print_error("Neither pip nor uv is available")
            return False
            
        # Check Redis availability
        redis_available = self.check_redis_available()
        if not redis_available:
            self.print_warning("Redis not found. Will use embedded Redis alternative.")
        else:
            deps["redis-server"] = "Redis server"
            
        missing = []
        for cmd, desc in deps.items():
            if cmd == "redis-server" and not redis_available:
                continue
                
            try:
                cmd_to_check = cmd
                if IS_WINDOWS and cmd in ["python3"]:
                    cmd_to_check = "python"
                    
                result = subprocess.run(
                    [cmd_to_check, "--version"],
                    capture_output=True,
                    shell=IS_WINDOWS
                )
                if result.returncode == 0:
                    self.print_success(f"{desc} is available")
                else:
                    missing.append((cmd, desc))
            except FileNotFoundError:
                missing.append((cmd, desc))
                
        if missing:
            self.print_error("Missing dependencies:")
            for cmd, desc in missing:
                self.print_error(f"  - {desc} ({cmd})")
            return False
            
        return True

    def check_redis_available(self) -> bool:
        """Check if Redis server is available."""
        try:
            subprocess.run(
                ["redis-server", "--version"],
                capture_output=True,
                check=True,
                shell=IS_WINDOWS
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def setup_embedded_redis(self) -> bool:
        """Setup embedded Redis alternative using fakeredis."""
        try:
            # Check if fakeredis is available
            import fakeredis
            self.print_success("Using embedded Redis (fakeredis)")
            return True
        except ImportError:
            # Try to install fakeredis
            self.print_info("Installing embedded Redis alternative...")
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "fakeredis[json]"
                ], check=True)
                self.print_success("Embedded Redis installed successfully")
                return True
            except subprocess.CalledProcessError:
                self.print_error("Failed to install embedded Redis")
                return False

    def start_redis(self) -> bool:
        """Start Redis server or embedded alternative."""
        if self.check_redis_available():
            return self.start_redis_server()
        else:
            return self.setup_embedded_redis()

    def start_redis_server(self) -> bool:
        """Start Redis server process."""
        self.print_info(f"Starting Redis server on port {self.redis_port}...")
        
        # Create data directory
        self.redis_data_dir.mkdir(exist_ok=True)
        
        cmd = [
            "redis-server",
            "--port", str(self.redis_port),
            "--dir", str(self.redis_data_dir),
            "--appendonly", "yes",
            "--bind", "127.0.0.1",
            "--protected-mode", "no",
            "--maxmemory", "1gb",
            "--maxmemory-policy", "allkeys-lru",
        ]
        
        try:
            self.redis_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.project_root)
            )
            
            # Wait a moment for Redis to start
            time.sleep(2)
            
            # Check if Redis is responding
            if self.check_redis_connection():
                self.print_success(f"Redis server started on port {self.redis_port}")
                return True
            else:
                self.print_error("Redis server failed to start properly")
                return False
                
        except Exception as e:
            self.print_error(f"Failed to start Redis: {e}")
            return False

    def check_redis_connection(self) -> bool:
        """Check if Redis is accessible."""
        try:
            result = subprocess.run(
                ["redis-cli", "-p", str(self.redis_port), "ping"],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.stdout.strip() == "PONG"
        except:
            return False

    def start_backend(self) -> bool:
        """Start the backend API server."""
        self.print_info("Starting backend API server...")
        
        backend_env = os.environ.copy()
        backend_env["REDIS_HOST"] = "localhost"
        backend_env["REDIS_PORT"] = str(self.redis_port)
        
        # Use python directly instead of uv
        python_cmd = "python" if IS_WINDOWS else "python3"
        cmd = [
            python_cmd, "-m", "uvicorn", 
            "api:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload",
            "--log-level", "info"
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                cwd=str(self.backend_dir),
                env=backend_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes["backend"] = process
            self.service_logs["backend"] = []
            
            # Start log monitoring thread
            threading.Thread(
                target=self._monitor_process_logs,
                args=("backend", process),
                daemon=True
            ).start()
            
            # Wait a moment and check if it's running
            time.sleep(3)
            if process.poll() is None:
                self.print_success("Backend API server started on http://localhost:8000")
                return True
            else:
                self.print_error("Backend API server failed to start")
                return False
                
        except Exception as e:
            self.print_error(f"Failed to start backend: {e}")
            return False

    def start_worker(self) -> bool:
        """Start the background worker process."""
        self.print_info("Starting background worker...")
        
        worker_env = os.environ.copy()
        worker_env["REDIS_HOST"] = "localhost"
        worker_env["REDIS_PORT"] = str(self.redis_port)
        
        python_cmd = "python" if IS_WINDOWS else "python3"
        cmd = [
            python_cmd, "-m", "dramatiq",
            "--processes", "2",
            "--threads", "4",
            "run_agent_background"
        ]
        
        try:
            process = subprocess.Popen(
                cmd,
                cwd=str(self.backend_dir),
                env=worker_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            self.processes["worker"] = process
            self.service_logs["worker"] = []
            
            # Start log monitoring thread
            threading.Thread(
                target=self._monitor_process_logs,
                args=("worker", process),
                daemon=True
            ).start()
            
            # Wait a moment and check if it's running
            time.sleep(2)
            if process.poll() is None:
                self.print_success("Background worker started")
                return True
            else:
                self.print_error("Background worker failed to start")
                return False
                
        except Exception as e:
            self.print_error(f"Failed to start worker: {e}")
            return False

    def start_frontend(self) -> bool:
        """Start the frontend development server."""
        self.print_info("Starting frontend server...")
        
        # Check if dependencies are installed
        if not (self.frontend_dir / "node_modules").exists():
            self.print_info("Installing frontend dependencies...")
            result = subprocess.run(
                ["npm", "install"],
                cwd=str(self.frontend_dir),
                shell=IS_WINDOWS
            )
            if result.returncode != 0:
                self.print_error("Failed to install frontend dependencies")
                return False
        
        cmd = ["npm", "run", "dev"]
        
        try:
            process = subprocess.Popen(
                cmd,
                cwd=str(self.frontend_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=IS_WINDOWS
            )
            
            self.processes["frontend"] = process
            self.service_logs["frontend"] = []
            
            # Start log monitoring thread
            threading.Thread(
                target=self._monitor_process_logs,
                args=("frontend", process),
                daemon=True
            ).start()
            
            # Wait a moment and check if it's running
            time.sleep(5)
            if process.poll() is None:
                self.print_success("Frontend server started on http://localhost:3000")
                return True
            else:
                self.print_error("Frontend server failed to start")
                return False
                
        except Exception as e:
            self.print_error(f"Failed to start frontend: {e}")
            return False

    def _monitor_process_logs(self, service_name: str, process: subprocess.Popen):
        """Monitor process logs and store them."""
        while process.poll() is None:
            try:
                if process.stdout:
                    output = process.stdout.readline()
                    if output:
                        line = output.decode('utf-8', errors='ignore').strip()
                        if line:
                            self.service_logs[service_name].append(f"[STDOUT] {line}")
                            
                if process.stderr:
                    error = process.stderr.readline()
                    if error:
                        line = error.decode('utf-8', errors='ignore').strip()
                        if line:
                            self.service_logs[service_name].append(f"[STDERR] {line}")
            except:
                break

    def start_all_services(self) -> bool:
        """Start all services in the correct order."""
        self.print_info("Starting all Suna services...")
        
        if not self.check_dependencies():
            return False
        
        # Start Redis first
        if not self.start_redis():
            return False
        
        # Start backend
        if not self.start_backend():
            self.stop_all_services()
            return False
            
        # Start worker
        if not self.start_worker():
            self.stop_all_services()
            return False
            
        # Start frontend
        if not self.start_frontend():
            self.stop_all_services()
            return False
            
        self.running = True
        self.print_success("All services started successfully!")
        self.print_info("Access Suna at: http://localhost:3000")
        self.print_info("API available at: http://localhost:8000")
        
        return True

    def stop_all_services(self):
        """Stop all running services."""
        self.print_info("Stopping all services...")
        self.running = False
        
        # Stop processes
        for service_name, process in self.processes.items():
            try:
                self.print_info(f"Stopping {service_name}...")
                if IS_WINDOWS:
                    process.terminate()
                else:
                    process.send_signal(signal.SIGTERM)
                
                # Wait for graceful shutdown
                try:
                    process.wait(timeout=10)
                    self.print_success(f"{service_name} stopped")
                except subprocess.TimeoutExpired:
                    self.print_warning(f"{service_name} didn't stop gracefully, forcing...")
                    process.kill()
                    
            except Exception as e:
                self.print_warning(f"Error stopping {service_name}: {e}")
        
        # Stop Redis
        if self.redis_process:
            try:
                self.print_info("Stopping Redis server...")
                if IS_WINDOWS:
                    self.redis_process.terminate()
                else:
                    self.redis_process.send_signal(signal.SIGTERM)
                    
                try:
                    self.redis_process.wait(timeout=5)
                    self.print_success("Redis server stopped")
                except subprocess.TimeoutExpired:
                    self.redis_process.kill()
            except Exception as e:
                self.print_warning(f"Error stopping Redis: {e}")
                
        self.processes.clear()
        self.redis_process = None
        self.print_success("All services stopped")

    def get_status(self) -> Dict[str, str]:
        """Get status of all services."""
        status = {}
        
        # Check Redis
        if self.redis_process and self.redis_process.poll() is None:
            status["redis"] = "running"
        else:
            status["redis"] = "stopped"
            
        # Check other services
        for service_name, process in self.processes.items():
            if process.poll() is None:
                status[service_name] = "running"
            else:
                status[service_name] = "stopped"
                
        return status

    def show_logs(self, service_name: Optional[str] = None, lines: int = 50):
        """Show logs for a service or all services."""
        if service_name:
            if service_name in self.service_logs:
                logs = self.service_logs[service_name][-lines:]
                self.print_info(f"Last {len(logs)} lines for {service_name}:")
                for log in logs:
                    print(log)
            else:
                self.print_warning(f"No logs found for service: {service_name}")
        else:
            for svc_name, logs in self.service_logs.items():
                recent_logs = logs[-lines//len(self.service_logs):] if len(self.service_logs) > 0 else []
                if recent_logs:
                    self.print_info(f"Recent logs for {svc_name}:")
                    for log in recent_logs:
                        print(f"  {log}")
                    print()

    def wait_for_shutdown(self):
        """Wait for shutdown signal."""
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.print_info("\nShutdown requested...")
            self.stop_all_services()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Usage: python service_manager.py [COMMAND]")
        print("Commands:")
        print("  start    - Start all services")
        print("  stop     - Stop all services")
        print("  status   - Show service status")
        print("  logs     - Show service logs")
        print("  --help   - Show this help")
        return
    
    project_root = Path(__file__).parent
    manager = ServiceManager(str(project_root))
    
    command = sys.argv[1] if len(sys.argv) > 1 else "start"
    
    def signal_handler(signum, frame):
        manager.stop_all_services()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    if not IS_WINDOWS:
        signal.signal(signal.SIGTERM, signal_handler)
    
    if command == "start":
        if manager.start_all_services():
            try:
                manager.wait_for_shutdown()
            except KeyboardInterrupt:
                pass
    elif command == "stop":
        manager.stop_all_services()
    elif command == "status":
        status = manager.get_status()
        for service, state in status.items():
            color = Colors.GREEN if state == "running" else Colors.RED
            print(f"{service}: {color}{state}{Colors.ENDC}")
    elif command == "logs":
        service = sys.argv[2] if len(sys.argv) > 2 else None
        manager.show_logs(service)
    else:
        print(f"Unknown command: {command}")
        print("Use --help for usage information")


if __name__ == "__main__":
    main()
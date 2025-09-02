#!/usr/bin/env python3

import subprocess
import sys
import platform
import os
import json
from pathlib import Path

IS_WINDOWS = platform.system() == "Windows"
PROGRESS_FILE = ".setup_progress"

# Import our new service manager
try:
    from service_manager import ServiceManager
    PURE_PYTHON_AVAILABLE = True
except ImportError:
    PURE_PYTHON_AVAILABLE = False

# --- ANSI Colors ---
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


def load_progress():
    """Loads the last saved step and data from setup."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            try:
                return json.load(f)
            except (json.JSONDecodeError, KeyError):
                return {"step": 0, "data": {}}
    return {"step": 0, "data": {}}


def get_setup_method():
    """Gets the setup method chosen during setup."""
    progress = load_progress()
    return progress.get("data", {}).get("setup_method")


def check_docker_available():
    """Check if Docker is available and running."""
    try:
        result = subprocess.run(["docker", "version"], capture_output=True, shell=IS_WINDOWS, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def check_docker_compose_up():
    result = subprocess.run(
        ["docker", "compose", "ps", "-q"],
        capture_output=True,
        text=True,
        shell=IS_WINDOWS,
    )
    return len(result.stdout.strip()) > 0


def print_pure_python_instructions():
    """Prints instructions for pure Python setup."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}🚀 Pure Python Setup Instructions{Colors.ENDC}\n")

    print("Suna is now running in Pure Python mode without Docker!\n")

    print(f"{Colors.BOLD}Services running:{Colors.ENDC}")
    print(f"{Colors.GREEN}✅ Redis (embedded or local){Colors.ENDC}")
    print(f"{Colors.GREEN}✅ Backend API (uvicorn){Colors.ENDC}")
    print(f"{Colors.GREEN}✅ Background Worker (dramatiq){Colors.ENDC}")
    print(f"{Colors.GREEN}✅ Frontend (Next.js){Colors.ENDC}\n")

    print("Access Suna at: http://localhost:3000")
    print("API available at: http://localhost:8000\n")

    print(f"{Colors.BOLD}Management commands:{Colors.ENDC}")
    print(f"{Colors.CYAN}   python service_manager.py status{Colors.ENDC}  - Check service status")
    print(f"{Colors.CYAN}   python service_manager.py logs{Colors.ENDC}    - View service logs")
    print(f"{Colors.CYAN}   python service_manager.py stop{Colors.ENDC}    - Stop all services")


def print_legacy_manual_instructions():
    """Prints instructions for manually starting Suna services (legacy)."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}🚀 Manual Startup Instructions{Colors.ENDC}\n")

    print("To start Suna, you need to run these commands in separate terminals:\n")

    print(f"{Colors.BOLD}1. Start Infrastructure (in project root):{Colors.ENDC}")
    print(f"{Colors.CYAN}   docker compose up redis -d{Colors.ENDC}\n")

    print(f"{Colors.BOLD}2. Start Frontend (in a new terminal):{Colors.ENDC}")
    print(f"{Colors.CYAN}   cd frontend && npm run dev{Colors.ENDC}\n")

    print(f"{Colors.BOLD}3. Start Backend (in a new terminal):{Colors.ENDC}")
    print(f"{Colors.CYAN}   cd backend && uv run api.py{Colors.ENDC}\n")

    print(f"{Colors.BOLD}4. Start Background Worker (in a new terminal):{Colors.ENDC}")
    print(
        f"{Colors.CYAN}   cd backend && uv run dramatiq run_agent_background{Colors.ENDC}\n"
    )

    print("Once all services are running, access Suna at: http://localhost:3000\n")

    print(
        f"{Colors.YELLOW}💡 Tip:{Colors.ENDC} You can use '{Colors.CYAN}./start.py{Colors.ENDC}' to start/stop the infrastructure services."
    )


def main():
    setup_method = get_setup_method()

    if "--help" in sys.argv:
        print("Usage: ./start.py [OPTION]")
        print("Manage Suna services - Pure Python implementation (Docker-free)")
        print("\nOptions:")
        print("  -f\t\tForce start without confirmation")
        print("  --legacy\tUse legacy Docker-based mode")
        print("  --help\tShow this help message")
        return

    # Check if legacy Docker mode is requested
    legacy_mode = "--legacy" in sys.argv
    
    if legacy_mode:
        print(f"{Colors.YELLOW}⚠️  Running in legacy Docker mode{Colors.ENDC}")
        run_legacy_docker_mode()
        return

    # Default to Pure Python mode
    print(f"{Colors.BLUE}{Colors.BOLD}🐍 Pure Python Mode (Docker-free){Colors.ENDC}")
    
    if not PURE_PYTHON_AVAILABLE:
        print(f"{Colors.RED}❌ Pure Python service manager not available{Colors.ENDC}")
        print(f"{Colors.YELLOW}Falling back to legacy mode...{Colors.ENDC}")
        run_legacy_docker_mode()
        return

    project_root = Path(__file__).parent
    manager = ServiceManager(str(project_root))

    force = "-f" in sys.argv
    if force:
        print("Force mode enabled. Skipping confirmation.")

    # Check if services are already running
    status = manager.get_status()
    services_running = any(state == "running" for state in status.values())

    if services_running:
        action = "stop"
        msg = "🛑 Stop all Suna services? [y/N] "
    else:
        action = "start"
        msg = "⚡ Start all Suna services? [Y/n] "

    if not force:
        response = input(msg).strip().lower()
        if action == "stop":
            if response != "y":
                print("Aborting.")
                return
        else:
            if response == "n":
                print("Aborting.")
                return

    if action == "stop":
        manager.stop_all_services()
    else:
        if manager.start_all_services():
            print_pure_python_instructions()
            try:
                manager.wait_for_shutdown()
            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}Shutdown requested...{Colors.ENDC}")
                manager.stop_all_services()


def run_legacy_docker_mode():
    """Run in legacy Docker mode for backward compatibility."""
    setup_method = get_setup_method()

    # If setup hasn't been run or method is not determined, default to docker
    if not setup_method:
        print(
            f"{Colors.YELLOW}⚠️  Setup method not detected. Run './setup.py' first or using Docker Compose as default.{Colors.ENDC}"
        )
        setup_method = "docker"

    if setup_method == "manual":
        # For manual setup, we only manage infrastructure services (redis)
        # and show instructions for the rest
        print(f"{Colors.BLUE}{Colors.BOLD}Manual Setup Detected{Colors.ENDC}")
        print("Managing infrastructure services (Redis)...\n")

        force = "-f" in sys.argv
        if force:
            print("Force awakened. Skipping confirmation.")

        is_infra_up = subprocess.run(
            ["docker", "compose", "ps", "-q", "redis"],
            capture_output=True,
            text=True,
            shell=IS_WINDOWS,
        )
        is_up = len(is_infra_up.stdout.strip()) > 0

        if is_up:
            action = "stop"
            msg = "🛑 Stop infrastructure services? [y/N] "
        else:
            action = "start"
            msg = "⚡ Start infrastructure services? [Y/n] "

        if not force:
            response = input(msg).strip().lower()
            if action == "stop":
                if response != "y":
                    print("Aborting.")
                    return
            else:
                if response == "n":
                    print("Aborting.")
                    return

        if action == "stop":
            subprocess.run(["docker", "compose", "down"], shell=IS_WINDOWS)
            print(f"\n{Colors.GREEN}✅ Infrastructure services stopped.{Colors.ENDC}")
        else:
            subprocess.run(
                ["docker", "compose", "up", "redis", "-d"], shell=IS_WINDOWS
            )
            print(f"\n{Colors.GREEN}✅ Infrastructure services started.{Colors.ENDC}")
            print_legacy_manual_instructions()

    else:  # docker setup
        print(f"{Colors.BLUE}{Colors.BOLD}Docker Setup Detected{Colors.ENDC}")
        print("Managing all Suna services with Docker Compose...\n")

        force = "-f" in sys.argv
        if force:
            print("Force awakened. Skipping confirmation.")

        if not check_docker_available():
            print(f"{Colors.RED}❌ Docker is not running or not installed.{Colors.ENDC}")
            print(f"{Colors.YELLOW}Please start Docker and try again, or use pure Python mode.{Colors.ENDC}")
            return
            
        is_up = check_docker_compose_up()

        if is_up:
            action = "stop"
            msg = "🛑 Stop all Suna services? [y/N] "
        else:
            action = "start"
            msg = "⚡ Start all Suna services? [Y/n] "

        if not force:
            response = input(msg).strip().lower()
            if action == "stop":
                if response != "y":
                    print("Aborting.")
                    return
            else:
                if response == "n":
                    print("Aborting.")
                    return

        if action == "stop":
            subprocess.run(["docker", "compose", "down"], shell=IS_WINDOWS)
            print(f"\n{Colors.GREEN}✅ All Suna services stopped.{Colors.ENDC}")
        else:
            subprocess.run(["docker", "compose", "up", "-d"], shell=IS_WINDOWS)
            print(f"\n{Colors.GREEN}✅ All Suna services started.{Colors.ENDC}")
            print(f"{Colors.CYAN}🌐 Access Suna at: http://localhost:3000{Colors.ENDC}")


if __name__ == "__main__":
    main()

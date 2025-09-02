#!/usr/bin/env python3

import sys
import platform
from pathlib import Path

# Import our service manager
try:
    from service_manager import ServiceManager
    PURE_PYTHON_AVAILABLE = True
except ImportError:
    PURE_PYTHON_AVAILABLE = False

IS_WINDOWS = platform.system() == "Windows"

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


# Setup progress functions removed - Pure Python mode only


# Docker functionality removed - Pure Python mode only


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


# Legacy Docker instructions removed - Pure Python mode only


def main():
    if "--help" in sys.argv:
        print("Usage: ./start.py [OPTION]")
        print("Manage Suna services - Pure Python implementation (Docker-free)")
        print("\nOptions:")
        print("  -f\t\tForce start without confirmation")
        print("  --help\tShow this help message")
        return

    # Pure Python mode only
    print(f"{Colors.BLUE}{Colors.BOLD}🐍 Pure Python Mode (Docker-free){Colors.ENDC}")
    
    if not PURE_PYTHON_AVAILABLE:
        print(f"{Colors.RED}❌ Pure Python service manager not available{Colors.ENDC}")
        print(f"{Colors.RED}Please ensure service_manager.py is properly configured{Colors.ENDC}")
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


# Legacy Docker mode removed - Pure Python mode only


if __name__ == "__main__":
    main()

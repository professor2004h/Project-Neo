import logging
from utils.env_manager import EnvironmentManager
from utils.docker_manager import DockerServiceManager

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class StatusChecker:
    """
    Provides comprehensive status checking for the local development environment.
    """
    def __init__(self):
        """
        Initializes the StatusChecker.
        """
        # We pass an empty config dict as it's not needed for validation checks
        self.env_manager = EnvironmentManager({})
        self.docker_manager = DockerServiceManager()

    def check_all(self) -> dict:
        """
        Runs all status checks and aggregates the results.
        """
        return {
            "configuration": self.check_configuration(),
            "docker_services": self.check_docker_services(),
        }

    def check_configuration(self) -> dict:
        """
        Checks the status of the environment configuration files.
        """
        return {
            "files_exist": self.env_manager.validate_env_files(),
        }

    def check_docker_services(self) -> dict:
        """
        Checks the status of required Docker services.
        """
        docker_available = self.docker_manager.check_docker_available()
        service_status = self.docker_manager.get_service_status() if docker_available else {}
        return {
            "docker_available": docker_available,
            "services": service_status,
        }

    def display_status_report(self, status: dict) -> None:
        """
        Displays a formatted status report to the console with troubleshooting guidance.
        """
        print("📊 Suna Local Development Status\n")
        all_ok = True

        # Configuration Check
        print("Configuration:")
        if status["configuration"]["files_exist"]:
            print("  ✅ Backend and Frontend environment files exist.")
        else:
            print("  ❌ Missing environment files.")
            print("     - Recommendation: Run 'python local-dev.py' to generate them.")
            all_ok = False

        # Docker Services Check
        print("\nDocker Services:")
        if status["docker_services"]["docker_available"]:
            print("  ✅ Docker daemon is running.")
            services = status["docker_services"]["services"]
            if not services:
                print("  ⚠️ Could not determine service status. Ensure Docker is properly configured.")
                all_ok = False

            for service, is_running in services.items():
                if is_running:
                    print(f"  ✅ {service.capitalize()} is running.")
                else:
                    print(f"  ❌ {service.capitalize()} is not running.")
                    print(f"     - Recommendation: Run 'docker compose up -d {service}' in the 'backend' directory.")
                    all_ok = False
        else:
            print("  ❌ Docker is not running.")
            print("     - Recommendation: Please start the Docker Desktop application.")
            all_ok = False

        if all_ok:
            print("\nReady for development! 🎉")
        else:
            print("\nSome checks failed. Please review the recommendations above. ❌")

    def _is_all_ok(self, status: dict) -> bool:
        """
        Checks if all components of the status report are 'OK'.
        """
        if not status["configuration"]["files_exist"]:
            return False
        if not status["docker_services"]["docker_available"]:
            return False
        if not all(status["docker_services"]["services"].values()):
            return False
        return True

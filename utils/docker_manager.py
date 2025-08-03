import subprocess
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class DockerServiceManager:
    """
    Manages Docker services required for local development.
    """
    def __init__(self):
        """
        Initializes the DockerServiceManager.
        """
        self.required_services = ['redis', 'rabbitmq']

    def check_docker_available(self) -> bool:
        """
        Checks if the Docker daemon is running.

        Returns:
            bool: True if Docker is running, False otherwise.
        """
        try:
            subprocess.run(["docker", "info"], check=True, capture_output=True)
            logging.info("Docker is available.")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logging.error("Docker is not running or not installed. Please start Docker and try again.")
            return False

    def start_services(self) -> bool:
        """
        Starts the required Docker services using docker-compose.

        Returns:
            bool: True if services start successfully, False otherwise.
        """
        if not self.check_docker_available():
            return False

        command = ["docker-compose", "up", "-d"] + self.required_services
        try:
            # Assuming docker-compose.yml is in the `backend` directory
            subprocess.run(command, check=True, capture_output=True, cwd="backend")
            logging.info(f"Successfully started Docker services: {', '.join(self.required_services)}")
            
            # Wait a moment for services to initialize
            time.sleep(10)
            return True
        except subprocess.CalledProcessError as e:
            logging.error(f"Failed to start Docker services. Error: {e.stderr.decode().strip()}")
            return False
        except FileNotFoundError:
            logging.error("Could not find docker-compose.yml in the `backend` directory.")
            return False

    def check_service_health(self, service_name: str) -> bool:
        """
        Checks the health of a specific Docker service.

        Args:
            service_name (str): The name of the service to check.

        Returns:
            bool: True if the service is running, False otherwise.
        """
        try:
            result = subprocess.run(
                ["docker-compose", "ps", "-q", service_name],
                check=True,
                capture_output=True,
                text=True,
                cwd="backend"
            )
            is_running = bool(result.stdout.strip())
            if is_running:
                logging.info(f"Service '{service_name}' is running.")
            else:
                logging.warning(f"Service '{service_name}' is not running.")
            return is_running
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logging.error(f"Error checking health of service '{service_name}': {e}")
            return False

    def get_service_status(self) -> dict:
        """
        Gets the status of all required Docker services.

        Returns:
            dict: A dictionary mapping service names to their running status (bool).
        """
        status = {}
        if not self.check_docker_available():
            for service in self.required_services:
                status[service] = False
            return status

        for service in self.required_services:
            status[service] = self.check_service_health(service)
        return status

import os
import sys
import re
from typing import Dict, Any

from utils.env_manager import EnvironmentManager
from utils.docker_manager import DockerServiceManager


class LocalDevSetup:
    """
    Orchestrates the local development setup process.
    """

    def __init__(self, skip_optional=False, reset=False):
        """
        Initializes the LocalDevSetup with default configuration.
        """
        self.config: Dict[str, Any] = {}
        self.env_manager = EnvironmentManager(self.config)
        self.docker_manager = DockerServiceManager()
        self.required_services = ['supabase', 'llm']
        self.optional_services = ['search', 'rapidapi', 'qstash', 'slack', 'pipedream']
        self.skip_optional = skip_optional
        self.reset = reset

    def check_requirements(self) -> bool:
        """
        Checks if the required dependencies (Docker) are available.
        """
        print("Checking requirements...")
        if not self.docker_manager.check_docker_available():
            print("Error: Docker is not installed or not running.")
            print("Please install Docker and ensure it is running before proceeding.")
            return False
        print("Requirements met.")
        return True

    def _get_user_input(self, prompt: str, validation_regex: str = None) -> str:
        """
        Prompts the user for input and validates it against a regex.
        """
        while True:
            user_input = input(prompt)
            if not user_input:
                return ""
            if validation_regex:
                if re.match(validation_regex, user_input):
                    return user_input
                else:
                    print("Invalid input. Please try again.")
            else:
                return user_input

    def collect_essential_config(self) -> None:
        """
        Collects essential configuration from the user.
        """
        print("\nCollecting essential configuration...")
        self.config['supabase'] = {
            'url': self._get_user_input("Enter your Supabase project URL: ", r"^https?://[^\s/$.?#].[^\s]*$"),
            'anon_key': self._get_user_input("Enter your Supabase anonymous key: "),
            'service_role_key': self._get_user_input("Enter your Supabase service role key: "),
        }
        llm_provider = self._get_user_input("Enter your LLM provider (e.g., openai, anthropic): ", r"^(openai|anthropic|gemini|openrouter)$").lower()
        self.config['llm'] = {
            'provider': llm_provider,
            'api_key': self._get_user_input(f"Enter your {llm_provider.capitalize()} API key: "),
            'model': self._get_user_input("Enter the model name to use (e.g., gpt-4): "),
        }
        print("Essential configuration collected.")

    def collect_optional_config(self) -> None:
        """
        Collects optional configuration from the user.
        """
        if self.skip_optional:
            print("\nSkipping optional services.")
            return
        print("\nCollecting optional configuration (press Enter to skip)...")
        self.config['optional'] = {}
        tavily_key = self._get_user_input("Enter your Tavily API key (optional): ")
        firecrawl_key = self._get_user_input("Enter your Firecrawl API key (optional): ")
        if tavily_key or firecrawl_key:
            self.config['optional']['search'] = {
                'tavily_key': tavily_key,
                'firecrawl_key': firecrawl_key,
            }
        daytona_api_key = self._get_user_input("Enter your Daytona API key (optional): ")
        if daytona_api_key:
            self.config['optional']['daytona'] = {'api_key': daytona_api_key}

    def configure_environment_files(self) -> None:
        """
        Creates the backend and frontend environment files.
        """
        print("\nConfiguring environment files...")
        self.env_manager.config = self.config  # Ensure env_manager has the latest config
        if self.reset:
            print("Resetting environment files...")
        self.env_manager.backup_existing_files()
        self.env_manager.create_backend_env()
        self.env_manager.create_frontend_env()
        print("Environment files configured.")

    def start_docker_services(self) -> bool:
        """
        Starts the required Docker services.
        """
        print("\nStarting Docker services...")
        if self.docker_manager.start_services():
            print("Docker services started successfully.")
            return True
        else:
            print("Error: Failed to start Docker services.")
            return False

    def validate_setup(self) -> bool:
        """
        Validates the entire setup.
        """
        print("\nValidating setup...")
        if not self.env_manager.validate_env_files():
            print("Error: Environment file validation failed.")
            return False
        for service in self.docker_manager.required_services:
            if not self.docker_manager.check_service_health(service):
                print(f"Error: Docker service '{service}' is not healthy.")
                return False
        print("Setup validated successfully.")
        return True

    def display_run_commands(self) -> None:
        """
        Displays the commands to run the frontend and backend.
        """
        print("\n🚀 Suna Local Development Setup Complete!")
        print("\nTo start your development environment:")
        print("\nBackend (Terminal 1):")
        print("  cd backend")
        print("  docker compose up redis rabbitmq -d")
        print("  uv run api.py")
        print("\nWorker (Terminal 2):")
        print("  cd backend")
        print("  uv run dramatiq --processes 4 --threads 4 run_agent_background")
        print("\nFrontend (Terminal 3):")
        print("  cd frontend")
        print("  npm install")
        print("  npm run dev")
        print("\nYour services will be available at:")
        print("  - Frontend: http://localhost:3000")
        print("  - Backend API: http://localhost:8000/api")
        print("  - Redis: localhost:6379")
        print("  - RabbitMQ: localhost:5672 (Management: http://localhost:15672)")

    def run(self) -> None:
        """
        Runs the entire local development setup process.
        """
        if not self.check_requirements():
            sys.exit(1)

        self.collect_essential_config()
        self.collect_optional_config()
        self.configure_environment_files()
        if not self.start_docker_services():
            sys.exit(1)
        if not self.validate_setup():
            print("\nSetup failed validation. Please check the errors above.")
            sys.exit(1)
        self.display_run_commands()

if __name__ == '__main__':
    skip = '--skip-optional' in sys.argv
    reset_env = '--reset' in sys.argv
    setup = LocalDevSetup(skip_optional=skip, reset=reset_env)
    setup.run()

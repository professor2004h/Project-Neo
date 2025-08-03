import os
import shutil
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class EnvironmentManager:
    """
    Handles creation and management of environment files for local development.
    """
    def __init__(self, config: dict):
        """
        Initializes the EnvironmentManager with a given configuration.

        Args:
            config (dict): A dictionary containing configuration values.
        """
        self.config = config
        self.backend_env_path = "backend/.env"
        self.frontend_env_path = "frontend/.env.local"
        self.backup_dir = "backup"

    def backup_existing_files(self) -> None:
        """
        Backs up existing backend and frontend environment files.
        """
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
            logging.info(f"Created backup directory at {self.backup_dir}")

        for env_path in [self.backend_env_path, self.frontend_env_path]:
            if os.path.exists(env_path):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(self.backup_dir, f"{os.path.basename(env_path)}_{timestamp}.bak")
                shutil.copy2(env_path, backup_path)
                logging.info(f"Backed up {env_path} to {backup_path}")

    def create_backend_env(self) -> None:
        """
        Creates the backend .env file from a template and configuration.
        """
        template = """
# Local Development Configuration
ENV_MODE=local

# Database (Required)
SUPABASE_URL={supabase_url}
SUPABASE_ANON_KEY={supabase_anon_key}
SUPABASE_SERVICE_ROLE_KEY={supabase_service_role_key}

# Infrastructure (Local Docker)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_SSL=false
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672

# LLM Provider (Required)
{llm_provider}_API_KEY={llm_api_key}
MODEL_TO_USE={model_name}

# Optional Services (can be empty for local dev)
TAVILY_API_KEY={tavily_key}
FIRECRAWL_API_KEY={firecrawl_key}
FIRECRAWL_URL=https://api.firecrawl.dev
DAYTONA_API_KEY={daytona_key}
DAYTONA_SERVER_URL=https://app.daytona.io/api
DAYTONA_TARGET=us

# MCP Configuration
MCP_CREDENTIAL_ENCRYPTION_KEY={generated_key}
"""
        # A secure key is not generated here as it's part of a later task.
        # For now, a placeholder is used.
        generated_key = self.config.get("mcp_credential_encryption_key", "dummy_key_placeholder")

        content = template.format(
            supabase_url=self.config.get("supabase", {}).get("url", ""),
            supabase_anon_key=self.config.get("supabase", {}).get("anon_key", ""),
            supabase_service_role_key=self.config.get("supabase", {}).get("service_role_key", ""),
            llm_provider=self.config.get("llm", {}).get("provider", "OPENAI").upper(),
            llm_api_key=self.config.get("llm", {}).get("api_key", ""),
            model_name=self.config.get("llm", {}).get("model", ""),
            tavily_key=self.config.get("optional", {}).get("search", {}).get("tavily_key", ""),
            firecrawl_key=self.config.get("optional", {}).get("search", {}).get("firecrawl_key", ""),
            daytona_key=self.config.get("optional", {}).get("daytona", {}).get("api_key", ""),
            generated_key=generated_key
        )

        with open(self.backend_env_path, "w") as f:
            f.write(content.strip())
        os.chmod(self.backend_env_path, 0o600)
        logging.info(f"Created backend environment file at {self.backend_env_path}")

    def create_frontend_env(self) -> None:
        """
        Creates the frontend .env.local file from a template and configuration.
        """
        template = """
# Local Development Configuration
NEXT_PUBLIC_ENV_MODE=LOCAL
NEXT_PUBLIC_SUPABASE_URL={supabase_url}
NEXT_PUBLIC_SUPABASE_ANON_KEY={supabase_anon_key}
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000/api
NEXT_PUBLIC_URL=http://localhost:3000
"""
        content = template.format(
            supabase_url=self.config.get("supabase", {}).get("url", ""),
            supabase_anon_key=self.config.get("supabase", {}).get("anon_key", ""),
        )

        with open(self.frontend_env_path, "w") as f:
            f.write(content.strip())
        os.chmod(self.frontend_env_path, 0o600)
        logging.info(f"Created frontend environment file at {self.frontend_env_path}")


    def validate_env_files(self) -> bool:
        """
        Validates that the environment files have been created.

        Returns:
            bool: True if both files exist, False otherwise.
        """
        backend_exists = os.path.exists(self.backend_env_path)
        frontend_exists = os.path.exists(self.frontend_env_path)

        if not backend_exists:
            logging.error(f"Backend environment file not found at {self.backend_env_path}")
        if not frontend_exists:
            logging.error(f"Frontend environment file not found at {self.frontend_env_path}")

        return backend_exists and frontend_exists

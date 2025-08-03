# Local Development Guide

This guide provides comprehensive instructions for setting up a local development environment for Suna. This setup is designed for developers who want to contribute to the project or run a lightweight instance for testing and development purposes. It configures only the essential services to get you up and running quickly.

## Quick Start

1.  **Clone the Repository**

    If you haven't already, clone the Suna repository to your local machine:
    ```bash
    git clone https://github.com/kortix-ai/suna.git
    cd suna
    ```

2.  **Run the Local Setup Script**

    Execute the local development setup script from the root of the project:
    ```bash
    python local-dev.py
    ```
    The script will prompt you for essential configuration details, such as your Supabase credentials and your preferred LLM provider.

3.  **Check Environment Status**

    After the setup is complete, you can verify your environment's status at any time by running:
    ```bash
    python local-dev-status.py
    ```
    This command checks your configuration files and ensures that all required services (like Docker) are running correctly.

## Detailed Setup Process

The `local-dev.py` script automates the following steps:

1.  **Requirement Checks**: Verifies that Docker is installed and running.
2.  **Configuration Collection**: Prompts for your Supabase URL and keys, and your LLM provider details.
3.  **Environment File Generation**: Creates `.env` for the backend and `.env.local` for the frontend with the appropriate configurations for local development.
4.  **Docker Service Initialization**: Starts the required Docker containers (`redis` and `rabbitmq`).
5.  **Validation**: Performs a final check to ensure all components are configured correctly.

### Running the Application

Once the setup is successful, the script will display the commands needed to run the backend, frontend, and worker processes in separate terminals.

-   **Backend**: `cd backend && docker-compose up -d redis rabbitmq && uv run api.py`
-   **Worker**: `cd backend && uv run dramatiq --processes 4 --threads 4 run_agent_background`
-   **Frontend**: `cd frontend && npm install && npm run dev`

## Troubleshooting

If you encounter any issues during the setup process, here are some common problems and their solutions:

| Error Message                      | Recommendation                                                                      |
| ---------------------------------- | ----------------------------------------------------------------------------------- |
| **Docker is not running**          | Ensure that Docker Desktop is running on your machine before starting the setup.      |
| **Missing environment files**      | Run `python local-dev.py` to regenerate the necessary `.env` files.                 |
| **Redis/RabbitMQ is not running**  | Run `docker-compose up -d redis rabbitmq` inside the `backend` directory.             |
| **Port conflict**                  | If a required port (e.g., 6379, 5672) is in use, stop the conflicting process.        |

For more complex issues, please refer to the main [Self-Hosting Guide](./SELF-HOSTING.md) or open an issue on our [GitHub repository](https://github.com/kortix-ai/suna/issues).

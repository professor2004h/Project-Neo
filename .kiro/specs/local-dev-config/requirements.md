# Requirements Document

## Introduction

This feature aims to create a streamlined configuration system for setting up Suna's frontend and backend for local development. While the existing setup.py wizard is comprehensive for production deployment, developers need a simpler, faster way to configure their local development environment with minimal required services and clear terminal-based instructions for running both frontend and backend locally.

## Requirements

### Requirement 1

**User Story:** As a developer, I want a quick local development setup command, so that I can start coding on Suna without going through the full production setup wizard.

#### Acceptance Criteria

1. WHEN a developer runs a local development setup command THEN the system SHALL create minimal configuration files for local development
2. WHEN the local setup runs THEN the system SHALL only require essential services (Supabase, at least one LLM provider)
3. WHEN the local setup completes THEN the system SHALL provide clear terminal commands to run frontend and backend separately
4. IF the developer already has some configuration THEN the system SHALL preserve existing values and only prompt for missing essentials

### Requirement 2

**User Story:** As a developer, I want clear terminal commands to run frontend and backend independently, so that I can develop and debug each service separately.

#### Acceptance Criteria

1. WHEN the setup completes THEN the system SHALL display exact terminal commands for running the backend locally
2. WHEN the setup completes THEN the system SHALL display exact terminal commands for running the frontend locally
3. WHEN running locally THEN the backend SHALL connect to local Redis and RabbitMQ containers
4. WHEN running locally THEN the frontend SHALL connect to the locally running backend API

### Requirement 3

**User Story:** As a developer, I want to skip optional services during local setup, so that I can get started quickly without configuring every integration.

#### Acceptance Criteria

1. WHEN running local setup THEN the system SHALL mark services like RapidAPI, QStash, Pipedream, and Slack as optional
2. WHEN optional services are skipped THEN the system SHALL still create a working local environment
3. WHEN optional services are needed later THEN the developer SHALL be able to run the full setup wizard
4. IF essential services are missing THEN the system SHALL prompt for them before proceeding

### Requirement 4

**User Story:** As a developer, I want the local setup to handle Docker services automatically, so that I don't need to manually manage Redis and RabbitMQ containers.

#### Acceptance Criteria

1. WHEN local setup runs THEN the system SHALL automatically start required Docker services (Redis, RabbitMQ)
2. WHEN Docker services are already running THEN the system SHALL detect and reuse them
3. WHEN Docker is not available THEN the system SHALL provide clear error messages and installation instructions
4. WHEN services fail to start THEN the system SHALL provide troubleshooting guidance

### Requirement 5

**User Story:** As a developer, I want environment files configured correctly for local development, so that services can communicate properly when running on localhost.

#### Acceptance Criteria

1. WHEN local setup runs THEN the system SHALL configure backend .env with localhost Redis and RabbitMQ hosts
2. WHEN local setup runs THEN the system SHALL configure frontend .env.local with localhost backend URL
3. WHEN environment files exist THEN the system SHALL backup existing files before making changes
4. WHEN configuration is complete THEN the system SHALL validate that all required environment variables are set

### Requirement 6

**User Story:** As a developer, I want a status command to check my local development environment, so that I can quickly diagnose configuration issues.

#### Acceptance Criteria

1. WHEN a developer runs the status command THEN the system SHALL check if all required services are configured
2. WHEN a developer runs the status command THEN the system SHALL check if Docker services are running
3. WHEN a developer runs the status command THEN the system SHALL validate environment file configurations
4. WHEN issues are found THEN the system SHALL provide specific guidance on how to fix them
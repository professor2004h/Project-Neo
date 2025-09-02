# Suna - Unified Next.js Application

This repository has been consolidated into a single Next.js application that includes both frontend and backend functionality.

## Structure

- **Root Directory**: Contains the Next.js application with all frontend code
- **backend/**: Contains the Python FastAPI backend (integrated via proxying)
- **src/**: Frontend React/TypeScript code
- **public/**: Static assets

## Configuration

All environment variables are now consolidated in `.env` at the root level with hardcoded API keys and configuration.

## Getting Started

### Prerequisites

- Node.js 20+
- Python 3.11+
- pip (Python package manager)

### Installation

1. Install frontend dependencies:
```bash
npm install
```

2. Install backend Python dependencies:
```bash
cd backend
pip install -r ../pure_python_requirements.txt
# You may also need to install the dependencies from pyproject.toml manually
```

### Running the Application

#### Unified Startup (Recommended)

Start both frontend and backend together:

```bash
python start.py
```

This will start:
- Redis (embedded)
- Python FastAPI backend on port 8000
- Background worker for agent tasks
- Next.js frontend on port 3000 (with API proxying)

#### Manual Startup

1. Start backend only:
```bash
npm run backend
```

2. Start frontend only:
```bash
npm run dev
```

3. Start all services:
```bash
npm run start-all
```

## API Integration

The Next.js application is configured to proxy all `/api/*` requests to the Python backend running on `localhost:8000`.

This allows the frontend to call backend APIs as if they were Next.js API routes:

```typescript
// This will be proxied to http://localhost:8000/api/agents
fetch('/api/agents')
```

## Environment Variables

All required environment variables are hardcoded in `.env`:

- Supabase configuration
- API keys for LLM providers (OpenAI, Anthropic, etc.)
- External service keys (Tavily, Firecrawl, etc.)
- Infrastructure settings (Redis, webhooks)

## Building for Production

```bash
npm run build
```

This creates an optimized production build of the Next.js application.

## Development

The application supports hot reloading for both frontend and backend during development.

## Architecture

- **Frontend**: Next.js 15 with React, TypeScript, Tailwind CSS
- **Backend**: FastAPI with Python, integrated via reverse proxy
- **Database**: Supabase (PostgreSQL)
- **Caching**: Redis (embedded for development)
- **Deployment**: Can be deployed as a single application unit
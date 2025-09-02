# Pure Python Setup Guide

Suna runs completely natively in Python! This guide explains the Pure Python mode.

## What's New

- **No Docker Required**: All services run as native Python/Node.js processes
- **Better Performance**: No container overhead, direct access to system resources  
- **Easier Debugging**: Native processes, standard logging, familiar tooling
- **Simplified Deployment**: Single Python environment, no container orchestration

## Quick Start

1. **Clone and Setup**
   ```bash
   git clone https://github.com/kortix-ai/suna.git
   cd suna
   python setup.py
   ```
   Choose "Pure Python" when prompted (option 1).

2. **Start Services**
   ```bash
   python start.py
   ```
   This starts all services: Redis, Backend API, Worker, and Frontend.

3. **Access Suna**
   - Web UI: http://localhost:3000
   - API: http://localhost:8000

## Service Management

The Pure Python mode includes a comprehensive service manager:

```bash
# Start all services  
python start.py

# Service management
python service_manager.py start    # Start services
python service_manager.py stop     # Stop services
python service_manager.py status   # Check status
python service_manager.py logs     # View logs
```

## Architecture

### Services Running

1. **Redis** - Local Redis server or embedded alternative (fakeredis)
2. **Backend API** - FastAPI server with uvicorn
3. **Background Worker** - Dramatiq worker for background tasks  
4. **Frontend** - Next.js development server
5. **Sandbox** - Python-based code execution environment

### Key Features

- **Process Management**: Automatic process lifecycle management
- **Health Monitoring**: Built-in health checks and restart logic
- **Logging**: Centralized logging from all services
- **Isolation**: Sandboxed code execution without containers
- **Browser Automation**: Playwright-based browser control

## Requirements

- **Python 3.11+** with `uv` package manager
- **Node.js 20+** with npm
- **Git** for repository management

Optional but recommended:
- **Redis** server (uses embedded alternative if not available)

## Environment Configuration

The setup wizard automatically configures environment files:

- `backend/.env` - Backend API configuration
- `frontend/.env.local` - Frontend configuration
- Both files include `PURE_PYTHON_MODE=true` flag

## Troubleshooting

### Common Issues

1. **Port Conflicts**
   - Check if ports 3000, 8000, 6379 are available
   - Use `python service_manager.py status` to check service state

2. **Redis Issues**
   - If Redis isn't installed, embedded Redis (fakeredis) is used automatically
   - For production, install Redis server: `brew install redis` (macOS) or `apt install redis` (Ubuntu)

3. **Dependencies**
   - Run `python service_manager.py logs` to check for missing dependencies
   - Install additional packages: `cd backend && uv add <package>`

4. **Browser Automation**
   - Playwright browsers install automatically
   - Manual install: `cd backend && uv run python -m playwright install chromium`

### Performance Tuning

- **Redis**: For better performance, use native Redis instead of embedded
- **Workers**: Adjust worker count in `service_manager.py` based on CPU cores
- **Memory**: Pure Python mode uses less memory than Docker containers

### Development

For development work:
- Services auto-reload when code changes
- Logs available in real-time with `python service_manager.py logs`
- Debug individual services by running them manually

## Next Steps

- **Production**: Consider using native Redis and reverse proxy
- **Scaling**: Use process managers like PM2 or supervisord
- **Monitoring**: Integrate with your preferred monitoring solution
- **Security**: Review sandbox isolation for your security requirements

The Pure Python mode provides a streamlined, performant, and developer-friendly experience maintaining all of Suna's powerful capabilities.
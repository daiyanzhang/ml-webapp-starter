# Getting Started

## Prerequisites

- [Docker & Docker Compose](https://docs.docker.com/get-docker/)
- [Node.js 18+](https://nodejs.org/) (for local development)
- [Python 3.11+](https://www.python.org/) (for local development)

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/your-username/webapp-starter.git
cd webapp-starter
```

### 2. Start Development Environment
```bash
# Start all services
./scripts/dev-start.sh

# Or manually
docker-compose -f docker-compose.dev.yml up -d
```

### 3. Create Admin User
```bash
# Create admin user (run after services are up)
docker-compose -f docker-compose.dev.yml exec backend python /scripts/create_admin.py
```

### 4. Launch Development Dashboard

Experience Airflow-like development with split-screen monitoring:

```bash
# Full development dashboard (recommended)
./scripts/dev-dashboard.sh

# Or simple logs only
./scripts/dev-logs.sh
```

### 5. Access Applications

| Service | URL | Description |
|---------|-----|-------------|
| 🌐 **Frontend** | http://localhost:3000 | Main application with hot reload |
| 🔧 **Backend API** | http://localhost:8000 | FastAPI backend with auto-docs |
| 📖 **API Documentation** | http://localhost:8000/docs | Interactive Swagger UI |
| 📚 **Storybook** | http://localhost:6006 | Component library documentation |
| 🔄 **Temporal Web** | http://localhost:8080 | Workflow management interface |
| ⚡ **Ray Dashboard** | http://localhost:8265 | Distributed computing dashboard |

## Default Account

- Username: `admin`
- Password: `admin123`

> ⚠️ **Important**: Please change the default password after first login

## Project Structure

```
webapp-starter/
├── 📱 frontend/             # React frontend application
├── 🐍 backend/             # FastAPI backend application
├── ⚡ ray-jobs/            # Distributed computing jobs
├── 🐳 deployment/          # Deployment configurations
├── 📚 docs/               # Documentation
└── 🔧 scripts/            # Utility scripts
```

## Next Steps

- [Development Guide](./development.md) - Development environment usage
- [API Documentation](./api-docs.md) - Backend API reference
- [Deployment Guide](./deployment.md) - Production deployment
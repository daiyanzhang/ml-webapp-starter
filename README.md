# 🚀 AI/ML Web Application Starter

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Ray](https://img.shields.io/badge/Ray-2.8+-orange.svg)](https://ray.io)
[![Temporal](https://img.shields.io/badge/Temporal-1.20+-purple.svg)](https://temporal.io)

A **production-ready full-stack web application starter** designed for **AI model training, inference, and big data management projects**. Built with **Ray distributed computing**, **Temporal workflows**, and **enterprise-grade infrastructure** to handle complex ML pipelines and data processing workflows.

## 🎯 Suitable For

- **🤖 AI/ML Projects**: Model development, training, and serving platforms
- **📊 Big Data Applications**: ETL pipelines, data analytics, and processing systems
- **⚡ Distributed Computing**: Multi-node computation and parallel processing
- **🔄 Workflow Orchestration**: Complex business process automation
- **🌐 Enterprise Web Apps**: Scalable web applications with microservices architecture

## ✨ Key Features

### 🤖 AI/ML Ready Infrastructure
- **Ray Integration**: Built-in distributed computing framework
- **Async Processing**: High-performance async API with FastAPI
- **Workflow Engine**: Temporal for complex pipeline orchestration
- **Database Support**: PostgreSQL with async ORM
- **Type Safety**: Pydantic for data validation

### 🏗️ Production Architecture
- **Microservices**: Clean separation between frontend and backend
- **Containerization**: Docker containers with Kubernetes support
- **Scalability**: Auto-scaling for compute-intensive workloads
- **Monitoring**: Comprehensive logging and debugging tools
- **Security**: JWT authentication and input validation

### 🛠️ Developer Experience
- **Hot Reload**: Instant code changes across all services
- **4-Quadrant Logs**: Airflow-like development dashboard
- **VSCode Debugging**: Full breakpoint support in containers
- **Auto Documentation**: Interactive API docs with Swagger
- **Component Library**: Storybook for UI development

## 🛠️ Technology Stack

### Backend
- **[FastAPI](https://fastapi.tiangolo.com)**: High-performance async Python web framework
- **[Ray](https://ray.io)**: Distributed computing framework for ML and data processing
- **[Temporal](https://temporal.io)**: Workflow orchestration engine
- **[PostgreSQL](https://postgresql.org)**: Robust relational database
- **[SQLAlchemy 2.0](https://sqlalchemy.org)**: Modern async ORM
- **[Pydantic](https://pydantic.dev)**: Data validation with Python type hints

### Frontend
- **[React 18](https://reactjs.org)**: Modern UI library with concurrent features
- **[Ant Design](https://ant.design)**: Enterprise-grade UI component library
- **[Vite](https://vitejs.dev)**: Next-generation frontend build tool
- **[Zustand](https://github.com/pmndrs/zustand)**: Lightweight state management
- **[React Query](https://tanstack.com/query)**: Server state management
- **[Storybook](https://storybook.js.org)**: Component development environment

### Infrastructure
- **[Docker](https://docker.com)**: Containerization platform
- **[Kubernetes](https://kubernetes.io)**: Container orchestration
- **[GitHub Actions](https://github.com/features/actions)**: CI/CD automation

## 📁 Project Structure

```
webapp-starter/
├── 📱 frontend/             # React frontend application
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/          # Application pages
│   │   ├── services/       # API service layer
│   │   ├── store/          # Global state management
│   │   └── utils/          # Helper utilities
│   ├── .storybook/         # Storybook configuration
│   └── package.json
├── 🐍 backend/             # FastAPI backend application
│   ├── app/
│   │   ├── api/            # REST API endpoints
│   │   ├── core/           # Core configurations
│   │   ├── crud/           # Database operations
│   │   ├── db/             # Database models
│   │   ├── schemas/        # Pydantic data models
│   │   ├── services/       # Business logic services
│   │   └── workflows/      # Temporal workflow definitions
│   ├── alembic/            # Database migrations
│   └── requirements.txt
├── 🐳 deployment/          # Deployment configurations
│   ├── docker/             # Docker configurations
│   └── k8s/               # Kubernetes manifests
├── 📚 docs/               # Documentation
│   ├── development.md      # Development guide
│   ├── deployment.md       # Deployment guide
│   └── api-docs.md         # API documentation
├── 🔧 scripts/            # Utility scripts
└── docker-compose*.yml    # Docker Compose files
```

## 🚀 Quick Start

### Prerequisites

- **[Docker](https://docs.docker.com/get-docker/) & [Docker Compose](https://docs.docker.com/compose/install/)** - Required for containerization
- **[Node.js 18+](https://nodejs.org/)** - For local frontend development (optional)
- **[Python 3.11+](https://www.python.org/)** - For local backend development (optional)

### 1. Clone and Start

```bash
# Clone the repository
git clone https://github.com/your-username/webapp-starter.git
cd webapp-starter

# Start all services with one command
./scripts/dev-start.sh
```

**What happens:**
- 🐳 Starts all Docker containers
- 🗄️ Initializes PostgreSQL database
- ⚡ Launches Ray cluster
- 🔄 Starts Temporal workflow engine
- 🌐 Serves frontend with hot reload
- 🐍 Starts FastAPI backend
- 👤 Creates admin user

### 2. Access Applications

| Service | URL | Description |
|---------|-----|-------------|
| 🌐 **Frontend** | http://localhost:3000 | Main web application |
| 🐍 **Backend API** | http://localhost:8000 | FastAPI backend |
| 📖 **API Docs** | http://localhost:8000/docs | Interactive API documentation |
| ⚡ **Ray Dashboard** | http://localhost:8265 | Distributed computing dashboard |
| 🔄 **Temporal UI** | http://localhost:8080 | Workflow management |
| 📚 **Storybook** | http://localhost:6006 | Component library |

All of the above tools can also be accessed directly from the Developer Tools menu in the frontend application.

### 3. Development Dashboard

```bash
# Launch 4-quadrant development logs (requires iTerm2)
./scripts/dev-logs-iterm.sh
```

This creates a 4-panel terminal layout showing real-time logs:
- **Frontend** (Port 3000) - React development server
- **Backend** (Port 8000) - FastAPI application logs
- **Ray Cluster** (Port 8265) - Distributed computing logs
- **Temporal** (Port 8080) - Workflow engine logs

## 🧪 Development Features

### VSCode Debugging

Pre-configured debugging support:

1. Open project in VSCode
2. Set breakpoints in Python code
3. Press `F5` → Select "Debug FastAPI (Docker)"
4. Debug with full IntelliSense support

### Hot Module Replacement

- ✅ **Frontend**: Instant React updates with Vite HMR
- ✅ **Backend**: Auto-reload on Python code changes
- ✅ **Database**: Automatic migrations with Alembic

### Testing

```bash
# Backend tests
docker-compose -f docker-compose.dev.yml exec backend-debug pytest

# Frontend tests
cd frontend && npm test

# View logs
docker-compose -f docker-compose.dev.yml logs -f backend
```

## 📚 Documentation

- **[Development Guide](./docs/development.md)** - Development setup and workflows
- **[API Documentation](./docs/api-docs.md)** - Backend API reference
- **[VSCode Debugging](./docs/vscode-debug.md)** - Debug configuration
- **[Deployment Guide](./docs/deployment.md)** - Production deployment

## 🤝 Contributing

We welcome contributions! Please read our [Contributing Guide](./CONTRIBUTING.md) for details.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

---

**⭐ Star this repository if you find it useful!**
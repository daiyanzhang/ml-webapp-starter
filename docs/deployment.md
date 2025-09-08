# Deployment Guide

## Docker Deployment

### Development Environment
```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# View status and logs
docker-compose -f docker-compose.dev.yml ps
docker-compose -f docker-compose.dev.yml logs -f

# Stop services
docker-compose -f docker-compose.dev.yml down
```

### Production Build
```bash
# Build backend image
cd backend && docker build -t webapp-starter/backend:latest .

# Build frontend image  
cd frontend && docker build -t webapp-starter/frontend:latest .

# Start production environment
docker-compose up -d
```

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (v1.20+)
- kubectl configured
- NGINX Ingress Controller

### Deploy
```bash
cd deployment/k8s

# One-click deployment
./deploy.sh

# Or manual deployment
kubectl apply -f namespace.yaml
kubectl apply -f postgres.yaml
kubectl apply -f backend.yaml  
kubectl apply -f frontend.yaml
```

### Monitor
```bash
# View all resources
kubectl get all -n webapp-starter

# View logs
kubectl logs -f deployment/backend -n webapp-starter

# Scale services
kubectl scale deployment backend --replicas=3 -n webapp-starter
```

## Environment Configuration

### Backend (.env)
```bash
# Database
POSTGRES_SERVER=postgres
POSTGRES_DB=webapp_starter
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# Security
SECRET_KEY=your-production-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Services
TEMPORAL_HOST=temporal:7233
RAY_ADDRESS=ray://ray-head:10001
```

### Frontend (build-time)
```bash
VITE_API_BASE_URL=/api/v1
```

## Health Checks

All services include health check endpoints:
- Backend: `GET /health`
- Frontend: `GET /health`
- Database: Built-in PostgreSQL checks

## Backup & Recovery

```bash
# Database backup
kubectl exec postgres-pod -- pg_dump -U postgres webapp_starter > backup.sql

# Database restore
kubectl exec -i postgres-pod -- psql -U postgres webapp_starter < backup.sql
```
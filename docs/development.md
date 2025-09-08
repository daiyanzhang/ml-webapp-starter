# Development Guide

## Quick Start

```bash
# Start development environment
./scripts/dev-start.sh

# Or manually
docker-compose -f docker-compose.dev.yml up -d

# Create admin user
docker-compose -f docker-compose.dev.yml exec backend python /scripts/create_admin.py
```

## Access URLs

- **Frontend**: http://localhost:3000 (with HMR)
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Storybook**: http://localhost:6006
- **Ray Dashboard**: http://localhost:8265
- **Temporal Web**: http://localhost:8080

## Development Logs

Experience Airflow-like development with 4-quadrant logs:

```bash
# Launch 4-quadrant logs dashboard
./scripts/dev-logs-iterm.sh
```

### 4-Quadrant Layout
```
┌─────────────┬─────────────┐
│ Frontend    │ Ray Cluster │
│ :3000       │ :8265       │
├─────────────┼─────────────┤
│ Backend     │ Temporal    │
│ :8000       │ :8080       │
└─────────────┴─────────────┘
```

### Perfect Text Selection
**No cross-pane selection issues!**
- **Navigation**: `Cmd+Option+Arrow` to move between panes  
- **Copy/Paste**: Standard `Cmd+C/Cmd+V` - works perfectly
- **Zoom Pane**: `Cmd+Enter` to toggle pane zoom
- **Split Control**: `Cmd+D` vertical, `Cmd+Shift+D` horizontal
- **Independent Sessions**: Each pane has its own shell session and scrollback

## Development Features

### Hot Module Replacement
- ✅ React Fast Refresh - Component state preservation
- ✅ CSS hot updates - Instant style changes
- ✅ File watching - Docker environment compatible
- ✅ Error overlay - Build error display

### VSCode Debugging
- Set breakpoints in Python code
- Press `F5` → Select "Debug FastAPI (Docker)"
- Full IntelliSense support

## Common Commands

```bash
# Service management
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml restart backend

# View logs
docker-compose -f docker-compose.dev.yml logs -f backend
docker-compose -f docker-compose.dev.yml logs -f frontend

# Container access
docker-compose -f docker-compose.dev.yml exec backend bash
docker-compose -f docker-compose.dev.yml exec frontend sh

# Database operations
docker-compose -f docker-compose.dev.yml exec postgres psql -U postgres webapp_starter
```

## Troubleshooting

### Common Issues

1. **Port conflicts**: Use `lsof -i :3000` to check port usage
2. **HMR not working**: Restart frontend service
3. **Database connection**: Check postgres service status
4. **Clean environment**: Run `docker system prune` and rebuild
# Contributing to Web App Starter

Thank you for your interest in contributing! This guide will help you get started.

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-username/webapp-starter.git
   cd webapp-starter
   ```

2. **Start Development Environment**
   ```bash
   ./scripts/dev-start.sh
   ```

3. **Create Admin User**
   ```bash
   docker-compose -f docker-compose.dev.yml exec backend python /scripts/create_admin.py
   ```

## Making Changes

### Code Style
- **Backend**: Follow PEP 8 Python style guide
- **Frontend**: Use ESLint and Prettier configurations
- **Commits**: Use conventional commit messages

### Development Workflow
1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes with proper testing
3. Ensure all services start without errors
4. Submit a pull request with clear description

### Testing
```bash
# Backend tests
docker-compose -f docker-compose.dev.yml exec backend pytest

# Frontend tests
cd frontend && npm test
```

## Project Architecture

### Backend (FastAPI)
- **API Routes**: `/backend/app/api/v1/`
- **Database Models**: `/backend/app/db/models.py`
- **Business Logic**: `/backend/app/services/`

### Frontend (React)
- **Pages**: `/frontend/src/pages/`
- **Components**: `/frontend/src/components/`
- **Services**: `/frontend/src/services/`

### Ray Jobs
- **Job Scripts**: `/ray-jobs/`
- **Local Debug**: `python script.py debug`

## Submitting Changes

### Pull Request Guidelines
- Include clear title and description
- Reference related issues
- Ensure CI passes
- Update documentation if needed

### Issue Reporting
- Use issue templates
- Provide reproduction steps
- Include environment details

## Need Help?

- Check existing [issues](https://github.com/your-username/webapp-starter/issues)
- Read the [documentation](./docs/)
- Join discussions in pull requests

We appreciate your contributions! 🚀
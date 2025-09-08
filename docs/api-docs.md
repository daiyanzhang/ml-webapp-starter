# API Documentation

## Auto-generated Docs

FastAPI provides interactive documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI Schema**: http://localhost:8000/api/v1/openapi.json

## Authentication

All protected endpoints use Bearer Token authentication:

```bash
# Login to get token
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"

# Use token for API calls
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## API Endpoints

### Authentication `/api/v1/auth`
- `POST /login` - User login, returns JWT token

### Users `/api/v1/users`
- `GET /users/` - List users (admin only)
- `POST /users/` - Create user (admin only)
- `GET /users/me` - Get current user
- `PUT /users/me` - Update current user
- `GET /users/{user_id}` - Get user by ID (admin only)
- `PUT /users/{user_id}` - Update user by ID (admin only)

### Ray Jobs `/api/v1/ray`
- `POST /ray/jobs/submit` - Submit new Ray job
- `GET /ray/jobs` - List all Ray jobs
- `GET /ray/jobs/{job_id}` - Get job details
- `DELETE /ray/jobs/{job_id}` - Cancel job
- `GET /ray/cluster/status` - Get cluster status

### Workflows `/api/v1/workflows`
- `POST /workflows/start` - Start workflow (uses current user automatically)
- `GET /workflows/{workflow_id}/status` - Get workflow status
- `GET /workflows/list` - List user's workflows
- `POST /workflows/{workflow_id}/cancel` - Cancel running workflow

## Error Responses

Standard HTTP status codes:
- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `422` - Validation Error
- `500` - Internal Server Error

Error format:
```json
{
  "detail": "Error description"
}
```
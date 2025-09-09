from fastapi import APIRouter

from app.api.v1 import auth, users, workflows, ray_jobs, notebooks

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(workflows.router, prefix="/workflows", tags=["workflows"])
api_router.include_router(ray_jobs.router, prefix="/ray", tags=["ray-jobs"])
api_router.include_router(notebooks.router, prefix="/notebooks", tags=["notebooks"])
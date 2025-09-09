"""
Ray作业管理API端点
"""

import json
from typing import List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from app.api.deps import get_current_active_user
from app.db.models import User
from app.services.ray_job_service import ray_job_service, GitHubJobRequest, JobStatus
from app.core.logging import logger

router = APIRouter()


@router.post("/submit-github", response_model=dict)
async def submit_github_ray_job(
    job_request: GitHubJobRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
):
    """提交基于GitHub的Ray作业"""
    try:
        logger.info(
            f"User {current_user.id} submitting GitHub Ray job: {job_request.github_repo}"
        )

        # 异步提交作业
        job_id = await ray_job_service.submit_github_job(job_request, current_user.id)

        return {
            "success": True,
            "job_id": job_id,
            "message": "Ray job submitted successfully",
            "github_repo": job_request.github_repo,
            "branch": job_request.branch,
        }

    except Exception as e:
        logger.error(f"Failed to submit GitHub Ray job: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to submit job: {str(e)}")


@router.get("/status/{job_id}", response_model=JobStatus)
async def get_ray_job_status(
    job_id: str, current_user: User = Depends(get_current_active_user)
):
    """获取Ray作业状态"""
    job_status = await ray_job_service.get_job_status(job_id)

    if not job_status:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    return job_status


@router.get("/list", response_model=List[JobStatus])
async def list_ray_jobs(
    limit: int = 10, current_user: User = Depends(get_current_active_user)
):
    """列出Ray作业"""
    jobs = await ray_job_service.list_jobs(limit)
    return jobs


@router.post("/cancel/{job_id}")
async def cancel_ray_job(
    job_id: str, current_user: User = Depends(get_current_active_user)
):
    """取消Ray作业"""
    success = await ray_job_service.cancel_job(job_id)

    if not success:
        raise HTTPException(
            status_code=404, detail=f"Job {job_id} not found or cannot be cancelled"
        )

    return {"success": True, "message": f"Job {job_id} cancelled successfully"}


@router.get("/templates", response_model=dict)
async def get_job_templates(current_user: User = Depends(get_current_active_user)):
    """获取可用的作业模板"""
    templates = {
        "custom": {
            "name": "Custom Script",
            "description": "Execute any Python script",
            "example_repo": "example/ray-custom-job",
            "supports_gpu": True,
        },
        # "data_processing": {
        #     "name": "Data Processing",
        #     "description": "Process CSV/JSON data with pandas",
        #     "required_function": "process_data(dataframe, config)",
        #     "example_repo": "example/ray-data-processing",
        #     "supports_gpu": False,
        # },
        # "ml_training": {
        #     "name": "ML Training",
        #     "description": "Machine learning model training",
        #     "required_function": "train_model(config) or process_data(data, config)",
        #     "example_repo": "example/ray-ml-training",
        #     "supports_gpu": True,
        # },
    }

    return {
        "templates": templates,
        "user_code_requirements": {
            "entry_point": "main.py (required)",
            "dependencies": "requirements.txt (optional)",
            "config": "ray_job_config.yaml (optional)",
            "max_size": "100MB",
            "timeout": "1 hour default",
        },
    }


@router.post("/validate-repo", response_model=dict)
async def validate_github_repository(
    repo_url: str,
    branch: str = "main",
    entry_point: str = "main.py",
    current_user: User = Depends(get_current_active_user),
):
    """验证GitHub仓库结构"""
    try:
        from app.services.github_service import github_service

        # 克隆仓库进行验证
        logger.info(f"Validating repository: {repo_url}")
        repo_path = await github_service.clone_public_repo(repo_url, branch)

        try:
            # 验证仓库结构
            validation = await github_service.validate_repository_structure(
                repo_path, entry_point
            )

            return {
                "success": True,
                "validation": validation,
                "repo_url": repo_url,
                "branch": branch,
                "entry_point": entry_point,
            }

        finally:
            # 清理临时文件
            await github_service.cleanup_repository(repo_path)

    except Exception as e:
        logger.error(f"Repository validation failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "repo_url": repo_url,
            "branch": branch,
        }


@router.get("/cluster/status", response_model=dict)
async def get_ray_cluster_status(current_user: User = Depends(get_current_active_user)):
    """获取Ray集群状态"""
    try:
        import ray

        if not ray.is_initialized():
            return {"status": "disconnected", "message": "Ray cluster not initialized"}

        # 获取集群资源信息
        cluster_resources = ray.cluster_resources()
        available_resources = ray.available_resources()

        return {
            "status": "connected",
            "cluster_resources": cluster_resources,
            "available_resources": available_resources,
            "nodes": len(ray.nodes()),
            "dashboard_url": "http://localhost:8265",
        }

    except Exception as e:
        return {"status": "error", "error": str(e)}


@router.post("/update-status")
async def update_ray_job_status(update_data: dict):
    """更新Ray作业状态 - 由ray_job_decorator调用"""
    try:
        job_id = update_data.get("job_id")
        status = update_data.get("status")

        if not job_id or not status:
            raise HTTPException(status_code=400, detail="Missing job_id or status")

        # 更新数据库
        from app.services.ray_job_service import ray_job_service

        update_fields = {"status": status}

        # 添加可选字段
        if "result" in update_data:
            update_fields["result"] = json.dumps(update_data["result"])
        if "error_message" in update_data:
            update_fields["error_message"] = update_data["error_message"]
        if "start_time" in update_data:
            update_fields["started_at"] = datetime.fromisoformat(
                update_data["start_time"].replace("Z", "+00:00")
            )
        if "end_time" in update_data:
            update_fields["completed_at"] = datetime.fromisoformat(
                update_data["end_time"].replace("Z", "+00:00")
            )

        # 调用service更新
        ray_job_service._update_db_job(job_id, **update_fields)

        logger.info(f"Updated job {job_id} status to {status}")
        return {"success": True, "message": f"Job {job_id} status updated to {status}"}

    except Exception as e:
        logger.error(f"Failed to update job status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/examples", response_model=dict)
async def get_example_repositories(
    current_user: User = Depends(get_current_active_user),
):
    """获取示例GitHub仓库"""
    examples = {
        "data_processing": {
            "name": "Data Processing Example",
            "repo": "ray-examples/data-processing-starter",
            "description": "Basic data processing with pandas",
            "files": ["main.py", "requirements.txt", "sample_data.csv"],
        },
        "ml_training": {
            "name": "ML Training Example",
            "repo": "ray-examples/ml-training-starter",
            "description": "Simple ML model training with scikit-learn",
            "files": ["main.py", "requirements.txt", "model_config.yaml"],
        },
        "custom": {
            "name": "Custom Script Example",
            "repo": "ray-examples/custom-script-starter",
            "description": "Template for custom Python scripts",
            "files": ["main.py", "requirements.txt", "README.md"],
        },
    }

    return {"examples": examples}

"""
Jupyter Notebook API endpoints
"""
import os
import json
import requests
import tempfile
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import ray
from ray.job_submission import JobSubmissionClient
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.models import User as UserModel, RayJob
from app.core.database import SessionLocal

router = APIRouter()

# Jupyter server configuration
JUPYTER_BASE_URL = "http://jupyter:8888"
JUPYTER_TOKEN = "webapp-starter-token"
NOTEBOOKS_DIR = "/home/jovyan/work"

# Ray cluster configuration
RAY_HEAD_URL = "http://ray-head:8265"
RAY_CLIENT_URL = "ray://ray-head:10001"


class NotebookCreate(BaseModel):
    name: str
    content: Optional[Dict[str, Any]] = None


class NotebookUpdate(BaseModel):
    content: Dict[str, Any]


def get_jupyter_headers():
    """Get headers for Jupyter API requests"""
    return {
        "Authorization": f"token {JUPYTER_TOKEN}",
        "Content-Type": "application/json"
    }


def _create_notebook_ray_job(job_id: str, notebook_path: str, user_id: int, queue: str = "default", ray_job_id: str = None) -> None:
    """创建notebook Ray作业数据库记录"""
    db = SessionLocal()
    try:
        db_job = RayJob(
            job_id=job_id,
            job_type="notebook",
            queue=queue,
            status="pending",
            user_id=user_id,
            notebook_path=notebook_path,
            ray_job_id=ray_job_id,
            dashboard_url=f"{RAY_HEAD_URL}/jobs/{ray_job_id}" if ray_job_id else None,
            created_at=datetime.now()
        )
        db.add(db_job)
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create job record: {str(e)}")
    finally:
        db.close()


@router.get("/")
async def list_notebooks(
    current_user: UserModel = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """获取所有 notebook 列表"""
    try:
        response = requests.get(
            f"{JUPYTER_BASE_URL}/api/contents",
            headers=get_jupyter_headers()
        )
        response.raise_for_status()
        
        contents = response.json()
        notebooks = []
        
        # 递归获取所有 notebook 文件
        def extract_notebooks(items, path=""):
            for item in items:
                if item["type"] == "notebook":
                    notebooks.append({
                        "name": item["name"],
                        "path": item["path"],
                        "last_modified": item["last_modified"],
                        "size": item.get("size", 0),
                        "url": f"{JUPYTER_BASE_URL}/notebooks/{item['path']}"
                    })
                elif item["type"] == "directory":
                    # 获取子目录内容
                    subdir_response = requests.get(
                        f"{JUPYTER_BASE_URL}/api/contents/{item['path']}",
                        headers=get_jupyter_headers()
                    )
                    if subdir_response.status_code == 200:
                        subdir_data = subdir_response.json()
                        extract_notebooks(subdir_data.get("content", []), item["path"])
        
        extract_notebooks(contents.get("content", []))
        return notebooks
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch notebooks: {str(e)}")


@router.post("/")
async def create_notebook(
    notebook: NotebookCreate,
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, Any]:
    """创建新的 notebook"""
    try:
        # 确保文件名以 .ipynb 结尾
        filename = notebook.name
        if not filename.endswith(".ipynb"):
            filename += ".ipynb"
        
        # 默认的 notebook 内容
        default_content = {
            "cells": [
                {
                    "cell_type": "markdown",
                    "metadata": {},
                    "source": [f"# {notebook.name}\n\nThis notebook was created via the web interface."]
                },
                {
                    "cell_type": "code",
                    "execution_count": None,
                    "metadata": {},
                    "outputs": [],
                    "source": ["# Write your code here\nprint('Hello, World!')"]
                }
            ],
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": "3.8.5"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        content = notebook.content or default_content
        
        # 通过 Jupyter API 创建文件
        response = requests.put(
            f"{JUPYTER_BASE_URL}/api/contents/{filename}",
            headers=get_jupyter_headers(),
            json={
                "type": "notebook",
                "content": content
            }
        )
        response.raise_for_status()
        
        result = response.json()
        return {
            "name": result["name"],
            "path": result["path"],
            "url": f"{JUPYTER_BASE_URL}/notebooks/{result['path']}",
            "created": result["created"]
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to create notebook: {str(e)}")


@router.get("/server/status")
async def get_server_status(
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取 Jupyter 服务器状态"""
    try:
        response = requests.get(
            f"{JUPYTER_BASE_URL}/api/status",
            headers=get_jupyter_headers()
        )
        response.raise_for_status()
        
        status_data = response.json()
        return {
            "status": "running",
            "url": JUPYTER_BASE_URL,
            "version": status_data.get("version", "unknown"),
            "started": status_data.get("started", None)
        }
        
    except requests.RequestException:
        return {
            "status": "unavailable",
            "url": JUPYTER_BASE_URL,
            "error": "Cannot connect to Jupyter server"
        }


@router.get("/ray/cluster/status")
async def get_ray_cluster_status(
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取Ray集群状态"""
    try:
        # 检查Ray Dashboard是否可访问（简单检查主页）
        response = requests.get(f"{RAY_HEAD_URL}", timeout=5)
        response.raise_for_status()
        
        # 尝试连接Ray Job API
        job_client = JobSubmissionClient(RAY_HEAD_URL)
        jobs = job_client.list_jobs()
        
        return {
            "status": "available",
            "total_jobs": len(jobs),
            "dashboard_url": RAY_HEAD_URL,
            "client_url": RAY_CLIENT_URL
        }
        
    except Exception as e:
        return {
            "status": "unavailable",
            "error": f"Cannot connect to Ray cluster: {str(e)}",
            "dashboard_url": RAY_HEAD_URL
        }




@router.get("/ray/jobs/{job_id}")
async def get_ray_job_status(
    job_id: str,
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取指定Ray任务的状态和日志"""
    try:
        client = JobSubmissionClient(RAY_HEAD_URL)
        
        # 获取任务信息
        job_info = client.get_job_info(job_id)
        
        # 获取任务日志
        logs = client.get_job_logs(job_id)
        
        return {
            "job_id": job_id,
            "status": job_info.status.value,
            "start_time": job_info.start_time,
            "end_time": job_info.end_time,
            "metadata": job_info.metadata,
            "logs": logs,
            "dashboard_url": f"{RAY_HEAD_URL}/jobs/{job_id}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch job status: {str(e)}")


@router.delete("/ray/jobs/{job_id}")
async def cancel_ray_job(
    job_id: str,
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, Any]:
    """取消Ray任务"""
    try:
        client = JobSubmissionClient(RAY_HEAD_URL)
        client.stop_job(job_id)
        
        return {
            "job_id": job_id,
            "status": "cancelled",
            "message": "Job cancellation requested"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel job: {str(e)}")


@router.post("/{notebook_path:path}/execute-on-ray")
async def execute_notebook_on_ray(
    notebook_path: str,
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, Any]:
    """在Ray集群上执行notebook"""
    try:
        # 连接到Ray集群
        client = JobSubmissionClient(RAY_HEAD_URL)
        
        # 生成唯一的job ID
        job_name = f"notebook-{uuid.uuid4().hex[:8]}"
        
        # 准备Ray job配置
        runtime_env = {
            "working_dir": "./ray-jobs",
            "pip": [
                "jupyter==1.0.0",
                "nbformat==5.9.2", 
                "nbconvert==7.11.0",
                "ipykernel==6.26.0",
                "requests==2.31.0"
            ]
        }
        
        # 设置环境变量
        env_vars = {
            "NOTEBOOK_PATH": notebook_path,
            "JUPYTER_BASE_URL": JUPYTER_BASE_URL,
            "JUPYTER_TOKEN": JUPYTER_TOKEN,
            "RAY_JOB_ID": job_name,  # 设置job_id供ray_job_decorator使用
            "RAY_SUBMISSION_ID": job_name
        }
        
        # 将环境变量添加到runtime_env中
        runtime_env["env_vars"] = env_vars
        
        # 提交Ray job - 使用ray-jobs目录中的脚本
        ray_job_id = client.submit_job(
            entrypoint="python notebook_executor.py",
            runtime_env=runtime_env,
            submission_id=job_name,  # 使用submission_id而不是job_id
            metadata={"notebook_path": notebook_path, "user": current_user.username}
        )
        
        # 保存作业到数据库
        _create_notebook_ray_job(
            job_id=job_name,
            notebook_path=notebook_path,
            user_id=current_user.id,
            ray_job_id=ray_job_id
        )
        
        return {
            "job_id": ray_job_id,
            "job_name": job_name,
            "notebook_path": notebook_path,
            "status": "submitted",
            "ray_dashboard": f"{RAY_HEAD_URL}/jobs/{ray_job_id}",
            "message": "Notebook submitted for execution on Ray cluster"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute on Ray: {str(e)}")


@router.get("/{notebook_path:path}")
async def get_notebook(
    notebook_path: str,
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取指定 notebook 的内容"""
    try:
        response = requests.get(
            f"{JUPYTER_BASE_URL}/api/contents/{notebook_path}",
            headers=get_jupyter_headers()
        )
        response.raise_for_status()
        
        notebook_data = response.json()
        return {
            "name": notebook_data["name"],
            "path": notebook_data["path"],
            "content": notebook_data["content"],
            "last_modified": notebook_data["last_modified"],
            "url": f"{JUPYTER_BASE_URL}/notebooks/{notebook_data['path']}"
        }
        
    except requests.RequestException as e:
        if hasattr(e, 'response') and e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Notebook not found")
        raise HTTPException(status_code=500, detail=f"Failed to get notebook: {str(e)}")


@router.put("/{notebook_path:path}")
async def update_notebook(
    notebook_path: str,
    notebook: NotebookUpdate,
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, Any]:
    """更新 notebook 内容"""
    try:
        response = requests.put(
            f"{JUPYTER_BASE_URL}/api/contents/{notebook_path}",
            headers=get_jupyter_headers(),
            json={
                "type": "notebook",
                "content": notebook.content
            }
        )
        response.raise_for_status()
        
        result = response.json()
        return {
            "name": result["name"],
            "path": result["path"],
            "last_modified": result["last_modified"]
        }
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to update notebook: {str(e)}")


@router.delete("/{notebook_path:path}")
async def delete_notebook(
    notebook_path: str,
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, str]:
    """删除 notebook"""
    try:
        response = requests.delete(
            f"{JUPYTER_BASE_URL}/api/contents/{notebook_path}",
            headers=get_jupyter_headers()
        )
        response.raise_for_status()
        
        return {"message": f"Notebook {notebook_path} deleted successfully"}
        
    except requests.RequestException as e:
        if hasattr(e, 'response') and e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Notebook not found")
        raise HTTPException(status_code=500, detail=f"Failed to delete notebook: {str(e)}")


@router.post("/{notebook_path:path}/execute")
async def execute_notebook(
    notebook_path: str,
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, Any]:
    """执行 notebook 中的所有 cells"""
    try:
        # 首先获取 notebook 内容
        response = requests.get(
            f"{JUPYTER_BASE_URL}/api/contents/{notebook_path}",
            headers=get_jupyter_headers()
        )
        response.raise_for_status()
        notebook_data = response.json()
        
        # 启动内核会话
        kernel_response = requests.post(
            f"{JUPYTER_BASE_URL}/api/kernels",
            headers=get_jupyter_headers(),
            json={"name": "python3"}
        )
        kernel_response.raise_for_status()
        kernel_data = kernel_response.json()
        kernel_id = kernel_data["id"]
        
        try:
            # 执行每个代码 cell
            results = []
            for i, cell in enumerate(notebook_data["content"]["cells"]):
                if cell["cell_type"] == "code" and cell["source"]:
                    source_code = "".join(cell["source"]) if isinstance(cell["source"], list) else cell["source"]
                    
                    # 执行代码
                    exec_response = requests.post(
                        f"{JUPYTER_BASE_URL}/api/kernels/{kernel_id}/execute",
                        headers=get_jupyter_headers(),
                        json={
                            "code": source_code,
                            "silent": False,
                            "store_history": True
                        }
                    )
                    
                    if exec_response.status_code == 200:
                        results.append({
                            "cell_index": i,
                            "executed": True,
                            "source": source_code
                        })
                    else:
                        results.append({
                            "cell_index": i,
                            "executed": False,
                            "error": "Failed to execute"
                        })
            
            return {
                "notebook_path": notebook_path,
                "kernel_id": kernel_id,
                "results": results,
                "status": "completed"
            }
            
        finally:
            # 清理内核
            requests.delete(
                f"{JUPYTER_BASE_URL}/api/kernels/{kernel_id}",
                headers=get_jupyter_headers()
            )
        
    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute notebook: {str(e)}")





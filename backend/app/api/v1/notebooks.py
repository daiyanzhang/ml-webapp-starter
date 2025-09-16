"""
Jupyter Notebook API endpoints
"""
import os
import json
import requests
import tempfile
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.db.models import User as UserModel
from app.services.jupyterhub_client import jupyterhub_client

router = APIRouter()

# JupyterHub configuration for notebook access
JUPYTERHUB_BASE_URL = "http://jupyterhub:8000"
JUPYTERHUB_TOKEN = "webapp-starter-hub-api-token"

class NotebookCreate(BaseModel):
    name: str
    content: Optional[Dict[str, Any]] = None


class NotebookUpdate(BaseModel):
    content: Dict[str, Any]



def get_jupyter_headers():
    """Get headers for JupyterHub API requests"""
    return {
        "Authorization": f"token {JUPYTERHUB_TOKEN}",
        "Content-Type": "application/json"
    }


def get_user_notebook_path(username: str, notebook_path: str = "") -> str:
    """获取用户专属的notebook路径"""
    user_dir = f"users/{username}"
    if notebook_path:
        return f"{user_dir}/{notebook_path}"
    return user_dir


def get_jupyter_api_path(path: str) -> str:
    """获取Jupyter API的完整路径，相对于/home/jovyan"""
    return f"{path}" if path else ""


def ensure_user_directory(username: str) -> None:
    """确保用户目录存在"""
    user_dir_path = get_user_notebook_path(username)
    jupyter_user_dir_path = get_jupyter_api_path(user_dir_path)

    try:
        # 尝试获取用户目录信息，如果不存在则创建
        response = requests.get(
            f"{JUPYTERHUB_BASE_URL}/api/contents/{jupyter_user_dir_path}",
            headers=get_jupyter_headers()
        )
        if response.status_code == 404:
            # 目录不存在，首先确保父目录存在
            parent_dir = "users"
            jupyter_parent_dir = get_jupyter_api_path(parent_dir)
            parent_response = requests.get(
                f"{JUPYTERHUB_BASE_URL}/api/contents/{jupyter_parent_dir}",
                headers=get_jupyter_headers()
            )
            if parent_response.status_code == 404:
                # 创建users父目录
                requests.put(
                    f"{JUPYTERHUB_BASE_URL}/api/contents/{jupyter_parent_dir}",
                    headers=get_jupyter_headers(),
                    json={
                        "type": "directory"
                    }
                )

            # 创建用户目录
            create_response = requests.put(
                f"{JUPYTERHUB_BASE_URL}/api/contents/{jupyter_user_dir_path}",
                headers=get_jupyter_headers(),
                json={
                    "type": "directory"
                }
            )
            create_response.raise_for_status()

    except requests.RequestException as e:
        # 记录错误但不中断程序
        print(f"Warning: Failed to ensure user directory {user_dir_path}: {e}")
        pass






@router.get("/")
async def list_notebooks(
    current_user: UserModel = Depends(get_current_user)
) -> List[Dict[str, Any]]:
    """获取用户的 notebook 列表"""
    try:
        # 确保用户的Jupyter会话已启动
        session_result = await jupyterhub_client.ensure_user_session(current_user.username)
        if session_result["status"] == "error":
            raise HTTPException(status_code=500, detail=f"Failed to start Jupyter session: {session_result['message']}")

        # 通过JupyterHub访问用户的notebook服务器
        response = requests.get(
            f"{JUPYTERHUB_BASE_URL}/user/{current_user.username}/api/contents/",
            headers=get_jupyter_headers()
        )

        response.raise_for_status()

        contents = response.json()
        notebooks = []

        # 递归获取用户目录下的所有 notebook 文件
        def extract_notebooks(items):
            for item in items:
                if item["type"] == "notebook":
                    # 移除用户目录前缀，只显示相对路径
                    user_prefix = f"work/users/{current_user.username}/"
                    relative_path = item["path"].replace(user_prefix, "") if item["path"].startswith(user_prefix) else item["path"]
                    notebooks.append({
                        "name": item["name"],
                        "path": relative_path,
                        "full_path": item["path"],
                        "last_modified": item["last_modified"],
                        "size": item.get("size", 0),
                        "url": f"{JUPYTERHUB_BASE_URL}/user/{current_user.username}/notebooks/{item['path']}"
                    })
                elif item["type"] == "directory":
                    # 获取子目录内容 - item['path']已经包含work/前缀
                    subdir_response = requests.get(
                        f"{JUPYTERHUB_BASE_URL}/user/{current_user.username}/api/contents/{item['path']}",
                        headers=get_jupyter_headers()
                    )
                    if subdir_response.status_code == 200:
                        subdir_data = subdir_response.json()
                        extract_notebooks(subdir_data.get("content", []))

        extract_notebooks(contents.get("content", []))
        return notebooks

    except requests.RequestException as e:
        # 如果是404错误，返回空列表而不是错误
        if hasattr(e, 'response') and e.response is not None and e.response.status_code == 404:
            return []
        raise HTTPException(status_code=500, detail=f"Failed to fetch notebooks: {str(e)}")


@router.post("/")
async def create_notebook(
    notebook: NotebookCreate,
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, Any]:
    """在用户目录中创建新的 notebook"""
    try:
        # 确保用户目录存在
        ensure_user_directory(current_user.username)

        # 确保文件名以 .ipynb 结尾
        filename = notebook.name
        if not filename.endswith(".ipynb"):
            filename += ".ipynb"

        # 构建用户专属路径
        user_notebook_path = get_user_notebook_path(current_user.username, filename)
        jupyter_notebook_path = get_jupyter_api_path(user_notebook_path)

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

        # 通过 Jupyter API 在用户目录中创建文件
        response = requests.put(
            f"{JUPYTERHUB_BASE_URL}/api/contents/{jupyter_notebook_path}",
            headers=get_jupyter_headers(),
            json={
                "type": "notebook",
                "content": content
            }
        )
        response.raise_for_status()

        result = response.json()
        # 返回相对路径给前端
        relative_path = filename
        return {
            "name": result["name"],
            "path": relative_path,
            "full_path": result["path"],
            "url": f"{JUPYTERHUB_BASE_URL}/notebooks/{result['path']}",
            "created": result["created"]
        }

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to create notebook: {str(e)}")


@router.get("/server/status")
async def get_server_status(
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取用户的 JupyterHub 服务器状态"""
    try:
        status = await jupyterhub_client.get_server_status(current_user.username)
        return status
    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to get server status: {str(e)}"
        }


@router.post("/session/start")
async def start_jupyter_session(
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, Any]:
    """启动用户的 JupyterHub 会话"""
    try:
        result = await jupyterhub_client.ensure_user_session(current_user.username)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")


@router.delete("/session/stop")
async def stop_jupyter_session(
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, Any]:
    """停止用户的 JupyterHub 会话"""
    try:
        success = await jupyterhub_client.stop_server(current_user.username)
        if success:
            return {"status": "stopped", "message": "Session stopped successfully"}
        else:
            return {"status": "error", "message": "Failed to stop session"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop session: {str(e)}")


@router.get("/session/url")
async def get_jupyter_url(
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取用户的 Jupyter 访问URL"""
    try:
        url = await jupyterhub_client.get_user_url(current_user.username)
        if url:
            return {"url": url, "status": "available"}
        else:
            return {"url": None, "status": "not_running"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get URL: {str(e)}")






@router.get("/{notebook_path:path}")
async def get_notebook(
    notebook_path: str,
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, Any]:
    """获取用户目录中指定 notebook 的内容"""
    try:
        response = requests.get(
            f"{JUPYTERHUB_BASE_URL}/user/{current_user.username}/api/contents/{notebook_path}",
            headers=get_jupyter_headers()
        )
        response.raise_for_status()

        notebook_data = response.json()
        return {
            "name": notebook_data["name"],
            "path": notebook_path,  # 返回相对路径
            "full_path": notebook_data["path"],  # 保留完整路径
            "content": notebook_data["content"],
            "last_modified": notebook_data["last_modified"],
            "url": f"{JUPYTERHUB_BASE_URL}/user/{current_user.username}/notebooks/{notebook_data['path']}"
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
    """更新用户目录中的 notebook 内容"""
    try:
        # 构建用户专属路径
        user_notebook_path = get_user_notebook_path(current_user.username, notebook_path)
        jupyter_notebook_path = get_jupyter_api_path(user_notebook_path)

        response = requests.put(
            f"{JUPYTERHUB_BASE_URL}/api/contents/{jupyter_notebook_path}",
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
            "path": notebook_path,  # 返回相对路径
            "full_path": result["path"],  # 保留完整路径
            "last_modified": result["last_modified"]
        }

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to update notebook: {str(e)}")


@router.delete("/{notebook_path:path}")
async def delete_notebook(
    notebook_path: str,
    current_user: UserModel = Depends(get_current_user)
) -> Dict[str, str]:
    """删除用户目录中的 notebook"""
    try:
        # 构建用户专属路径
        user_notebook_path = get_user_notebook_path(current_user.username, notebook_path)
        jupyter_notebook_path = get_jupyter_api_path(user_notebook_path)

        response = requests.delete(
            f"{JUPYTERHUB_BASE_URL}/api/contents/{jupyter_notebook_path}",
            headers=get_jupyter_headers()
        )
        response.raise_for_status()

        return {"message": f"Notebook {notebook_path} deleted successfully"}

    except requests.RequestException as e:
        if hasattr(e, 'response') and e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Notebook not found")
        raise HTTPException(status_code=500, detail=f"Failed to delete notebook: {str(e)}")




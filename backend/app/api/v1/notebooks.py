"""
Jupyter Notebook API endpoints
"""
import os
import json
import requests
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.db.models import User as UserModel

router = APIRouter()

# Jupyter server configuration
JUPYTER_BASE_URL = "http://jupyter:8888"
JUPYTER_TOKEN = "webapp-starter-token"
NOTEBOOKS_DIR = "/home/jovyan/work"


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



#!/usr/bin/env python3
"""
通用的 GitHub Ray Job Runner
在 Ray 任务内部下载并执行 GitHub 仓库代码
"""
import os
import sys
import json
import shutil
import tempfile
import subprocess
import importlib.util
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

from ray_job_decorator import ray_job_monitor
from debug_utils import log_info, log_error, get_job_context


def clone_github_repo(repo_url: str, branch: str = "main", commit_sha: str = None) -> str:
    """在 Ray worker 内部克隆 GitHub 仓库"""
    log_info(f"Cloning repository: {repo_url}")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="ray_job_")
    repo_path = os.path.join(temp_dir, "repo")
    
    try:
        # 克隆仓库
        clone_cmd = ["git", "clone", "--depth", "1"]
        if branch and branch != "main":
            clone_cmd.extend(["--branch", branch])
        clone_cmd.extend([repo_url, repo_path])
        
        result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            raise Exception(f"Git clone failed: {result.stderr}")
        
        # 如果指定了commit，切换到指定commit
        if commit_sha:
            result = subprocess.run(
                ["git", "checkout", commit_sha],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            if result.returncode != 0:
                raise Exception(f"Git checkout failed: {result.stderr}")
        
        log_info(f"Repository cloned successfully to: {repo_path}")
        return repo_path
        
    except Exception as e:
        # 清理失败的下载
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise e


def execute_user_code(repo_path: str, entry_point: str, config: Dict[str, Any]) -> Any:
    """动态执行用户代码"""
    log_info(f"Executing user code: {entry_point}")
    
    # 将仓库路径添加到 Python 路径
    if repo_path not in sys.path:
        sys.path.insert(0, repo_path)
    
    try:
        # 解析入口点文件路径
        entry_file = os.path.join(repo_path, entry_point)
        if not os.path.exists(entry_file):
            raise FileNotFoundError(f"Entry point file not found: {entry_point}")
        
        # 动态加载模块
        spec = importlib.util.spec_from_file_location("user_module", entry_file)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load module from: {entry_point}")
        
        user_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(user_module)
        
        # 查找并执行主函数
        if hasattr(user_module, 'main'):
            log_info("Executing user main() function")
            return user_module.main()
        elif hasattr(user_module, 'run'):
            log_info("Executing user run() function with config")
            return user_module.run(config)
        else:
            raise AttributeError("User module must have a 'main()' or 'run(config)' function")
            
    except Exception as e:
        log_error("Failed to execute user code", e)
        raise
    finally:
        # 从 Python 路径中移除仓库路径
        if repo_path in sys.path:
            sys.path.remove(repo_path)


def cleanup_repo(repo_path: str):
    """清理临时下载的仓库"""
    if repo_path and os.path.exists(repo_path):
        parent_dir = os.path.dirname(repo_path)
        shutil.rmtree(parent_dir, ignore_errors=True)
        log_info(f"Cleaned up repository: {repo_path}")


@ray_job_monitor(api_base_url="http://backend:8000")
def main():
    """通用 GitHub Job Runner 入口函数"""
    # 获取任务上下文
    context = get_job_context()
    log_info("GitHub Job Runner started", **context)
    
    # 从环境变量获取 GitHub 仓库信息
    github_repo = os.environ.get("GITHUB_REPO", "")
    branch = os.environ.get("GITHUB_BRANCH", "main")
    commit_sha = os.environ.get("GITHUB_COMMIT", None)
    entry_point = os.environ.get("ENTRY_POINT", "main.py")
    
    if not github_repo:
        raise ValueError("GITHUB_REPO environment variable is required")
    
    # 解析任务配置
    try:
        config = json.loads(context["task_params"]) if context["task_params"] else {}
    except json.JSONDecodeError:
        log_error("Failed to parse task parameters, using empty config")
        config = {}
    
    log_info("GitHub job configuration", 
             repo=github_repo, 
             branch=branch, 
             commit=commit_sha or "latest",
             entry_point=entry_point)
    
    repo_path = None
    try:
        # 1. 在 Ray worker 内部下载 GitHub 仓库
        repo_path = clone_github_repo(github_repo, branch, commit_sha)
        
        # 2. 执行用户代码
        result = execute_user_code(repo_path, entry_point, config)
        
        # 3. 构建最终结果
        final_result = {
            "job_id": context["job_id"],
            "github_repo": github_repo,
            "branch": branch,
            "commit_sha": commit_sha,
            "entry_point": entry_point,
            "config": config,
            "result": result,
            "timestamp": context["timestamp"],
            "status": "completed",
        }
        
        log_info("GitHub Job Runner completed successfully")
        return final_result
        
    except Exception as e:
        log_error("GitHub Job Runner failed", e)
        return {
            "job_id": context["job_id"],
            "github_repo": github_repo,
            "error": str(e),
            "status": "failed",
            "timestamp": context["timestamp"],
        }
        
    finally:
        # 清理临时文件
        if repo_path:
            cleanup_repo(repo_path)


if __name__ == "__main__":
    main()
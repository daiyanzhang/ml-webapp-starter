"""
GitHub集成服务 - 用于Ray作业的代码获取和管理
"""
import os
import asyncio
import subprocess
import shutil
from typing import Optional, Dict, Any
from uuid import uuid4
from pathlib import Path
import ast

from app.core.config import settings
from app.core.logging import logger


class GitHubService:
    """GitHub仓库操作服务"""
    
    def __init__(self):
        self.temp_base_dir = Path("/tmp/ray_jobs")
        self.temp_base_dir.mkdir(exist_ok=True)
    
    async def clone_public_repo(
        self, 
        repo_url: str, 
        branch: str = "main",
        commit_sha: Optional[str] = None
    ) -> str:
        """
        克隆公共GitHub仓库
        
        Args:
            repo_url: GitHub仓库URL (支持 username/repo 或完整URL)
            branch: 分支名称
            commit_sha: 可选的特定commit
            
        Returns:
            本地仓库路径
        """
        # 标准化仓库URL
        normalized_url = self._normalize_repo_url(repo_url)
        
        # 创建临时目录
        temp_dir = self.temp_base_dir / str(uuid4())
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # 构建git clone命令
            cmd = [
                "git", "clone",
                "--branch", branch,
                "--depth", "1",  # 浅克隆，只获取最新commit
                normalized_url,
                str(temp_dir)
            ]
            
            logger.info(f"Cloning repository: {normalized_url} (branch: {branch})")
            
            # 执行克隆
            result = await self._run_git_command(cmd)
            
            if result.returncode != 0:
                raise Exception(f"Git clone failed: {result.stderr}")
            
            # 如果指定了特定commit，则checkout
            if commit_sha:
                await self._checkout_commit(temp_dir, commit_sha)
            
            logger.info(f"Successfully cloned repository to: {temp_dir}")
            return str(temp_dir)
            
        except Exception as e:
            # 清理失败的目录
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)
            raise Exception(f"Failed to clone repository: {str(e)}")
    
    async def validate_repository_structure(self, repo_path: str, entry_point: str = "main.py") -> Dict[str, Any]:
        """
        验证仓库结构和用户代码
        
        Args:
            repo_path: 本地仓库路径
            entry_point: 入口文件名
            
        Returns:
            验证结果和仓库信息
        """
        repo_path = Path(repo_path)
        entry_file = repo_path / entry_point
        
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "info": {
                "entry_point_exists": False,
                "has_requirements": False,
                "has_config": False,
                "file_count": 0,
                "size_mb": 0
            }
        }
        
        # 检查入口文件
        if not entry_file.exists():
            validation_result["valid"] = False
            validation_result["errors"].append(f"Entry point '{entry_point}' not found")
        else:
            validation_result["info"]["entry_point_exists"] = True
            
            # 验证入口文件内容
            await self._validate_entry_file(entry_file, validation_result)
        
        # 检查requirements.txt (先检查entry point目录，再检查根目录)
        entry_dir = (repo_path / entry_point).parent
        requirements_locations = [
            entry_dir / "requirements.txt",  # entry point目录
            repo_path / "requirements.txt"   # 根目录
        ]
        
        requirements_found = False
        for req_file in requirements_locations:
            if req_file.exists():
                validation_result["info"]["has_requirements"] = True
                requirements_found = True
                break
        
        if not requirements_found:
            validation_result["warnings"].append("No requirements.txt found - assuming no dependencies")
        
        # 检查配置文件
        config_file = repo_path / "ray_job_config.yaml"
        if config_file.exists():
            validation_result["info"]["has_config"] = True
        
        # 统计文件信息
        validation_result["info"]["file_count"] = len(list(repo_path.rglob("*")))
        validation_result["info"]["size_mb"] = round(self._get_directory_size(repo_path) / (1024 * 1024), 2)
        
        # 大小限制检查
        if validation_result["info"]["size_mb"] > 100:  # 100MB限制
            validation_result["valid"] = False
            validation_result["errors"].append(f"Repository size ({validation_result['info']['size_mb']}MB) exceeds limit (100MB)")
        
        return validation_result
    
    async def cleanup_repository(self, repo_path: str) -> None:
        """清理临时仓库目录"""
        try:
            repo_path = Path(repo_path)
            if repo_path.exists() and repo_path.is_relative_to(self.temp_base_dir):
                shutil.rmtree(repo_path, ignore_errors=True)
                logger.info(f"Cleaned up repository: {repo_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup repository {repo_path}: {str(e)}")
    
    def _normalize_repo_url(self, repo_url: str) -> str:
        """标准化GitHub仓库URL"""
        if repo_url.startswith("http"):
            return repo_url
        
        # 处理 username/repo 格式
        if "/" in repo_url and not repo_url.startswith("git@"):
            return f"https://github.com/{repo_url}.git"
        
        return repo_url
    
    async def _run_git_command(self, cmd: list[str]) -> subprocess.CompletedProcess:
        """异步执行git命令"""
        def run_command():
            return subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
        
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, run_command)
    
    async def _checkout_commit(self, repo_path: Path, commit_sha: str) -> None:
        """切换到特定commit"""
        cmd = ["git", "-C", str(repo_path), "checkout", commit_sha]
        result = await self._run_git_command(cmd)
        
        if result.returncode != 0:
            raise Exception(f"Failed to checkout commit {commit_sha}: {result.stderr}")
    
    async def _validate_entry_file(self, entry_file: Path, validation_result: Dict[str, Any]) -> None:
        """验证入口文件内容"""
        try:
            with open(entry_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查文件大小
            if len(content) > 1_000_000:  # 1MB限制
                validation_result["valid"] = False
                validation_result["errors"].append("Entry file too large (>1MB)")
                return
            
            # AST语法检查
            try:
                ast.parse(content)
            except SyntaxError as e:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Syntax error in entry file: {str(e)}")
                return
            
            # 检查必需的函数
            tree = ast.parse(content)
            functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            
            if "process_data" not in functions:
                validation_result["warnings"].append("No 'process_data' function found - will execute entire script")
            
            # 检查危险代码模式
            dangerous_patterns = ["os.system", "subprocess.call", "eval(", "exec(", "__import__"]
            for pattern in dangerous_patterns:
                if pattern in content:
                    validation_result["valid"] = False
                    validation_result["errors"].append(f"Dangerous code pattern detected: {pattern}")
            
        except Exception as e:
            validation_result["errors"].append(f"Failed to validate entry file: {str(e)}")
    
    def _get_directory_size(self, directory: Path) -> int:
        """计算目录大小(字节)"""
        total_size = 0
        try:
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
        except Exception:
            pass
        return total_size


# 单例服务实例
github_service = GitHubService()
"""
Ray作业执行服务 - 基于GitHub代码的分布式任务执行
"""
import os
import uuid
import importlib.util
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

import ray
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import logger
from app.services.github_service import github_service


class JobConfig(BaseModel):
    """Ray作业配置"""
    memory: int = 1024  # MB
    cpu: float = 1.0
    gpu: int = 0
    timeout: int = 3600  # seconds
    retry: int = 3


class GitHubJobRequest(BaseModel):
    """GitHub作业提交请求"""
    template_type: str = "custom"  # data_processing, ml_training, custom
    github_repo: str  # username/repo或完整URL
    branch: str = "main"
    entry_point: str = "main.py"
    commit_sha: Optional[str] = None
    config: Dict[str, Any] = {}
    job_config: JobConfig = JobConfig()


class JobStatus(BaseModel):
    """作业状态"""
    job_id: str
    status: str  # pending, running, completed, failed
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    github_repo: str
    branch: str
    entry_point: str


class RayJobService:
    """Ray作业管理服务"""
    
    def __init__(self):
        self.active_jobs: Dict[str, JobStatus] = {}
        self._ensure_ray_initialized()
    
    def _ensure_ray_initialized(self):
        """确保Ray已初始化"""
        try:
            if not ray.is_initialized():
                # 连接到现有的Ray集群或初始化本地集群
                if hasattr(settings, 'RAY_ADDRESS') and settings.RAY_ADDRESS:
                    ray.init(address=settings.RAY_ADDRESS)
                    logger.info(f"Connected to Ray cluster at: {settings.RAY_ADDRESS}")
                else:
                    ray.init()
                    logger.info("Initialized local Ray cluster")
        except Exception as e:
            logger.error(f"Failed to initialize Ray: {str(e)}")
            raise
    
    async def submit_github_job(
        self, 
        job_request: GitHubJobRequest,
        user_id: int
    ) -> str:
        """
        提交基于GitHub的Ray作业
        
        Args:
            job_request: 作业请求参数
            user_id: 用户ID
            
        Returns:
            作业ID
        """
        job_id = f"ray_job_{uuid.uuid4().hex[:8]}"
        
        # 创建作业状态记录
        job_status = JobStatus(
            job_id=job_id,
            status="pending",
            created_at=datetime.now(),
            github_repo=job_request.github_repo,
            branch=job_request.branch,
            entry_point=job_request.entry_point
        )
        self.active_jobs[job_id] = job_status
        
        try:
            # 1. 克隆GitHub仓库
            logger.info(f"Job {job_id}: Cloning repository {job_request.github_repo}")
            repo_path = await github_service.clone_public_repo(
                job_request.github_repo,
                job_request.branch,
                job_request.commit_sha
            )
            
            # 2. 验证仓库结构
            validation = await github_service.validate_repository_structure(
                repo_path, 
                job_request.entry_point
            )
            
            if not validation["valid"]:
                error_msg = f"Repository validation failed: {', '.join(validation['errors'])}"
                job_status.status = "failed"
                job_status.error = error_msg
                await github_service.cleanup_repository(repo_path)
                raise Exception(error_msg)
            
            # 3. 提交Ray作业
            logger.info(f"Job {job_id}: Submitting to Ray cluster")
            job_status.status = "running"
            job_status.started_at = datetime.now()
            
            # 执行作业
            result = await self._execute_ray_job(
                job_id=job_id,
                repo_path=repo_path,
                entry_point=job_request.entry_point,
                config=job_request.config,
                job_config=job_request.job_config,
                template_type=job_request.template_type
            )
            
            # 4. 处理结果
            job_status.status = "completed"
            job_status.completed_at = datetime.now()
            job_status.result = result
            
            logger.info(f"Job {job_id}: Completed successfully")
            
            # 5. 清理临时文件
            await github_service.cleanup_repository(repo_path)
            
            return job_id
            
        except Exception as e:
            job_status.status = "failed"
            job_status.error = str(e)
            job_status.completed_at = datetime.now()
            logger.error(f"Job {job_id}: Failed - {str(e)}")
            raise
    
    async def _execute_ray_job(
        self,
        job_id: str,
        repo_path: str,
        entry_point: str,
        config: Dict[str, Any],
        job_config: JobConfig,
        template_type: str
    ) -> Any:
        """执行Ray作业"""
        
        # 准备运行时环境
        runtime_env = {
            "working_dir": repo_path,
        }
        
        # 如果有requirements.txt，添加pip依赖
        requirements_path = os.path.join(repo_path, "requirements.txt")
        if os.path.exists(requirements_path):
            runtime_env["pip"] = requirements_path
        
        # 根据模板类型选择执行函数
        if template_type == "data_processing":
            executor_func = self._create_data_processing_executor(runtime_env, job_config)
        elif template_type == "ml_training":
            executor_func = self._create_ml_training_executor(runtime_env, job_config)
        else:
            executor_func = self._create_custom_executor(runtime_env, job_config)
        
        # 提交Ray任务
        try:
            future = executor_func.remote(entry_point, config)
            result = ray.get(future)
            return result
        except Exception as e:
            logger.error(f"Ray job execution failed: {str(e)}")
            raise
    
    def _create_custom_executor(self, runtime_env: Dict[str, Any], job_config: JobConfig):
        """创建自定义执行器"""
        
        @ray.remote(
            runtime_env=runtime_env,
            memory=job_config.memory * 1024 * 1024,  # 转换为字节
            num_cpus=job_config.cpu,
            num_gpus=job_config.gpu
        )
        def execute_custom_code(entry_file: str, config: dict):
            """执行用户自定义代码"""
            import sys
            import os
            
            try:
                # 动态加载用户模块
                spec = importlib.util.spec_from_file_location("user_module", entry_file)
                if spec is None or spec.loader is None:
                    raise ImportError(f"Cannot load module from {entry_file}")
                
                user_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(user_module)
                
                # 尝试执行process_data函数
                if hasattr(user_module, 'process_data'):
                    logger.info("Executing user's process_data function")
                    result = user_module.process_data(config.get('input_data'), config)
                    return {"success": True, "result": result, "type": "function_result"}
                else:
                    # 如果没有process_data函数，整个脚本已经执行了
                    logger.info("No process_data function found, script executed during import")
                    return {"success": True, "result": "Script executed successfully", "type": "script_execution"}
                
            except Exception as e:
                logger.error(f"User code execution failed: {str(e)}")
                return {"success": False, "error": str(e)}
        
        return execute_custom_code
    
    def _create_data_processing_executor(self, runtime_env: Dict[str, Any], job_config: JobConfig):
        """创建数据处理执行器"""
        
        @ray.remote(
            runtime_env=runtime_env,
            memory=job_config.memory * 1024 * 1024,
            num_cpus=job_config.cpu,
            num_gpus=job_config.gpu
        )
        def execute_data_processing(entry_file: str, config: dict):
            """执行数据处理作业"""
            import pandas as pd
            
            try:
                # 加载用户模块
                spec = importlib.util.spec_from_file_location("user_module", entry_file)
                user_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(user_module)
                
                # 准备输入数据
                input_data = None
                if 'data_source' in config:
                    # 这里可以扩展支持多种数据源
                    data_source = config['data_source']
                    if data_source.endswith('.csv'):
                        input_data = pd.read_csv(data_source)
                    elif data_source.endswith('.json'):
                        input_data = pd.read_json(data_source)
                
                # 执行用户的数据处理函数
                if hasattr(user_module, 'process_data'):
                    result = user_module.process_data(input_data, config)
                    
                    # 保存结果
                    if 'output_path' in config and isinstance(result, pd.DataFrame):
                        result.to_csv(config['output_path'], index=False)
                    
                    return {"success": True, "result": result, "type": "data_processing"}
                else:
                    raise Exception("process_data function not found in user code")
                
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        return execute_data_processing
    
    def _create_ml_training_executor(self, runtime_env: Dict[str, Any], job_config: JobConfig):
        """创建机器学习训练执行器"""
        
        @ray.remote(
            runtime_env=runtime_env,
            memory=job_config.memory * 1024 * 1024,
            num_cpus=job_config.cpu,
            num_gpus=job_config.gpu
        )
        def execute_ml_training(entry_file: str, config: dict):
            """执行机器学习训练作业"""
            try:
                # 加载用户模块
                spec = importlib.util.spec_from_file_location("user_module", entry_file)
                user_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(user_module)
                
                # ML训练通常需要更复杂的数据处理
                if hasattr(user_module, 'train_model'):
                    result = user_module.train_model(config)
                    return {"success": True, "result": result, "type": "ml_training"}
                elif hasattr(user_module, 'process_data'):
                    result = user_module.process_data(None, config)
                    return {"success": True, "result": result, "type": "ml_processing"}
                else:
                    raise Exception("Neither train_model nor process_data function found")
                
            except Exception as e:
                return {"success": False, "error": str(e)}
        
        return execute_ml_training
    
    async def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """获取作业状态"""
        return self.active_jobs.get(job_id)
    
    async def list_jobs(self, limit: int = 10) -> List[JobStatus]:
        """列出作业"""
        jobs = list(self.active_jobs.values())
        # 按创建时间倒序排序
        jobs.sort(key=lambda x: x.created_at, reverse=True)
        return jobs[:limit]
    
    async def cancel_job(self, job_id: str) -> bool:
        """取消作业"""
        # TODO: 实现作业取消逻辑
        if job_id in self.active_jobs:
            job = self.active_jobs[job_id]
            if job.status == "running":
                job.status = "cancelled"
                job.completed_at = datetime.now()
                return True
        return False


# 单例服务实例
ray_job_service = RayJobService()
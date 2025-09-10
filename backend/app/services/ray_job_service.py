"""
Ray作业执行服务 - 基于GitHub代码的分布式任务执行
"""
import os
import uuid
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

import ray
from ray.job_submission import JobSubmissionClient
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.config import settings
from app.core.logging import logger
from app.core.database import SessionLocal
from app.db.models import RayJob
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
    job_type: str  # github, notebook
    status: str  # pending, running, completed, failed
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    github_repo: Optional[str] = None
    branch: Optional[str] = None
    entry_point: Optional[str] = None
    notebook_path: Optional[str] = None
    ray_job_id: Optional[str] = None  # Ray集群中的作业ID
    dashboard_url: Optional[str] = None  # Ray Dashboard链接


class RayJobService:
    """Ray作业管理服务"""
    
    def __init__(self):
        self._ensure_ray_initialized()
    
    def _create_db_job(self, job_status: JobStatus, job_request: 'GitHubJobRequest', user_id: int) -> None:
        """创建数据库作业记录"""
        db = SessionLocal()
        try:
            db_job = RayJob(
                job_id=job_status.job_id,
                job_type="github",
                status=job_status.status,
                user_id=user_id,
                github_repo=job_request.github_repo,
                branch=job_request.branch,
                entry_point=job_request.entry_point,
                template_type=job_request.template_type,
                config=json.dumps(job_request.config) if job_request.config else None,
                job_config=json.dumps(job_request.job_config.dict()) if job_request.job_config else None,
                created_at=job_status.created_at
            )
            db.add(db_job)
            db.commit()
            logger.info(f"Created database record for job {job_status.job_id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create database record for job {job_status.job_id}: {e}")
        finally:
            db.close()
    
    def _update_db_job(self, job_id: str, **updates) -> None:
        """更新数据库作业记录"""
        db = SessionLocal()
        try:
            db_job = db.query(RayJob).filter(RayJob.job_id == job_id).first()
            if db_job:
                for key, value in updates.items():
                    if hasattr(db_job, key):
                        setattr(db_job, key, value)
                db.commit()
                logger.info(f"Updated database record for job {job_id}")
            else:
                logger.warning(f"Job {job_id} not found in database")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update database record for job {job_id}: {e}")
        finally:
            db.close()
    
    def _job_status_from_db(self, db_job: RayJob) -> JobStatus:
        """将数据库记录转换为JobStatus对象"""
        return JobStatus(
            job_id=db_job.job_id,
            job_type=db_job.job_type,
            status=db_job.status,
            created_at=db_job.created_at,
            started_at=db_job.started_at,
            completed_at=db_job.completed_at,
            result=json.loads(db_job.result) if db_job.result else None,
            error=db_job.error_message,
            github_repo=db_job.github_repo,
            branch=db_job.branch,
            entry_point=db_job.entry_point,
            notebook_path=db_job.notebook_path,
            ray_job_id=db_job.ray_job_id,
            dashboard_url=db_job.dashboard_url
        )
    
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
        提交基于GitHub的Ray作业（异步）
        
        Args:
            job_request: 作业请求参数
            user_id: 用户ID
            
        Returns:
            作业ID（立即返回，无需等待执行完成）
        """
        job_id = f"ray_job_{uuid.uuid4().hex[:8]}"
        
        # 创建作业状态记录
        job_status = JobStatus(
            job_id=job_id,
            job_type="github",
            status="pending",
            created_at=datetime.now(),
            github_repo=job_request.github_repo,
            branch=job_request.branch,
            entry_point=job_request.entry_point
        )
        
        # 保存到数据库
        self._create_db_job(job_status, job_request, user_id)
        
        # 立即在后台启动作业执行，不阻塞API响应
        asyncio.create_task(self._execute_github_job_async(job_id, job_request))
        
        logger.info(f"Job {job_id}: Submitted for execution")
        return job_id
    
    async def _execute_github_job_async(
        self, 
        job_id: str, 
        job_request: GitHubJobRequest
    ) -> None:
        """
        异步执行GitHub Ray作业
        """
        
        try:
            # 直接提交Ray作业 - GitHub仓库操作在Ray任务内部完成
            logger.info(f"Job {job_id}: Submitting to Ray cluster")
            
            # 执行作业并获取Ray job ID - 直接传递 GitHub 仓库信息
            result, ray_job_id = await self._execute_ray_job(
                job_id=job_id,
                github_repo=job_request.github_repo,
                branch=job_request.branch,
                commit_sha=job_request.commit_sha,
                entry_point=job_request.entry_point,
                config=job_request.config,
                job_config=job_request.job_config
            )
            
            # 更新数据库状态为pending，dashboard链接由前端拼接
            self._update_db_job(job_id,
                              status="pending",  # Ray job已提交，状态为pending，后续由ray_job_decorator更新
                              ray_job_id=ray_job_id)
            
            logger.info(f"Job {job_id}: Ray job {ray_job_id} submitted, status set to pending")
            
        except Exception as e:
            error_msg = str(e)
            self._update_db_job(job_id,
                              status="failed",
                              error_message=error_msg,
                              completed_at=datetime.now())
            logger.error(f"Job {job_id}: Failed - {error_msg}")
    
    async def _execute_ray_job(
        self,
        job_id: str,
        github_repo: str,
        branch: str,
        commit_sha: str,
        entry_point: str,
        config: Dict[str, Any],
        job_config: JobConfig
    ) -> tuple[Any, Optional[str]]:
        """执行Ray作业 - 使用通用的 GitHub job runner"""
        
        # 构建运行时环境 - 回到原来的 working_dir 方式
        runtime_env = {
            "working_dir": "/app/ray-jobs"  # 使用容器内的挂载路径
        }
        
        # 设置环境变量传递 GitHub 仓库信息和任务配置
        runtime_env["env_vars"] = {
            "RAY_JOB_CONFIG": json.dumps(config),
            "RAY_JOB_ID": job_id,
            "RAY_JOB_TYPE": "github_job",
            "GITHUB_REPO": github_repo,
            "GITHUB_BRANCH": branch,
            "ENTRY_POINT": entry_point,
            "PYTHONPATH": "./ray-jobs:$PYTHONPATH"
        }
        
        # 如果指定了 commit，添加到环境变量
        if commit_sha:
            runtime_env["env_vars"]["GITHUB_COMMIT"] = commit_sha
        
        # 提交Ray Job - 使用通用的 GitHub runner
        try:
            # 连接到Ray集群
            client = JobSubmissionClient("http://ray-head:8265")
            
            # 使用通用的 GitHub job runner
            entrypoint = "python github_job_runner.py"
            
            # 异步提交job
            loop = asyncio.get_event_loop()
            job_submission_id = await loop.run_in_executor(
                None,
                lambda: client.submit_job(
                    entrypoint=entrypoint,
                    runtime_env=runtime_env,
                    metadata={"internal_job_id": job_id}
                )
            )
            
            logger.info(f"Submitted GitHub job {job_submission_id} for internal job {job_id}")
            
            # 异步提交完成，立即返回
            return {"success": True, "message": "GitHub job submitted successfully"}, job_submission_id
        except Exception as e:
            logger.error(f"GitHub job execution failed: {str(e)}")
            raise
    
    async def get_job_status(self, job_id: str) -> Optional[JobStatus]:
        """获取作业状态"""
        db = SessionLocal()
        try:
            db_job = db.query(RayJob).filter(RayJob.job_id == job_id).first()
            if db_job:
                return self._job_status_from_db(db_job)
            return None
        finally:
            db.close()
    
    async def list_jobs(self, limit: int = 10) -> List[JobStatus]:
        """列出作业"""
        db = SessionLocal()
        try:
            db_jobs = db.query(RayJob).order_by(desc(RayJob.created_at)).limit(limit).all()
            return [self._job_status_from_db(job) for job in db_jobs]
        finally:
            db.close()
    
    async def cancel_job(self, job_id: str) -> bool:
        """取消作业"""
        # TODO: 实现Ray作业取消逻辑
        db = SessionLocal()
        try:
            db_job = db.query(RayJob).filter(RayJob.job_id == job_id).first()
            if db_job and db_job.status == "running":
                db_job.status = "cancelled"
                db_job.completed_at = datetime.now()
                db.commit()
                logger.info(f"Cancelled job {job_id}")
                return True
            return False
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False
        finally:
            db.close()


# 单例服务实例
ray_job_service = RayJobService()
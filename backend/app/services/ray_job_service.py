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
    status: str  # pending, running, completed, failed
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    github_repo: str
    branch: str
    entry_point: str
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
            status=db_job.status,
            created_at=db_job.created_at,
            started_at=db_job.started_at,
            completed_at=db_job.completed_at,
            result=json.loads(db_job.result) if db_job.result else None,
            error=db_job.error_message,
            github_repo=db_job.github_repo,
            branch=db_job.branch,
            entry_point=db_job.entry_point,
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
                self._update_db_job(job_id, 
                                  status="failed",
                                  error_message=error_msg,
                                  completed_at=datetime.now())
                await github_service.cleanup_repository(repo_path)
                logger.error(f"Job {job_id}: {error_msg}")
                return
            
            # 3. 提交Ray作业
            logger.info(f"Job {job_id}: Submitting to Ray cluster")
            
            # 执行作业并获取Ray job ID
            result, ray_job_id = await self._execute_ray_job(
                job_id=job_id,
                repo_path=repo_path,
                entry_point=job_request.entry_point,
                config=job_request.config,
                job_config=job_request.job_config,
                template_type=job_request.template_type
            )
            
            # 更新数据库状态为pending，dashboard链接由前端拼接
            self._update_db_job(job_id,
                              status="pending",  # Ray job已提交，状态为pending，后续由ray_job_decorator更新
                              ray_job_id=ray_job_id)
            
            logger.info(f"Job {job_id}: Ray job {ray_job_id} submitted, status set to pending")
            
            # 5. 清理临时文件
            await github_service.cleanup_repository(repo_path)
            
        except Exception as e:
            error_msg = str(e)
            self._update_db_job(job_id,
                              status="failed",
                              error_message=error_msg,
                              completed_at=datetime.now())
            logger.error(f"Job {job_id}: Failed - {error_msg}")
            
            # 尝试清理，但不再抛出异常影响其他作业
            try:
                if 'repo_path' in locals():
                    await github_service.cleanup_repository(repo_path)
            except:
                pass
    
    async def _execute_ray_job(
        self,
        job_id: str,
        repo_path: str,
        entry_point: str,
        config: Dict[str, Any],
        job_config: JobConfig,
        template_type: str
    ) -> tuple[Any, Optional[str]]:
        """执行Ray作业"""
        
        # 准备运行时环境 - 将整个仓库目录作为working_dir
        runtime_env = {
            "working_dir": repo_path
        }
        
        # 检查requirements.txt位置（先检查entry point目录，再检查根目录）
        entry_dir = os.path.join(repo_path, os.path.dirname(entry_point))
        requirements_locations = [
            os.path.join(entry_dir, "requirements.txt"),  # entry point目录
            os.path.join(repo_path, "requirements.txt")   # 根目录
        ]
        
        for req_path in requirements_locations:
            if os.path.exists(req_path):
                runtime_env["pip"] = req_path
                break
        
        # 不再硬编码py_modules，而是通过PYTHONPATH让Python自然找到依赖
        
        # 不再需要创建executor，直接使用Job Submission API
        
        # 提交Ray Job (使用Job Submission API)
        try:
            # 连接到Ray集群
            client = JobSubmissionClient("http://ray-head:8265")
            
            # 设置环境变量传递配置
            runtime_env["env_vars"] = {
                "RAY_JOB_CONFIG": json.dumps(config),
                "RAY_JOB_ID": job_id,
                "RAY_JOB_TYPE": template_type,
                "PYTHONPATH": "./ray-jobs:$PYTHONPATH"  # 将ray-jobs目录添加到Python路径
            }
            
            # 直接执行用户的Python文件
            entrypoint = f"python {entry_point}"
            
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
            
            logger.info(f"Submitted Ray job {job_submission_id} for internal job {job_id}")
            
            # 异步提交完成，立即返回
            return {"success": True, "message": "Ray job submitted successfully"}, job_submission_id
        except Exception as e:
            logger.error(f"Ray job execution failed: {str(e)}")
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
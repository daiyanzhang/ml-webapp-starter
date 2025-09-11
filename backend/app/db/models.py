from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float
from sqlalchemy.sql import func

from app.core.database import Base


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class RayJob(Base):
    """Ray任务模型"""
    __tablename__ = "ray_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True, nullable=False)
    job_type = Column(String, nullable=False)  # github, notebook
    queue = Column(String, nullable=False, default="default")  # 队列名称
    status = Column(String, nullable=False)  # pending, running, completed, failed
    user_id = Column(Integer, nullable=True)  # 可选：记录提交任务的用户
    
    # GitHub集成字段 (nullable for notebook jobs)
    github_repo = Column(String, nullable=True)
    branch = Column(String, nullable=True)
    entry_point = Column(String, nullable=True)
    template_type = Column(String, nullable=True)
    
    # Notebook集成字段 (nullable for github jobs)
    notebook_path = Column(String, nullable=True)
    
    # Ray相关字段
    ray_job_id = Column(String, nullable=True)  # Ray集群中的作业ID
    dashboard_url = Column(String, nullable=True)  # Ray Dashboard链接
    
    # 执行配置和结果
    config = Column(Text, nullable=True)  # JSON字符串：用户配置
    job_config = Column(Text, nullable=True)  # JSON字符串：作业配置(CPU/内存等)
    result = Column(Text, nullable=True)  # JSON字符串：执行结果
    error_message = Column(Text, nullable=True)  # 错误信息
    
    # 时间戳
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
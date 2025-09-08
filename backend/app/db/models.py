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
    job_type = Column(String, nullable=False)
    status = Column(String, nullable=False)  # completed, failed, running
    user_id = Column(Integer, nullable=True)  # 可选：记录提交任务的用户
    parameters = Column(Text, nullable=True)  # JSON字符串
    result = Column(Text, nullable=True)  # JSON字符串
    error_message = Column(Text, nullable=True)
    execution_time = Column(Float, nullable=True)  # 执行时间（秒）
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
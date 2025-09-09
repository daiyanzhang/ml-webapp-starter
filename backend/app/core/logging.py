"""
日志配置模块
"""
import logging
import sys
from typing import Dict, Any
from app.core.config import settings

# 日志格式
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

def setup_logging() -> None:
    """设置项目日志配置"""
    
    # 配置根日志器
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO),
        format=LOG_FORMAT,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("temporalio").setLevel(logging.INFO)
    logging.getLogger("ray").setLevel(logging.INFO)

def get_logger(name: str) -> logging.Logger:
    """获取指定名称的日志器"""
    return logging.getLogger(name)

# 创建默认的项目日志器
logger = get_logger("webapp-starter")

# 确保日志配置已初始化
setup_logging()
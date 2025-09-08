"""
Temporal配置和客户端连接
"""
from temporalio.client import Client
from app.core.config import settings


async def get_temporal_client() -> Client:
    """获取Temporal客户端"""
    return await Client.connect(
        target_host=settings.TEMPORAL_HOST,
        namespace=settings.TEMPORAL_NAMESPACE
    )


def get_task_queue() -> str:
    """获取任务队列名称"""
    return settings.TEMPORAL_TASK_QUEUE
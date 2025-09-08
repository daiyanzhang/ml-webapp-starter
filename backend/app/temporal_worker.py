"""
Temporal Worker - 后台任务处理器
"""
import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent.parent
sys.path.insert(0, str(current_dir))

from temporalio.client import Client
from temporalio.worker import Worker

from app.core.temporal_config import get_temporal_client, get_task_queue
from app.workflows.example_workflow import (
    ExampleWorkflow,
    send_email_activity,
    process_data_activity
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """启动Temporal Worker"""
    
    # 连接到Temporal服务器
    client = await get_temporal_client()
    logger.info(f"Connected to Temporal server")
    
    # 创建并启动Worker
    worker = Worker(
        client,
        task_queue=get_task_queue(),
        workflows=[ExampleWorkflow],
        activities=[send_email_activity, process_data_activity],
        max_concurrent_activities=10,
    )
    
    logger.info(f"Starting worker on task queue: {get_task_queue()}")
    
    # 运行Worker
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
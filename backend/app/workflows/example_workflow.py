"""
示例Temporal工作流和活动
"""
import asyncio
from datetime import timedelta
from typing import Any

from temporalio import workflow, activity
from temporalio.common import RetryPolicy


@activity.defn
async def send_email_activity(recipient: str, subject: str, content: str) -> bool:
    """发送邮件活动"""
    # 模拟发送邮件
    print(f"发送邮件到 {recipient}: {subject}")
    await asyncio.sleep(2)  # 模拟网络延迟
    return True


@activity.defn
async def process_data_activity(data: dict) -> dict:
    """处理数据活动"""
    # 模拟数据处理
    print(f"处理数据: {data}")
    await asyncio.sleep(1)
    return {"status": "processed", "result": f"Processed {len(data)} items"}


@workflow.defn
class ExampleWorkflow:
    """示例工作流"""

    @workflow.run
    async def run(self, user_id: int, action: str) -> dict:
        """
        执行示例工作流
        
        Args:
            user_id: 用户ID
            action: 操作类型
            
        Returns:
            工作流结果
        """
        
        # 第一步：处理数据
        data_result = await workflow.execute_activity(
            process_data_activity,
            args=[{"user_id": user_id, "action": action}],
            start_to_close_timeout=timedelta(minutes=1),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=1),
                maximum_interval=timedelta(seconds=60),
                maximum_attempts=3
            )
        )
        
        # 第二步：发送通知邮件
        email_result = await workflow.execute_activity(
            send_email_activity,
            args=[
                f"user_{user_id}@example.com",
                f"操作完成: {action}",
                f"您的操作已完成，结果: {data_result}"
            ],
            start_to_close_timeout=timedelta(minutes=1)
        )
        
        # 返回工作流结果
        return {
            "user_id": user_id,
            "action": action,
            "data_result": data_result,
            "email_sent": email_result,
            "workflow_id": workflow.info().workflow_id
        }
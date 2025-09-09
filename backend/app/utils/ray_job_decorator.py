"""
Ray Job监控装饰器
在Ray Job脚本中使用，自动处理状态更新和结果报告
"""

import json
import os
import sys
import traceback
from datetime import datetime
from typing import Dict, Any, Callable
import requests
from functools import wraps


def ray_job_monitor(api_base_url: str = "http://backend:8000"):
    """
    Ray Job监控装饰器

    使用方法:
    @ray_job_monitor(api_base_url="http://backend:8000")
    def my_ray_job():
        # job logic here
        return result
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # 从环境变量获取job信息
            job_id = os.environ.get("RAY_JOB_ID", "unknown")
            submission_id = os.environ.get("RAY_SUBMISSION_ID", "unknown")

            print(f"=== Ray Job Monitor Started ===")
            print(f"Job ID: {job_id}")
            print(f"Submission ID: {submission_id}")
            print(f"Function: {func.__name__}")

            start_time = datetime.now()

            try:
                # 更新状态为运行中
                update_job_status(
                    api_base_url, job_id, "running", start_time=start_time.isoformat()
                )

                # 执行实际的job函数
                result = func(*args, **kwargs)

                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()

                # 更新状态为完成
                update_job_status(
                    api_base_url,
                    job_id,
                    "completed",
                    result=result,
                    execution_time=execution_time,
                    end_time=end_time.isoformat(),
                )

                print(f"=== Ray Job Monitor Completed ===")
                print(
                    f"Job {job_id} completed successfully in {execution_time:.2f} seconds"
                )
                return result

            except Exception as e:
                end_time = datetime.now()
                execution_time = (end_time - start_time).total_seconds()
                error_msg = str(e)
                traceback_str = traceback.format_exc()

                # 更新状态为失败
                update_job_status(
                    api_base_url,
                    job_id,
                    "failed",
                    error_message=error_msg,
                    traceback=traceback_str,
                    execution_time=execution_time,
                    end_time=end_time.isoformat(),
                )

                print(f"=== Ray Job Monitor Failed ===")
                print(f"Job {job_id} failed after {execution_time:.2f} seconds")
                print(f"Error: {error_msg}")

                # 重新抛出异常
                raise

        return wrapper

    return decorator


def update_job_status(
    api_base_url: str,
    job_id: str,
    status: str,
    result: Any = None,
    error_message: str = None,
    traceback: str = None,
    execution_time: float = None,
    start_time: str = None,
    end_time: str = None,
):
    """更新job状态到API服务器"""
    try:
        update_data = {"job_id": job_id, "status": status}

        if result is not None:
            update_data["result"] = result
        if error_message:
            update_data["error_message"] = error_message
        if traceback:
            update_data["traceback"] = traceback
        if execution_time is not None:
            update_data["execution_time"] = execution_time
        if start_time:
            update_data["start_time"] = start_time
        if end_time:
            update_data["end_time"] = end_time

        response = requests.post(
            f"{api_base_url}/api/v1/ray/update-status", json=update_data, timeout=10
        )

        if response.status_code == 200:
            print(f"Status updated successfully: {status}")
        else:
            print(f"Failed to update status: {response.status_code} - {response.text}")

    except Exception as e:
        print(f"Error updating job status: {e}")
        # 不抛出异常，避免影响主要的job执行


def setup_job_environment(job_id: str, submission_id: str = None):
    """设置job环境变量（用于测试）"""
    os.environ["RAY_JOB_ID"] = job_id
    if submission_id:
        os.environ["RAY_SUBMISSION_ID"] = submission_id


if __name__ == "__main__":
    # 测试装饰器
    setup_job_environment("test_job_123", "sub_456")

    @ray_job_monitor(api_base_url="http://backend:8000")
    def test_job():
        import time

        print("执行测试任务...")
        time.sleep(2)
        return {"message": "任务完成", "data": [1, 2, 3, 4, 5]}

    try:
        result = test_job()
        print("Test result:", result)
    except Exception as e:
        print("Test failed:", e)

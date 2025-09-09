#!/usr/bin/env python3
"""
独立的Ray Job脚本 - 数据处理任务
在Ray集群上作为独立Job运行
"""
import ray
import sys
import json
import time
import os
import random
import numpy as np
from datetime import datetime
from typing import Dict, Any, List

# 导入调试工具（可选）
from debug_utils import log_info, log_error


@ray.remote
def process_data_batch(data_batch: List[float], batch_id: int) -> Dict[str, Any]:
    """处理单个数据批次"""
    log_info(f"Processing batch {batch_id} with {len(data_batch)} items")

    # 模拟数据处理时间
    time.sleep(0.2)

    # 计算统计信息
    stats = {
        "batch_id": batch_id,
        "size": len(data_batch),
        "min": float(np.min(data_batch)),
        "max": float(np.max(data_batch)),
        "mean": float(np.mean(data_batch)),
        "std": float(np.std(data_batch)),
        "sum": float(np.sum(data_batch)),
    }

    return stats


@ray.remote
def generate_sample_data(size: int, seed: int = None) -> List[float]:
    """生成样本数据"""
    if seed:
        random.seed(seed)
        np.random.seed(seed)

    log_info(f"Generating {size} data points")

    # 生成混合分布数据
    data = []
    for i in range(size):
        if i % 3 == 0:
            # 正态分布
            data.append(np.random.normal(100, 15))
        elif i % 3 == 1:
            # 均匀分布
            data.append(np.random.uniform(50, 150))
        else:
            # 指数分布
            data.append(np.random.exponential(20))

    return data


def main():
    """主函数 - 作为独立Ray Job运行"""
    # 从环境变量获取参数
    job_id = os.environ.get("RAY_JOB_ID", "unknown")
    task_type = os.environ.get("TASK_TYPE", "data_processing")
    params_str = os.environ.get("TASK_PARAMS", "{}")

    try:
        params = json.loads(params_str)
    except:
        params = {}

    log_info("=== Ray Data Processing Job Started ===")
    log_info(f"Job ID: {job_id}")
    log_info(f"Task Type: {task_type}")
    log_info(f"Parameters: {params}")

    # 连接到Ray集群
    if not ray.is_initialized():
        ray.init()

    start_time = datetime.now()

    # 获取参数
    data_size = params.get("data_size", 10000)
    batch_size = params.get("batch_size", 1000)

    log_info(f"Processing {data_size} data points in batches of {batch_size}")

    # 第一步：生成数据
    log_info("Step 1: Generating sample data...")
    data_future = generate_sample_data.remote(data_size, seed=42)
    data = ray.get(data_future)

    # 第二步：分批处理数据
    log_info("Step 2: Processing data in parallel batches...")
    batch_futures = []

    for i in range(0, len(data), batch_size):
        batch_data = data[i : i + batch_size]
        batch_id = i // batch_size
        future = process_data_batch.remote(batch_data, batch_id)
        batch_futures.append(future)

    log_info(f"Created {len(batch_futures)} parallel processing tasks")

    # 收集所有批次结果
    batch_results = ray.get(batch_futures)

    # 第三步：聚合结果
    log_info("Step 3: Aggregating results...")

    total_processed = sum(result["size"] for result in batch_results)
    global_min = min(result["min"] for result in batch_results)
    global_max = max(result["max"] for result in batch_results)
    global_sum = sum(result["sum"] for result in batch_results)
    global_mean = global_sum / total_processed

    # 计算全局标准差（简化版）
    batch_variances = []
    for result in batch_results:
        variance_contribution = result["std"] ** 2 * result["size"]
        batch_variances.append(variance_contribution)

    global_variance = sum(batch_variances) / total_processed
    global_std = np.sqrt(global_variance)

    # 构建最终结果
    final_result = {
        "job_id": job_id,
        "task_type": task_type,
        "parameters": params,
        "result": {
            "data_processing_summary": {
                "total_data_points": total_processed,
                "batches_processed": len(batch_results),
                "batch_size": batch_size,
                "global_statistics": {
                    "min": float(global_min),
                    "max": float(global_max),
                    "mean": float(global_mean),
                    "std": float(global_std),
                    "sum": float(global_sum),
                },
            },
            "batch_statistics": batch_results[:5],  # 只返回前5个批次的详细统计
        },
        "start_time": start_time.isoformat(),
        "end_time": datetime.now().isoformat(),
        "status": "completed",
    }

    log_info("=== Ray Data Processing Job Logic Completed ===")
    log_info(f"Processed {total_processed} data points in {len(batch_results)} batches")
    return final_result


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
独立的Ray Job脚本 - 简单计算任务
在Ray集群上作为独立Job运行
"""
import ray
import sys
import json
import time
import os
from datetime import datetime
from typing import Dict, Any

# 导入装饰器和调试工具
from ray_job_decorator import ray_job_monitor
from debug_utils import log_info, log_error, debug_print, progress_tracker, measure_execution_time, get_job_context


@ray.remote
def compute_prime_count(start: int, end: int) -> Dict[str, Any]:
    """计算指定范围内的素数数量"""
    def is_prime(n):
        if n < 2:
            return False
        for i in range(2, int(n ** 0.5) + 1):
            if n % i == 0:
                return False
        return True
    
    print(f"Computing primes from {start} to {end}")
    primes = []
    for num in range(start, end + 1):
        if is_prime(num):
            primes.append(num)
    
    return {
        "range": f"{start}-{end}",
        "prime_count": len(primes),
        "primes": primes[:10] if len(primes) > 10 else primes
    }


@ray.remote 
def parallel_sum(numbers: list) -> float:
    """并行计算数组和"""
    print(f"Computing sum of {len(numbers)} numbers")
    time.sleep(0.5)  # 模拟计算时间
    return sum(numbers)


@ray.remote
def fibonacci_compute(n: int) -> int:
    """计算斐波那契数列（迭代版本，避免递归爆炸）"""
    if n <= 1:
        return n
    
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b


# === 核心业务逻辑函数 - 可以本地调试 ===

@measure_execution_time("prime_computation")
def compute_primes_core(start_range: int, end_range: int, chunk_size: int) -> Dict[str, Any]:
    """核心素数计算逻辑 - 可在本地调试"""
    log_info("Starting prime computation", start=start_range, end=end_range, chunk_size=chunk_size)
    
    # 分块并行计算
    futures = []
    for i in range(start_range, end_range + 1, chunk_size):
        chunk_end = min(i + chunk_size - 1, end_range)
        future = compute_prime_count.remote(i, chunk_end)
        futures.append(future)
    
    log_info("Created parallel tasks", task_count=len(futures))
    
    # 使用进度跟踪器
    tracker = progress_tracker(len(futures), "Prime computation")
    
    # 收集结果
    results = []
    for i, future in enumerate(futures):
        result = ray.get(future)
        results.append(result)
        tracker.update()
    
    tracker.finish()
    
    # 合并结果
    total_primes = sum(r["prime_count"] for r in results)
    all_primes = []
    for r in results:
        all_primes.extend(r["primes"])
    
    final_result = {
        "total_prime_count": total_primes,
        "range": f"{start_range}-{end_range}",
        "chunks_processed": len(results),
        "sample_primes": sorted(set(all_primes))[:20]
    }
    
    debug_print("Prime computation completed", {
        "total_primes": total_primes,
        "chunks": len(results),
        "sample_size": len(final_result["sample_primes"])
    })
    
    return final_result


@measure_execution_time("parallel_sum")
def compute_parallel_sum_core(array_size: int, chunk_size: int) -> Dict[str, Any]:
    """核心并行求和逻辑 - 可在本地调试"""
    log_info("Starting parallel sum", array_size=array_size, chunk_size=chunk_size)
    
    # 生成测试数据
    import random
    numbers = [random.random() * 100 for _ in range(array_size)]
    debug_print("Generated test data", {"sample": numbers[:5]})
    
    # 分块并行计算
    futures = []
    for i in range(0, len(numbers), chunk_size):
        chunk = numbers[i:i + chunk_size]
        future = parallel_sum.remote(chunk)
        futures.append(future)
    
    log_info("Created parallel tasks", task_count=len(futures))
    
    # 收集结果
    chunk_sums = ray.get(futures)
    total_sum = sum(chunk_sums)
    
    result = {
        "array_size": array_size,
        "chunk_size": chunk_size,
        "chunks_processed": len(futures),
        "total_sum": total_sum,
        "average": total_sum / array_size
    }
    
    debug_print("Parallel sum completed", result)
    return result


@measure_execution_time("fibonacci")
def compute_fibonacci_core(n: int) -> Dict[str, Any]:
    """核心斐波那契计算逻辑 - 可在本地调试"""
    log_info("Starting fibonacci computation", n=n)
    
    if n > 50:  # 安全限制
        log_error("Fibonacci n too large, limiting to 50", n=n)
        n = 50
    
    result = ray.get(fibonacci_compute.remote(n))
    
    final_result = {
        "fibonacci_n": n,
        "result": result
    }
    
    debug_print("Fibonacci completed", final_result)
    return final_result


# === Ray Job入口函数 ===

@ray_job_monitor(api_base_url="http://backend-debug:8000")
def main():
    """Ray Job入口函数 - 只负责参数解析和调用核心逻辑"""
    # 获取任务上下文
    context = get_job_context()
    log_info("Ray Job started", **context)
    
    # 解析参数
    try:
        params = json.loads(context["task_params"])
    except:
        params = {}
        log_error("Failed to parse task parameters, using defaults")
    
    task_type = context["task_type"]
    debug_print("Parsed parameters", {"task_type": task_type, "params": params})
    
    # 确保Ray已初始化
    if not ray.is_initialized():
        ray.init()
        log_info("Ray initialized")
    
    # 根据任务类型调用对应的核心逻辑
    try:
        if task_type == "prime_count":
            start_range = params.get("start", 1)
            end_range = params.get("end", 1000)
            chunk_size = params.get("chunk_size", 100)
            task_result = compute_primes_core(start_range, end_range, chunk_size)
            
        elif task_type == "parallel_sum":
            array_size = params.get("array_size", 10000)
            chunk_size = params.get("chunk_size", 1000)
            task_result = compute_parallel_sum_core(array_size, chunk_size)
            
        elif task_type == "fibonacci":
            n = params.get("n", 20)
            task_result = compute_fibonacci_core(n)
            
        else:
            log_error("Unknown task type", task_type=task_type)
            task_result = {"error": f"Unknown task type: {task_type}"}
            
    except Exception as e:
        log_error("Task execution failed", e, task_type=task_type)
        task_result = {"error": str(e), "task_type": task_type}
    
    # 构建最终结果
    final_result = {
        "job_id": context["job_id"],
        "task_type": task_type,
        "parameters": params,
        "result": task_result,
        "timestamp": context["timestamp"],
        "status": "completed" if "error" not in task_result else "failed"
    }
    
    log_info("Ray Job completed", status=final_result["status"])
    return final_result


# === 本地调试支持 ===

def local_debug_prime_count():
    """本地调试素数计算"""
    print("=== 本地调试：素数计算 ===")
    
    # 启用调试模式
    os.environ['RAY_DEBUG_MODE'] = 'true'
    
    # 初始化Ray (本地)
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True)
    
    # 直接调用核心逻辑进行调试
    result = compute_primes_core(1, 100, 25)  # 在这里设置断点
    print(f"调试结果: {result}")
    
    # 关闭Ray
    ray.shutdown()
    
    return result


def local_debug_parallel_sum():
    """本地调试并行求和"""
    print("=== 本地调试：并行求和 ===")
    
    # 启用调试模式
    os.environ['RAY_DEBUG_MODE'] = 'true'
    
    # 初始化Ray (本地)
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True)
    
    # 直接调用核心逻辑进行调试
    result = compute_parallel_sum_core(1000, 200)  # 在这里设置断点
    print(f"调试结果: {result}")
    
    # 关闭Ray
    ray.shutdown()
    
    return result


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        # 本地调试模式
        print("🐛 进入本地调试模式")
        
        if len(sys.argv) > 2:
            debug_type = sys.argv[2]
            if debug_type == "prime":
                local_debug_prime_count()
            elif debug_type == "sum":
                local_debug_parallel_sum()
            else:
                print(f"未知调试类型: {debug_type}")
        else:
            # 默认调试素数计算
            local_debug_prime_count()
    else:
        # Ray Job模式
        main()
#!/usr/bin/env python3
"""
Ray Job调试测试脚本
用于测试VSCode远程调试功能
"""
import os
import time
from ray_job_decorator import ray_job_monitor


@ray_job_monitor(
    api_base_url="http://backend-debug:8000", 
    enable_debug=True, 
    debug_port=5679
)
def main():
    """调试测试主函数"""
    print("=== 调试测试开始 ===")
    
    # 测试变量
    test_data = {
        "message": "Hello from Ray Job!",
        "numbers": [1, 2, 3, 4, 5],
        "config": {
            "debug_mode": True,
            "timeout": 30
        }
    }
    
    print(f"测试数据: {test_data}")
    
    # 循环处理数据（方便设置断点）
    results = []
    for i, num in enumerate(test_data["numbers"]):
        # 在这里设置断点来调试
        processed = num ** 2
        results.append({
            "index": i,
            "original": num, 
            "squared": processed
        })
        print(f"处理第{i+1}个数字: {num} -> {processed}")
        time.sleep(1)  # 模拟处理时间
    
    # 计算最终结果
    final_result = {
        "message": test_data["message"],
        "processed_count": len(results),
        "results": results,
        "sum_of_squares": sum(r["squared"] for r in results)
    }
    
    print("=== 调试测试完成 ===")
    print(f"最终结果: {final_result}")
    
    return final_result


if __name__ == "__main__":
    # 设置测试环境变量
    os.environ['RAY_JOB_ID'] = 'debug_test_job'
    os.environ['TASK_TYPE'] = 'debug_test'
    os.environ['TASK_PARAMS'] = '{"test": true}'
    
    result = main()
    print("调试测试脚本执行完成!")
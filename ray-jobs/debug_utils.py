"""
Ray Job调试工具
提供简单实用的调试功能
"""
import os
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ray_job_debug')


def is_debug_mode() -> bool:
    """检查是否在调试模式"""
    return os.environ.get('RAY_DEBUG_MODE', 'false').lower() == 'true'


def debug_print(message: str, data: Any = None):
    """调试打印 - 只在调试模式下输出"""
    if is_debug_mode():
        print(f"🐛 DEBUG: {message}")
        if data is not None:
            try:
                print(f"   Data: {json.dumps(data, indent=2, default=str)}")
            except Exception:
                print(f"   Data: {str(data)}")


def log_info(message: str, **kwargs):
    """记录信息日志"""
    extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    log_message = f"{message} | {extra_info}" if extra_info else message
    logger.info(log_message)
    print(f"ℹ️  {log_message}")


def log_error(message: str, error: Exception = None, **kwargs):
    """记录错误日志"""
    extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    log_message = f"❌ {message} | {extra_info}" if extra_info else f"❌ {message}"
    
    if error:
        log_message += f" | Error: {str(error)}"
        logger.error(log_message, exc_info=True)
    else:
        logger.error(log_message)
    
    print(log_message)


def create_checkpoint(name: str, data: Dict, job_id: str = None):
    """创建调试检查点"""
    if not is_debug_mode():
        return
        
    job_id = job_id or os.environ.get('RAY_JOB_ID', 'unknown')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    checkpoint_file = f"/tmp/debug_{job_id}_{name}_{timestamp}.json"
    
    try:
        with open(checkpoint_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        print(f"📋 Checkpoint saved: {checkpoint_file}")
        debug_print(f"Checkpoint '{name}' created", {"file": checkpoint_file, "keys": list(data.keys())})
    except Exception as e:
        log_error(f"Failed to create checkpoint '{name}'", e)


def measure_execution_time(func_name: str = None):
    """装饰器：测量函数执行时间"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            name = func_name or func.__name__
            start_time = datetime.now()
            log_info(f"Starting {name}")
            
            try:
                result = func(*args, **kwargs)
                execution_time = (datetime.now() - start_time).total_seconds()
                log_info(f"Completed {name}", execution_time=f"{execution_time:.2f}s")
                return result
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                log_error(f"Failed {name}", e, execution_time=f"{execution_time:.2f}s")
                raise
        
        return wrapper
    return decorator


def progress_tracker(total: int, description: str = "Processing"):
    """创建进度跟踪器"""
    class ProgressTracker:
        def __init__(self, total: int, description: str):
            self.total = total
            self.description = description
            self.current = 0
            self.start_time = datetime.now()
            
        def update(self, increment: int = 1):
            self.current += increment
            progress = (self.current / self.total) * 100
            elapsed = (datetime.now() - self.start_time).total_seconds()
            
            if self.current % max(1, self.total // 10) == 0:  # 每10%打印一次
                eta = elapsed * (self.total / self.current - 1) if self.current > 0 else 0
                log_info(
                    f"{self.description} progress", 
                    progress=f"{progress:.1f}%",
                    current=self.current,
                    total=self.total,
                    elapsed=f"{elapsed:.1f}s",
                    eta=f"{eta:.1f}s"
                )
            
        def finish(self):
            elapsed = (datetime.now() - self.start_time).total_seconds()
            log_info(f"{self.description} completed", total=self.total, time=f"{elapsed:.1f}s")
    
    return ProgressTracker(total, description)


def validate_data(data: Any, name: str = "data", checks: List[callable] = None) -> bool:
    """验证数据"""
    log_info(f"Validating {name}", type=type(data).__name__)
    
    # 基本检查
    if data is None:
        log_error(f"{name} is None")
        return False
        
    if isinstance(data, (list, dict, str)) and len(data) == 0:
        log_error(f"{name} is empty")
        return False
    
    # 自定义检查
    if checks:
        for i, check_func in enumerate(checks):
            try:
                if not check_func(data):
                    log_error(f"{name} failed validation check {i+1}")
                    return False
            except Exception as e:
                log_error(f"Validation check {i+1} raised exception", e)
                return False
    
    log_info(f"{name} validation passed")
    return True


def get_job_context() -> Dict[str, Any]:
    """获取当前Job上下文信息"""
    return {
        "job_id": os.environ.get('RAY_JOB_ID', 'unknown'),
        "task_type": os.environ.get('RAY_JOB_TYPE', 'unknown'),
        "task_params": os.environ.get('RAY_JOB_CONFIG', '{}'),
        "debug_mode": is_debug_mode(),
        "timestamp": datetime.now().isoformat()
    }


# 使用示例
if __name__ == "__main__":
    # 设置调试模式
    os.environ['RAY_DEBUG_MODE'] = 'true'
    os.environ['RAY_JOB_ID'] = 'test_job_123'
    
    # 测试调试工具
    debug_print("Debug utils test", {"version": "1.0"})
    log_info("Starting test", job_id="test_job_123")
    
    # 测试进度跟踪
    tracker = progress_tracker(100, "Test processing")
    for i in range(0, 101, 10):
        tracker.update(10)
    tracker.finish()
    
    # 测试检查点
    create_checkpoint("test", {"status": "ok", "count": 100})
    
    print("✅ Debug utils test completed")
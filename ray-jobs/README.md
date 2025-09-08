# Ray Jobs 调试指南 - 最佳实践版本

本目录包含独立的Ray Job脚本，采用**本地调试友好**的架构设计。

## 📁 文件结构

```
ray-jobs/
├── README.md                    # 本调试指南
├── debug_utils.py              # 🧰 调试工具库
├── ray_job_decorator.py        # 📊 Ray Job监控装饰器（简化版）
├── simple_job.py              # ✨ 简单计算任务（支持本地调试）
├── data_processing_job.py     # 📈 数据处理任务
├── machine_learning_job.py    # 🤖 机器学习任务
└── debug_test.py              # 🧪 调试功能测试脚本
```

## 🎯 调试最佳实践

### ⭐ **方法1: 本地调试（推荐）**

**核心理念**: 将业务逻辑与Ray Job入口分离，让核心逻辑可以在本地直接调试。

```python
# === 核心业务逻辑 - 可本地调试 ===
@measure_execution_time("computation")
def compute_core_logic(param1: int, param2: int) -> Dict[str, Any]:
    """核心计算逻辑 - 在这里设置断点进行本地调试"""
    log_info("Starting computation", param1=param1, param2=param2)
    
    # 在这里设置断点 🔴
    results = []
    for i in range(param1, param2):
        result = expensive_calculation(i)  # 可以单步调试
        results.append(result)
        debug_print(f"Processed {i}", {"result": result})
    
    return {"results": results, "count": len(results)}

# === Ray Job入口 - 只负责参数解析 ===
@ray_job_monitor(api_base_url="http://backend-debug:8000")
def main():
    context = get_job_context()
    params = json.loads(context["task_params"])
    
    # 调用核心逻辑
    result = compute_core_logic(params["start"], params["end"])
    return result

# === 本地调试支持 ===
def local_debug():
    """本地调试函数 - 可以直接运行和调试"""
    os.environ['RAY_DEBUG_MODE'] = 'true'
    ray.init(ignore_reinit_error=True)
    
    # 直接调用核心逻辑，可以设置断点
    result = compute_core_logic(1, 10)  # 🔴 断点在这里
    print(f"调试结果: {result}")
    
    ray.shutdown()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "debug":
        local_debug()  # python simple_job.py debug
    else:
        main()  # Ray Job模式
```

### ⭐ **方法2: 日志调试（最实用）**

```python
from debug_utils import log_info, log_error, debug_print, progress_tracker

@ray_job_monitor(api_base_url="http://backend-debug:8000")
def main():
    # 详细日志记录
    log_info("Ray Job started", job_id=get_job_context()["job_id"])
    
    data = load_data()
    log_info("Data loaded", count=len(data))
    debug_print("Sample data", data[:3])  # 只在调试模式显示
    
    # 进度跟踪
    tracker = progress_tracker(len(data), "Processing data")
    
    results = []
    for i, item in enumerate(data):
        try:
            result = process_item(item)
            results.append(result)
            tracker.update()
            
            # 每处理100个记录一次日志
            if i % 100 == 0:
                log_info(f"Progress update", processed=i, total=len(data))
                
        except Exception as e:
            log_error(f"Failed to process item {i}", e, item=str(item)[:100])
    
    tracker.finish()
    log_info("Job completed", total_results=len(results))
```

### ⭐ **方法3: Ray Dashboard监控**

访问 http://localhost:8265 查看：
- 实时日志输出
- Job执行状态
- 资源使用情况
- 错误堆栈信息

## 🧰 调试工具库

`debug_utils.py` 提供了强大的调试工具：

### 日志工具
```python
from debug_utils import log_info, log_error, debug_print

log_info("操作开始", param1=value1, param2=value2)  # 结构化日志
debug_print("调试信息", data_dict)  # 只在调试模式显示
log_error("出错了", exception_obj, context="additional info")
```

### 执行时间测量
```python
from debug_utils import measure_execution_time

@measure_execution_time("数据处理")
def process_data():
    # 自动记录执行时间
    pass
```

### 进度跟踪
```python
from debug_utils import progress_tracker

tracker = progress_tracker(1000, "处理数据")
for i in range(1000):
    process_item(i)
    tracker.update()
tracker.finish()
```

### 调试检查点
```python
from debug_utils import create_checkpoint

# 保存调试快照
create_checkpoint("after_preprocessing", {
    "data_count": len(data),
    "sample": data[:5]
})
```

## 🚀 如何开始调试

### 1. 本地调试Ray Job逻辑

```bash
# 进入ray-jobs目录
cd ray-jobs/

# 启用调试模式运行
python simple_job.py debug

# 调试特定功能
python simple_job.py debug prime  # 调试素数计算
python simple_job.py debug sum    # 调试并行求和
```

在VSCode中：
1. 打开 `ray-jobs/simple_job.py`
2. 在 `compute_primes_core` 函数设置断点
3. 按F5选择"Python File"运行
4. 输入参数: `debug prime`

### 2. 通过Ray Job运行调试

```bash
# 提交Ray Job
curl -X POST "http://localhost:8000/api/v1/ray/test/simple?task_type=prime_count" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 查看日志
docker logs -f webapp-starter-ray-head-1
```

### 3. 启用详细调试模式

设置环境变量：
```bash
# 在Ray Job提交时添加调试环境变量
export RAY_DEBUG_MODE=true
```

或在代码中：
```python
os.environ['RAY_DEBUG_MODE'] = 'true'  # 启用详细调试输出
```

## 💡 调试技巧

### 1. 单元测试驱动
```bash
# 为Ray Job逻辑编写单元测试
pytest test_simple_job.py -v

# 测试特定函数
pytest test_simple_job.py::test_compute_primes_core -v -s
```

### 2. 数据验证
```python
from debug_utils import validate_data

# 验证输入数据
if not validate_data(input_data, "input_data", [
    lambda x: len(x) > 0,
    lambda x: all(isinstance(i, int) for i in x)
]):
    return {"error": "Invalid input data"}
```

### 3. 分阶段调试
```python
# 将复杂任务分解为小步骤
def process_data_pipeline(data):
    # 步骤1: 预处理
    preprocessed = preprocess_data(data)
    create_checkpoint("after_preprocess", {"count": len(preprocessed)})
    
    # 步骤2: 核心处理
    processed = core_processing(preprocessed)
    create_checkpoint("after_process", {"count": len(processed)})
    
    # 步骤3: 后处理
    result = postprocess_data(processed)
    return result
```

## ⚡ 性能调试

### 内存使用监控
```python
import psutil
import os

def log_memory_usage(stage: str):
    process = psutil.Process(os.getpid())
    memory_mb = process.memory_info().rss / 1024 / 1024
    log_info(f"Memory usage at {stage}", memory_mb=f"{memory_mb:.1f}")
```

### 执行时间分析
```python
import cProfile
import pstats

def profile_function(func, *args, **kwargs):
    profiler = cProfile.Profile()
    profiler.enable()
    result = func(*args, **kwargs)
    profiler.disable()
    
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(10)  # 显示前10个最耗时的函数
    
    return result
```

## 🔍 常见问题解决

### Ray初始化问题
```python
# 安全的Ray初始化
try:
    if not ray.is_initialized():
        ray.init(ignore_reinit_error=True)
except Exception as e:
    log_error("Ray initialization failed", e)
    # 降级到非Ray模式
```

### 内存不足
```python
# 批处理大数据集
def process_large_dataset(data, batch_size=1000):
    for i in range(0, len(data), batch_size):
        batch = data[i:i+batch_size]
        result = process_batch(batch)
        yield result
```

### 调试信息过多
```python
# 条件调试输出
if os.environ.get('RAY_VERBOSE_DEBUG') == 'true':
    debug_print("详细调试信息", large_data_structure)
else:
    log_info("简化信息", count=len(large_data_structure))
```

---

## 🎉 总结

这种**分层调试架构**的优势：

1. ✅ **本地调试**: 核心逻辑可以在本地VSCode中断点调试
2. ✅ **快速迭代**: 不需要每次都提交Ray Job
3. ✅ **详细日志**: 结构化日志便于问题定位
4. ✅ **性能监控**: 内置执行时间和进度跟踪
5. ✅ **生产就绪**: 可以轻松关闭调试模式

**推荐调试流程**:
1. 先在本地调试核心逻辑 (`python script.py debug`)
2. 确保逻辑正确后再提交Ray Job测试
3. 使用Ray Dashboard监控执行状态
4. 通过日志分析性能和错误

这样既保持了开发效率，又确保了代码质量！
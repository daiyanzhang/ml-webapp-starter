# Ray Jobs 示例

这个目录包含了用于测试Ray分布式计算的示例作业。现在已改造为用户代码仓库格式，支持子目录结构。

## 目录结构

```
ray-jobs/
├── examples/
│   ├── simple/                    # 简单计算示例
│   │   ├── main.py               # 入口点: examples/simple/main.py
│   │   └── requirements.txt
│   ├── data-processing/          # 数据处理示例  
│   │   ├── main.py               # 入口点: examples/data-processing/main.py
│   │   └── requirements.txt
│   └── machine-learning/         # 机器学习示例
│       ├── main.py               # 入口点: examples/machine-learning/main.py
│       └── requirements.txt
├── debug_utils.py                # 调试工具
├── ray_job_decorator.py          # 装饰器工具
├── debug_test.py                 # 调试功能测试脚本  
└── README.md
```

## 使用方法

在前端提交Ray作业时，可以指定子目录路径作为入口点：

- `examples/simple/main.py` - 简单计算任务
- `examples/data-processing/main.py` - 数据处理任务  
- `examples/machine-learning/main.py` - 机器学习任务

## 示例仓库格式

每个子目录都是一个独立的项目，包含：

- `main.py` - 主入口文件
- `requirements.txt` - Python依赖列表
- 其他支持文件（可选）

这种结构模拟了真实的GitHub仓库，便于测试Ray作业的GitHub集成功能。

## 调试工具

- `debug_utils.py` - 提供日志记录、进度跟踪、执行时间测量等调试工具
- `ray_job_decorator.py` - Ray Job监控装饰器
- `debug_test.py` - 调试功能测试脚本

## 本地调试

每个示例都支持本地调试模式：

```bash
cd ray-jobs/examples/simple
python main.py debug
```

在Ray Job模式下运行：

```bash
python main.py
```
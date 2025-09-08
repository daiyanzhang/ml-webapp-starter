#!/usr/bin/env python3
"""
VSCode调试器专用的FastAPI服务启动脚本
"""
import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 设置环境变量
os.environ.setdefault("POSTGRES_SERVER", "postgres")
os.environ.setdefault("POSTGRES_PORT", "5432")
os.environ.setdefault("POSTGRES_USER", "postgres")
os.environ.setdefault("POSTGRES_PASSWORD", "postgres")
os.environ.setdefault("POSTGRES_DB", "webapp_starter")

if __name__ == "__main__":
    import uvicorn
    
    # 导入FastAPI应用
    from app.main import app
    
    # 启动服务器，支持调试
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # debugpy模式下禁用reload
        log_level="info"
    )
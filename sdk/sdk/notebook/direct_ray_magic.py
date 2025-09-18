#!/usr/bin/env python3
"""
Direct Ray Magic - 直接连接Ray集群的魔法命令
"""

import uuid
import time
import base64
from typing import Dict, Any
from IPython.core.magic import Magics, magics_class, cell_magic, line_magic
from IPython.display import display, Image
from ray.job_submission import JobSubmissionClient

@magics_class
class DirectRayMagic(Magics):
    """直接连接Ray集群的魔法命令类"""
    
    def __init__(self, shell=None):
        super(DirectRayMagic, self).__init__(shell)
        # Ray集群地址 - 在Docker环境中使用ray-head服务名
        import os
        ray_head_host = os.getenv('RAY_HEAD_HOST', 'ray-head')
        ray_head_port = os.getenv('RAY_HEAD_PORT', '8265')
        self.ray_head_url = f"http://{ray_head_host}:{ray_head_port}"
        
    @line_magic
    def ray_status(self, line):
        """检查Ray集群状态"""
        try:
            client = JobSubmissionClient(self.ray_head_url)
            jobs = client.list_jobs()
            
            print(f"🟢 Ray Cluster Status: Available")
            print(f"📊 Dashboard: {self.ray_head_url}")
            print(f"📋 Active Jobs: {len(jobs)}")
            
        except Exception as e:
            print(f"❌ Ray Cluster Status: Unavailable")
            print(f"🔗 Trying to connect to: {self.ray_head_url}")
            print(f"❌ Error: {e}")
    
    @line_magic 
    def ray_jobs(self, line):
        """列出Ray作业"""
        try:
            client = JobSubmissionClient(self.ray_head_url)
            jobs = client.list_jobs()
            
            if not jobs:
                print("📝 No Ray jobs found.")
                return
            
            print(f"📋 Ray Jobs ({len(jobs)} total):")
            for job_id in jobs:
                try:
                    info = client.get_job_info(job_id)
                    print(f"  • {job_id}: {info.status.value}")
                except:
                    print(f"  • {job_id}: status unknown")
                    
        except Exception as e:
            print(f"❌ Error getting Ray jobs: {e}")
    
    @cell_magic
    def ray_exec(self, line, cell):
        """在Ray集群上执行cell代码 - 直接连接版本"""
        
        # 解析参数 - 使用时间戳确保唯一性
        import time
        timestamp = int(time.time())
        name = f"cell-{timestamp}-{uuid.uuid4().hex[:6]}"
        timeout = 60
        is_async = False
        
        if line:
            parts = line.split()
            for i, part in enumerate(parts):
                if part == "--name" and i + 1 < len(parts):
                    name = f"{parts[i + 1]}_{timestamp}"
                elif part == "--timeout" and i + 1 < len(parts):
                    timeout = int(parts[i + 1])
                elif part == "--async":
                    is_async = True
        
        try:
            client = JobSubmissionClient(self.ray_head_url)
            
            # 准备Ray job配置 - 使用当前notebooks目录作为working_dir
            runtime_env = {
                "working_dir": "./",  # 当前目录（比如notebooks/users/user_1）
                "pip": "./requirements.txt"  # 指向requirements.txt文件路径
            }
            
            # 设置环境变量 - 直接传递代码
            env_vars = {
                "CELL_CODE": cell,
                "NOTEBOOK_PATH": name
            }
            
            runtime_env["env_vars"] = env_vars
            
            print(f"🚀 Submitting job '{name}' to Ray cluster...")
            print(f"📍 Working dir: ./notebooks (auto-install requirements.txt)")
            
            # 提交Ray job - 使用模块导入方式执行
            job_id = client.submit_job(
                entrypoint="python -m sdk.notebook.cell_executor",
                runtime_env=runtime_env,
                submission_id=name,
                metadata={"notebook_path": name, "code_preview": cell[:100]}
            )
            
            print(f"✅ Job submitted! Job ID: {job_id}")
            
            if is_async:
                print("🔄 Job is running asynchronously.")
                print(f"💡 Use '%ray_result {job_id}' to check results.")
                return job_id
            
            # 同步等待结果
            print("⏳ Waiting for execution...")
            result = self._wait_for_result(client, job_id, timeout)
            
            if result:
                self._display_result(result)
                return result
            else:
                print(f"⚠️ Job timed out. Use '%ray_result {job_id}' to check status.")
                return job_id
                
        except Exception as e:
            print(f"❌ Error executing on Ray: {e}")
            return None
    
    @line_magic
    def ray_result(self, line):
        """获取Ray作业结果"""
        job_id = line.strip()
        if not job_id:
            print("💡 Usage: %ray_result <job_id>")
            return
            
        try:
            client = JobSubmissionClient(self.ray_head_url)
            info = client.get_job_info(job_id)
            logs = client.get_job_logs(job_id)
            
            result = {
                "job_id": job_id,
                "status": info.status.value,
                "start_time": info.start_time,
                "end_time": info.end_time,
                "metadata": info.metadata,
                "logs": logs
            }
            
            self._display_result(result)
            return result
            
        except Exception as e:
            print(f"❌ Error getting result: {e}")
    
    def _wait_for_result(self, client: JobSubmissionClient, job_id: str, timeout: int = 60) -> Dict[str, Any]:
        """等待作业完成并返回结果"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                info = client.get_job_info(job_id)
                status = info.status.value.lower()
                
                if status in ['succeeded', 'completed', 'finished']:
                    logs = client.get_job_logs(job_id)
                    return {
                        "job_id": job_id,
                        "status": status,
                        "start_time": info.start_time,
                        "end_time": info.end_time,
                        "metadata": info.metadata,
                        "logs": logs
                    }
                elif status in ['failed', 'stopped', 'cancelled']:
                    logs = client.get_job_logs(job_id)
                    print(f"❌ Job {status}")
                    return {
                        "job_id": job_id,
                        "status": status,
                        "logs": logs
                    }
                else:
                    print(".", end="", flush=True)
                    time.sleep(2)
                    
            except Exception:
                time.sleep(2)
        
        return None
    
    def _display_result(self, result: Dict[str, Any]):
        """显示执行结果"""
        status = result.get('status', 'unknown')
        
        # 显示状态
        if status.lower() in ['succeeded', 'completed', 'finished']:
            print("\n✅ Execution completed successfully!")
        elif status.lower() in ['failed', 'stopped']:
            print("\n❌ Execution failed!")
        else:
            print(f"\nℹ️ Job status: {status}")
        
        # 从日志中提取用户代码的实际输出
        logs = result.get('logs', '')
        if logs:
            # 解析日志，找到用户代码的输出
            user_output = self._extract_user_output_from_logs(logs)
            
            if user_output:
                print("\n🎯 Your Code Output:")
                print("-" * 40)
                print(user_output)
                print("-" * 40)
            else:
                # 如果没有找到用户输出，显示完整日志（调试用）
                print("\n📄 Ray Job Logs:")
                print("-" * 50)
                print(logs)
                print("-" * 50)
        
        # 检查是否有任何运行时信息
        metadata = result.get('metadata', {})
        if metadata:
            code_preview = metadata.get('code_preview', '')
            if code_preview:
                print(f"\n💡 Code executed: {code_preview}")
    
    def _extract_user_output_from_logs(self, logs: str) -> str:
        """从Ray作业日志中提取用户代码的实际输出"""
        lines = logs.split('\n')
        output_lines = []
        capturing = False
        
        for line in lines:
            # 开始捕获用户输出
            if '=== USER OUTPUT ===' in line:
                capturing = True
                continue
            
            # 停止捕获用户输出    
            if '=== END OUTPUT ===' in line:
                capturing = False
                continue
                
            # 捕获期间，收集所有行
            if capturing:
                output_lines.append(line)
        
        return '\n'.join(output_lines) if output_lines else ""


def load_direct_ray_magic():
    """加载直接连接Ray的魔法命令"""
    from IPython import get_ipython
    ip = get_ipython()
    if ip:
        magic_instance = DirectRayMagic(ip)
        ip.register_magic_function(magic_instance.ray_status, 'line', 'ray_status')
        ip.register_magic_function(magic_instance.ray_jobs, 'line', 'ray_jobs') 
        ip.register_magic_function(magic_instance.ray_exec, 'cell', 'ray_exec')
        ip.register_magic_function(magic_instance.ray_result, 'line', 'ray_result')
        
        print("✅ Direct Ray magic commands loaded!")
        print("🔗 Connecting directly to Ray cluster (no backend API needed)")
        print("\nAvailable commands:")
        print("  %ray_status           - Check Ray cluster status")
        print("  %ray_jobs             - List Ray jobs")  
        print("  %%ray_exec [options]  - Execute cell on Ray cluster")
        print("  %ray_result <job_id>  - Get Ray job result")
        print("\n💡 Options for %%ray_exec:")
        print("  --name <name>    : Job name")
        print("  --timeout <sec>  : Timeout in seconds") 
        print("  --async          : Run asynchronously")
        print("\n🔧 Features:")
        print("  • Auto-install requirements.txt from notebooks/")
        print("  • Direct Ray cluster connection") 
        print("  • Full output capture including plots")
    else:
        print("❌ IPython not available")

if __name__ == "__main__":
    load_direct_ray_magic()
#!/usr/bin/env python3
"""
Ray Cell Executor - 在Ray集群上执行单个notebook cell
"""
import os
import sys
import json
import pickle
import base64
import tempfile
import traceback
import logging
from io import StringIO, BytesIO
import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
from utils.ray_job_decorator import ray_job_monitor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def log_info(message):
    """统一的日志输出函数"""
    logging.info(f"[CELL-EXECUTOR] {message}")

class OutputCapture:
    """捕获代码执行的输出和图像"""
    
    def __init__(self):
        self.stdout = StringIO()
        self.stderr = StringIO()
        self.images = []
        self.variables = {}
        
    def start_capture(self):
        """开始捕获输出"""
        self.old_stdout = sys.stdout
        self.old_stderr = sys.stderr
        sys.stdout = self.stdout
        sys.stderr = self.stderr
        
        # 设置matplotlib保存图像
        plt.ioff()  # 关闭交互模式
        
    def stop_capture(self):
        """停止捕获输出"""
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr
        
        # 捕获所有matplotlib图像
        figures = plt.get_fignums()
        for fig_num in figures:
            fig = plt.figure(fig_num)
            if fig.get_axes():  # 只有当图像有内容时才保存
                buffer = BytesIO()
                fig.savefig(buffer, format='png', bbox_inches='tight', dpi=100)
                buffer.seek(0)
                img_data = base64.b64encode(buffer.read()).decode()
                self.images.append({
                    'figure_num': fig_num,
                    'data': img_data,
                    'format': 'png'
                })
            plt.close(fig)
        
    def get_output(self):
        """获取捕获的输出"""
        return {
            'stdout': self.stdout.getvalue(),
            'stderr': self.stderr.getvalue(),
            'images': self.images,
            'variables': self.variables
        }

@ray_job_monitor(api_base_url="http://backend:8000")
def main():
    """主执行函数"""
    # 从环境变量获取参数
    cell_code = os.environ.get("CELL_CODE", "")
    notebook_path = os.environ.get("NOTEBOOK_PATH", "temp_cell")
    
    if not cell_code:
        log_info("ERROR: CELL_CODE environment variable is required")
        sys.exit(1)
    
    log_info(f"Starting cell execution for: {notebook_path}")
    log_info(f"Code preview: {cell_code[:100]}...")
    
    try:
        # 初始化输出捕获器
        output_capture = OutputCapture()
        
        # 准备执行环境
        exec_globals = {
            '__name__': '__main__',
            '__file__': f'<ray-cell-{notebook_path}>',
        }
        
        # 导入常用库到执行环境
        common_imports = """
        """
        
        log_info("Setting up execution environment...")
        exec(common_imports, exec_globals)
        
        # 初始化Ray（如果代码需要）
        if 'ray.' in cell_code or '@ray.remote' in cell_code:
            log_info("Initializing Ray for distributed computing...")
            import ray
            if not ray.is_initialized():
                try:
                    ray.init(address='auto', ignore_reinit_error=True)
                    log_info("Connected to Ray cluster")
                except:
                    ray.init(ignore_reinit_error=True)
                    log_info("Started local Ray instance")
        
        # 开始捕获输出
        output_capture.start_capture()
        
        log_info("Executing cell code...")
        execution_result = None
        
        try:
            # 执行用户代码
            exec_result = exec(cell_code, exec_globals)
            
            # 捕获最后的表达式结果（如果有）
            if cell_code.strip().split('\n')[-1].strip() and not cell_code.strip().endswith(':'):
                last_line = cell_code.strip().split('\n')[-1].strip()
                if not any(last_line.startswith(kw) for kw in ['print', 'plt.', 'import', 'from', 'def', 'class', 'if', 'for', 'while', 'try', 'with']):
                    try:
                        execution_result = eval(last_line, exec_globals)
                        if execution_result is not None:
                            print(repr(execution_result))
                    except:
                        pass
                        
        except Exception as e:
            log_info(f"Execution error: {str(e)}")
            print(f"Error: {str(e)}", file=sys.stderr)
            traceback.print_exc()
        
        finally:
            # 停止捕获输出
            output_capture.stop_capture()
        
        # 获取输出结果
        output = output_capture.get_output()
        
        log_info(f"Execution completed. Output length: {len(output['stdout'])}, Images: {len(output['images'])}")
        
        # 构建结果
        result = {
            'status': 'success',
            'cell_code': cell_code,
            'notebook_path': notebook_path,
            'output': output,
            'execution_result': str(execution_result) if execution_result is not None else None,
            'has_images': len(output['images']) > 0,
            'execution_time': 'completed'
        }
        
        # 如果有stderr输出，标记为warning
        if output['stderr'].strip():
            result['status'] = 'warning'
            result['warning'] = 'Execution completed with warnings'
        
        log_info(f"Cell execution result: {result['status']}")
        
        # 输出用户代码的结果到stdout（这样会出现在Ray日志中）
        if output['stdout']:
            print("\n=== USER OUTPUT ===")
            print(output['stdout'])
            print("=== END OUTPUT ===")
        
        if output['stderr']:
            print("\n=== USER ERRORS ===", file=sys.stderr)
            print(output['stderr'], file=sys.stderr)
            print("=== END ERRORS ===", file=sys.stderr)
        
        # 关闭Ray（如果使用了）
        import ray
        if ray.is_initialized():
            ray.shutdown()
            log_info("Ray shutdown completed")
            
        return result
        
    except Exception as e:
        error_msg = f"Cell execution failed: {str(e)}"
        log_info(f"ERROR: {error_msg}")
        traceback.print_exc()
        
        return {
            'status': 'error',
            'cell_code': cell_code,
            'notebook_path': notebook_path,
            'error_message': error_msg,
            'traceback': traceback.format_exc(),
            'output': {'stdout': '', 'stderr': str(e), 'images': [], 'variables': {}}
        }

if __name__ == "__main__":
    try:
        result = main()
        log_info(f"Ray cell execution completed with status: {result['status']}")
    except Exception as e:
        log_info(f"Ray cell execution failed: {e}")
        sys.exit(1)
#!/usr/bin/env python3
"""
Ray Notebook Executor - 在Ray集群上执行Jupyter Notebook
"""
import os
import sys
import tempfile
import json
import requests
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor
from ray_job_decorator import ray_job_monitor
import ast
import re


def log_info(message):
    """统一的日志输出函数"""
    print(f"[NOTEBOOK-EXECUTOR] {message}")


@ray_job_monitor(api_base_url="http://backend:8000")
def main():
    """主执行函数"""
    # 从环境变量获取参数
    notebook_path = os.environ.get("NOTEBOOK_PATH", "")
    jupyter_base_url = os.environ.get("JUPYTER_BASE_URL", "http://jupyter:8888")
    jupyter_token = os.environ.get("JUPYTER_TOKEN", "webapp-starter-token")
    
    if not notebook_path:
        log_info("ERROR: NOTEBOOK_PATH environment variable is required")
        sys.exit(1)
    
    log_info(f"Starting notebook execution: {notebook_path}")
    log_info(f"Jupyter URL: {jupyter_base_url}")
    
    try:
        # 1. 从Jupyter服务器下载notebook
        log_info("Downloading notebook from Jupyter server...")
        headers = {'Authorization': f'token {jupyter_token}'}
        response = requests.get(
            f'{jupyter_base_url}/api/contents/{notebook_path}', 
            headers=headers,
            timeout=30
        )
        response.raise_for_status()
        
        notebook_content = response.json()
        log_info(f"Downloaded notebook: {notebook_content['name']}")
        
        # 2. 创建临时文件保存notebook
        with tempfile.NamedTemporaryFile(mode='w', suffix='.ipynb', delete=False) as f:
            nbformat.write(nbformat.from_dict(notebook_content['content']), f)
            temp_path = f.name
        
        log_info(f"Created temporary notebook file: {temp_path}")
        
        try:
            # 3. 读取并执行notebook
            log_info("Reading notebook for execution...")
            with open(temp_path, 'r') as f:
                nb = nbformat.read(f, as_version=4)
            
            log_info(f"Notebook has {len(nb.cells)} cells")
            
            # 4. 预处理notebook，检查是否有pip install命令
            pip_install_commands = []
            for i, cell in enumerate(nb.cells):
                if cell.cell_type == 'code':
                    source = ''.join(cell.source)
                    if '!pip install' in source or 'pip.main(' in source:
                        pip_install_commands.append(f"Cell {i+1}: {source.strip()[:50]}...")
            
            if pip_install_commands:
                log_info(f"Detected {len(pip_install_commands)} pip install commands:")
                for cmd in pip_install_commands:
                    log_info(f"  - {cmd}")
            
            # 5. 配置执行器
            ep = ExecutePreprocessor(
                timeout=900,  # 15分钟超时（给pip install更多时间）
                kernel_name='python3',
                allow_errors=True,  # 允许错误，继续执行其他单元格
                startup_timeout=60,  # kernel启动超时
                interrupt_on_timeout=True,
                # 启用shell命令支持
                store_widget_state=False,
                record_timing=True
            )
            
            log_info("Starting notebook execution on Ray cluster...")
            
            # 5. 执行notebook
            try:
                log_info("Executing notebook cells...")
                ep.preprocess(nb, {'metadata': {'path': os.path.dirname(temp_path)}})
                log_info("Notebook execution completed successfully")
                
                # 6. 统计执行结果
                executed_cells = 0
                cells_with_output = 0
                cells_with_errors = 0
                
                for i, cell in enumerate(nb.cells):
                    if cell.cell_type == 'code':
                        executed_cells += 1
                        if cell.get('outputs'):
                            cells_with_output += 1
                        # 检查是否有错误输出
                        for output in cell.get('outputs', []):
                            if output.get('output_type') == 'error':
                                cells_with_errors += 1
                                log_info(f"Cell {i+1} error: {output.get('ename', 'Unknown')}: {output.get('evalue', '')}")
                                break
                
                log_info(f"Executed {executed_cells} code cells, {cells_with_output} cells have output, {cells_with_errors} cells have errors")
                
            except Exception as exec_error:
                log_info(f"Notebook execution failed: {exec_error}")
                # 即使执行失败，也尝试上传部分结果
                pass
            
            # 7. 上传执行结果回Jupyter
            log_info("Uploading executed notebook back to Jupyter...")
            executed_content = {
                'type': 'notebook',
                'content': nb
            }
            
            put_response = requests.put(
                f'{jupyter_base_url}/api/contents/{notebook_path}', 
                headers=headers,
                json=executed_content,
                timeout=30
            )
            put_response.raise_for_status()
            
            log_info("Successfully uploaded executed notebook")
            
            # 8. 返回执行结果
            result = {
                'status': 'success',
                'notebook_path': notebook_path,
                'total_cells': len(nb.cells),
                'executed_cells': executed_cells,
                'cells_with_output': cells_with_output,
                'execution_time': 'completed'
            }
            
            log_info(f"Execution result: {json.dumps(result, indent=2)}")
            return result
            
        finally:
            # 9. 清理临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                log_info("Cleaned up temporary files")
    
    except requests.RequestException as e:
        error_msg = f"HTTP request failed: {str(e)}"
        log_info(f"ERROR: {error_msg}")
        raise Exception(error_msg)
    
    except nbformat.ValidationError as e:
        error_msg = f"Notebook format validation failed: {str(e)}"
        log_info(f"ERROR: {error_msg}")
        raise Exception(error_msg)
    
    except Exception as e:
        error_msg = f"Notebook execution failed: {str(e)}"
        log_info(f"ERROR: {error_msg}")
        raise Exception(error_msg)


if __name__ == "__main__":
    try:
        result = main()
        log_info("Ray notebook execution completed successfully")
    except Exception as e:
        log_info(f"Ray notebook execution failed: {e}")
        sys.exit(1)
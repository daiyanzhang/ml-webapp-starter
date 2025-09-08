"""
Temporal服务 - 工作流管理
"""
import uuid
from typing import Any, Dict, List
from datetime import datetime
from temporalio.client import Client
from temporalio.common import WorkflowIDReusePolicy
from temporalio.service import WorkflowService

from app.core.temporal_config import get_temporal_client, get_task_queue
from app.core.config import settings
from app.workflows.example_workflow import ExampleWorkflow


class TemporalService:
    """Temporal工作流服务"""
    
    def __init__(self):
        self.client: Client = None
    
    async def _ensure_client(self):
        """确保客户端连接"""
        if not self.client:
            self.client = await get_temporal_client()
    
    async def start_example_workflow(
        self, 
        user_id: int, 
        action: str,
        workflow_id: str = None
    ) -> str:
        """
        启动示例工作流
        
        Args:
            user_id: 用户ID
            action: 操作类型
            workflow_id: 可选的工作流ID
            
        Returns:
            工作流ID
        """
        await self._ensure_client()
        
        if not workflow_id:
            # 使用时间戳和UUID确保唯一性
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            unique_id = str(uuid.uuid4())[:8]
            workflow_id = f"workflow-{user_id}-{action}-{timestamp}-{unique_id}"
        
        handle = await self.client.start_workflow(
            ExampleWorkflow.run,
            args=[user_id, action],
            id=workflow_id,
            task_queue=get_task_queue(),
            id_reuse_policy=WorkflowIDReusePolicy.REJECT_DUPLICATE,
        )
        
        return handle.id
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """
        获取工作流状态（旧版本，保持兼容性）
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            工作流状态信息
        """
        await self._ensure_client()
        
        handle = self.client.get_workflow_handle(workflow_id)
        
        try:
            # 尝试获取结果（非阻塞）
            result = await handle.result()
            return {
                "status": "completed",
                "result": result,
                "workflow_id": workflow_id
            }
        except Exception as e:
            # 工作流可能还在运行
            return {
                "status": "running",
                "error": None,
                "workflow_id": workflow_id
            }
    
    async def get_workflow_details(self, workflow_id: str) -> Dict[str, Any]:
        """
        获取工作流详细信息
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            工作流详细信息
        """
        await self._ensure_client()
        
        handle = self.client.get_workflow_handle(workflow_id)
        
        # 获取Temporal UI链接
        temporal_ui_url = f"http://localhost:8080/namespaces/default/workflows/{workflow_id}"
        
        try:
            # 获取描述信息
            description = await handle.describe()
            start_time = description.start_time.isoformat() if description.start_time else None
            end_time = description.close_time.isoformat() if description.close_time else None
            
            # 尝试获取结果
            try:
                result = await handle.result()
                return {
                    "workflow_id": workflow_id,
                    "status": "completed",
                    "start_time": start_time,
                    "end_time": end_time,
                    "result": result,
                    "error": None,
                    "temporal_ui_url": temporal_ui_url
                }
            except Exception:
                # 工作流还在运行或者失败了
                status = description.status.name.lower() if description.status else "unknown"
                return {
                    "workflow_id": workflow_id,
                    "status": status,
                    "start_time": start_time,
                    "end_time": end_time,
                    "result": None,
                    "error": None,
                    "temporal_ui_url": temporal_ui_url
                }
                
        except Exception as e:
            return {
                "workflow_id": workflow_id,
                "status": "error",
                "start_time": None,
                "end_time": None,
                "result": None,
                "error": str(e),
                "temporal_ui_url": temporal_ui_url
            }
    
    async def list_workflows(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        获取工作流列表
        
        Args:
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            工作流列表
        """
        await self._ensure_client()
        
        try:
            workflows = []
            count = 0
            max_count = limit + offset + 20  # 获取更多用于分页
            
            print(f"Querying workflows with limit={limit}, offset={offset}")
            
            # 直接使用Temporal的list API查询所有工作流
            async for workflow in self.client.list_workflows():
                if count >= max_count:
                    break
                    
                print(f"Found workflow: {workflow.id}")
                
                temporal_ui_url = f"http://localhost:8080/namespaces/default/workflows/{workflow.id}"
                
                # 获取基本信息
                status = "running"
                if workflow.status and hasattr(workflow.status, 'name'):
                    status = workflow.status.name.lower()
                
                workflow_info = {
                    "workflow_id": workflow.id,
                    "status": status,
                    "start_time": workflow.start_time.isoformat() if workflow.start_time else None,
                    "end_time": workflow.close_time.isoformat() if workflow.close_time else None,
                    "result": None,  # 简化处理，不获取详细结果
                    "error": None,
                    "temporal_ui_url": temporal_ui_url
                }
                
                workflows.append(workflow_info)
                count += 1
            
            print(f"Found {len(workflows)} workflows total")
            
            # 按开始时间倒序排序（最新的在前面）
            workflows.sort(key=lambda x: x["start_time"] or "", reverse=True)
            
            # 应用分页
            return workflows[offset:offset + limit]
            
        except Exception as e:
            print(f"List workflows error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """
        取消工作流
        
        Args:
            workflow_id: 工作流ID
            
        Returns:
            是否成功取消
        """
        await self._ensure_client()
        
        try:
            handle = self.client.get_workflow_handle(workflow_id)
            await handle.cancel()
            return True
        except Exception:
            return False


# 单例服务实例
temporal_service = TemporalService()
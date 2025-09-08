"""
工作流相关API端点
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel

from app.core.deps import get_current_user
from app.db.models import User as UserModel
from app.services.temporal_service import temporal_service

router = APIRouter()


class WorkflowStartRequest(BaseModel):
    """启动工作流请求"""
    action: str
    workflow_id: str = None


class WorkflowResponse(BaseModel):
    """工作流响应"""
    workflow_id: str
    status: str
    message: str = None


class WorkflowDetailResponse(BaseModel):
    """工作流详细信息响应"""
    workflow_id: str
    status: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    temporal_ui_url: str


@router.post("/start", response_model=WorkflowResponse)
async def start_workflow(
    request: WorkflowStartRequest,
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """启动示例工作流"""
    
    try:
        workflow_id = await temporal_service.start_example_workflow(
            user_id=current_user.id,
            action=request.action,
            workflow_id=request.workflow_id
        )
        
        return WorkflowResponse(
            workflow_id=workflow_id,
            status="started",
            message=f"工作流已启动: {workflow_id}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"启动工作流失败: {str(e)}"
        )


@router.get("/list", response_model=List[WorkflowDetailResponse])
async def list_workflows(
    limit: int = Query(default=10, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """获取工作流列表"""
    
    try:
        workflows = await temporal_service.list_workflows(limit=limit, offset=offset)
        return workflows
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取工作流列表失败: {str(e)}"
        )


@router.get("/{workflow_id}/status", response_model=WorkflowDetailResponse)
async def get_workflow_status(
    workflow_id: str,
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """获取工作流状态"""
    
    try:
        status = await temporal_service.get_workflow_details(workflow_id)
        return status
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取工作流状态失败: {str(e)}"
        )


@router.post("/{workflow_id}/cancel")
async def cancel_workflow(
    workflow_id: str,
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """取消工作流"""
    
    try:
        success = await temporal_service.cancel_workflow(workflow_id)
        
        if success:
            return {"message": f"工作流 {workflow_id} 已取消"}
        else:
            raise HTTPException(
                status_code=404,
                detail=f"工作流 {workflow_id} 不存在或无法取消"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"取消工作流失败: {str(e)}"
        )
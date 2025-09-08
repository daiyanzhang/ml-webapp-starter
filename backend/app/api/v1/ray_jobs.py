"""
Ray分布式计算API端点
"""
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.core.deps import get_current_user
from app.db.models import User as UserModel
from app.services.ray_service import ray_service

router = APIRouter()


class RayJobRequest(BaseModel):
    """Ray任务请求"""
    job_type: str = Field(..., description="任务类型")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="任务参数")


class RayJobResponse(BaseModel):
    """Ray任务响应"""
    job_id: str
    status: str
    result: Dict[str, Any] = None
    error: str = None
    submitted_at: str


class RayClusterStatus(BaseModel):
    """Ray集群状态响应"""
    status: str
    cluster_resources: Dict[str, Any] = None
    nodes: int = None
    nodes_info: List[Dict[str, Any]] = None
    ray_version: str = None
    error: str = None
    connected_at: str = None
    checked_at: str = None


class AvailableJob(BaseModel):
    """可用任务类型"""
    job_type: str
    name: str
    description: str
    parameters: Dict[str, Any]


class RayJobHistory(BaseModel):
    """Ray任务历史记录"""
    id: int
    job_id: str
    job_type: str
    status: str
    user_id: Optional[int]
    parameters: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    execution_time: Optional[float]
    created_at: Optional[str]
    completed_at: Optional[str]


class JobStatusUpdate(BaseModel):
    """任务状态更新请求"""
    job_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    traceback: Optional[str] = None
    execution_time: Optional[float] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None


@router.get("/cluster/status", response_model=RayClusterStatus)
async def get_cluster_status(
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """获取Ray集群状态"""
    
    try:
        status = await ray_service.get_cluster_status()
        return status
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取集群状态失败: {str(e)}"
        )


@router.get("/available", response_model=List[AvailableJob])
async def get_available_jobs(
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """获取可用的任务类型"""
    
    try:
        jobs = await ray_service.get_available_jobs()
        return jobs
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取可用任务失败: {str(e)}"
        )


@router.post("/submit", response_model=RayJobResponse)
async def submit_ray_job(
    request: RayJobRequest,
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """提交Ray任务"""
    
    # 验证任务类型
    available_jobs = await ray_service.get_available_jobs()
    valid_job_types = [job["job_type"] for job in available_jobs]
    
    if request.job_type not in valid_job_types:
        raise HTTPException(
            status_code=400,
            detail=f"无效的任务类型: {request.job_type}. 可用类型: {valid_job_types}"
        )
    
    try:
        result = await ray_service.submit_job(
            job_type=request.job_type,
            parameters=request.parameters,
            user_id=current_user.id
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"提交任务失败: {str(e)}"
        )


@router.post("/test/simple")
async def test_simple_job(
    task_type: str = "prime_count",
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """测试简单Ray任务"""
    
    test_params = {
        "prime_count": {
            "task_type": "prime_count",
            "params": {"start": 1, "end": 500, "chunk_size": 50}
        },
        "parallel_sum": {
            "task_type": "parallel_sum", 
            "params": {"array_size": 5000, "chunk_size": 500}
        },
        "fibonacci": {
            "task_type": "fibonacci",
            "params": {"n": 15}
        }
    }
    
    if task_type not in test_params:
        raise HTTPException(
            status_code=400,
            detail=f"无效的测试类型: {task_type}. 可用类型: {list(test_params.keys())}"
        )
    
    try:
        result = await ray_service.submit_job(
            job_type="simple_job",
            parameters=test_params[task_type],
            user_id=current_user.id
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"测试任务失败: {str(e)}"
        )


@router.post("/test/data-processing")
async def test_data_processing_job(
    data_size: int = 5000,
    batch_size: int = 500,
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """测试数据处理任务"""
    
    if data_size < 100 or data_size > 50000:
        raise HTTPException(
            status_code=400,
            detail="data_size必须在100到50000之间"
        )
    
    if batch_size < 10 or batch_size > 5000:
        raise HTTPException(
            status_code=400,
            detail="batch_size必须在10到5000之间"
        )
    
    try:
        result = await ray_service.submit_job(
            job_type="data_processing",
            parameters={
                "data_size": data_size,
                "batch_size": batch_size
            },
            user_id=current_user.id
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"数据处理任务失败: {str(e)}"
        )


@router.post("/test/machine-learning")
async def test_ml_job(
    n_samples: int = 5000,
    n_features: int = 15,
    n_classes: int = 3,
    n_models: int = 3,
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """测试机器学习任务"""
    
    # 参数验证
    if n_samples < 100 or n_samples > 20000:
        raise HTTPException(
            status_code=400,
            detail="n_samples必须在100到20000之间"
        )
    
    if n_features < 5 or n_features > 50:
        raise HTTPException(
            status_code=400,
            detail="n_features必须在5到50之间"
        )
    
    if n_classes < 2 or n_classes > 10:
        raise HTTPException(
            status_code=400,
            detail="n_classes必须在2到10之间"
        )
    
    if n_models < 1 or n_models > 5:
        raise HTTPException(
            status_code=400,
            detail="n_models必须在1到5之间"
        )
    
    try:
        result = await ray_service.submit_job(
            job_type="machine_learning",
            parameters={
                "n_samples": n_samples,
                "n_features": n_features,
                "n_classes": n_classes,
                "n_models": n_models
            },
            user_id=current_user.id
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"机器学习任务失败: {str(e)}"
        )


@router.get("/jobs", response_model=List[RayJobHistory])
async def get_job_history(
    limit: int = Query(50, ge=1, le=100, description="返回记录数量限制"),
    offset: int = Query(0, ge=0, description="偏移量"),
    user_id: Optional[int] = Query(None, description="用户ID筛选"),
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """获取Ray任务历史记录"""
    
    try:
        # 如果不是超级用户，只能查看自己的任务历史
        filter_user_id = user_id
        if not current_user.is_superuser:
            filter_user_id = current_user.id
            
        jobs = await ray_service.get_job_history(
            limit=limit,
            offset=offset,
            user_id=filter_user_id
        )
        
        return jobs
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取任务历史失败: {str(e)}"
        )


@router.get("/jobs/{job_id}", response_model=RayJobHistory)
async def get_job_by_id(
    job_id: str,
    current_user: UserModel = Depends(get_current_user),
) -> Any:
    """根据ID获取Ray任务详情"""
    
    try:
        job = await ray_service.get_job_by_id(job_id)
        
        if not job:
            raise HTTPException(
                status_code=404,
                detail=f"未找到任务: {job_id}"
            )
        
        # 如果不是超级用户，只能查看自己的任务
        if not current_user.is_superuser and job.get("user_id") != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="无权访问该任务"
            )
            
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取任务详情失败: {str(e)}"
        )


@router.post("/update-status")
async def update_job_status(
    update_data: JobStatusUpdate,
) -> Any:
    """更新任务状态（从Ray Job装饰器调用，无需认证）"""
    
    try:
        result = await ray_service.update_job_status_from_decorator(
            update_data.model_dump()
        )
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"更新任务状态失败: {str(e)}"
        )
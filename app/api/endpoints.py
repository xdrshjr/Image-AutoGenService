from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from app.services.image_generation import image_service, TaskStatus

router = APIRouter()


class ImageRequest(BaseModel):
    """图像生成请求模型"""
    prompt: str
    seed: Optional[int] = 42


class ImageResponse(BaseModel):
    """图像生成响应模型"""
    image_base64: str
    file_path: str
    prompt: str
    seed: int
    timestamp: str


class TaskCreationResponse(BaseModel):
    """任务创建响应模型"""
    task_id: str
    status: str


class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    id: str
    status: str
    progress: int
    total_steps: int
    prompt: str
    seed: int
    created_at: str
    completed_at: Optional[str] = None
    error: Optional[str] = None


class TaskListResponse(BaseModel):
    """任务列表响应模型"""
    tasks: List[Dict[str, Any]]


@router.post("/generate", response_model=ImageResponse)
async def generate_image(request: ImageRequest):
    """生成图像接口（同步方式，为了兼容性保留）
    
    Args:
        request: 包含提示词和随机种子的请求
        
    Returns:
        生成的图像及相关信息
    """
    try:
        result = image_service.generate_image(
            prompt=request.prompt,
            seed=request.seed
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"图像生成失败: {str(e)}")


@router.post("/generate-async", response_model=TaskCreationResponse)
async def create_generation_task(request: ImageRequest):
    """创建异步图像生成任务
    
    Args:
        request: 包含提示词和随机种子的请求
        
    Returns:
        任务ID和初始状态
    """
    try:
        task_id = image_service.create_task(
            prompt=request.prompt,
            seed=request.seed
        )
        return {
            "task_id": task_id,
            "status": TaskStatus.PENDING.value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str = Path(..., description="任务ID")):
    """获取任务状态
    
    Args:
        task_id: 任务ID
        
    Returns:
        任务状态信息
    """
    task = image_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    
    task_dict = task.to_dict()
    return TaskStatusResponse(
        id=task_dict["id"],
        status=task_dict["status"],
        progress=task_dict["progress"],
        total_steps=task_dict["total_steps"],
        prompt=task_dict["prompt"],
        seed=task_dict["seed"],
        created_at=task_dict["created_at"],
        completed_at=task_dict["completed_at"],
        error=task_dict["error"]
    )


@router.get("/result/{task_id}", response_model=ImageResponse)
async def get_task_result(task_id: str = Path(..., description="任务ID")):
    """获取已完成任务的结果
    
    Args:
        task_id: 任务ID
        
    Returns:
        生成的图像及相关信息
    """
    task = image_service.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    
    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=400, 
            detail=f"任务尚未完成，当前状态: {task.status.value}"
        )
    
    if not task.result:
        raise HTTPException(status_code=500, detail="任务结果为空")
    
    return task.result


@router.get("/tasks", response_model=TaskListResponse)
async def list_tasks(limit: int = 10):
    """列出最近的任务
    
    Args:
        limit: 最大返回数量
        
    Returns:
        任务列表
    """
    tasks = image_service.list_tasks(limit=limit)
    return {"tasks": tasks}


@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "model_loaded": image_service.model_loaded} 
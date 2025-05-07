from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.services.image_generation import image_service

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


@router.post("/generate", response_model=ImageResponse)
async def generate_image(request: ImageRequest):
    """生成图像接口
    
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


@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "ok", "model_loaded": image_service.model_loaded} 
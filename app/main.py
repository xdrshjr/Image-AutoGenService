import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import time

from app.api.endpoints import router as api_router
from app.config import config
from app.services.image_generation import image_service

# 创建FastAPI应用
app = FastAPI(
    title="AI图像生成服务",
    description="基于FLUX模型的AI图像生成服务",
    version="1.0.0",
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加请求处理时间中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# 注册API路由
app.include_router(api_router, prefix="/api")

# 启动时预加载模型
@app.on_event("startup")
async def startup_event():
    # 预加载模型
    print("正在加载模型...")
    image_service.load_model()
    print("模型加载完成！")

@app.get("/")
async def root():
    """根路径，返回服务信息"""
    return {
        "service": "AI图像生成服务",
        "version": "1.0.0",
        "status": "running",
        "api_docs": "/docs",
    }

# 直接运行文件时启动服务
if __name__ == "__main__":
    server_config = config.server
    uvicorn.run(
        "app.main:app",
        host=server_config.host,
        port=server_config.port,
        reload=True,
    ) 
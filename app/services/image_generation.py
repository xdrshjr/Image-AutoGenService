import os
import torch
from diffusers import FluxPipeline
from datetime import datetime
from PIL import Image
from io import BytesIO
import base64
from app.config import config
import uuid
import asyncio
from enum import Enum
from typing import Dict, Optional, List, Callable, Any


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"     # 等待中
    RUNNING = "running"     # 运行中
    COMPLETED = "completed" # 已完成
    FAILED = "failed"       # 失败


class Task:
    """生成任务类"""
    def __init__(self, task_id: str, prompt: str, seed: int):
        self.id = task_id
        self.prompt = prompt
        self.seed = seed
        self.status = TaskStatus.PENDING
        self.progress = 0
        self.total_steps = 0
        self.result = None
        self.error = None
        self.created_at = datetime.now()
        self.completed_at = None
    
    def to_dict(self) -> dict:
        """转换为字典表示"""
        return {
            "id": self.id,
            "prompt": self.prompt,
            "seed": self.seed,
            "status": self.status.value,
            "progress": self.progress,
            "total_steps": self.total_steps,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "result": self.result,
            "error": self.error
        }


class ImageGenerationService:
    """图像生成服务"""
    
    def __init__(self):
        self.pipe = None
        self.model_loaded = False
        self.tasks: Dict[str, Task] = {}
        self.current_task: Optional[Task] = None
        self.is_generating: bool = False
        
    def load_model(self):
        """加载模型和LORA"""
        if self.model_loaded:
            return
        
        model_config = config.model
        
        # 确保输出目录存在
        os.makedirs(model_config.output_dir, exist_ok=True)
        
        # 加载主模型
        self.pipe = FluxPipeline.from_pretrained(
            model_config.model_id, 
            torch_dtype=torch.bfloat16
        )
        
        # 加载LORA
        if model_config.use_lora and model_config.lora:
            self.pipe.load_lora_weights(
                model_config.lora.lora_dir, 
                weight_name=model_config.lora.weight_name
            )
        
        # 启用CPU卸载
        if model_config.use_cpu_offload:
            self.pipe.enable_model_cpu_offload()
            
        self.model_loaded = True
        print(f"模型已加载: {model_config.model_id}")
        if model_config.use_lora and model_config.lora:
            print(f"LORA已加载: {model_config.lora.lora_dir}/{model_config.lora.weight_name}")
    
    def create_task(self, prompt: str, seed: int = 42) -> str:
        """创建新的图像生成任务
        
        Args:
            prompt: 提示词
            seed: 随机种子
            
        Returns:
            str: 任务ID
        """
        task_id = str(uuid.uuid4())
        task = Task(task_id, prompt, seed)
        self.tasks[task_id] = task
        
        # 启动任务处理
        asyncio.create_task(self._process_task(task))
        
        return task_id
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            Optional[Task]: 任务对象，如果找不到则返回None
        """
        return self.tasks.get(task_id)
    
    def list_tasks(self, limit: int = 10) -> List[dict]:
        """列出最近的任务
        
        Args:
            limit: 最大返回数量
            
        Returns:
            List[dict]: 任务列表
        """
        # 按创建时间排序，最新的优先
        sorted_tasks = sorted(
            self.tasks.values(), 
            key=lambda t: t.created_at, 
            reverse=True
        )
        return [task.to_dict() for task in sorted_tasks[:limit]]
    
    def _diffusion_callback(self, step: int, timestep: int, latents: torch.FloatTensor) -> None:
        """扩散模型步骤回调函数
        
        Args:
            step: 当前步骤
            timestep: 当前时间步
            latents: 潜在空间张量
        """
        if self.current_task:
            self.current_task.progress = step
            print(f"生成进度: {step}/{self.current_task.total_steps} ({step/self.current_task.total_steps*100:.1f}%)")
    
    async def _update_progress(self, task: Task):
        """更新任务进度的异步任务
        
        由于无法使用回调，我们使用定时更新的方式来模拟进度
        """
        if not task or not task.total_steps:
            return
            
        # 每500毫秒更新一次进度，模拟实际进展
        step_increment = max(1, task.total_steps // 20)  # 约5%的步骤增量
        
        while (self.is_generating and 
               task.status == TaskStatus.RUNNING and 
               task.progress < task.total_steps):
            # 增加进度，但不超过总步数
            task.progress = min(task.progress + step_increment, task.total_steps - 1)
            
            # 打印进度
            print(f"生成进度: {task.progress}/{task.total_steps} ({task.progress/task.total_steps*100:.1f}%)")
            
            # 等待一段时间
            await asyncio.sleep(0.5)

    async def _process_task(self, task: Task) -> None:
        """处理图像生成任务
        
        Args:
            task: 任务对象
        """
        # 更新任务状态
        task.status = TaskStatus.RUNNING
        self.current_task = task
        self.is_generating = True
        
        try:
            if not self.model_loaded:
                self.load_model()
            
            model_config = config.model
            
            # 设置总步数
            task.total_steps = model_config.num_inference_steps
            
            # 启动进度更新任务
            update_task = asyncio.create_task(self._update_progress(task))
            
            # 生成图像 - 移除不支持的callback和callback_steps参数
            image = self.pipe(
                task.prompt,
                output_type="pil",
                num_inference_steps=model_config.num_inference_steps,
                generator=torch.Generator("cpu").manual_seed(task.seed)
            ).images[0]
            
            # 生成完成，停止更新进度
            self.is_generating = False
            
            # 等待进度更新任务完成
            if not update_task.done():
                update_task.cancel()
            
            # 任务完成，设置进度为最大值
            task.progress = task.total_steps
            
            # 保存图像
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(model_config.output_dir, f"{timestamp}.jpg")
            image.save(output_file)
            
            # 转换为base64
            buffered = BytesIO()
            image.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
            
            # 更新任务结果
            task.result = {
                "image_base64": img_str,
                "file_path": output_file,
                "prompt": task.prompt,
                "seed": task.seed,
                "timestamp": timestamp
            }
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            
        except Exception as e:
            # 处理错误
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            print(f"任务失败: {task.id}, 错误: {str(e)}")
        
        finally:
            # 确保进度更新停止
            self.is_generating = False
            # 清除当前任务引用
            if self.current_task and self.current_task.id == task.id:
                self.current_task = None
    
    def generate_image(self, prompt: str, seed: int = 42) -> dict:
        """生成图像 (同步方式，为了兼容性保留)
        
        Args:
            prompt: 提示词
            seed: 随机种子
            
        Returns:
            dict: 包含图像和元数据的字典
        """
        if not self.model_loaded:
            self.load_model()
        
        model_config = config.model
        
        # 生成图像
        image = self.pipe(
            prompt,
            output_type="pil",
            num_inference_steps=model_config.num_inference_steps,
            generator=torch.Generator("cpu").manual_seed(seed)
        ).images[0]
        
        # 保存图像
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(model_config.output_dir, f"{timestamp}.jpg")
        image.save(output_file)
        
        # 转换为base64
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return {
            "image_base64": img_str,
            "file_path": output_file,
            "prompt": prompt,
            "seed": seed,
            "timestamp": timestamp
        }


# 全局服务实例
image_service = ImageGenerationService() 
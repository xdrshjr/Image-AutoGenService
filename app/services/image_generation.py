import os
import torch
from diffusers import FluxPipeline
from datetime import datetime
from PIL import Image
from io import BytesIO
import base64
from app.config import config


class ImageGenerationService:
    """图像生成服务"""
    
    def __init__(self):
        self.pipe = None
        self.model_loaded = False
        
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
    
    def generate_image(self, prompt: str, seed: int = 42) -> dict:
        """生成图像
        
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